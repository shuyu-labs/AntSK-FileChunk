"""
FastAPI应用程序 - AntSK文件切片服务API
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
import uvicorn
import numpy as np

from src.antsk_filechunk.enhanced_semantic_chunker import SemanticChunker, ChunkConfig, TextChunk

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_convert_numeric(value):
    """安全转换数值类型，确保可以序列化"""
    if isinstance(value, (np.float32, np.float64)):
        return float(value)
    elif isinstance(value, (np.int32, np.int64)):
        return int(value)
    elif isinstance(value, np.ndarray):
        return value.tolist()
    elif isinstance(value, dict):
        # 递归处理字典中的值
        return {k: safe_convert_numeric(v) for k, v in value.items()}
    elif isinstance(value, list):
        # 递归处理列表中的值
        return [safe_convert_numeric(item) for item in value]
    return value

# 创建FastAPI应用
app = FastAPI(
    title="AntSK文件切片服务",
    description="基于语义理解的智能文本切片API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 创建必要的目录
from pathlib import Path
Path("temp").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
Path("templates").mkdir(exist_ok=True)

# 设置静态文件和模板
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 全局切片器实例
chunker = None

class ChunkConfigRequest(BaseModel):
    """切片配置请求模型"""
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
    """切片结果响应模型"""
    content: str = Field(description="切片内容")
    start_pos: int = Field(description="起始位置")
    end_pos: int = Field(description="结束位置")
    semantic_score: float = Field(description="语义连贯性得分")
    token_count: int = Field(description="Token数量")
    paragraph_indices: List[int] = Field(description="包含的段落索引")
    chunk_type: str = Field(description="切片类型")
    metadata: Dict = Field(description="元数据信息")

class ProcessResponse(BaseModel):
    """处理结果响应模型"""
    success: bool = Field(description="是否成功")
    message: str = Field(description="响应消息")
    chunks: List[ChunkResponse] = Field(description="切片结果列表")
    total_chunks: int = Field(description="切片总数")
    processing_time: float = Field(description="处理时间（秒）")
    file_info: Dict = Field(description="文件信息")

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global chunker
    try:
        logger.info("正在初始化语义切片器...")
        chunker = SemanticChunker()
        logger.info("语义切片器初始化完成")
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        raise

@app.get("/", response_class=HTMLResponse)
async def root():
    """根路径重定向到主页"""
    return FileResponse("home.html")

@app.get("/home", response_class=HTMLResponse)
async def home():
    """主页 - 产品介绍页面"""
    return FileResponse("home.html")

@app.get("/chunker", response_class=HTMLResponse)
async def chunker():
    """文档切片工具页面"""
    return FileResponse("chunker.html")

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "AntSK文件切片服务"}

@app.post("/api/process-file", response_model=ProcessResponse)
async def process_file(
    file: UploadFile = File(..., description="上传的文件（支持PDF、Word格式）"),
    config: Optional[str] = Form(None, description="切片配置JSON字符串（可选）")
):
    """
    处理上传的文件，进行语义切片
    """
    import time
    start_time = time.time()
    
    try:
        # 检查文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.pdf', '.docx', '.doc', '.txt']:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式: {file_ext}，支持格式: .pdf, .docx, .doc, .txt"
            )
        
        # 解析配置
        chunk_config = ChunkConfig()
        if config:
            try:
                config_dict = json.loads(config)
                config_request = ChunkConfigRequest(**config_dict)
                chunk_config = ChunkConfig(
                    min_chunk_size=config_request.min_chunk_size,
                    max_chunk_size=config_request.max_chunk_size,
                    target_chunk_size=config_request.target_chunk_size,
                    overlap_ratio=config_request.overlap_ratio,
                    semantic_threshold=config_request.semantic_threshold,
                    paragraph_merge_threshold=config_request.paragraph_merge_threshold,
                    language=config_request.language,
                    preserve_structure=config_request.preserve_structure,
                    handle_special_content=config_request.handle_special_content
                )
            except Exception as e:
                logger.warning(f"配置解析失败，使用默认配置: {e}")
        
        # 更新切片器配置
        chunker.config = chunk_config
        
        # 保存临时文件
        temp_dir = Path("temp")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / file.filename
        
        with open(temp_file, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # 处理文件
        chunks = chunker.process_file(str(temp_file))
        
        # 清理临时文件
        temp_file.unlink(missing_ok=True)
        
        # 转换为响应格式
        chunk_responses = []
        for chunk in chunks:
            chunk_response = ChunkResponse(
                content=chunk.content,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                semantic_score=safe_convert_numeric(chunk.semantic_score),
                token_count=safe_convert_numeric(chunk.token_count),
                paragraph_indices=chunk.paragraph_indices,
                chunk_type=chunk.chunk_type,
                metadata=safe_convert_numeric(chunk.metadata)  # 转换metadata
            )
            chunk_responses.append(chunk_response)
        
        processing_time = time.time() - start_time
        
        return ProcessResponse(
            success=True,
            message="文件处理成功",
            chunks=chunk_responses,
            total_chunks=len(chunks),
            processing_time=processing_time,
            file_info={
                "filename": file.filename,
                "size": len(content),
                "type": file_ext,
                "content_type": file.content_type
            }
        )
        
    except Exception as e:
        logger.error(f"文件处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")

@app.post("/api/process-text", response_model=ProcessResponse)
async def process_text(
    text: str = Form(..., description="要处理的文本内容"),
    config: Optional[str] = Form(None, description="切片配置JSON字符串（可选）")
):
    """
    直接处理文本内容，进行语义切片
    """
    import time
    start_time = time.time()
    
    try:
        if not text.strip():
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 解析配置
        chunk_config = ChunkConfig()
        if config:
            try:
                config_dict = json.loads(config)
                config_request = ChunkConfigRequest(**config_dict)
                chunk_config = ChunkConfig(
                    min_chunk_size=config_request.min_chunk_size,
                    max_chunk_size=config_request.max_chunk_size,
                    target_chunk_size=config_request.target_chunk_size,
                    overlap_ratio=config_request.overlap_ratio,
                    semantic_threshold=config_request.semantic_threshold,
                    paragraph_merge_threshold=config_request.paragraph_merge_threshold,
                    language=config_request.language,
                    preserve_structure=config_request.preserve_structure,
                    handle_special_content=config_request.handle_special_content
                )
            except Exception as e:
                logger.warning(f"配置解析失败，使用默认配置: {e}")
        
        # 更新切片器配置
        chunker.config = chunk_config
        
        # 处理文本
        chunks = chunker.process_text(text)
        
        # 转换为响应格式
        chunk_responses = []
        for chunk in chunks:
            chunk_response = ChunkResponse(
                content=chunk.content,
                start_pos=chunk.start_pos,
                end_pos=chunk.end_pos,
                semantic_score=safe_convert_numeric(chunk.semantic_score),
                token_count=safe_convert_numeric(chunk.token_count),
                paragraph_indices=chunk.paragraph_indices,
                chunk_type=chunk.chunk_type,
                metadata=safe_convert_numeric(chunk.metadata)  # 转换metadata
            )
            chunk_responses.append(chunk_response)
        
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
                "encoding": "utf-8"
            }
        )
        
    except Exception as e:
        logger.error(f"文本处理失败: {e}")
        raise HTTPException(status_code=500, detail=f"文本处理失败: {str(e)}")

@app.get("/api/config/default", response_model=ChunkConfigRequest)
async def get_default_config():
    """获取默认切片配置"""
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
        handle_special_content=config.handle_special_content
    )

if __name__ == "__main__":
    # 创建必要的目录
    Path("temp").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    Path("templates").mkdir(exist_ok=True)
    
    # 启动服务
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
