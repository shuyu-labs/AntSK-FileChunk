"""
FastAPI application for the AntSK semantic chunking service.
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.antsk_filechunk.enhanced_semantic_chunker import (
    ChunkConfig,
    EnhancedSemanticChunker,
)
from src.antsk_filechunk.semantic_analyzer import SemanticAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
STATIC_DIR = Path("static")
TEMPLATES_DIR = Path("templates")
SUPPORTED_FORMATS = [".pdf", ".docx", ".txt", ".xlsx", ".xls", ".pptx"]
IMAGE_BASE_URL = os.getenv("IMAGE_BASE_URL")

for directory in (TEMP_DIR, STATIC_DIR, TEMPLATES_DIR):
    directory.mkdir(exist_ok=True)

app = FastAPI(
    title="AntSK文件切片服务",
    description="基于语义理解的智能文本切片 API 服务",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.mount("/static", StaticFiles(directory="static"), name="static")

service_chunker: Optional[EnhancedSemanticChunker] = None


def safe_convert_numeric(value):
    """Convert numpy values so they can be serialized by FastAPI."""
    if isinstance(value, (np.float32, np.float64)):
        return float(value)
    if isinstance(value, (np.int32, np.int64)):
        return int(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {key: safe_convert_numeric(item) for key, item in value.items()}
    if isinstance(value, list):
        return [safe_convert_numeric(item) for item in value]
    return value


class ChunkConfigRequest(BaseModel):
    min_chunk_size: int = Field(default=200, ge=50, le=1000, description="最小切片字符数")
    max_chunk_size: int = Field(default=1500, ge=500, le=5000, description="最大切片字符数")
    target_chunk_size: int = Field(default=800, ge=200, le=2000, description="目标切片字符数")
    overlap_ratio: float = Field(default=0.1, ge=0.0, le=0.5, description="重叠比例")
    semantic_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="语义相似度阈值")
    paragraph_merge_threshold: float = Field(default=0.8, ge=0.0, le=1.0, description="段落合并阈值")
    language: str = Field(default="zh", pattern="^(zh|en)$", description="语言设置")
    preserve_structure: bool = Field(default=True, description="是否保持文档结构")
    handle_special_content: bool = Field(default=True, description="是否处理特殊内容")


class ChunkResponse(BaseModel):
    content: str = Field(description="切片内容")
    start_pos: int = Field(description="起始位置")
    end_pos: int = Field(description="结束位置")
    semantic_score: float = Field(description="语义连贯得分")
    token_count: int = Field(description="Token 数量")
    paragraph_indices: List[int] = Field(description="包含的段落索引")
    chunk_type: str = Field(description="切片类型")
    metadata: Dict = Field(description="元数据")
    has_table: bool = Field(default=False, description="是否包含表格")
    has_image: bool = Field(default=False, description="是否包含图片")
    element_count: int = Field(default=0, description="包含的元素数量")
    content_types: List[str] = Field(default_factory=list, description="内容类型列表")


class ProcessResponse(BaseModel):
    success: bool = Field(description="是否成功")
    message: str = Field(description="响应消息")
    chunks: List[ChunkResponse] = Field(description="切片结果列表")
    total_chunks: int = Field(description="切片总数")
    processing_time: float = Field(description="处理耗时，单位秒")
    file_info: Dict = Field(description="文件信息")
    document_summary: Dict = Field(default_factory=dict, description="文档摘要信息")
    extraction_info: Dict = Field(default_factory=dict, description="提取统计信息")


def parse_chunk_config(config_payload: Optional[str]) -> ChunkConfig:
    """Parse request config once and keep API logic simple."""
    if not config_payload:
        return ChunkConfig()

    try:
        config_dict = json.loads(config_payload)
        request_config = ChunkConfigRequest(**config_dict)
        return ChunkConfig(
            min_chunk_size=request_config.min_chunk_size,
            max_chunk_size=request_config.max_chunk_size,
            target_chunk_size=request_config.target_chunk_size,
            overlap_ratio=request_config.overlap_ratio,
            semantic_threshold=request_config.semantic_threshold,
            paragraph_merge_threshold=request_config.paragraph_merge_threshold,
            language=request_config.language,
            preserve_structure=request_config.preserve_structure,
            handle_special_content=request_config.handle_special_content,
        )
    except Exception as exc:
        logger.warning("Failed to parse config, using defaults: %s", exc)
        return ChunkConfig()


def build_image_base_url(request: Request) -> str:
    if IMAGE_BASE_URL:
        return IMAGE_BASE_URL

    host = request.headers.get("host", "localhost:8000")
    return f"{request.url.scheme}://{host}"


def build_request_chunker(config: ChunkConfig, image_base_url: str) -> EnhancedSemanticChunker:
    """Create a request-scoped chunker without sharing mutable runtime config."""
    model_name = service_chunker.model_name if service_chunker is not None else "all-MiniLM-L6-v2"
    return EnhancedSemanticChunker(
        config=config,
        model_name=model_name,
        image_base_url=image_base_url,
    )


async def save_upload_to_temp(upload: UploadFile) -> Tuple[Path, int]:
    """Stream upload content to disk to avoid loading the whole file in memory."""
    original_name = Path(upload.filename or "upload.bin").name
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}_{original_name}"
    total_size = 0

    with temp_path.open("wb") as output_file:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total_size += len(chunk)
            output_file.write(chunk)

    await upload.seek(0)
    return temp_path, total_size


def build_chunk_responses(chunks) -> Tuple[List[ChunkResponse], int, int]:
    chunk_responses: List[ChunkResponse] = []
    total_tables = 0
    total_images = 0

    for chunk in chunks:
        chunk_metadata = chunk.metadata or {}
        has_table = bool(chunk_metadata.get("has_table", False))
        has_image = bool(chunk_metadata.get("has_image", False))
        element_count = int(chunk_metadata.get("element_count", 0))

        if has_table:
            total_tables += 1
        if has_image:
            total_images += 1

        if chunk.chunk_type == "table_content":
            content_types = ["table"]
        elif chunk.chunk_type == "image_content":
            content_types = ["image"]
        elif chunk.chunk_type == "mixed_content":
            content_types = ["text", "table", "image"]
        else:
            content_types = ["text"]

        chunk_responses.append(
            ChunkResponse(
                content=chunk.content,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                semantic_score=safe_convert_numeric(chunk.semantic_score),
                token_count=safe_convert_numeric(chunk.token_count),
                paragraph_indices=chunk.paragraph_indices,
                chunk_type=chunk.chunk_type,
                metadata=safe_convert_numeric(chunk.metadata),
                has_table=has_table,
                has_image=has_image,
                element_count=element_count,
                content_types=content_types,
            )
        )

    return chunk_responses, total_tables, total_images


@app.on_event("startup")
async def startup_event():
    global service_chunker
    try:
        logger.info("Initializing semantic chunker service...")
        service_chunker = EnhancedSemanticChunker(
            image_base_url=IMAGE_BASE_URL or "http://localhost:8000"
        )
        logger.info("Semantic chunker service is ready")
    except Exception as exc:
        logger.error("Failed to initialize chunker service: %s", exc)
        raise


@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse("home.html")


@app.get("/home", response_class=HTMLResponse)
async def home():
    return FileResponse("home.html")


@app.get("/chunker", response_class=HTMLResponse)
async def chunker_page():
    return FileResponse("chunker.html")


@app.get("/health")
async def health_check():
    chunker_health = service_chunker.health_check() if service_chunker is not None else {}
    return {
        "status": "healthy",
        "service": "AntSK文件切片服务",
        "model_cache": SemanticAnalyzer.get_cache_stats(),
        "chunker": chunker_health,
    }


@app.post("/api/process-file", response_model=ProcessResponse)
async def process_file(
    request: Request,
    file: UploadFile = File(..., description="上传的文件，支持 PDF、Word、Excel、PPT、TXT"),
    config: Optional[str] = Form(None, description="切片配置 JSON 字符串，可选"),
):
    start_time = time.time()
    temp_file: Optional[Path] = None

    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file_ext}，支持格式: {', '.join(SUPPORTED_FORMATS)}",
            )

        chunk_config = parse_chunk_config(config)
        image_base_url = build_image_base_url(request)
        request_chunker = build_request_chunker(chunk_config, image_base_url)

        temp_file, file_size = await save_upload_to_temp(file)
        chunks = request_chunker.process_file_safe(str(temp_file))
        chunk_responses, total_tables, total_images = build_chunk_responses(chunks)

        processing_time = time.time() - start_time
        return ProcessResponse(
            success=True,
            message="文件处理成功",
            chunks=chunk_responses,
            total_chunks=len(chunks),
            processing_time=processing_time,
            file_info={
                "filename": file.filename,
                "size": file_size,
                "type": file_ext,
                "content_type": file.content_type,
            },
            document_summary={
                "total_paragraphs": sum(
                    1 for chunk in chunks if chunk.chunk_type in ["text_content", "mixed_content"]
                ),
                "total_tables": total_tables,
                "total_images": total_images,
                "chunk_types": sorted({chunk.chunk_type for chunk in chunks}),
            },
            extraction_info={
                "chunks_with_tables": total_tables,
                "chunks_with_images": total_images,
                "average_chunk_size": (
                    sum(chunk.token_count for chunk in chunks) / len(chunks) if chunks else 0
                ),
                "supported_formats": SUPPORTED_FORMATS,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("File processing failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"文件处理失败: {exc}")
    finally:
        if temp_file is not None:
            temp_file.unlink(missing_ok=True)
        await file.close()


@app.post("/api/process-text", response_model=ProcessResponse)
async def process_text(
    request: Request,
    text: str = Form(..., description="需要处理的文本内容"),
    config: Optional[str] = Form(None, description="切片配置 JSON 字符串，可选"),
):
    start_time = time.time()

    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本内容不能为空")

        chunk_config = parse_chunk_config(config)
        request_chunker = build_request_chunker(chunk_config, build_image_base_url(request))
        chunks = request_chunker.process_text_enhanced(text)
        chunk_responses, _, _ = build_chunk_responses(chunks)

        processing_time = time.time() - start_time
        return ProcessResponse(
            success=True,
            message="文本处理成功",
            chunks=chunk_responses,
            total_chunks=len(chunks),
            processing_time=processing_time,
            file_info={
                "type": "text",
                "size": len(text),
                "encoding": "utf-8",
            },
            document_summary={
                "total_paragraphs": len(chunks),
                "total_tables": 0,
                "total_images": 0,
                "chunk_types": sorted({chunk.chunk_type for chunk in chunks}) or ["text_content"],
            },
            extraction_info={
                "chunks_with_tables": 0,
                "chunks_with_images": 0,
                "average_chunk_size": (
                    sum(chunk.token_count for chunk in chunks) / len(chunks) if chunks else 0
                ),
                "supported_formats": SUPPORTED_FORMATS,
            },
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Text processing failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"文本处理失败: {exc}")


@app.get("/api/config/default", response_model=ChunkConfigRequest)
async def get_default_config():
    config = ChunkConfig()
    return ChunkConfigRequest(
        min_chunk_size=config.min_chunk_size,
        max_chunk_size=config.max_chunk_size,
        target_chunk_size=config.target_chunk_size,
        overlap_ratio=config.overlap_ratio,
        semantic_threshold=config.semantic_threshold,
        paragraph_merge_threshold=config.paragraph_merge_threshold,
        language=config.language,
        preserve_structure=config.preserve_structure,
        handle_special_content=config.handle_special_content,
    )


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
