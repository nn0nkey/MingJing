"""
性能监控模块

收集和暴露系统指标
"""

import time
import threading
import psutil
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import logging

logger = logging.getLogger("mingjing.metrics")


@dataclass
class MetricsData:
    """指标数据"""
    # 请求统计
    requests_total: int = 0
    requests_success: int = 0
    requests_failed: int = 0
    
    # 响应时间
    response_times: list = field(default_factory=list)
    avg_response_time: float = 0.0
    
    # 实体统计
    entities_detected: int = 0
    entities_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # 文件统计
    files_processed: int = 0
    files_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # 系统状态
    start_time: float = field(default_factory=time.time)
    uptime: float = 0.0
    memory_usage: int = 0
    cpu_percent: float = 0.0
    
    # 缓存统计
    cache_hits: int = 0
    cache_misses: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        self.uptime = time.time() - self.start_time
        
        # 计算平均响应时间
        if self.response_times:
            recent_times = self.response_times[-100:]  # 最近100次
            self.avg_response_time = sum(recent_times) / len(recent_times)
        
        # 获取系统资源
        try:
            process = psutil.Process()
            self.memory_usage = process.memory_info().rss
            self.cpu_percent = process.cpu_percent()
        except Exception:
            pass
        
        return {
            "requests_total": self.requests_total,
            "requests_success": self.requests_success,
            "requests_failed": self.requests_failed,
            "avg_response_time": round(self.avg_response_time, 3),
            "entities_detected": self.entities_detected,
            "entities_by_type": dict(self.entities_by_type),
            "files_processed": self.files_processed,
            "files_by_type": dict(self.files_by_type),
            "uptime": int(self.uptime),
            "memory_usage": self.memory_usage,
            "cpu_percent": round(self.cpu_percent, 1),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
        }


class MetricsCollector:
    """
    指标收集器
    
    用法:
        collector = MetricsCollector()
        
        # 记录请求
        with collector.track_request():
            # 处理请求
            pass
        
        # 记录实体
        collector.record_entity("CN_ID_CARD")
        
        # 获取指标
        metrics = collector.get_metrics()
    """
    
    _instance: Optional["MetricsCollector"] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._data = MetricsData()
        self._lock = threading.Lock()
        self._initialized = True
        
        logger.info("指标收集器初始化完成")
    
    def track_request(self):
        """请求追踪上下文管理器"""
        return RequestTracker(self)
    
    def record_request(self, success: bool, response_time: float) -> None:
        """记录请求"""
        with self._lock:
            self._data.requests_total += 1
            if success:
                self._data.requests_success += 1
            else:
                self._data.requests_failed += 1
            
            self._data.response_times.append(response_time)
            # 保留最近1000次
            if len(self._data.response_times) > 1000:
                self._data.response_times = self._data.response_times[-1000:]
    
    def record_entity(self, entity_type: str, count: int = 1) -> None:
        """记录识别到的实体"""
        with self._lock:
            self._data.entities_detected += count
            self._data.entities_by_type[entity_type] += count
    
    def record_file(self, file_type: str) -> None:
        """记录处理的文件"""
        with self._lock:
            self._data.files_processed += 1
            self._data.files_by_type[file_type] += 1
    
    def record_cache_hit(self) -> None:
        """记录缓存命中"""
        with self._lock:
            self._data.cache_hits += 1
    
    def record_cache_miss(self) -> None:
        """记录缓存未命中"""
        with self._lock:
            self._data.cache_misses += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        with self._lock:
            return self._data.to_dict()
    
    def reset(self) -> None:
        """重置指标"""
        with self._lock:
            self._data = MetricsData()


class RequestTracker:
    """请求追踪器"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
        self.start_time = 0.0
        self.success = True
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        response_time = time.time() - self.start_time
        success = exc_type is None
        self.collector.record_request(success, response_time)
        return False  # 不抑制异常
    
    def set_failed(self):
        """标记请求失败"""
        self.success = False


# 全局指标收集器
def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    return MetricsCollector()
