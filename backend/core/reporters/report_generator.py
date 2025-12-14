"""
报告生成器

生成敏感信息识别报告，包括:
- 识别结果汇总
- 风险等级评估
- 统计分析
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
from collections import Counter
import logging

logger = logging.getLogger("mingjing.reporter")


@dataclass
class EntityInfo:
    """实体信息"""
    entity_type: str
    text: str
    start: int
    end: int
    score: float
    source: str  # 来源文件/位置
    verified: bool = False
    llm_reason: Optional[str] = None


@dataclass
class FileResult:
    """单个文件的识别结果"""
    filename: str
    filepath: str
    file_type: str
    file_size: int
    entities: List[EntityInfo] = field(default_factory=list)
    error: Optional[str] = None
    process_time: float = 0.0  # 处理时间（秒）
    
    @property
    def entity_count(self) -> int:
        return len(self.entities)
    
    @property
    def entity_types(self) -> List[str]:
        return list(set(e.entity_type for e in self.entities))


@dataclass
class RiskSummary:
    """风险摘要"""
    level: str  # critical, high, medium, low
    score: int  # 风险分数
    description: str
    affected_files: List[str] = field(default_factory=list)
    entity_counts: Dict[str, int] = field(default_factory=dict)


@dataclass
class Statistics:
    """统计信息"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    total_entities: int = 0
    entity_type_counts: Dict[str, int] = field(default_factory=dict)
    file_type_counts: Dict[str, int] = field(default_factory=dict)
    avg_entities_per_file: float = 0.0
    total_process_time: float = 0.0


@dataclass
class AnalysisReport:
    """分析报告"""
    report_id: str
    created_at: str
    title: str = "敏感信息识别报告"
    description: str = ""
    
    # 结果
    file_results: List[FileResult] = field(default_factory=list)
    
    # 风险评估
    risk_level: str = "low"  # critical, high, medium, low
    risk_score: int = 0
    risk_summaries: List[RiskSummary] = field(default_factory=list)
    
    # 统计
    statistics: Statistics = field(default_factory=Statistics)
    
    # 元数据
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


class ReportGenerator:
    """
    报告生成器
    
    用法:
        generator = ReportGenerator()
        
        # 添加文件结果
        generator.add_file_result(file_result)
        
        # 生成报告
        report = generator.generate()
        
        # 导出
        generator.export_json("report.json")
        generator.export_html("report.html")
    """
    
    # 风险等级定义
    RISK_LEVELS = {
        "critical": {"min_score": 80, "color": "#dc2626"},
        "high": {"min_score": 60, "color": "#ea580c"},
        "medium": {"min_score": 40, "color": "#ca8a04"},
        "low": {"min_score": 0, "color": "#16a34a"},
    }
    
    # 实体类型风险权重
    ENTITY_WEIGHTS = {
        "CN_ID_CARD": 10,
        "CN_BANK_CARD": 10,
        "CN_PASSPORT": 8,
        "CN_PHONE": 5,
        "CN_EMAIL": 3,
        "PERSON": 4,
        "CN_DRIVER_LICENSE": 6,
        "CN_MILITARY_ID": 8,
        "CN_SOCIAL_CREDIT_CODE": 5,
        "CN_JWT": 7,
        "CN_CLOUD_KEY": 9,
        "PRIVATE_KEY": 10,
        "DB_CONNECTION": 8,
        "default": 2,
    }
    
    def __init__(
        self,
        title: str = "敏感信息识别报告",
        description: str = "",
        output_dir: Optional[str] = None,
    ):
        """
        初始化
        
        :param title: 报告标题
        :param description: 报告描述
        :param output_dir: 输出目录
        """
        self.title = title
        self.description = description
        self.output_dir = Path(output_dir) if output_dir else Path("./reports")
        
        self._file_results: List[FileResult] = []
        self._report: Optional[AnalysisReport] = None
    
    def add_file_result(self, result: FileResult) -> None:
        """添加文件结果"""
        self._file_results.append(result)
    
    def add_entity(
        self,
        filename: str,
        entity_type: str,
        text: str,
        start: int,
        end: int,
        score: float,
        source: str = "",
        verified: bool = False,
        llm_reason: Optional[str] = None,
    ) -> None:
        """添加单个实体到指定文件"""
        # 查找或创建文件结果
        file_result = None
        for fr in self._file_results:
            if fr.filename == filename:
                file_result = fr
                break
        
        if not file_result:
            file_result = FileResult(
                filename=filename,
                filepath="",
                file_type=Path(filename).suffix,
                file_size=0,
            )
            self._file_results.append(file_result)
        
        file_result.entities.append(EntityInfo(
            entity_type=entity_type,
            text=text,
            start=start,
            end=end,
            score=score,
            source=source or filename,
            verified=verified,
            llm_reason=llm_reason,
        ))
    
    def generate(self, config: Optional[Dict[str, Any]] = None) -> AnalysisReport:
        """
        生成报告
        
        :param config: 配置信息
        :return: AnalysisReport对象
        """
        report_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 计算统计信息
        statistics = self._calculate_statistics()
        
        # 计算风险评估
        risk_score, risk_level = self._calculate_risk()
        risk_summaries = self._generate_risk_summaries()
        
        self._report = AnalysisReport(
            report_id=report_id,
            created_at=datetime.now().isoformat(),
            title=self.title,
            description=self.description,
            file_results=self._file_results,
            risk_level=risk_level,
            risk_score=risk_score,
            risk_summaries=risk_summaries,
            statistics=statistics,
            config=config or {},
        )
        
        return self._report
    
    def _calculate_statistics(self) -> Statistics:
        """计算统计信息"""
        stats = Statistics()
        
        stats.total_files = len(self._file_results)
        stats.processed_files = sum(1 for f in self._file_results if not f.error)
        stats.failed_files = sum(1 for f in self._file_results if f.error)
        
        # 实体统计
        entity_types = Counter()
        file_types = Counter()
        total_entities = 0
        total_time = 0.0
        
        for fr in self._file_results:
            file_types[fr.file_type] += 1
            total_entities += fr.entity_count
            total_time += fr.process_time
            
            for entity in fr.entities:
                entity_types[entity.entity_type] += 1
        
        stats.total_entities = total_entities
        stats.entity_type_counts = dict(entity_types)
        stats.file_type_counts = dict(file_types)
        stats.total_process_time = total_time
        
        if stats.processed_files > 0:
            stats.avg_entities_per_file = total_entities / stats.processed_files
        
        return stats
    
    def _calculate_risk(self) -> tuple[int, str]:
        """计算风险分数和等级"""
        score = 0
        
        for fr in self._file_results:
            for entity in fr.entities:
                weight = self.ENTITY_WEIGHTS.get(
                    entity.entity_type,
                    self.ENTITY_WEIGHTS["default"]
                )
                # 考虑置信度
                score += int(weight * entity.score)
        
        # 限制最大分数
        score = min(score, 100)
        
        # 确定风险等级
        risk_level = "low"
        for level, config in self.RISK_LEVELS.items():
            if score >= config["min_score"]:
                risk_level = level
                break
        
        return score, risk_level
    
    def _generate_risk_summaries(self) -> List[RiskSummary]:
        """生成风险摘要"""
        summaries = []
        
        # 按实体类型分组
        type_files: Dict[str, List[str]] = {}
        type_counts: Dict[str, int] = {}
        
        for fr in self._file_results:
            for entity in fr.entities:
                if entity.entity_type not in type_files:
                    type_files[entity.entity_type] = []
                    type_counts[entity.entity_type] = 0
                
                if fr.filename not in type_files[entity.entity_type]:
                    type_files[entity.entity_type].append(fr.filename)
                type_counts[entity.entity_type] += 1
        
        # 生成摘要
        high_risk_types = ["CN_ID_CARD", "CN_BANK_CARD", "CN_PASSPORT", "PRIVATE_KEY", "CN_CLOUD_KEY"]
        medium_risk_types = ["CN_PHONE", "CN_JWT", "DB_CONNECTION", "PERSON"]
        
        for entity_type, count in type_counts.items():
            if entity_type in high_risk_types:
                level = "high"
                description = f"发现 {count} 个高风险敏感信息 ({entity_type})"
            elif entity_type in medium_risk_types:
                level = "medium"
                description = f"发现 {count} 个中等风险敏感信息 ({entity_type})"
            else:
                level = "low"
                description = f"发现 {count} 个低风险敏感信息 ({entity_type})"
            
            summaries.append(RiskSummary(
                level=level,
                score=count * self.ENTITY_WEIGHTS.get(entity_type, 2),
                description=description,
                affected_files=type_files.get(entity_type, []),
                entity_counts={entity_type: count},
            ))
        
        # 按风险等级排序
        level_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        summaries.sort(key=lambda x: (level_order.get(x.level, 4), -x.score))
        
        return summaries
    
    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        导出JSON报告
        
        :param filepath: 文件路径
        :return: 文件路径
        """
        if not self._report:
            self.generate()
        
        if not filepath:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            filepath = str(self.output_dir / f"report_{self._report.report_id}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self._report.to_json())
        
        logger.info(f"JSON报告已导出: {filepath}")
        return filepath
    
    def export_html(self, filepath: Optional[str] = None) -> str:
        """
        导出HTML报告
        
        :param filepath: 文件路径
        :return: 文件路径
        """
        if not self._report:
            self.generate()
        
        if not filepath:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            filepath = str(self.output_dir / f"report_{self._report.report_id}.html")
        
        from .formatters import HtmlFormatter
        formatter = HtmlFormatter()
        html_content = formatter.format(self._report)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML报告已导出: {filepath}")
        return filepath
    
    def export_excel(self, filepath: Optional[str] = None) -> str:
        """
        导出Excel报告
        
        :param filepath: 文件路径
        :return: 文件路径
        """
        if not self._report:
            self.generate()
        
        if not filepath:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            filepath = str(self.output_dir / f"report_{self._report.report_id}.xlsx")
        
        from .formatters import ExcelFormatter
        formatter = ExcelFormatter()
        formatter.format(self._report, filepath)
        
        logger.info(f"Excel报告已导出: {filepath}")
        return filepath
    
    def get_report(self) -> Optional[AnalysisReport]:
        """获取报告对象"""
        return self._report
    
    def clear(self) -> None:
        """清空结果"""
        self._file_results.clear()
        self._report = None
