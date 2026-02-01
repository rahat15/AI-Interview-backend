"""
Performance Monitoring and Metrics Collection
Tracks API response times and LLM performance
"""

import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from contextlib import asynccontextmanager
from functools import wraps
import asyncio

from core.db import get_database

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Track and log performance metrics"""
    
    def __init__(self):
        self.metrics: Dict[str, list] = {
            "llm_calls": [],
            "api_requests": [],
            "cache_hits": [],
            "cache_misses": []
        }
    
    def record_llm_call(self, duration: float, model: str, operation: str):
        """Record LLM API call timing"""
        self.metrics["llm_calls"].append({
            "duration": duration,
            "model": model,
            "operation": operation,
            "timestamp": time.time()
        })
        
        logger.info(f"🤖 LLM Call: {operation} with {model} took {duration:.2f}s")
        
        # Alert on slow calls
        if duration > 5.0:
            logger.warning(f"⚠️ SLOW LLM CALL: {operation} took {duration:.2f}s")
    
    def record_api_request(self, endpoint: str, duration: float):
        """Record API request timing"""
        self.metrics["api_requests"].append({
            "endpoint": endpoint,
            "duration": duration,
            "timestamp": time.time()
        })
        
        logger.info(f"🌐 API Request: {endpoint} took {duration:.2f}s")
        
        # Alert on slow requests
        if duration > 3.0:
            logger.warning(f"⚠️ SLOW API: {endpoint} took {duration:.2f}s")
    
    def record_cache_hit(self, cache_key: str):
        """Record cache hit"""
        self.metrics["cache_hits"].append({
            "key": cache_key,
            "timestamp": time.time()
        })
        logger.debug(f"✅ Cache HIT: {cache_key}")
    
    def record_cache_miss(self, cache_key: str):
        """Record cache miss"""
        self.metrics["cache_misses"].append({
            "key": cache_key,
            "timestamp": time.time()
        })
        logger.debug(f"❌ Cache MISS: {cache_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        llm_durations = [m["duration"] for m in self.metrics["llm_calls"]]
        api_durations = [m["duration"] for m in self.metrics["api_requests"]]
        
        total_cache = len(self.metrics["cache_hits"]) + len(self.metrics["cache_misses"])
        cache_hit_rate = len(self.metrics["cache_hits"]) / total_cache if total_cache > 0 else 0
        
        return {
            "llm_calls": {
                "total": len(llm_durations),
                "avg_duration": sum(llm_durations) / len(llm_durations) if llm_durations else 0,
                "min_duration": min(llm_durations) if llm_durations else 0,
                "max_duration": max(llm_durations) if llm_durations else 0
            },
            "api_requests": {
                "total": len(api_durations),
                "avg_duration": sum(api_durations) / len(api_durations) if api_durations else 0,
                "min_duration": min(api_durations) if api_durations else 0,
                "max_duration": max(api_durations) if api_durations else 0
            },
            "cache": {
                "hits": len(self.metrics["cache_hits"]),
                "misses": len(self.metrics["cache_misses"]),
                "hit_rate": cache_hit_rate,
                "hit_rate_percentage": f"{cache_hit_rate * 100:.1f}%"
            }
        }
    
    def reset_metrics(self):
        """Reset all metrics"""
        self.metrics = {
            "llm_calls": [],
            "api_requests": [],
            "cache_hits": [],
            "cache_misses": []
        }
        logger.info("🔄 Metrics reset")
    
    async def save_to_db(self, session_id: Optional[str] = None):
        """Save metrics to MongoDB for analysis"""
        try:
            db = await get_database()
            
            doc = {
                "timestamp": datetime.utcnow(),
                "session_id": session_id,
                "stats": self.get_stats(),
                "raw_metrics": self.metrics
            }
            
            await db.performance_metrics.insert_one(doc)
            logger.info(f"💾 Saved metrics to database")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")


# Global monitor instance
monitor = PerformanceMonitor()


# Decorators for easy monitoring
def track_llm_call(model: str, operation: str):
    """Decorator to track LLM API calls"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                monitor.record_llm_call(duration, model, operation)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                monitor.record_llm_call(duration, model, operation)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


def track_api_request(endpoint: str):
    """Decorator to track API request timing"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                monitor.record_api_request(endpoint, duration)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                monitor.record_api_request(endpoint, duration)
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator


@asynccontextmanager
async def track_operation(name: str, operation_type: str = "general"):
    """Context manager for tracking any operation"""
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        logger.info(f"⏱️ {operation_type}: {name} took {duration:.2f}s")
        
        if operation_type == "llm":
            monitor.record_llm_call(duration, "unknown", name)
        elif operation_type == "api":
            monitor.record_api_request(name, duration)


class RequestTimer:
    """Simple timer for tracking request duration"""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, *args):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        logger.info(f"⏱️ {self.name}: {duration:.3f}s")
    
    @property
    def duration(self) -> float:
        if self.end_time and self.start_time:
            return self.end_time - self.start_time
        return 0.0


# Performance tips logger
def log_performance_tips():
    """Log performance optimization tips"""
    stats = monitor.get_stats()
    
    tips = []
    
    # Check LLM performance
    if stats["llm_calls"]["avg_duration"] > 2.0:
        tips.append("💡 Consider using faster models (gemini-2.5-flash) for non-critical operations")
    
    # Check cache hit rate
    if stats["cache"]["hit_rate"] < 0.5:
        tips.append("💡 Low cache hit rate - consider increasing cache TTL or warming cache")
    
    # Check API response times
    if stats["api_requests"]["avg_duration"] > 1.5:
        tips.append("💡 High API latency - review async operations and caching strategy")
    
    if tips:
        logger.info("🎯 Performance Optimization Suggestions:")
        for tip in tips:
            logger.info(f"   {tip}")


# Export for easy access
__all__ = [
    "monitor",
    "track_llm_call",
    "track_api_request",
    "track_operation",
    "RequestTimer",
    "log_performance_tips"
]
