# apps/worker/queue.py

import sys
from typing import Dict, Any, List

from redis import Redis
from rq import Queue, Worker
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
            "low": Queue("low", connection=self.redis_conn),
        }

    def enqueue_job(self, job_name: str, queue_name: str = "default", **kwargs) -> Job:
        if job_name not in JOB_REGISTRY:
            raise ValueError(f"Unknown job: {job_name}")

        queue = self.queues.get(queue_name, self.queues["default"])
        return queue.enqueue(JOB_REGISTRY[job_name], **kwargs)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        job = Job.fetch(job_id, connection=self.redis_conn)
        return {
            "id": job.id,
            "status": job.get_status(),
            "result": job.result,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "ended_at": job.ended_at.isoformat() if job.ended_at else None,
            "meta": job.meta,
        }

    def cancel_job(self, job_id: str) -> bool:
        try:
            Job.fetch(job_id, connection=self.redis_conn).cancel()
            return True
        except Exception:
            return False

    def clear_queue(self, queue_name: str) -> bool:
        queue = self.queues.get(queue_name)
        if not queue:
            return False
        queue.empty()
        return True


# -------------------- WORKER STARTUP --------------------

def start_worker(queue_names: List[str] | None = None, worker_name: str | None = None):
    if queue_names is None:
        queue_names = ["default"]

    redis_conn = Redis.from_url(settings.redis_url)
    queues = [Queue(name, connection=redis_conn) for name in queue_names]

    worker = Worker(queues, connection=redis_conn, name=worker_name)
    worker.work()


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "default"

    if arg == "high":
        start_worker(["high", "default"], "high-priority-worker")
    elif arg == "low":
        start_worker(["low", "default"], "low-priority-worker")
    else:
        start_worker(["default"], "default-worker")
