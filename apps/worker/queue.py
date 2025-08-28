import os
import sys
from typing import Dict, Any
from redis import Redis
from rq import Queue, Worker, Connection
from rq.job import Job
from core.config import settings
from apps.worker.jobs import JOB_REGISTRY


class QueueManager:
    """Manages Redis queues and job processing"""
    
    def __init__(self):
        self.redis_conn = Redis.from_url(settings.redis_url)
        self.queues = {
            "default": Queue("default", connection=self.redis_conn),
            "high": Queue("high", connection=self.redis_conn),
            "low": Queue("low", connection=self.redis_conn)
        }
    
    def enqueue_job(self, job_name: str, queue_name: str = "default", **kwargs) -> Job:
        """Enqueue a job"""
        if job_name not in JOB_REGISTRY:
            raise ValueError(f"Unknown job: {job_name}")
        
        queue = self.queues.get(queue_name, self.queues["default"])
        job = queue.enqueue(JOB_REGISTRY[job_name], **kwargs)
        
        return job
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a job"""
        job = Job.fetch(job_id, connection=self.redis_conn)
        
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "meta": job.meta
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job"""
        try:
            job = Job.fetch(job_id, connection=self.redis_conn)
            job.cancel()
            return True
        except Exception:
            return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get statistics for all queues"""
        stats = {}
        
        for name, queue in self.queues.items():
            stats[name] = {
                "name": name,
                "length": len(queue),
                "jobs": queue.jobs,
                "failed_jobs": len(queue.failed_job_registry),
                "deferred_jobs": len(queue.deferred_job_registry),
                "scheduled_jobs": len(queue.scheduled_job_registry)
            }
        
        return stats
    
    def clear_queue(self, queue_name: str) -> bool:
        """Clear all jobs from a queue"""
        try:
            queue = self.queues.get(queue_name)
            if queue:
                queue.empty()
                return True
            return False
        except Exception:
            return False


def start_worker(queue_names: list = None, worker_name: str = None):
    """Start an RQ worker"""
    if queue_names is None:
        queue_names = ["default"]
    
    with Connection(Redis.from_url(settings.redis_url)):
        worker = Worker(queue_names, name=worker_name)
        worker.work()


def start_high_priority_worker():
    """Start a high-priority worker"""
    start_worker(["high", "default"], "high-priority-worker")


def start_default_worker():
    """Start a default priority worker"""
    start_worker(["default"], "default-worker")


def start_low_priority_worker():
    """Start a low-priority worker"""
    start_worker(["low", "default"], "low-priority-worker")


# Convenience functions for enqueueing specific jobs
def enqueue_scoring_job(answer_id: str, queue_name: str = "high") -> str:
    """Enqueue a job to score an answer"""
    queue_manager = QueueManager()
    job = queue_manager.enqueue_job("score_answer", queue_name, answer_id=answer_id)
    return job.id


def enqueue_audio_processing_job(answer_id: str, audio_url: str, queue_name: str = "default") -> str:
    """Enqueue a job to process audio"""
    queue_manager = QueueManager()
    job = queue_manager.enqueue_job("process_audio", queue_name, answer_id=answer_id, audio_url=audio_url)
    return job.id


def enqueue_embedding_generation_job(artifact_id: str, queue_name: str = "low") -> str:
    """Enqueue a job to generate embeddings"""
    queue_manager = QueueManager()
    job = queue_manager.enqueue_job("generate_embeddings", queue_name, artifact_id=artifact_id)
    return job.id


def enqueue_session_cleanup_job(session_id: str, queue_name: str = "low") -> str:
    """Enqueue a job to cleanup session data"""
    queue_manager = QueueManager()
    job = queue_manager.enqueue_job("cleanup_session", queue_name, session_id=session_id)
    return job.id


if __name__ == "__main__":
    # Command line interface for starting workers
    if len(sys.argv) > 1:
        worker_type = sys.argv[1]
        
        if worker_type == "high":
            start_high_priority_worker()
        elif worker_type == "low":
            start_low_priority_worker()
        else:
            start_default_worker()
    else:
        start_default_worker()
