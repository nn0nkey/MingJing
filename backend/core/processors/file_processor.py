"""
文件处理器

统一的文件处理入口，支持:
- 多格式文件解析
- 压缩包穿透
- 大文件分片
- 批量处理
"""

import os
import logging
from pathlib import Path
from typing import Generator, List, Optional, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from .extractors import get_extractor, ExtractedContent, BaseExtractor
from .archive_handler import ArchiveHandler, ArchivedFile

logger = logging.getLogger("mingjing.processor")


@dataclass
class ProcessedFile:
    """处理后的文件"""
    filename: str  # 原始文件名
    filepath: str  # 文件路径
    file_type: str  # 文件类型
    size: int  # 文件大小（字节）
    contents: List[ExtractedContent] = field(default_factory=list)  # 提取的内容
    is_archive: bool = False  # 是否是压缩包
    archive_files: List[str] = field(default_factory=list)  # 压缩包中的文件列表
    error: Optional[str] = None  # 错误信息
    
    @property
    def total_text(self) -> str:
        """获取所有内容的合并文本"""
        return '\n'.join(c.text for c in self.contents)
    
    @property
    def content_count(self) -> int:
        """内容块数量"""
        return len(self.contents)


class FileProcessor:
    """
    文件处理器
    
    用法:
        processor = FileProcessor()
        
        # 处理单个文件
        result = processor.process_file("document.pdf")
        print(result.total_text)
        
        # 处理目录
        for result in processor.process_directory("/path/to/dir"):
            print(f"{result.filename}: {result.content_count} 块内容")
        
        # 处理上传的文件
        result = processor.process_bytes(file_bytes, "uploaded.xlsx")
    """
    
    def __init__(
        self,
        supported_formats: Optional[List[str]] = None,
        archive_formats: Optional[List[str]] = None,
        max_file_size: int = 100 * 1024 * 1024,  # 100MB
        chunk_size: int = 10 * 1024 * 1024,  # 10MB
        temp_dir: Optional[str] = None,
        recursive_extract: bool = True,
        max_workers: int = 4,
    ):
        """
        初始化
        
        :param supported_formats: 支持的文件格式列表
        :param archive_formats: 压缩包格式列表
        :param max_file_size: 最大文件大小（字节）
        :param chunk_size: 分片大小（字节）
        :param temp_dir: 临时目录
        :param recursive_extract: 是否递归解压
        :param max_workers: 最大并发数
        """
        self.supported_formats = supported_formats or [
            ".txt", ".csv", ".json", ".jsonl", ".xml", ".html", ".htm",
            ".md", ".log", ".pdf", ".docx", ".xlsx", ".xls",
        ]
        self.archive_formats = archive_formats or [
            ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".tar.gz",
        ]
        self.max_file_size = max_file_size
        self.chunk_size = chunk_size
        self.temp_dir = temp_dir
        self.recursive_extract = recursive_extract
        self.max_workers = max_workers
        
        # 压缩包处理器
        self.archive_handler = ArchiveHandler(
            temp_dir=temp_dir,
            recursive=recursive_extract,
        )
    
    def is_supported(self, file_path: Union[str, Path]) -> bool:
        """检查文件是否支持"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        return suffix in self.supported_formats or suffix in self.archive_formats
    
    def process_file(self, file_path: Union[str, Path]) -> ProcessedFile:
        """
        处理单个文件
        
        :param file_path: 文件路径
        :return: ProcessedFile对象
        """
        path = Path(file_path)
        
        # 基本信息
        result = ProcessedFile(
            filename=path.name,
            filepath=str(path.absolute()),
            file_type=path.suffix.lower(),
            size=path.stat().st_size if path.exists() else 0,
        )
        
        # 检查文件是否存在
        if not path.exists():
            result.error = "文件不存在"
            return result
        
        # 检查文件大小
        if result.size > self.max_file_size:
            result.error = f"文件过大: {result.size / 1024 / 1024:.1f}MB > {self.max_file_size / 1024 / 1024:.1f}MB"
            return result
        
        try:
            # 检查是否是压缩包
            if self.archive_handler.is_archive(path):
                result.is_archive = True
                result = self._process_archive(path, result)
            else:
                result = self._process_regular_file(path, result)
        except Exception as e:
            result.error = str(e)
            logger.error(f"处理文件失败 {path}: {e}")
        
        return result
    
    def _process_regular_file(self, path: Path, result: ProcessedFile) -> ProcessedFile:
        """处理普通文件"""
        extractor = get_extractor(path)
        
        if not extractor:
            result.error = f"不支持的文件类型: {path.suffix}"
            return result
        
        for content in extractor.extract(path):
            result.contents.append(content)
        
        return result
    
    def _process_archive(self, path: Path, result: ProcessedFile) -> ProcessedFile:
        """处理压缩包"""
        try:
            for file_info, extracted_path in self.archive_handler.extract_all(path):
                result.archive_files.append(file_info.path)
                
                # 获取提取器
                extractor = get_extractor(extracted_path)
                if extractor:
                    for content in extractor.extract(extracted_path):
                        # 更新来源信息
                        content.source = f"{path.name}/{file_info.path}"
                        result.contents.append(content)
        finally:
            # 清理临时文件
            pass  # 可以选择在这里清理或者统一清理
        
        return result
    
    def process_bytes(self, data: bytes, filename: str) -> ProcessedFile:
        """
        处理字节数据（用于文件上传）
        
        :param data: 文件字节数据
        :param filename: 文件名
        :return: ProcessedFile对象
        """
        path = Path(filename)
        
        result = ProcessedFile(
            filename=filename,
            filepath="<uploaded>",
            file_type=path.suffix.lower(),
            size=len(data),
        )
        
        # 检查大小
        if result.size > self.max_file_size:
            result.error = f"文件过大: {result.size / 1024 / 1024:.1f}MB"
            return result
        
        try:
            # 检查是否是压缩包
            if self.archive_handler.is_archive(filename):
                result.is_archive = True
                # 需要先保存到临时文件
                import tempfile
                with tempfile.NamedTemporaryFile(suffix=path.suffix, delete=False) as tmp:
                    tmp.write(data)
                    tmp_path = Path(tmp.name)
                
                try:
                    result = self._process_archive(tmp_path, result)
                finally:
                    tmp_path.unlink(missing_ok=True)
            else:
                extractor = get_extractor(filename)
                if extractor:
                    for content in extractor.extract_from_bytes(data, filename):
                        result.contents.append(content)
                else:
                    result.error = f"不支持的文件类型: {path.suffix}"
        except Exception as e:
            result.error = str(e)
            logger.error(f"处理上传文件失败 {filename}: {e}")
        
        return result
    
    def process_directory(
        self,
        dir_path: Union[str, Path],
        recursive: bool = True,
        pattern: str = "*",
    ) -> Generator[ProcessedFile, None, None]:
        """
        处理目录中的所有文件
        
        :param dir_path: 目录路径
        :param recursive: 是否递归处理子目录
        :param pattern: 文件匹配模式
        :yield: ProcessedFile对象
        """
        path = Path(dir_path)
        
        if not path.is_dir():
            logger.error(f"不是有效的目录: {path}")
            return
        
        # 获取文件列表
        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))
        
        # 过滤支持的文件
        files = [f for f in files if f.is_file() and self.is_supported(f)]
        
        logger.info(f"找到 {len(files)} 个待处理文件")
        
        # 并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_file, f): f for f in files}
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    yield result
                except Exception as e:
                    file_path = futures[future]
                    logger.error(f"处理文件失败 {file_path}: {e}")
                    yield ProcessedFile(
                        filename=file_path.name,
                        filepath=str(file_path),
                        file_type=file_path.suffix,
                        size=0,
                        error=str(e),
                    )
    
    def process_files(self, file_paths: List[Union[str, Path]]) -> Generator[ProcessedFile, None, None]:
        """
        批量处理多个文件
        
        :param file_paths: 文件路径列表
        :yield: ProcessedFile对象
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.process_file, f): f for f in file_paths}
            
            for future in as_completed(futures):
                try:
                    yield future.result()
                except Exception as e:
                    file_path = futures[future]
                    logger.error(f"处理文件失败 {file_path}: {e}")
    
    def cleanup(self) -> None:
        """清理临时文件"""
        self.archive_handler.cleanup()
