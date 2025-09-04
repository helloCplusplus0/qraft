#!/usr/bin/env python3

"""
性能测试脚本，用于测试系统性能

用法:
    python benchmark.py --mode <模式> [--count <数量>] [--concurrency <并发数>] [--output <输出文件>]

参数:
    --mode: 测试模式，可选值：ingest, process, detect, api
    --count: 测试数量，默认为10000
    --concurrency: 并发数，默认为10
    --output: 输出文件，默认为benchmark_results.json
"""

import os
import sys
import json
import time
import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

import aiohttp
import nats
import numpy as np
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


async def generate_event(index: int) -> Dict[str, Any]:
    """生成测试事件
    
    Args:
        index: 事件索引
        
    Returns:
        事件数据
    """
    return {
        "event_id": f"benchmark-{index}-{int(time.time())}",
        "source": "benchmark",
        "type": "test",
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "index": index,
            "value": np.random.random(),
            "category": np.random.choice(["A", "B", "C"]),
            "flag": np.random.choice([True, False])
        },
        "meta": {
            "benchmark": True,
            "timestamp": time.time()
        }
    }


async def ingest_test(nats_client: nats.NATS, count: int, concurrency: int) -> Dict[str, Any]:
    """摄取性能测试
    
    Args:
        nats_client: NATS客户端
        count: 测试数量
        concurrency: 并发数
        
    Returns:
        测试结果
    """
    topic = "events.benchmark"
    results = []
    
    async def send_batch(batch_index: int, batch_size: int):
        batch_results = []
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, count)
        
        for i in range(start_index, end_index):
            event = await generate_event(i)
            start_time = time.time()
            await nats_client.publish(topic, json.dumps(event).encode())
            elapsed = time.time() - start_time
            batch_results.append(elapsed)
        
        return batch_results
    
    # 计算批次大小
    batch_size = (count + concurrency - 1) // concurrency
    batch_count = (count + batch_size - 1) // batch_size
    
    # 创建并发任务
    start_time = time.time()
    tasks = [send_batch(i, batch_size) for i in range(batch_count)]
    batch_results = await asyncio.gather(*tasks)
    total_elapsed = time.time() - start_time
    
    # 合并结果
    for batch in batch_results:
        results.extend(batch)
    
    # 计算统计数据
    latencies = np.array(results)
    stats = {
        "mode": "ingest",
        "count": count,
        "concurrency": concurrency,
        "total_time": total_elapsed,
        "throughput": count / total_elapsed,
        "latency": {
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "mean": float(np.mean(latencies)),
            "median": float(np.median(latencies)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99))
        }
    }
    
    logger.info(f"Ingest test completed: {count} events in {total_elapsed:.2f} seconds ({stats['throughput']:.2f} events/s)")
    logger.info(f"Latency (ms): min={stats['latency']['min']*1000:.2f}, mean={stats['latency']['mean']*1000:.2f}, p95={stats['latency']['p95']*1000:.2f}, max={stats['latency']['max']*1000:.2f}")
    
    return stats


async def api_test(count: int, concurrency: int, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """API性能测试
    
    Args:
        count: 测试数量
        concurrency: 并发数
        api_url: API地址
        
    Returns:
        测试结果
    """
    results = []
    
    async def send_batch(batch_index: int, batch_size: int):
        batch_results = []
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, count)
        
        async with aiohttp.ClientSession() as session:
            for i in range(start_index, end_index):
                start_time = time.time()
                async with session.get(f"{api_url}/api/events?limit=10") as response:
                    await response.json()
                elapsed = time.time() - start_time
                batch_results.append(elapsed)
        
        return batch_results
    
    # 计算批次大小
    batch_size = (count + concurrency - 1) // concurrency
    batch_count = (count + batch_size - 1) // batch_size
    
    # 创建并发任务
    start_time = time.time()
    tasks = [send_batch(i, batch_size) for i in range(batch_count)]
    batch_results = await asyncio.gather(*tasks)
    total_elapsed = time.time() - start_time
    
    # 合并结果
    for batch in batch_results:
        results.extend(batch)
    
    # 计算统计数据
    latencies = np.array(results)
    stats = {
        "mode": "api",
        "count": count,
        "concurrency": concurrency,
        "total_time": total_elapsed,
        "throughput": count / total_elapsed,
        "latency": {
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "mean": float(np.mean(latencies)),
            "median": float(np.median(latencies)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99))
        }
    }
    
    logger.info(f"API test completed: {count} requests in {total_elapsed:.2f} seconds ({stats['throughput']:.2f} requests/s)")
    logger.info(f"Latency (ms): min={stats['latency']['min']*1000:.2f}, mean={stats['latency']['mean']*1000:.2f}, p95={stats['latency']['p95']*1000:.2f}, max={stats['latency']['max']*1000:.2f}")
    
    return stats


async def process_test(nats_client: nats.NATS, count: int, concurrency: int) -> Dict[str, Any]:
    """处理性能测试
    
    Args:
        nats_client: NATS客户端
        count: 测试数量
        concurrency: 并发数
        
    Returns:
        测试结果
    """
    # 订阅处理后的事件
    processed_events = []
    processed_event = asyncio.Event()
    
    async def process_handler(msg):
        data = json.loads(msg.data.decode())
        meta = data.get("meta", {})
        
        if meta.get("benchmark"):
            send_time = meta.get("timestamp", 0)
            receive_time = time.time()
            latency = receive_time - send_time
            processed_events.append(latency)
            processed_event.set()
    
    # 订阅处理后的事件
    await nats_client.subscribe("processed.events", cb=process_handler)
    
    # 发送测试事件
    topic = "events.benchmark"
    
    async def send_batch(batch_index: int, batch_size: int):
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, count)
        
        for i in range(start_index, end_index):
            event = await generate_event(i)
            await nats_client.publish(topic, json.dumps(event).encode())
            
            # 等待事件处理完成
            processed_event.clear()
            try:
                await asyncio.wait_for(processed_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for event {i} to be processed")
    
    # 计算批次大小
    batch_size = (count + concurrency - 1) // concurrency
    batch_count = (count + batch_size - 1) // batch_size
    
    # 创建并发任务
    start_time = time.time()
    tasks = [send_batch(i, batch_size) for i in range(batch_count)]
    await asyncio.gather(*tasks)
    total_elapsed = time.time() - start_time
    
    # 计算统计数据
    latencies = np.array(processed_events)
    stats = {
        "mode": "process",
        "count": len(processed_events),
        "concurrency": concurrency,
        "total_time": total_elapsed,
        "throughput": len(processed_events) / total_elapsed,
        "latency": {
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "mean": float(np.mean(latencies)),
            "median": float(np.median(latencies)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99))
        }
    }
    
    logger.info(f"Process test completed: {len(processed_events)} events in {total_elapsed:.2f} seconds ({stats['throughput']:.2f} events/s)")
    logger.info(f"Latency (ms): min={stats['latency']['min']*1000:.2f}, mean={stats['latency']['mean']*1000:.2f}, p95={stats['latency']['p95']*1000:.2f}, max={stats['latency']['max']*1000:.2f}")
    
    return stats


async def detect_test(nats_client: nats.NATS, count: int, concurrency: int) -> Dict[str, Any]:
    """检测性能测试
    
    Args:
        nats_client: NATS客户端
        count: 测试数量
        concurrency: 并发数
        
    Returns:
        测试结果
    """
    # 订阅模式事件
    pattern_events = []
    pattern_event = asyncio.Event()
    
    async def pattern_handler(msg):
        data = json.loads(msg.data.decode())
        details = data.get("details", {})
        
        if details.get("benchmark"):
            send_time = details.get("timestamp", 0)
            receive_time = time.time()
            latency = receive_time - send_time
            pattern_events.append(latency)
            pattern_event.set()
    
    # 订阅模式事件
    await nats_client.subscribe("patterns", cb=pattern_handler)
    
    # 发送测试事件
    topic = "processed.events"
    
    async def send_batch(batch_index: int, batch_size: int):
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, count)
        
        for i in range(start_index, end_index):
            # 创建异常事件
            event = {
                "event_id": f"benchmark-{i}-{int(time.time())}",
                "source": "benchmark",
                "type": "test",
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "index": i,
                    "price": 100 + (i % 10) * 10,  # 价格波动
                    "volume": 1000 + (i % 5) * 100  # 成交量波动
                },
                "meta": {
                    "benchmark": True,
                    "timestamp": time.time()
                }
            }
            
            await nats_client.publish(topic, json.dumps(event).encode())
            
            # 等待模式检测完成
            pattern_event.clear()
            try:
                await asyncio.wait_for(pattern_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning(f"Timeout waiting for pattern from event {i} to be detected")
    
    # 计算批次大小
    batch_size = (count + concurrency - 1) // concurrency
    batch_count = (count + batch_size - 1) // batch_size
    
    # 创建并发任务
    start_time = time.time()
    tasks = [send_batch(i, batch_size) for i in range(batch_count)]
    await asyncio.gather(*tasks)
    total_elapsed = time.time() - start_time
    
    # 计算统计数据
    latencies = np.array(pattern_events)
    stats = {
        "mode": "detect",
        "count": len(pattern_events),
        "concurrency": concurrency,
        "total_time": total_elapsed,
        "throughput": len(pattern_events) / total_elapsed,
        "latency": {
            "min": float(np.min(latencies)),
            "max": float(np.max(latencies)),
            "mean": float(np.mean(latencies)),
            "median": float(np.median(latencies)),
            "p95": float(np.percentile(latencies, 95)),
            "p99": float(np.percentile(latencies, 99))
        }
    }
    
    logger.info(f"Detect test completed: {len(pattern_events)} patterns in {total_elapsed:.2f} seconds ({stats['throughput']:.2f} patterns/s)")
    logger.info(f"Latency (ms): min={stats['latency']['min']*1000:.2f}, mean={stats['latency']['mean']*1000:.2f}, p95={stats['latency']['p95']*1000:.2f}, max={stats['latency']['max']*1000:.2f}")
    
    return stats


async def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="Benchmark the system performance")
    parser.add_argument("--mode", required=True, choices=["ingest", "process", "detect", "api"], help="Test mode")
    parser.add_argument("--count", type=int, default=10000, help="Test count (default: 10000)")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrency (default: 10)")
    parser.add_argument("--output", default="benchmark_results.json", help="Output file (default: benchmark_results.json)")
    parser.add_argument("--nats", default="nats://localhost:4222", help="NATS server address")
    parser.add_argument("--api", default="http://localhost:8000", help="API server address")
    
    args = parser.parse_args()
    
    # 设置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # 连接NATS（除了API测试）
    nats_client = None
    if args.mode != "api":
        nats_client = await connect_nats(args.nats)
    
    try:
        # 执行测试
        logger.info(f"Starting {args.mode} benchmark (count: {args.count}, concurrency: {args.concurrency})")
        
        if args.mode == "ingest":
            stats = await ingest_test(nats_client, args.count, args.concurrency)
        elif args.mode == "process":
            stats = await process_test(nats_client, args.count, args.concurrency)
        elif args.mode == "detect":
            stats = await detect_test(nats_client, args.count, args.concurrency)
        elif args.mode == "api":
            stats = await api_test(args.count, args.concurrency, args.api)
        
        # 保存结果
        with open(args.output, "w") as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Results saved to {args.output}")
    finally:
        # 关闭NATS连接
        if nats_client:
            await nats_client.close()


if __name__ == "__main__":
    asyncio.run(main())