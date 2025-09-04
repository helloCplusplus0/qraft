from datetime import datetime
from typing import Dict, Any, List, Optional


class PatternFormatter:
    """模式格式化器，用于格式化模式事件并生成解释"""
    
    def __init__(self):
        """初始化模式格式化器"""
        pass
    
    def format_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """格式化模式事件
        
        Args:
            pattern: 模式事件
            
        Returns:
            格式化后的模式事件
        """
        # 确保必要字段存在
        if "details" not in pattern:
            pattern["details"] = {}
        
        if "contributors" not in pattern:
            pattern["contributors"] = []
        
        # 添加人类可读的解释
        pattern["explanation"] = self.generate_explanation(pattern)
        
        return pattern
    
    def generate_explanation(self, pattern: Dict[str, Any]) -> str:
        """生成模式解释
        
        Args:
            pattern: 模式事件
            
        Returns:
            模式解释文本
        """
        pattern_type = pattern.get("type")
        timestamp = pattern.get("timestamp")
        source = pattern.get("source")
        details = pattern.get("details", {})
        contributors = pattern.get("contributors", [])
        
        # 格式化时间戳
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            formatted_time = timestamp
        
        # 格式化贡献因子
        contributor_text = ""
        if contributors:
            top_contributors = sorted(contributors, key=lambda x: x.get("score", 0), reverse=True)[:3]
            contributor_parts = []
            for contributor in top_contributors:
                field = contributor.get("field", "")
                score = contributor.get("score", 0)
                contributor_parts.append(f"{field} ({score:.2f})")
            contributor_text = ", ".join(contributor_parts)
        
        # 根据模式类型生成解释
        if pattern_type == "drift":
            return self._generate_drift_explanation(formatted_time, source, details, contributor_text)
        elif pattern_type == "anomaly":
            return self._generate_anomaly_explanation(formatted_time, source, details, contributor_text)
        elif pattern_type == "cluster_change":
            return self._generate_cluster_change_explanation(formatted_time, source, details, contributor_text)
        else:
            return f"在 {formatted_time} 检测到未知模式类型 {pattern_type}，来源于 {source}。"
    
    def _generate_drift_explanation(self, time: str, source: str, details: Dict[str, Any], contributors: str) -> str:
        """生成漂移解释
        
        Args:
            time: 格式化时间
            source: 数据源
            details: 模式详情
            contributors: 贡献因子文本
            
        Returns:
            漂移解释文本
        """
        # 提取详情
        detector = details.get("detector", "未知检测器")
        confidence = details.get("confidence", 0)
        
        # 查找变化最大的字段
        max_change_field = None
        max_change_pct = 0
        for key, value in details.items():
            if key.endswith("_change_pct") and isinstance(value, (int, float)):
                field = key.replace("_change_pct", "")
                if abs(value) > abs(max_change_pct):
                    max_change_field = field
                    max_change_pct = value
        
        # 生成解释
        explanation = f"在 {time} 检测到概念漂移，来源于 {source}。"
        
        if max_change_field and max_change_pct != 0:
            prev_mean = details.get(f"{max_change_field}_prev_mean")
            new_mean = details.get(f"{max_change_field}_new_mean")
            
            if prev_mean is not None and new_mean is not None:
                direction = "增加" if max_change_pct > 0 else "减少"
                explanation += f" {max_change_field} 从 {prev_mean:.2f} {direction}到 {new_mean:.2f}，变化率 {abs(max_change_pct):.2f}%。"
        
        if contributors:
            explanation += f" 主要贡献因子: {contributors}。"
        
        explanation += f" 置信度: {confidence:.2f}。"
        
        return explanation
    
    def _generate_anomaly_explanation(self, time: str, source: str, details: Dict[str, Any], contributors: str) -> str:
        """生成异常解释
        
        Args:
            time: 格式化时间
            source: 数据源
            details: 模式详情
            contributors: 贡献因子文本
            
        Returns:
            异常解释文本
        """
        # 提取详情
        detector = details.get("detector", "未知检测器")
        score = details.get("score", 0)
        threshold = details.get("threshold", 0)
        confidence = details.get("confidence", 0)
        
        # 生成解释
        explanation = f"在 {time} 检测到异常，来源于 {source}。"
        explanation += f" 异常分数 {score:.2f}，超过阈值 {threshold:.2f}。"
        
        if contributors:
            explanation += f" 主要贡献因子: {contributors}。"
        
        explanation += f" 置信度: {confidence:.2f}。"
        
        return explanation
    
    def _generate_cluster_change_explanation(self, time: str, source: str, details: Dict[str, Any], contributors: str) -> str:
        """生成聚类变化解释
        
        Args:
            time: 格式化时间
            source: 数据源
            details: 模式详情
            contributors: 贡献因子文本
            
        Returns:
            聚类变化解释文本
        """
        # 提取详情
        detector = details.get("detector", "未知检测器")
        prev_cluster = details.get("prev_cluster")
        new_cluster = details.get("new_cluster")
        confidence = details.get("confidence", 0)
        
        # 生成解释
        explanation = f"在 {time} 检测到聚类变化，来源于 {source}。"
        
        if prev_cluster is not None and new_cluster is not None:
            explanation += f" 聚类从 {prev_cluster} 变化到 {new_cluster}。"
        
        if contributors:
            explanation += f" 主要贡献因子: {contributors}。"
        
        explanation += f" 置信度: {confidence:.2f}。"
        
        return explanation