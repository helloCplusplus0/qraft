from typing import Dict, Any, Optional

from prometheus_client import Counter, Gauge, Histogram, Summary


class Metrics:
    """指标收集器，用于收集和导出指标"""
    
    def __init__(self):
        """初始化指标收集器"""
        # 事件计数器
        self.event_counter = Counter(
            "qraft_events_total",
            "Total number of events processed",
            ["source", "type"]
        )
        
        # 模式计数器
        self.pattern_counter = Counter(
            "qraft_patterns_total",
            "Total number of patterns detected",
            ["source", "type"]
        )
        
        # 处理延迟直方图
        self.processing_latency = Histogram(
            "qraft_processing_latency_seconds",
            "Event processing latency in seconds",
            ["source", "type"],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5)
        )
        
        # 检测延迟直方图
        self.detection_latency = Histogram(
            "qraft_detection_latency_seconds",
            "Pattern detection latency in seconds",
            ["source", "type"],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5)
        )
        
        # 队列大小仪表
        self.queue_size = Gauge(
            "qraft_queue_size",
            "Number of events in queue",
            ["queue"]
        )
        
        # 错误计数器
        self.error_counter = Counter(
            "qraft_errors_total",
            "Total number of errors",
            ["component", "type"]
        )
        
        # 反馈计数器
        self.feedback_counter = Counter(
            "qraft_feedback_total",
            "Total number of feedback submissions",
            ["rating"]
        )
        
        # API请求计数器
        self.api_request_counter = Counter(
            "qraft_api_requests_total",
            "Total number of API requests",
            ["endpoint", "method", "status"]
        )
        
        # API延迟直方图
        self.api_latency = Histogram(
            "qraft_api_latency_seconds",
            "API request latency in seconds",
            ["endpoint", "method"],
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5)
        )
    
    def record_event(self, source: str, event_type: str):
        """记录事件
        
        Args:
            source: 数据源
            event_type: 事件类型
        """
        self.event_counter.labels(source=source, type=event_type).inc()
    
    def record_pattern(self, source: str, pattern_type: str):
        """记录模式
        
        Args:
            source: 数据源
            pattern_type: 模式类型
        """
        self.pattern_counter.labels(source=source, type=pattern_type).inc()
    
    def record_processing_latency(self, source: str, event_type: str, latency: float):
        """记录处理延迟
        
        Args:
            source: 数据源
            event_type: 事件类型
            latency: 延迟（秒）
        """
        self.processing_latency.labels(source=source, type=event_type).observe(latency)
    
    def record_detection_latency(self, source: str, pattern_type: str, latency: float):
        """记录检测延迟
        
        Args:
            source: 数据源
            pattern_type: 模式类型
            latency: 延迟（秒）
        """
        self.detection_latency.labels(source=source, type=pattern_type).observe(latency)
    
    def set_queue_size(self, queue: str, size: int):
        """设置队列大小
        
        Args:
            queue: 队列名称
            size: 队列大小
        """
        self.queue_size.labels(queue=queue).set(size)
    
    def record_error(self, component: str, error_type: str):
        """记录错误
        
        Args:
            component: 组件名称
            error_type: 错误类型
        """
        self.error_counter.labels(component=component, type=error_type).inc()
    
    def record_feedback(self, rating: int):
        """记录反馈
        
        Args:
            rating: 评分（-1, 0, 1）
        """
        rating_str = "negative" if rating == -1 else "neutral" if rating == 0 else "positive"
        self.feedback_counter.labels(rating=rating_str).inc()
    
    def record_api_request(self, endpoint: str, method: str, status: int):
        """记录API请求
        
        Args:
            endpoint: 端点
            method: 方法
            status: 状态码
        """
        self.api_request_counter.labels(endpoint=endpoint, method=method, status=str(status)).inc()
    
    def record_api_latency(self, endpoint: str, method: str, latency: float):
        """记录API延迟
        
        Args:
            endpoint: 端点
            method: 方法
            latency: 延迟（秒）
        """
        self.api_latency.labels(endpoint=endpoint, method=method).observe(latency)


# 全局指标实例
metrics = Metrics()