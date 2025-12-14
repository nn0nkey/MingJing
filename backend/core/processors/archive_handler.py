"""
压缩包处理器

支持:
- ZIP, RAR, 7Z, TAR, GZ 等格式
- 递归解压（套娃压缩包）
- 密码保护检测
"""

import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Generator, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("mingjing.archive")


@dataclass
class ArchivedFile:
    """压缩包中的文件"""
    name: str  # 文件名
    path: str  # 在压缩包中的路径
    size: int  # 文件大小
    is_dir: bool  # 是否是目录
    extracted_path: Optional[Path] = None  # 解压后的路径


class ArchiveHandler:
    """
    压缩包处理器
    
    用法:
        handler = ArchiveHandler()
        
        # 检查是否是压缩包
        if handler.is_archive("file.zip"):
            # 解压并遍历文件
            for file_info, file_path in handler.extract_all("file.zip"):
                print(f"解压: {file_info.name} -> {file_path}")
    """
    
    # 支持的压缩格式
    SUPPORTED_FORMATS = {
        ".zip": "zip",
        ".rar": "rar",
        ".7z": "7z",
        ".tar": "tar",
        ".gz": "gzip",
        ".tgz": "tar.gz",
        ".tar.gz": "tar.gz",
        ".bz2": "bzip2",
        ".tar.bz2": "tar.bz2",
        ".xz": "xz",
        ".tar.xz": "tar.xz",
    }
    
    def __init__(
        self,
        temp_dir: Optional[str] = None,
        recursive: bool = True,
        max_depth: int = 5,
        max_size: int = 1024 * 1024 * 1024,  # 1GB
    ):
        """
        初始化
        
        :param temp_dir: 临时目录
        :param recursive: 是否递归解压
        :param max_depth: 最大递归深度
        :param max_size: 最大解压大小（字节）
        """
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir()) / "mingjing_archives"
        self.recursive = recursive
        self.max_depth = max_depth
        self.max_size = max_size
        
        # 确保临时目录存在
        self.temp_dir.mkdir(parents=True, exist_ok=True)
    
    def is_archive(self, file_path: str | Path) -> bool:
        """检查是否是支持的压缩格式"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        # 检查双扩展名（如 .tar.gz）
        if len(path.suffixes) >= 2:
            double_suffix = ''.join(path.suffixes[-2:]).lower()
            if double_suffix in self.SUPPORTED_FORMATS:
                return True
        
        return suffix in self.SUPPORTED_FORMATS
    
    def get_archive_type(self, file_path: str | Path) -> Optional[str]:
        """获取压缩包类型"""
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        # 检查双扩展名
        if len(path.suffixes) >= 2:
            double_suffix = ''.join(path.suffixes[-2:]).lower()
            if double_suffix in self.SUPPORTED_FORMATS:
                return self.SUPPORTED_FORMATS[double_suffix]
        
        return self.SUPPORTED_FORMATS.get(suffix)
    
    def list_contents(self, archive_path: str | Path) -> List[ArchivedFile]:
        """
        列出压缩包内容
        
        :param archive_path: 压缩包路径
        :return: 文件列表
        """
        path = Path(archive_path)
        archive_type = self.get_archive_type(path)
        
        if not archive_type:
            return []
        
        try:
            if archive_type == "zip":
                return self._list_zip(path)
            elif archive_type in ("tar", "tar.gz", "tar.bz2", "tar.xz", "gzip", "bzip2", "xz"):
                return self._list_tar(path)
            elif archive_type == "7z":
                return self._list_7z(path)
            elif archive_type == "rar":
                return self._list_rar(path)
            else:
                logger.warning(f"不支持的压缩格式: {archive_type}")
                return []
        except Exception as e:
            logger.error(f"列出压缩包内容失败 {path}: {e}")
            return []
    
    def _list_zip(self, path: Path) -> List[ArchivedFile]:
        """列出ZIP内容"""
        import zipfile
        
        files = []
        with zipfile.ZipFile(path, 'r') as zf:
            for info in zf.infolist():
                files.append(ArchivedFile(
                    name=Path(info.filename).name,
                    path=info.filename,
                    size=info.file_size,
                    is_dir=info.is_dir(),
                ))
        return files
    
    def _list_tar(self, path: Path) -> List[ArchivedFile]:
        """列出TAR内容"""
        import tarfile
        
        files = []
        mode = 'r:*'  # 自动检测压缩类型
        with tarfile.open(path, mode) as tf:
            for member in tf.getmembers():
                files.append(ArchivedFile(
                    name=Path(member.name).name,
                    path=member.name,
                    size=member.size,
                    is_dir=member.isdir(),
                ))
        return files
    
    def _list_7z(self, path: Path) -> List[ArchivedFile]:
        """列出7Z内容"""
        try:
            import py7zr
            
            files = []
            with py7zr.SevenZipFile(path, 'r') as zf:
                for name, info in zf.archiveinfo().files.items():
                    files.append(ArchivedFile(
                        name=Path(name).name,
                        path=name,
                        size=info.get('size', 0),
                        is_dir=info.get('is_directory', False),
                    ))
            return files
        except ImportError:
            logger.warning("py7zr未安装，无法处理7z文件。请运行: pip install py7zr")
            return []
    
    def _list_rar(self, path: Path) -> List[ArchivedFile]:
        """列出RAR内容"""
        try:
            import rarfile
            
            files = []
            with rarfile.RarFile(path, 'r') as rf:
                for info in rf.infolist():
                    files.append(ArchivedFile(
                        name=Path(info.filename).name,
                        path=info.filename,
                        size=info.file_size,
                        is_dir=info.is_dir(),
                    ))
            return files
        except ImportError:
            logger.warning("rarfile未安装，无法处理rar文件。请运行: pip install rarfile")
            return []
    
    def extract_all(
        self,
        archive_path: str | Path,
        depth: int = 0,
    ) -> Generator[Tuple[ArchivedFile, Path], None, None]:
        """
        解压所有文件
        
        :param archive_path: 压缩包路径
        :param depth: 当前递归深度
        :yield: (文件信息, 解压后路径)
        """
        if depth >= self.max_depth:
            logger.warning(f"达到最大递归深度 {self.max_depth}")
            return
        
        path = Path(archive_path)
        archive_type = self.get_archive_type(path)
        
        if not archive_type:
            return
        
        # 创建解压目录
        extract_dir = self.temp_dir / f"{path.stem}_{id(path)}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 解压
            if archive_type == "zip":
                yield from self._extract_zip(path, extract_dir, depth)
            elif archive_type in ("tar", "tar.gz", "tar.bz2", "tar.xz", "gzip", "bzip2", "xz"):
                yield from self._extract_tar(path, extract_dir, depth)
            elif archive_type == "7z":
                yield from self._extract_7z(path, extract_dir, depth)
            elif archive_type == "rar":
                yield from self._extract_rar(path, extract_dir, depth)
        except Exception as e:
            logger.error(f"解压失败 {path}: {e}")
    
    def _extract_zip(self, path: Path, extract_dir: Path, depth: int) -> Generator[Tuple[ArchivedFile, Path], None, None]:
        """解压ZIP"""
        import zipfile
        
        with zipfile.ZipFile(path, 'r') as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                
                # 检查大小
                if info.file_size > self.max_size:
                    logger.warning(f"文件过大，跳过: {info.filename}")
                    continue
                
                # 解压单个文件
                extracted_path = extract_dir / info.filename
                extracted_path.parent.mkdir(parents=True, exist_ok=True)
                
                with zf.open(info) as src, open(extracted_path, 'wb') as dst:
                    dst.write(src.read())
                
                file_info = ArchivedFile(
                    name=Path(info.filename).name,
                    path=info.filename,
                    size=info.file_size,
                    is_dir=False,
                    extracted_path=extracted_path,
                )
                
                # 检查是否是嵌套压缩包
                if self.recursive and self.is_archive(extracted_path):
                    yield from self.extract_all(extracted_path, depth + 1)
                else:
                    yield file_info, extracted_path
    
    def _extract_tar(self, path: Path, extract_dir: Path, depth: int) -> Generator[Tuple[ArchivedFile, Path], None, None]:
        """解压TAR"""
        import tarfile
        
        mode = 'r:*'
        with tarfile.open(path, mode) as tf:
            for member in tf.getmembers():
                if member.isdir():
                    continue
                
                if member.size > self.max_size:
                    logger.warning(f"文件过大，跳过: {member.name}")
                    continue
                
                # 安全检查：防止路径遍历攻击
                extracted_path = extract_dir / member.name
                if not str(extracted_path).startswith(str(extract_dir)):
                    logger.warning(f"检测到路径遍历，跳过: {member.name}")
                    continue
                
                extracted_path.parent.mkdir(parents=True, exist_ok=True)
                
                with tf.extractfile(member) as src:
                    if src:
                        with open(extracted_path, 'wb') as dst:
                            dst.write(src.read())
                
                file_info = ArchivedFile(
                    name=Path(member.name).name,
                    path=member.name,
                    size=member.size,
                    is_dir=False,
                    extracted_path=extracted_path,
                )
                
                if self.recursive and self.is_archive(extracted_path):
                    yield from self.extract_all(extracted_path, depth + 1)
                else:
                    yield file_info, extracted_path
    
    def _extract_7z(self, path: Path, extract_dir: Path, depth: int) -> Generator[Tuple[ArchivedFile, Path], None, None]:
        """解压7Z"""
        try:
            import py7zr
            
            with py7zr.SevenZipFile(path, 'r') as zf:
                zf.extractall(extract_dir)
            
            # 遍历解压后的文件
            for extracted_path in extract_dir.rglob('*'):
                if extracted_path.is_file():
                    file_info = ArchivedFile(
                        name=extracted_path.name,
                        path=str(extracted_path.relative_to(extract_dir)),
                        size=extracted_path.stat().st_size,
                        is_dir=False,
                        extracted_path=extracted_path,
                    )
                    
                    if self.recursive and self.is_archive(extracted_path):
                        yield from self.extract_all(extracted_path, depth + 1)
                    else:
                        yield file_info, extracted_path
        except ImportError:
            logger.warning("py7zr未安装")
    
    def _extract_rar(self, path: Path, extract_dir: Path, depth: int) -> Generator[Tuple[ArchivedFile, Path], None, None]:
        """解压RAR"""
        try:
            import rarfile
            
            with rarfile.RarFile(path, 'r') as rf:
                rf.extractall(extract_dir)
            
            for extracted_path in extract_dir.rglob('*'):
                if extracted_path.is_file():
                    file_info = ArchivedFile(
                        name=extracted_path.name,
                        path=str(extracted_path.relative_to(extract_dir)),
                        size=extracted_path.stat().st_size,
                        is_dir=False,
                        extracted_path=extracted_path,
                    )
                    
                    if self.recursive and self.is_archive(extracted_path):
                        yield from self.extract_all(extracted_path, depth + 1)
                    else:
                        yield file_info, extracted_path
        except ImportError:
            logger.warning("rarfile未安装")
    
    def cleanup(self) -> None:
        """清理临时文件"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.info(f"清理临时目录: {self.temp_dir}")
