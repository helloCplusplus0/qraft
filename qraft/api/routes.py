from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from qraft.api.models import (
    EventResponse, PatternResponse, FeedbackRequest, FeedbackResponse,
    SourceResponse, PatternTypeResponse
)


router = APIRouter()


@router.get("/events", response_model=List[EventResponse])
async def get_events(
    source: Optional[str] = None,
    event_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """获取事件列表
    
    Args:
        source: 数据源
        event_type: 事件类型
        start_time: 开始时间
        end_time: 结束时间
        limit: 限制数量
        
    Returns:
        事件列表
    """
    # 构建过滤条件
    filters = {}
    if source:
        filters["source"] = source
    if event_type:
        filters["type"] = event_type
    if start_time:
        filters["start_time"] = start_time
    if end_time:
        filters["end_time"] = end_time
    
    try:
        # 从依赖注入获取ClickHouse客户端
        from qraft.api.main import app
        clickhouse_client = app.state.clickhouse_client
        
        # 查询事件
        events = await clickhouse_client.query_events("clean_events", filters, limit)
        return events
    except Exception as e:
        logger.error(f"Get events error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns", response_model=List[PatternResponse])
async def get_patterns(
    source: Optional[str] = None,
    pattern_type: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """获取模式列表
    
    Args:
        source: 数据源
        pattern_type: 模式类型
        start_time: 开始时间
        end_time: 结束时间
        limit: 限制数量
        
    Returns:
        模式列表
    """
    # 构建过滤条件
    filters = {}
    if source:
        filters["source"] = source
    if pattern_type:
        filters["type"] = pattern_type
    if start_time:
        filters["start_time"] = start_time
    if end_time:
        filters["end_time"] = end_time
    
    try:
        # 从依赖注入获取ClickHouse客户端
        from qraft.api.main import app
        clickhouse_client = app.state.clickhouse_client
        
        # 查询模式
        patterns = await clickhouse_client.query_events("pattern_events", filters, limit)
        
        # 格式化模式
        from qraft.patterns.formatter import PatternFormatter
        formatter = PatternFormatter()
        formatted_patterns = [formatter.format_pattern(pattern) for pattern in patterns]
        
        return formatted_patterns
    except Exception as e:
        logger.error(f"Get patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{pattern_id}", response_model=PatternResponse)
async def get_pattern(pattern_id: str):
    """获取模式详情
    
    Args:
        pattern_id: 模式ID
        
    Returns:
        模式详情
    """
    try:
        # 从依赖注入获取ClickHouse客户端
        from qraft.api.main import app
        clickhouse_client = app.state.clickhouse_client
        
        # 查询模式
        patterns = await clickhouse_client.query_events("pattern_events", {"pattern_id": pattern_id}, 1)
        
        if not patterns:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # 格式化模式
        from qraft.patterns.formatter import PatternFormatter
        formatter = PatternFormatter()
        pattern = formatter.format_pattern(patterns[0])
        
        return pattern
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get pattern error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/{pattern_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(pattern_id: str, feedback: FeedbackRequest):
    """提交模式反馈
    
    Args:
        pattern_id: 模式ID
        feedback: 反馈数据
        
    Returns:
        反馈结果
    """
    try:
        # 从依赖注入获取ClickHouse客户端
        from qraft.api.main import app
        clickhouse_client = app.state.clickhouse_client
        
        # 检查模式是否存在
        patterns = await clickhouse_client.query_events("pattern_events", {"pattern_id": pattern_id}, 1)
        
        if not patterns:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        # 创建反馈数据
        import uuid
        from datetime import datetime
        
        feedback_data = {
            "feedback_id": str(uuid.uuid4()),
            "pattern_id": pattern_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": feedback.user_id,
            "rating": feedback.rating,
            "comment": feedback.comment
        }
        
        # 插入反馈
        await clickhouse_client.insert_pattern_feedback(feedback_data)
        
        return {
            "feedback_id": feedback_data["feedback_id"],
            "pattern_id": pattern_id,
            "timestamp": feedback_data["timestamp"],
            "status": "success"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", response_model=List[SourceResponse])
async def get_sources():
    """获取数据源列表
    
    Returns:
        数据源列表
    """
    try:
        # 从依赖注入获取ClickHouse客户端
        from qraft.api.main import app
        clickhouse_client = app.state.clickhouse_client
        
        # 查询唯一数据源
        query = "SELECT DISTINCT source FROM clean_events"
        rows = clickhouse_client.client.execute(query)
        
        sources = []
        for row in rows:
            sources.append({"name": row[0]})
        
        return sources
    except Exception as e:
        logger.error(f"Get sources error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pattern-types", response_model=List[PatternTypeResponse])
async def get_pattern_types():
    """获取模式类型列表
    
    Returns:
        模式类型列表
    """
    try:
        # 从依赖注入获取ClickHouse客户端
        from qraft.api.main import app
        clickhouse_client = app.state.clickhouse_client
        
        # 查询唯一模式类型
        query = "SELECT DISTINCT type FROM pattern_events"
        rows = clickhouse_client.client.execute(query)
        
        pattern_types = []
        for row in rows:
            pattern_types.append({"name": row[0]})
        
        return pattern_types
    except Exception as e:
        logger.error(f"Get pattern types error: {e}")
        raise HTTPException(status_code=500, detail=str(e))