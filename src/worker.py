import uuid
from threading import Thread
from typing import Optional
from job_entity import JobEntity
from logger import base_logger
from job_status import JobStatus
import time
import random
from datetime import datetime, timedelta


class ConcurrentWorker(Thread):
    """Concurrent static thread worker domain object."""
    def __init__(self, worker_name: str, job_scheduler: "JobScheduler"):
        super().__init__(name=worker_name, daemon=True)
        self.worker_name = worker_name
        self.worker_id = str(uuid.uuid4())
        self.job_scheduler = job_scheduler
        self.current_job: Optional[JobEntity] = None
        self.running: bool = True


    def run(self) -> None:
        """Main worker thread loop that processes jobs."""
        base_logger.info(f"Worker {self.name} started with id {self.worker_id}. ")
        while self.running:
            try:
                # fetch a job from the scheduler
                job = self.job_scheduler.fetch_next_job()
                if job:
                    self.execute_job(job)
                else:
                    # No jobs available, sleep briefly
                    time.sleep(0.1)
            except Exception as e:
                base_logger.error(f"Worker {self.name} encountered an error: {e}")
                time.sleep(1)

    def stop(self) -> None:
        """Stop the worker thread."""
        self.running = False
        self.join(timeout=1)

    def execute_job(self, job: JobEntity) -> None:
        """Execute a job and handle success/failure."""
        self.current_job = job

        # Log job start
        job.status = JobStatus.RUNNING
        base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")

        try:
            # Simulate job execution for the specified duration
            time.sleep(job.execution_duration)

            # Simulate random success/failure (70% chance of success)
            if random.random() > 0.3:
                # Job completed successfully
                job.status = JobStatus.COMPLETED
                base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")
                self.job_scheduler.job_complete(job)
            else:
                # Job failed
                raise Exception("ExternalError")

        except Exception as e:
            # Handle job failure
            job.status = JobStatus.FAILED
            base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")

            # Check if retry is possible
            if job.retry_count < job.max_retries:
                job.retry_count += 1

                # Schedule retry after delay
                retry_time = datetime.now() + timedelta(seconds=job.retry_delay)
                job.status = JobStatus.PENDING
                job.start_time = retry_time
                self.job_scheduler.schedule_job(job)
            else:
                # Max retries reached
                job.status = JobStatus.TERMINATED
                base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")
                self.job_scheduler.job_complete(job)

        # Clear current job
        self.current_job = None
