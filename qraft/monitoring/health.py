import asyncio
import time
from typing import Dict, Any, List, Optional

from loguru import logger


class HealthCheck:
    """健康检查器，用于监控系统健康状态"""
    
    def __init__(self):
        """初始化健康检查器"""
        self.components = {}
        self.logger = logger.bind(component="health_check")
    
    def register_component(self, name: str, check_func):
        """注册组件
        
        Args:
            name: 组件名称
            check_func: 检查函数，返回(bool, str)元组
        """
        self.components[name] = {
            "check_func": check_func,
            "status": "unknown",
            "message": "Not checked yet",
            "last_check": 0,
            "last_success": 0
        }
    
    async def check_component(self, name: str) -> Dict[str, Any]:
        """检查组件健康状态
        
        Args:
            name: 组件名称
            
        Returns:
            组件状态
        """
        if name not in self.components:
            return {
                "name": name,
                "status": "unknown",
                "message": "Component not registered",
                "last_check": 0,
                "last_success": 0
            }
        
        component = self.components[name]
        check_func = component["check_func"]
        
        try:
            # 执行检查
            status, message = await check_func()
            
            # 更新状态
            now = time.time()
            component["status"] = "healthy" if status else "unhealthy"
            component["message"] = message
            component["last_check"] = now
            if status:
                component["last_success"] = now
            
            return {
                "name": name,
                "status": component["status"],
                "message": component["message"],
                "last_check": component["last_check"],
                "last_success": component["last_success"]
            }
        except Exception as e:
            # 更新状态
            now = time.time()
            component["status"] = "unhealthy"
            component["message"] = str(e)
            component["last_check"] = now
            
            self.logger.error(f"Health check error for {name}: {e}")
            
            return {
                "name": name,
                "status": component["status"],
                "message": component["message"],
                "last_check": component["last_check"],
                "last_success": component["last_success"]
            }
    
    async def check_all(self) -> Dict[str, Any]:
        """检查所有组件健康状态
        
        Returns:
            所有组件状态
        """
        results = {}
        overall_status = "healthy"
        
        for name in self.components:
            result = await self.check_component(name)
            results[name] = result
            
            if result["status"] == "unhealthy":
                overall_status = "unhealthy"
            elif result["status"] == "unknown" and overall_status == "healthy":
                overall_status = "unknown"
        
        return {
            "status": overall_status,
            "components": results
        }


# 全局健康检查实例
health_check = HealthCheck()


# 示例检查函数
async def check_nats():
    """检查NATS连接
    
    Returns:
        (状态, 消息)元组
    """
    try:
        # 从依赖注入获取NATS客户端
        from qraft.api.main import app
        nats_client = app.state.nats_client
        
        # 检查连接状态
        if nats_client and nats_client.is_connected:
            return True, "Connected"
        else:
            return False, "Not connected"
    except Exception as e:
        return False, str(e)


async def check_clickhouse():
    """检查ClickHouse连接
    
    Returns:
        (状态, 消息)元组
    """
    try:
        # 从依赖注入获取ClickHouse客户端
        from qraft.api.main import app
        clickhouse_client = app.state.clickhouse_client
        
        # 执行简单查询
        result = clickhouse_client.client.execute("SELECT 1")
        if result and result[0][0] == 1:
            return True, "Connected"
        else:
            return False, "Query failed"
    except Exception as e:
        return False, str(e)