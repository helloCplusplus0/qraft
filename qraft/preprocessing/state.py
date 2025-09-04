import json
import os
from typing import Dict, Any, Optional

from loguru import logger


class StateManager:
    """状态管理器，用于管理有状态操作符的状态"""
    
    def __init__(self, state_dir: str = "./data/states"):
        """
        初始化状态管理器
        
        Args:
            state_dir: 状态文件目录
        """
        self.state_dir = state_dir
        self.states: Dict[str, Dict[str, Any]] = {}
        self.logger = logger.bind(component="state_manager")
        
        # 创建状态目录
        os.makedirs(state_dir, exist_ok=True)
    
    def get_state(self, operator_id: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        获取操作符状态
        
        Args:
            operator_id: 操作符ID
            default: 默认状态
            
        Returns:
            操作符状态
        """
        if default is None:
            default = {}
        
        if operator_id not in self.states:
            # 尝试从文件加载
            state_file = os.path.join(self.state_dir, f"{operator_id}.json")
            if os.path.exists(state_file):
                try:
                    with open(state_file, "r") as f:
                        self.states[operator_id] = json.load(f)
                except Exception as e:
                    self.logger.error(f"Failed to load state for {operator_id}: {e}")
                    self.states[operator_id] = default.copy()
            else:
                self.states[operator_id] = default.copy()
        
        return self.states[operator_id]
    
    def set_state(self, operator_id: str, state: Dict[str, Any]):
        """
        设置操作符状态
        
        Args:
            operator_id: 操作符ID
            state: 操作符状态
        """
        self.states[operator_id] = state
    
    def save_state(self, operator_id: str):
        """
        保存操作符状态到文件
        
        Args:
            operator_id: 操作符ID
        """
        if operator_id in self.states:
            state_file = os.path.join(self.state_dir, f"{operator_id}.json")
            try:
                with open(state_file, "w") as f:
                    json.dump(self.states[operator_id], f)
            except Exception as e:
                self.logger.error(f"Failed to save state for {operator_id}: {e}")
    
    def save_all_states(self):
        """保存所有操作符状态到文件"""
        for operator_id in self.states:
            self.save_state(operator_id)
    
    def clear_state(self, operator_id: str):
        """
        清除操作符状态
        
        Args:
            operator_id: 操作符ID
        """
        if operator_id in self.states:
            del self.states[operator_id]
            
            # 删除状态文件
            state_file = os.path.join(self.state_dir, f"{operator_id}.json")
            if os.path.exists(state_file):
                try:
                    os.remove(state_file)
                except Exception as e:
                    self.logger.error(f"Failed to delete state file for {operator_id}: {e}")