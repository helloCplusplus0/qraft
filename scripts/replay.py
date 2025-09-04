#!/usr/bin/env python3

"""
数据回放脚本，用于回放历史数据进行测试

用法:
    python replay.py --source <数据源> --file <文件路径> [--rate <速率>] [--loop]

参数:
    --source: 数据源名称
    --file: 数据文件路径
    --rate: 回放速率，默认为1.0（实时）
    --loop: 循环回放
"""

import os
import sys
import json
import csv
import time
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

import nats
from loguru import logger


async def connect_nats(server: str = "nats://localhost:4222") -> nats.NATS:
    """连接NATS服务器
    
    Args:
        server: NATS服务器地址
        
    Returns:
        NATS客户端
    """
    try:
        client = await nats.connect(server)
        logger.info(f"Connected to NATS server at {server}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to NATS server: {e}")
        sys.exit(1)


def load_csv_data(file_path: str) -> List[Dict[str, Any]]:
    """加载CSV数据
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        数据列表
    """
    data = []
    
    try:
        with open(file_path, "r", newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(dict(row))
        
        logger.info(f"Loaded {len(data)} records from {file_path}")
        return data
    except Exception as e:
        logger.error(f"Failed to load CSV data: {e}")
        sys.exit(1)


def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """加载JSON数据
    
    Args:
        file_path: JSON文件路径
        
    Returns:
        数据列表
    """
    try:
        with open(file_path, "r") as jsonfile:
            data = json.load(jsonfile)
        
        if isinstance(data, list):
            logger.info(f"Loaded {len(data)} records from {file_path}")
            return data
        else:
            logger.info(f"Loaded 1 record from {file_path}")
            return [data]
    except Exception as e:
        logger.error(f"Failed to load JSON data: {e}")
        sys.exit(1)


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """加载数据
    
    Args:
        file_path: 数据文件路径
        
    Returns:
        数据列表
    """
    _, ext = os.path.splitext(file_path)
    
    if ext.lower() == ".csv":
        return load_csv_data(file_path)
    elif ext.lower() == ".json":
        return load_json_data(file_path)
    else:
        logger.error(f"Unsupported file format: {ext}")
        sys.exit(1)


async def replay_data(nats_client: nats.NATS, source: str, data: List[Dict[str, Any]], rate: float = 1.0, loop: bool = False):
    """回放数据
    
    Args:
        nats_client: NATS客户端
        source: 数据源名称
        data: 数据列表
        rate: 回放速率
        loop: 是否循环回放
    """
    if not data:
        logger.error("No data to replay")
        return
    
    topic = f"events.{source}"
    count = 0
    
    while True:
        start_time = time.time()
        
        for i, record in enumerate(data):
            # 创建事件
            event = {
                "event_id": f"replay-{i}-{int(time.time())}",
                "source": source,
                "type": "replay",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": record,
                "meta": {
                    "replay": True,
                    "original_index": i
                }
            }
            
            # 发布事件
            await nats_client.publish(topic, json.dumps(event).encode())
            count += 1
            
            # 按速率控制发送间隔
            if i < len(data) - 1 and rate > 0:
                await asyncio.sleep(1.0 / rate)
        
        elapsed = time.time() - start_time
        logger.info(f"Replayed {len(data)} records in {elapsed:.2f} seconds (rate: {len(data)/elapsed:.2f} records/s)")
        
        if not loop:
            break
    
    logger.info(f"Total records replayed: {count}")


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Replay data for testing")
    parser.add_argument("--source", required=True, help="Data source name")
    parser.add_argument("--file", required=True, help="Data file path")
    parser.add_argument("--rate", type=float, default=1.0, help="Replay rate (default: 1.0)")
    parser.add_argument("--loop", action="store_true", help="Loop replay")
    parser.add_argument("--nats", default="nats://localhost:4222", help="NATS server address")
    
    args = parser.parse_args()
    
    # 设置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # 连接NATS
    nats_client = await connect_nats(args.nats)
    
    try:
        # 加载数据
        data = load_data(args.file)
        
        # 回放数据
        logger.info(f"Starting replay from {args.file} to {args.source} (rate: {args.rate}, loop: {args.loop})")
        await replay_data(nats_client, args.source, data, args.rate, args.loop)
    finally:
        # 关闭NATS连接
        await nats_client.close()


if __name__ == "__main__":
    asyncio.run(main())