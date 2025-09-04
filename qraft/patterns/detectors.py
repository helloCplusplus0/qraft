import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from loguru import logger

# River库导入
import river.drift as drift
import river.anomaly as anomaly
import river.cluster as cluster


def get_detector(name: str, detector_type: str, config: Dict[str, Any]):
    """获取检测器实例
    
    Args:
        name: 检测器名称
        detector_type: 检测器类型
        config: 检测器配置
        
    Returns:
        检测器实例，如果不存在则返回None
    """
    if detector_type == "adwin":
        return DriftDetector(name, config)
    elif detector_type == "half_space_trees":
        return AnomalyDetector(name, config)
    elif detector_type == "cluster_detector":
        return ClusterDetector(name, config)
    return None


class BaseDetector:
    """检测器基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化检测器
        
        Args:
            name: 检测器名称
            config: 检测器配置
        """
        self.name = name
        self.config = config
        self.feature_fields = config.get("fields", [])
        self.logger = logger.bind(detector=name)
    
    async def detect(self, features: Dict[str, float], event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检测模式，子类必须实现
        
        Args:
            features: 特征数据
            event: 事件数据
            
        Returns:
            模式事件，如果没有检测到模式则返回None
        """
        raise NotImplementedError("Subclasses must implement detect()")
    
    def _create_pattern_event(self, event: Dict[str, Any], pattern_type: str, details: Dict[str, Any], contributors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """创建模式事件
        
        Args:
            event: 原始事件
            pattern_type: 模式类型
            details: 模式详情
            contributors: 贡献因子列表
            
        Returns:
            模式事件
        """
        return {
            "pattern_id": str(uuid.uuid4()),
            "type": pattern_type,
            "timestamp": event.get("timestamp"),
            "source": event.get("source"),
            "details": details,
            "contributors": contributors
        }


class DriftDetector(BaseDetector):
    """概念漂移检测器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化概念漂移检测器
        
        Args:
            name: 检测器名称
            config: 检测器配置
        """
        super().__init__(name, config)
        self.delta = config.get("delta", 0.002)
        self.grace_period = config.get("grace_period", 100)
        
        # 为每个特征创建一个检测器
        self.detectors = {}
        for field in self.feature_fields:
            self.detectors[field] = drift.ADWIN(delta=self.delta)
        
        # 保存最近的值用于计算变化
        self.recent_values = {field: [] for field in self.feature_fields}
        self.max_recent = 100
        self.sample_count = 0
    
    async def detect(self, features: Dict[str, float], event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检测概念漂移
        
        Args:
            features: 特征数据
            event: 事件数据
            
        Returns:
            模式事件，如果没有检测到漂移则返回None
        """
        drift_detected = False
        drift_fields = []
        details = {"detector": self.name}
        
        # 增加样本计数
        self.sample_count += 1
        
        # 在宽限期内不检测漂移
        if self.sample_count < self.grace_period:
            return None
        
        for field, value in features.items():
            if field in self.detectors:
                # 更新检测器
                detector = self.detectors[field]
                old_mean = detector.mean if hasattr(detector, "mean") else None
                drift_detected_on_field = detector.update(value)
                
                # 保存最近的值
                self.recent_values[field].append(value)
                if len(self.recent_values[field]) > self.max_recent:
                    self.recent_values[field].pop(0)
                
                # 如果检测到漂移
                if drift_detected_on_field:
                    drift_detected = True
                    drift_fields.append(field)
                    
                    # 计算变化
                    new_mean = detector.mean if hasattr(detector, "mean") else None
                    if old_mean is not None and new_mean is not None and old_mean != 0:
                        change_pct = (new_mean - old_mean) / abs(old_mean) * 100
                    else:
                        change_pct = 0
                    
                    details[f"{field}_prev_mean"] = old_mean
                    details[f"{field}_new_mean"] = new_mean
                    details[f"{field}_change_pct"] = change_pct
        
        if drift_detected:
            # 计算置信度（简化实现）
            confidence = 0.9
            details["confidence"] = confidence
            
            # 创建贡献者列表
            contributors = []
            for field in drift_fields:
                contributors.append({"field": field, "score": 1.0 / len(drift_fields)})
            
            return self._create_pattern_event(
                event, "drift", details, contributors
            )
        
        return None


class AnomalyDetector(BaseDetector):
    """异常检测器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化异常检测器
        
        Args:
            name: 检测器名称
            config: 检测器配置
        """
        super().__init__(name, config)
        self.n_trees = config.get("n_trees", 10)
        self.height = config.get("height", 8)
        self.window_size = config.get("window_size", 100)
        self.threshold = config.get("threshold", 0.95)
        
        # 创建异常检测器
        self.detector = anomaly.HalfSpaceTrees(
            n_trees=self.n_trees,
            height=self.height,
            window_size=self.window_size
        )
        
        # 保存最近的异常分数
        self.recent_scores = []
        self.max_recent = 100
        self.sample_count = 0
    
    async def detect(self, features: Dict[str, float], event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检测异常
        
        Args:
            features: 特征数据
            event: 事件数据
            
        Returns:
            模式事件，如果没有检测到异常则返回None
        """
        # 增加样本计数
        self.sample_count += 1
        
        # 在窗口大小内不检测异常
        if self.sample_count < self.window_size:
            # 更新检测器
            self.detector.learn_one(features)
            return None
        
        # 计算异常分数
        score = self.detector.score_one(features)
        
        # 更新检测器
        self.detector.learn_one(features)
        
        # 保存最近的分数
        self.recent_scores.append(score)
        if len(self.recent_scores) > self.max_recent:
            self.recent_scores.pop(0)
        
        # 计算分数阈值
        if len(self.recent_scores) > 10:  # 至少需要一些历史数据
            threshold = np.percentile(self.recent_scores, self.threshold * 100)
        else:
            threshold = 0.5  # 默认阈值
        
        # 如果分数超过阈值，检测到异常
        if score > threshold:
            # 计算贡献因子
            contributors = []
            for field in features:
                # 简化实现，均匀分配贡献度
                contributors.append({"field": field, "score": 1.0 / len(features)})
            
            details = {
                "detector": self.name,
                "score": score,
                "threshold": threshold,
                "confidence": (score - threshold) / (1 - threshold) if threshold < 1 else 0.5
            }
            
            return self._create_pattern_event(
                event, "anomaly", details, contributors
            )
        
        return None


class ClusterDetector(BaseDetector):
    """聚类变化检测器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """
        初始化聚类变化检测器
        
        Args:
            name: 检测器名称
            config: 检测器配置
        """
        super().__init__(name, config)
        self.n_clusters = config.get("n_clusters", 4)
        self.window_size = config.get("window_size", 50)
        self.threshold = config.get("threshold", 0.3)
        
        # 创建聚类器
        self.clusterer = cluster.STREAMKMeans(n_clusters=self.n_clusters)
        
        # 保存最近的数据和聚类结果
        self.recent_data = []
        self.recent_clusters = []
        self.max_recent = self.window_size * 2
        self.sample_count = 0
        self.current_cluster = None
    
    async def detect(self, features: Dict[str, float], event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """检测聚类变化
        
        Args:
            features: 特征数据
            event: 事件数据
            
        Returns:
            模式事件，如果没有检测到聚类变化则返回None
        """
        # 增加样本计数
        self.sample_count += 1
        
        # 保存最近的数据
        self.recent_data.append(features)
        if len(self.recent_data) > self.max_recent:
            self.recent_data.pop(0)
        
        # 在窗口大小内不检测变化
        if self.sample_count < self.window_size:
            # 更新聚类器
            self.clusterer.learn_one(features)
            return None
        
        # 预测聚类
        cluster = self.clusterer.predict_one(features)
        
        # 更新聚类器
        self.clusterer.learn_one(features)
        
        # 保存最近的聚类结果
        self.recent_clusters.append(cluster)
        if len(self.recent_clusters) > self.max_recent:
            self.recent_clusters.pop(0)
        
        # 如果是第一个聚类结果，设置当前聚类
        if self.current_cluster is None:
            self.current_cluster = cluster
            return None
        
        # 计算最近窗口内的主导聚类
        if len(self.recent_clusters) >= self.window_size:
            window_clusters = self.recent_clusters[-self.window_size:]
            cluster_counts = {}
            for c in window_clusters:
                if c not in cluster_counts:
                    cluster_counts[c] = 0
                cluster_counts[c] += 1
            
            # 找出主导聚类
            dominant_cluster = max(cluster_counts, key=cluster_counts.get)
            dominant_ratio = cluster_counts[dominant_cluster] / self.window_size
            
            # 如果主导聚类变化且比例超过阈值，检测到聚类变化
            if dominant_cluster != self.current_cluster and dominant_ratio >= self.threshold:
                # 计算贡献因子
                contributors = []
                for field in features:
                    # 简化实现，均匀分配贡献度
                    contributors.append({"field": field, "score": 1.0 / len(features)})
                
                details = {
                    "detector": self.name,
                    "prev_cluster": self.current_cluster,
                    "new_cluster": dominant_cluster,
                    "confidence": dominant_ratio
                }
                
                # 更新当前聚类
                self.current_cluster = dominant_cluster
                
                return self._create_pattern_event(
                    event, "cluster_change", details, contributors
                )
        
        return None