#!/usr/bin/env python3
"""
情感分析压力测试脚本
测试系统在高负载下的稳定性和性能
"""

import time
import threading
import queue
import logging
from datetime import datetime

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
    "工作上遇到了困难，需要想办法解决。",
    "这部电影的特效非常震撼，剧情也很吸引人。",
    "这个品牌的产品一直都很可靠，值得信赖。",
    "今天的会议很有成效，解决了很多问题。",
    "最近工作进展顺利，感觉很有成就感。",
    "这个景点的风景真美，下次还想再来。",
    "服务态度非常差，再也不会来了。",
    "这个价格太离谱了，完全不值得。",
    "质量很好，性价比高，推荐购买。",
    "物流速度很快，包装也很精美。",
    "客服态度很好，问题解决得很及时。"
]

class StressTestWorker(threading.Thread):
    """压力测试工作线程"""
    def __init__(self, worker_id, task_queue, results_queue):
        super().__init__()
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.results_queue = results_queue
        self.running = True
    
    def run(self):
        while self.running:
            try:
                # 从队列获取任务，超时1秒
                text = self.task_queue.get(timeout=1)
                if text is None:
                    # 收到终止信号
                    break
                
                start_time = time.time()
                result = SentimentService.analyze(text, mode="simple")
                end_time = time.time()
                
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                self.results_queue.put({
                    "worker_id": self.worker_id,
                    "response_time": response_time,
                    "success": True
                })
                
                self.task_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.results_queue.put({
                    "worker_id": self.worker_id,
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                })
                self.task_queue.task_done()

def run_stress_test(duration_seconds, concurrency, requests_per_second):
    """运行压力测试
    
    Args:
        duration_seconds: 测试持续时间（秒）
        concurrency: 并发线程数
        requests_per_second: 每秒请求数
    """
    logger.info(f"\n开始压力测试: 持续时间={duration_seconds}秒, 并发数={concurrency}, 每秒请求数={requests_per_second}")
    
    # 重置缓存统计
    SentimentService.reset_cache_stats()
    
    # 初始化任务队列和结果队列
    task_queue = queue.Queue()
    results_queue = queue.Queue()
    
    # 启动工作线程
    workers = []
    for i in range(concurrency):
        worker = StressTestWorker(i, task_queue, results_queue)
        worker.start()
        workers.append(worker)
    
    # 计算每个批次的请求数和间隔
    batch_interval = 1.0 / requests_per_second
    total_requests = 0
    start_time = time.time()
    end_time = start_time + duration_seconds
    
    # 生成测试任务
    while time.time() < end_time:
        # 从测试数据中随机选择文本
        text = test_texts[total_requests % len(test_texts)]
        task_queue.put(text)
        total_requests += 1
        
        # 控制请求速率
        time.sleep(batch_interval)
    
    # 等待所有任务完成
    task_queue.join()
    
    # 发送终止信号给所有工作线程
    for _ in workers:
        task_queue.put(None)
    
    # 等待所有工作线程结束
    for worker in workers:
        worker.running = False
        worker.join()
    
    # 收集测试结果
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    
    # 计算统计数据
    successful_requests = sum(1 for r in results if r['success'])
    failed_requests = len(results) - successful_requests
    response_times = [r['response_time'] for r in results if r['success']]
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    min_response_time = min(response_times) if response_times else 0
    max_response_time = max(response_times) if response_times else 0
    
    # 计算实际吞吐量
    actual_duration = time.time() - start_time
    actual_throughput = len(results) / actual_duration
    
    # 获取缓存统计
    cache_stats = SentimentService.get_cache_stats()
    
    # 输出测试结果
    logger.info("\n压力测试结果:")
    logger.info(f"总请求数: {len(results)}")
    logger.info(f"成功请求数: {successful_requests}")
    logger.info(f"失败请求数: {failed_requests}")
    logger.info(f"成功率: {successful_requests / len(results) * 100:.2f}%")
    logger.info(f"平均响应时间: {avg_response_time:.2f} ms")
    logger.info(f"最小响应时间: {min_response_time:.2f} ms")
    logger.info(f"最大响应时间: {max_response_time:.2f} ms")
    logger.info(f"实际吞吐量: {actual_throughput:.2f} 请求/秒")
    logger.info(f"缓存命中率: {cache_stats['cache_stats']['hit_rate']}")
    
    return {
        "total_requests": len(results),
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": successful_requests / len(results) * 100,
        "avg_response_time": avg_response_time,
        "min_response_time": min_response_time,
        "max_response_time": max_response_time,
        "throughput": actual_throughput,
        "cache_stats": cache_stats
    }

def test_different_load_levels():
    """测试不同负载水平下的性能"""
    logger.info("=== 开始不同负载水平测试 ===")
    
    # 测试配置
    test_configs = [
        # (持续时间, 并发数, 每秒请求数)
        (30, 5, 10),    # 低负载
        (30, 10, 50),   # 中等负载
        (30, 20, 100),  # 高负载
        (60, 30, 200),  # 极高负载
    ]
    
    test_results = []
    
    for config in test_configs:
        duration, concurrency, rps = config
        result = run_stress_test(duration, concurrency, rps)
        test_results.append({
            "duration": duration,
            "concurrency": concurrency,
            "target_rps": rps,
            "actual_rps": result["throughput"],
            "success_rate": result["success_rate"],
            "avg_response_time": result["avg_response_time"]
        })
    
    logger.info("\n=== 负载测试总结 ===")
    for result in test_results:
        logger.info(f"持续时间={result['duration']}秒, 并发数={result['concurrency']}, 目标RPS={result['target_rps']}, 实际RPS={result['actual_rps']:.2f}, 成功率={result['success_rate']:.2f}%, 平均响应时间={result['avg_response_time']:.2f}ms")
    
    return test_results

def test_peak_load():
    """测试系统的峰值负载能力"""
    logger.info("\n=== 开始峰值负载测试 ===")
    
    # 逐渐增加负载直到系统开始出现故障
    concurrency = 10
    rps = 50
    max_rps = 500
    step = 50
    
    while rps <= max_rps:
        logger.info(f"测试 RPS={rps}")
        result = run_stress_test(10, concurrency, rps)
        
        if result["success_rate"] < 95:
            logger.info(f"系统在 RPS={rps} 时开始出现性能下降，成功率={result['success_rate']:.2f}%")
            break
        
        rps += step
    
    return result

def main():
    """运行所有压力测试"""
    logger.info("=== 情感分析压力测试 ===")
    
    # 测试不同负载水平
    load_test_results = test_different_load_levels()
    
    # 测试峰值负载
    peak_result = test_peak_load()
    
    logger.info("\n=== 压力测试完成 ===")
    logger.info(f"系统峰值负载能力: {peak_result['throughput']:.2f} 请求/秒")
    logger.info(f"最大成功率: {peak_result['success_rate']:.2f}%")
    logger.info(f"对应平均响应时间: {peak_result['avg_response_time']:.2f} ms")

if __name__ == "__main__":
    main()
