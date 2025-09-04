from datetime import datetime
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field


class EventResponse(BaseModel):
    """事件响应模型"""
    event_id: str
    source: str
    type: str
    timestamp: str
    payload: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PatternResponse(BaseModel):
    """模式响应模型"""
    pattern_id: str
    type: str
    timestamp: str
    source: str
    details: Dict[str, Any] = Field(default_factory=dict)
    contributors: List[Dict[str, Any]] = Field(default_factory=list)
    explanation: Optional[str] = None


class FeedbackRequest(BaseModel):
    """反馈请求模型"""
    user_id: str
    rating: int = Field(..., ge=-1, le=1, description="-1: 负面, 0: 中性, 1: 正面")
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    """反馈响应模型"""
    feedback_id: str
    pattern_id: str
    timestamp: str
    status: str


class SourceResponse(BaseModel):
    """数据源响应模型"""
    name: str


class PatternTypeResponse(BaseModel):
    """模式类型响应模型"""
    name: str