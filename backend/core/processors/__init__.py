"""
文件处理模块

支持:
- 多格式文件解析 (txt, csv, json, pdf, docx, xlsx等)
- 压缩包穿透解压
- 大文件分片处理
- 流式读取
"""

from .file_processor import FileProcessor, ProcessedFile
from .extractors import (
    BaseExtractor,
    TextExtractor,
    CsvExtractor,
    JsonExtractor,
    PdfExtractor,
    DocxExtractor,
    XlsxExtractor,
    HtmlExtractor,
)
from .archive_handler import ArchiveHandler

__all__ = [
    "FileProcessor",
    "ProcessedFile",
    "BaseExtractor",
    "TextExtractor",
    "CsvExtractor",
    "JsonExtractor",
    "PdfExtractor",
    "DocxExtractor",
    "XlsxExtractor",
    "HtmlExtractor",
    "ArchiveHandler",
]
