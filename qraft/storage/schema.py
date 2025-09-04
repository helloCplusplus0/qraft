from typing import Dict, Any, List


class Schema:
    """表结构定义"""
    
    @staticmethod
    def get_raw_events_schema() -> str:
        """获取原始事件表结构
        
        Returns:
            表结构SQL
        """
        return """
        CREATE TABLE IF NOT EXISTS raw_events (
            event_id String,
            source String,
            type String,
            timestamp DateTime64(3),
            ingest_time DateTime64(3),
            payload String,  -- JSON
            meta String      -- JSON
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(timestamp)
        ORDER BY (timestamp, source, type, event_id)
        """
    
    @staticmethod
    def get_clean_events_schema() -> str:
        """获取处理后事件表结构
        
        Returns:
            表结构SQL
        """
        return """
        CREATE TABLE IF NOT EXISTS clean_events (
            event_id String,
            source String,
            type String,
            timestamp DateTime64(3),
            processing_time DateTime64(3),
            payload String,  -- JSON
            meta String      -- JSON
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(timestamp)
        ORDER BY (timestamp, source, type, event_id)
        """
    
    @staticmethod
    def get_pattern_events_schema() -> str:
        """获取模式事件表结构
        
        Returns:
            表结构SQL
        """
        return """
        CREATE TABLE IF NOT EXISTS pattern_events (
            pattern_id String,
            type String,
            timestamp DateTime64(3),
            source String,
            details String,  -- JSON
            contributors String  -- JSON
        ) ENGINE = MergeTree()
        PARTITION BY toYYYYMMDD(timestamp)
        ORDER BY (timestamp, source, type, pattern_id)
        """
    
    @staticmethod
    def get_pattern_feedback_schema() -> str:
        """获取模式反馈表结构
        
        Returns:
            表结构SQL
        """
        return """
        CREATE TABLE IF NOT EXISTS pattern_feedback (
            feedback_id String,
            pattern_id String,
            timestamp DateTime64(3),
            user_id String,
            rating Int8,  -- -1: 负面, 0: 中性, 1: 正面
            comment String
        ) ENGINE = MergeTree()
        ORDER BY (pattern_id, timestamp)
        """
    
    @staticmethod
    def get_all_schemas() -> List[str]:
        """获取所有表结构
        
        Returns:
            表结构SQL列表
        """
        return [
            Schema.get_raw_events_schema(),
            Schema.get_clean_events_schema(),
            Schema.get_pattern_events_schema(),
            Schema.get_pattern_feedback_schema()
        ]