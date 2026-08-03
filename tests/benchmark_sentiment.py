#!/usr/bin/env python3
"""
情感分析性能测试脚本
测试响应时间、吞吐量和缓存命中率
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import logging

from src.services.sentiment_service import SentimentService

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 测试数据
test_texts = [
    "这部电影真的很棒，演员表演出色，剧情紧凑，推荐大家观看！",
    "这个产品质量太差了，用了几天就坏了，非常失望。",
    "今天天气不错，心情很好，准备出去走走。",
    "工作压力很大，感觉有点疲惫，希望能早点休息。",
    "这家餐厅的食物味道很好，服务也很周到，下次还会再来。",
    "交通拥堵严重，上班迟到了，心情很糟糕。",
    "收到了期待已久的礼物，非常开心！",
    "最近身体不太舒服，需要好好调理一下。",
    "假期过得很愉快，和家人一起旅行很开心。",
    "工作上遇到了困难，需要想办法解决。"
]

# 重复测试数据以增加测试量
test_texts = test_texts * 10  # 100条测试数据

def test_single_requests():
    """测试单个请求的响应时间"""
    logger.info("开始测试单个请求响应时间...")
    
    # 先预热缓存
    for text in test_texts[:10]:
        SentimentService.analyze(text, mode="simple")
    
    # 重置缓存统计
    SentimentService.reset_cache_stats()
    
    response_times = []
    for i, text in enumerate(test_texts):
        start_time = time.time()
        result = SentimentService.analyze(text, mode="simple")
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        response_times.append(response_time)
        
        if (i + 1) % 10 == 0:
            logger.info(f"已完成 {i + 1}/{len(test_texts)} 个请求")
    
    # 计算统计数据
    avg_time = statistics.mean(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    std_time = statistics.stdev(response_times) if len(response_times) > 1 else 0
    
    # 获取缓存统计
    cache_stats = SentimentService.get_cache_stats()
    
    logger.info("\n单个请求测试结果:")
    logger.info(f"平均响应时间: {avg_time:.2f} ms")
    logger.info(f"最小响应时间: {min_time:.2f} ms")
    logger.info(f"最大响应时间: {max_time:.2f} ms")
    logger.info(f"响应时间标准差: {std_time:.2f} ms")
    logger.info(f"缓存命中率: {cache_stats['cache_stats']['hit_rate']}")
    logger.info(f"缓存命中次数: {cache_stats['cache_stats']['hits']}")
    logger.info(f"缓存未命中次数: {cache_stats['cache_stats']['misses']}")
    
    return {
        "avg_time": avg_time,
        "min_time": min_time,
        "max_time": max_time,
        "std_time": std_time,
        "cache_stats": cache_stats
    }

def test_batch_requests():
    """测试批量请求的响应时间和吞吐量"""
    logger.info("\n开始测试批量请求响应时间...")
    
    # 重置缓存统计
    SentimentService.reset_cache_stats()
    
    # 测试不同批量大小
    batch_sizes = [10, 50, 100]
    batch_results = []
    
    for batch_size in batch_sizes:
        # 准备批量数据
        batch_texts = test_texts[:batch_size]
        
        start_time = time.time()
        results = SentimentService.analyze_batch(batch_texts, mode="simple")
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000  # 转换为毫秒
        avg_time_per_request = total_time / batch_size
        throughput = batch_size / (end_time - start_time)  # 请求/秒
        
        batch_results.append({
            "batch_size": batch_size,
            "total_time": total_time,
            "avg_time_per_request": avg_time_per_request,
            "throughput": throughput
        })
        
        logger.info(f"批量大小 {batch_size}: 总时间 {total_time:.2f} ms, 平均每请求 {avg_time_per_request:.2f} ms, 吞吐量 {throughput:.2f} 请求/秒")
    
    # 获取缓存统计
    cache_stats = SentimentService.get_cache_stats()
    
    logger.info("\n批量请求测试结果:")
    for result in batch_results:
        logger.info(f"批量大小 {result['batch_size']}: 总时间 {result['total_time']:.2f} ms, 平均每请求 {result['avg_time_per_request']:.2f} ms, 吞吐量 {result['throughput']:.2f} 请求/秒")
    logger.info(f"缓存命中率: {cache_stats['cache_stats']['hit_rate']}")
    
    return batch_results

def test_concurrent_requests():
    """测试并发请求的性能"""
    logger.info("\n开始测试并发请求性能...")
    
    # 重置缓存统计
    SentimentService.reset_cache_stats()
    
    # 测试不同并发数
    concurrency_levels = [5, 10, 20]
    concurrent_results = []
    
    for concurrency in concurrency_levels:
        start_time = time.time()
        
        # 使用线程池执行并发请求
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            # 每个线程处理相同的文本集
            futures = []
            for i in range(concurrency):
                # 每个线程处理部分文本
                batch_size = len(test_texts) // concurrency
                start_idx = i * batch_size
                end_idx = (i + 1) * batch_size if i < concurrency - 1 else len(test_texts)
                batch_texts = test_texts[start_idx:end_idx]
                
                futures.append(executor.submit(SentimentService.analyze_batch, batch_texts, "simple"))
            
            # 等待所有任务完成
            for future in futures:
                future.result()
        
        end_time = time.time()
        total_time = end_time - start_time
        total_requests = len(test_texts)
        throughput = total_requests / total_time  # 请求/秒
        avg_time_per_request = (total_time * 1000) / total_requests  # 毫秒/请求
        
        concurrent_results.append({
            "concurrency": concurrency,
            "total_time": total_time,
            "throughput": throughput,
            "avg_time_per_request": avg_time_per_request
        })
        
        logger.info(f"并发数 {concurrency}: 总时间 {total_time:.2f} 秒, 吞吐量 {throughput:.2f} 请求/秒, 平均每请求 {avg_time_per_request:.2f} ms")
    
    # 获取缓存统计
    cache_stats = SentimentService.get_cache_stats()
    
    logger.info("\n并发请求测试结果:")
    for result in concurrent_results:
        logger.info(f"并发数 {result['concurrency']}: 总时间 {result['total_time']:.2f} 秒, 吞吐量 {result['throughput']:.2f} 请求/秒, 平均每请求 {result['avg_time_per_request']:.2f} ms")
    logger.info(f"缓存命中率: {cache_stats['cache_stats']['hit_rate']}")
    
    return concurrent_results

def test_different_modes():
    """测试不同分析模式的性能"""
    logger.info("\n开始测试不同分析模式的性能...")
    
    modes = ["simple", "custom"]
    mode_results = []
    
    for mode in modes:
        # 重置缓存统计
        SentimentService.reset_cache_stats()
        
        start_time = time.time()
        results = SentimentService.analyze_batch(test_texts[:50], mode=mode)
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000  # 转换为毫秒
        avg_time_per_request = total_time / 50
        
        # 获取缓存统计
        cache_stats = SentimentService.get_cache_stats()
        
        mode_results.append({
            "mode": mode,
            "total_time": total_time,
            "avg_time_per_request": avg_time_per_request,
            "cache_hit_rate": cache_stats['cache_stats']['hit_rate']
        })
        
        logger.info(f"模式 {mode}: 总时间 {total_time:.2f} ms, 平均每请求 {avg_time_per_request:.2f} ms, 缓存命中率 {cache_stats['cache_stats']['hit_rate']}")
    
    return mode_results

def main():
    """运行所有性能测试"""
    logger.info("=== 情感分析性能测试 ===")
    
    # 测试单个请求
    single_results = test_single_requests()
    
    # 测试批量请求
    batch_results = test_batch_requests()
    
    # 测试并发请求
    concurrent_results = test_concurrent_requests()
    
    # 测试不同模式
    mode_results = test_different_modes()
    
    logger.info("\n=== 性能测试完成 ===")
    logger.info("总结:")
    logger.info(f"单个请求平均响应时间: {single_results['avg_time']:.2f} ms")
    logger.info(f"最大吞吐量 (并发): {max(r['throughput'] for r in concurrent_results):.2f} 请求/秒")
    logger.info(f"最佳批量大小: {max(batch_results, key=lambda x: x['throughput'])['batch_size']}")

if __name__ == "__main__":
    main()
