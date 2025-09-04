import json
from typing import Dict, Any, List, Optional, Union

from clickhouse_driver import Client
from loguru import logger


class ClickHouseClient:
    """ClickHouse客户端，用于与ClickHouse数据库交互"""
    
    def __init__(self, host: str = "localhost", port: int = 9000, user: str = "default", password: str = "", database: str = "default"):
        """
        初始化ClickHouse客户端
        
        Args:
            host: 主机名
            port: 端口
            user: 用户名
            password: 密码
            database: 数据库名
        """
        self.client = Client(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        self.logger = logger.bind(component="clickhouse")
    
    async def insert_event(self, table: str, event: Dict[str, Any]):
        """
        插入事件到ClickHouse
        
        Args:
            table: 表名
            event: 事件数据
        """
        try:
            # 根据表名选择插入方法
            if table == "raw_events":
                await self._insert_raw_event(event)
            elif table == "clean_events":
                await self._insert_clean_event(event)
            elif table == "pattern_events":
                await self._insert_pattern_event(event)
            else:
                self.logger.error(f"Unknown table: {table}")
        except Exception as e:
            self.logger.error(f"Insert error: {e}")
            raise
    
    async def _insert_raw_event(self, event: Dict[str, Any]):
        """
        插入原始事件
        
        Args:
            event: 原始事件数据
        """
        # 提取字段
        event_id = event.get("event_id", "")
        source = event.get("source", "")
        event_type = event.get("type", "")
        timestamp = event.get("timestamp", "")
        ingest_time = event.get("ingest_time", "")
        payload = json.dumps(event.get("payload", {}))
        meta = json.dumps(event.get("meta", {}))
        
        # 插入数据
        query = """
        INSERT INTO raw_events 
        (event_id, source, type, timestamp, ingest_time, payload, meta) 
        VALUES
        """
        
        self.client.execute(
            query,
            [(event_id, source, event_type, timestamp, ingest_time, payload, meta)]
        )
    
    async def _insert_clean_event(self, event: Dict[str, Any]):
        """
        插入处理后的事件
        
        Args:
            event: 处理后的事件数据
        """
        # 提取字段
        event_id = event.get("event_id", "")
        source = event.get("source", "")
        event_type = event.get("type", "")
        timestamp = event.get("timestamp", "")
        processing_time = event.get("meta", {}).get("processing_time", "")
        payload = json.dumps(event.get("payload", {}))
        meta = json.dumps(event.get("meta", {}))
        
        # 插入数据
        query = """
        INSERT INTO clean_events 
        (event_id, source, type, timestamp, processing_time, payload, meta) 
        VALUES
        """
        
        self.client.execute(
            query,
            [(event_id, source, event_type, timestamp, processing_time, payload, meta)]
        )
    
    async def _insert_pattern_event(self, event: Dict[str, Any]):
        """
        插入模式事件
        
        Args:
            event: 模式事件数据
        """
        # 提取字段
        pattern_id = event.get("pattern_id", "")
        pattern_type = event.get("type", "")
        timestamp = event.get("timestamp", "")
        source = event.get("source", "")
        details = json.dumps(event.get("details", {}))
        contributors = json.dumps(event.get("contributors", []))
        
        # 插入数据
        query = """
        INSERT INTO pattern_events 
        (pattern_id, type, timestamp, source, details, contributors) 
        VALUES
        """
        
        self.client.execute(
            query,
            [(pattern_id, pattern_type, timestamp, source, details, contributors)]
        )
    
    async def insert_pattern_feedback(self, feedback: Dict[str, Any]):
        """
        插入模式反馈
        
        Args:
            feedback: 反馈数据
        """
        # 提取字段
        feedback_id = feedback.get("feedback_id", "")
        pattern_id = feedback.get("pattern_id", "")
        timestamp = feedback.get("timestamp", "")
        user_id = feedback.get("user_id", "")
        rating = feedback.get("rating", 0)
        comment = feedback.get("comment", "")
        
        # 插入数据
        query = """
        INSERT INTO pattern_feedback 
        (feedback_id, pattern_id, timestamp, user_id, rating, comment) 
        VALUES
        """
        
        self.client.execute(
            query,
            [(feedback_id, pattern_id, timestamp, user_id, rating, comment)]
        )
    
    async def query_events(self, table: str, filters: Dict[str, Any] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        查询事件
        
        Args:
            table: 表名
            filters: 过滤条件
            limit: 限制数量
            
        Returns:
            事件列表
        """
        if filters is None:
            filters = {}
        
        # 构建查询条件
        where_clauses = []
        params = {}
        
        for key, value in filters.items():
            if key == "start_time":
                where_clauses.append("timestamp >= %(start_time)s")
                params["start_time"] = value
            elif key == "end_time":
                where_clauses.append("timestamp <= %(end_time)s")
                params["end_time"] = value
            elif key == "source":
                where_clauses.append("source = %(source)s")
                params["source"] = value
            elif key == "type":
                where_clauses.append("type = %(type)s")
                params["type"] = value
            elif key == "pattern_id":
                where_clauses.append("pattern_id = %(pattern_id)s")
                params["pattern_id"] = value
        
        # 构建查询语句
        query = f"SELECT * FROM {table}"
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += f" ORDER BY timestamp DESC LIMIT {limit}"
        
        # 执行查询
        rows = self.client.execute(query, params)
        
        # 处理结果
        if table == "raw_events":
            return self._process_raw_events(rows)
        elif table == "clean_events":
            return self._process_clean_events(rows)
        elif table == "pattern_events":
            return self._process_pattern_events(rows)
        else:
            self.logger.error(f"Unknown table: {table}")
            return []
    
    def _process_raw_events(self, rows: List[tuple]) -> List[Dict[str, Any]]:
        """
        处理原始事件查询结果
        
        Args:
            rows: 查询结果行
            
        Returns:
            处理后的事件列表
        """
        events = []
        
        for row in rows:
            event_id, source, event_type, timestamp, ingest_time, payload_str, meta_str = row
            
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = {}
            
            try:
                meta = json.loads(meta_str)
            except json.JSONDecodeError:
                meta = {}
            
            events.append({
                "event_id": event_id,
                "source": source,
                "type": event_type,
                "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else timestamp,
                "ingest_time": ingest_time.isoformat() if hasattr(ingest_time, "isoformat") else ingest_time,
                "payload": payload,
                "meta": meta
            })
        
        return events
    
    def _process_clean_events(self, rows: List[tuple]) -> List[Dict[str, Any]]:
        """
        处理处理后的事件查询结果
        
        Args:
            rows: 查询结果行
            
        Returns:
            处理后的事件列表
        """
        events = []
        
        for row in rows:
            event_id, source, event_type, timestamp, processing_time, payload_str, meta_str = row
            
            try:
                payload = json.loads(payload_str)
            except json.JSONDecodeError:
                payload = {}
            
            try:
                meta = json.loads(meta_str)
            except json.JSONDecodeError:
                meta = {}
            
            events.append({
                "event_id": event_id,
                "source": source,
                "type": event_type,
                "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else timestamp,
                "processing_time": processing_time.isoformat() if hasattr(processing_time, "isoformat") else processing_time,
                "payload": payload,
                "meta": meta
            })
        
        return events
    
    def _process_pattern_events(self, rows: List[tuple]) -> List[Dict[str, Any]]:
        """
        处理模式事件查询结果
        
        Args:
            rows: 查询结果行
            
        Returns:
            处理后的事件列表
        """
        events = []
        
        for row in rows:
            pattern_id, pattern_type, timestamp, source, details_str, contributors_str = row
            
            try:
                details = json.loads(details_str)
            except json.JSONDecodeError:
                details = {}
            
            try:
                contributors = json.loads(contributors_str)
            except json.JSONDecodeError:
                contributors = []
            
            events.append({
                "pattern_id": pattern_id,
                "type": pattern_type,
                "timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else timestamp,
                "source": source,
                "details": details,
                "contributors": contributors
            })
        
        return events