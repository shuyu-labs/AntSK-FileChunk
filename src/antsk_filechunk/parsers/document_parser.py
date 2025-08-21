"""
文档解析器模块
支持Word和PDF文档的内容提取和结构化处理
"""

import os
import re
import logging
from typing import List, Dict, Optional, Union
from pathlib import Path
from dataclasses import dataclass

import fitz  # PyMuPDF
from docx import Document as DocxDocument
from docx.document import Document as DocxDocumentType
from docx.text.paragraph import Paragraph
from docx.table import Table
import chardet

logger = logging.getLogger(__name__)

@dataclass
class DocumentContent:
    """文档内容数据结构"""
    paragraphs: List[Dict]  # 段落列表，每个段落包含内容和元数据
    tables: List[Dict]      # 表格列表
    images: List[Dict]      # 图片信息列表
    metadata: Dict          # 文档元数据
    structure: Dict         # 文档结构信息

class DocumentParser:
    """文档解析器主类"""
    
    def __init__(self):
        """初始化文档解析器"""
        self.supported_formats = {'.pdf', '.docx', '.doc', '.txt'}
        
    def parse_file(self, file_path: Union[str, Path]) -> DocumentContent:
        """
        解析文档文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            文档内容对象
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_extension = file_path.suffix.lower()
        
        if file_extension not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {file_extension}")
        
        logger.info(f"开始解析文件: {file_path} (格式: {file_extension})")
        
        try:
            if file_extension == '.pdf':
                return self._parse_pdf(file_path)
            elif file_extension in ['.docx', '.doc']:
                return self._parse_docx(file_path)
            elif file_extension == '.txt':
                return self._parse_txt(file_path)
            else:
                raise ValueError(f"未实现的文件格式处理: {file_extension}")
                
        except Exception as e:
            logger.error(f"文件解析失败: {e}")
            raise
    
    def _parse_pdf(self, file_path: Path) -> DocumentContent:
        """
        解析PDF文件
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            文档内容对象
        """
        paragraphs = []
        tables = []
        images = []
        
        try:
            doc = fitz.open(str(file_path))
            
            # 获取文档元数据
            metadata = self._extract_pdf_metadata(doc)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 提取文本内容
                page_paragraphs = self._extract_pdf_paragraphs(page, page_num)
                paragraphs.extend(page_paragraphs)
                
                # 提取表格（如果需要）
                page_tables = self._extract_pdf_tables(page, page_num)
                tables.extend(page_tables)
                
                # 提取图片信息
                page_images = self._extract_pdf_images(page, page_num)
                images.extend(page_images)
            
            doc.close()
            
            # 后处理段落
            paragraphs = self._postprocess_paragraphs(paragraphs)
            
            # 构建文档结构
            structure = self._build_document_structure(paragraphs, tables, images)
            
            return DocumentContent(
                paragraphs=paragraphs,
                tables=tables,
                images=images,
                metadata=metadata,
                structure=structure
            )
            
        except Exception as e:
            logger.error(f"PDF解析失败: {e}")
            raise
    
    def _extract_pdf_metadata(self, doc) -> Dict:
        """提取PDF元数据"""
        metadata = doc.metadata or {}
        return {
            'title': metadata.get('title', ''),
            'author': metadata.get('author', ''),
            'subject': metadata.get('subject', ''),
            'creator': metadata.get('creator', ''),
            'producer': metadata.get('producer', ''),
            'creation_date': metadata.get('creationDate', ''),
            'modification_date': metadata.get('modDate', ''),
            'page_count': len(doc),
            'format': 'PDF'
        }
    
    def _extract_pdf_paragraphs(self, page, page_num: int) -> List[Dict]:
        """从PDF页面提取段落"""
        paragraphs = []
        
        # 获取文本块
        blocks = page.get_text("dict")["blocks"]
        
        for block_num, block in enumerate(blocks):
            if "lines" not in block:
                continue
            
            # 合并同一块中的所有行
            block_text = ""
            font_info = []
            
            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text:
                        line_text += text + " "
                        font_info.append({
                            'font': span.get('font', ''),
                            'size': span.get('size', 0),
                            'flags': span.get('flags', 0)
                        })
                
                if line_text.strip():
                    block_text += line_text.strip() + "\n"
            
            block_text = block_text.strip()
            
            if block_text and len(block_text) > 10:  # 过滤过短的文本块
                # 判断是否为标题
                is_heading = self._is_heading_pdf(block_text, font_info)
                
                paragraphs.append({
                    'content': block_text,
                    'page': page_num + 1,
                    'block': block_num,
                    'type': 'heading' if is_heading else 'paragraph',
                    'font_info': font_info,
                    'bbox': block.get('bbox', [])
                })
        
        return paragraphs
    
    def _extract_pdf_tables(self, page, page_num: int) -> List[Dict]:
        """从PDF页面提取表格（简化版）"""
        tables = []
        
        try:
            # 这里可以集成更专业的表格提取库，如 tabula-py 或 camelot
            # 暂时返回空列表，表示检测到的表格区域
            pass
        except Exception as e:
            logger.warning(f"页面 {page_num + 1} 表格提取失败: {e}")
        
        return tables
    
    def _extract_pdf_images(self, page, page_num: int) -> List[Dict]:
        """从PDF页面提取图片信息"""
        images = []
        
        try:
            image_list = page.get_images()
            for img_index, img in enumerate(image_list):
                images.append({
                    'page': page_num + 1,
                    'index': img_index,
                    'xref': img[0],
                    'bbox': img[1:5] if len(img) > 4 else [],
                    'type': 'image'
                })
        except Exception as e:
            logger.warning(f"页面 {page_num + 1} 图片提取失败: {e}")
        
        return images
    
    def _is_heading_pdf(self, text: str, font_info: List[Dict]) -> bool:
        """判断PDF文本是否为标题"""
        if not font_info:
            return False
        
        # 简单的标题判断逻辑
        # 1. 文本较短
        if len(text) > 100:
            return False
        
        # 2. 字体较大或加粗
        avg_size = sum(f.get('size', 0) for f in font_info) / len(font_info)
        has_bold = any(f.get('flags', 0) & 2**4 for f in font_info)  # 粗体标志
        
        if avg_size > 14 or has_bold:
            return True
        
        # 3. 数字开头（如"1. 标题"）
        if re.match(r'^\d+\.?\s', text.strip()):
            return True
        
        return False
    
    def _parse_docx(self, file_path: Path) -> DocumentContent:
        """
        解析Word文档
        
        Args:
            file_path: Word文档路径
            
        Returns:
            文档内容对象
        """
        paragraphs = []
        tables = []
        images = []
        
        try:
            doc = DocxDocument(str(file_path))
            
            # 获取文档元数据
            metadata = self._extract_docx_metadata(doc)
            
            # 处理文档内容
            for element in doc.element.body:
                if element.tag.endswith('p'):  # 段落
                    para = Paragraph(element, doc)
                    para_data = self._extract_docx_paragraph(para, len(paragraphs))
                    if para_data and para_data['content'].strip():
                        paragraphs.append(para_data)
                
                elif element.tag.endswith('tbl'):  # 表格
                    table = Table(element, doc)
                    table_data = self._extract_docx_table(table, len(tables))
                    if table_data:
                        tables.append(table_data)
            
            # 提取图片信息
            images = self._extract_docx_images(doc)
            
            # 后处理段落
            paragraphs = self._postprocess_paragraphs(paragraphs)
            
            # 构建文档结构
            structure = self._build_document_structure(paragraphs, tables, images)
            
            return DocumentContent(
                paragraphs=paragraphs,
                tables=tables,
                images=images,
                metadata=metadata,
                structure=structure
            )
            
        except Exception as e:
            logger.error(f"Word文档解析失败: {e}")
            raise
    
    def _extract_docx_metadata(self, doc: DocxDocumentType) -> Dict:
        """提取Word文档元数据"""
        core_props = doc.core_properties
        return {
            'title': core_props.title or '',
            'author': core_props.author or '',
            'subject': core_props.subject or '',
            'keywords': core_props.keywords or '',
            'comments': core_props.comments or '',
            'created': str(core_props.created) if core_props.created else '',
            'modified': str(core_props.modified) if core_props.modified else '',
            'format': 'DOCX'
        }
    
    def _extract_docx_paragraph(self, paragraph: Paragraph, index: int) -> Optional[Dict]:
        """提取Word段落信息"""
        text = paragraph.text.strip()
        
        if not text:
            return None
        
        # 判断段落类型
        para_type = 'paragraph'
        if paragraph.style.name.startswith('Heading'):
            para_type = 'heading'
        elif paragraph.style.name in ['Title', 'Subtitle']:
            para_type = 'title'
        
        return {
            'content': text,
            'index': index,
            'type': para_type,
            'style': paragraph.style.name,
            'level': self._get_heading_level(paragraph.style.name),
        }
    
    def _extract_docx_table(self, table: Table, index: int) -> Dict:
        """提取Word表格信息"""
        table_data = []
        
        for row in table.rows:
            row_data = []
            for cell in row.cells:
                cell_text = cell.text.strip()
                row_data.append(cell_text)
            table_data.append(row_data)
        
        return {
            'index': index,
            'data': table_data,
            'rows': len(table.rows),
            'cols': len(table.columns) if table.rows else 0,
            'type': 'table'
        }
    
    def _extract_docx_images(self, doc: DocxDocumentType) -> List[Dict]:
        """提取Word文档中的图片信息"""
        images = []
        
        try:
            # 简化的图片信息提取
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    images.append({
                        'target': rel.target_ref,
                        'type': 'image'
                    })
        except Exception as e:
            logger.warning(f"图片信息提取失败: {e}")
        
        return images
    
    def _get_heading_level(self, style_name: str) -> int:
        """获取标题级别"""
        if 'Heading' in style_name:
            try:
                level = int(re.search(r'Heading (\d+)', style_name).group(1))
                return level
            except:
                return 1
        return 0
    
    def _parse_txt(self, file_path: Path) -> DocumentContent:
        """
        解析纯文本文件
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            文档内容对象
        """
        paragraphs = []
        
        try:
            # 检测文件编码
            with open(file_path, 'rb') as f:
                raw_data = f.read()
                encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'
            
            # 读取文本内容
            with open(file_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            # 按空行分割段落
            para_texts = re.split(r'\n\s*\n', content)
            
            for i, para_text in enumerate(para_texts):
                para_text = para_text.strip()
                if para_text and len(para_text) > 10:
                    paragraphs.append({
                        'content': para_text,
                        'index': i,
                        'type': 'paragraph',
                        'line_start': 0,  # 简化处理
                        'line_end': 0
                    })
            
            metadata = {
                'title': file_path.stem,
                'format': 'TXT',
                'encoding': encoding,
                'size': len(content)
            }
            
            structure = self._build_document_structure(paragraphs, [], [])
            
            return DocumentContent(
                paragraphs=paragraphs,
                tables=[],
                images=[],
                metadata=metadata,
                structure=structure
            )
            
        except Exception as e:
            logger.error(f"文本文件解析失败: {e}")
            raise
    
    def _postprocess_paragraphs(self, paragraphs: List[Dict]) -> List[Dict]:
        """
        后处理段落列表
        
        Args:
            paragraphs: 原始段落列表
            
        Returns:
            处理后的段落列表
        """
        processed = []
        
        for para in paragraphs:
            content = para['content']
            
            # 清理内容
            content = self._clean_paragraph_content(content)
            
            # 过滤空内容
            if not content.strip():
                continue
            
            # 过滤过短的段落
            if len(content.strip()) < 10:
                continue
            
            para['content'] = content
            processed.append(para)
        
        return processed
    
    def _clean_paragraph_content(self, content: str) -> str:
        """清理段落内容"""
        # 移除多余的空白字符
        content = re.sub(r'\s+', ' ', content)
        
        # 移除页眉页脚常见模式
        patterns_to_remove = [
            r'^第\s*\d+\s*页.*$',  # 页码
            r'^\d+\s*$',          # 纯数字行
            r'^[-=_]{3,}$',       # 分隔线
        ]
        
        for pattern in patterns_to_remove:
            if re.match(pattern, content.strip()):
                return ''
        
        return content.strip()
    
    def _build_document_structure(
        self, 
        paragraphs: List[Dict], 
        tables: List[Dict], 
        images: List[Dict]
    ) -> Dict:
        """构建文档结构信息"""
        structure = {
            'paragraph_count': len(paragraphs),
            'table_count': len(tables),
            'image_count': len(images),
            'headings': [],
            'sections': []
        }
        
        # 提取标题信息
        current_section = {'title': '', 'level': 0, 'start_index': 0, 'paragraphs': []}
        
        for i, para in enumerate(paragraphs):
            if para.get('type') == 'heading':
                # 如果当前章节有内容，保存它
                if current_section['paragraphs']:
                    structure['sections'].append(current_section)
                
                # 开始新章节
                level = para.get('level', 1)
                current_section = {
                    'title': para['content'],
                    'level': level,
                    'start_index': i,
                    'paragraphs': []
                }
                
                structure['headings'].append({
                    'text': para['content'],
                    'level': level,
                    'index': i
                })
            else:
                current_section['paragraphs'].append(i)
        
        # 保存最后一个章节
        if current_section['paragraphs']:
            structure['sections'].append(current_section)
        
        return structure
