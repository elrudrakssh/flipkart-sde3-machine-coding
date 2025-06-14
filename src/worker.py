import uuid
from threading import Thread
from typing import Optional

from pydantic.v1.config import inherit_config

from job_entity import JobEntity
from logger import base_logger
from job_status import JobStatus
import time
import random
from datetime import datetime, timedelta
from kink import di, inject


@inject
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
        # base_logger.info(f"{self.name} started with id {self.worker_id}. ")
        self.job_scheduler.job_logs.append(
            f"{self.name} started with id {self.worker_id}. ")

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
                self.job_scheduler.job_logs.append(
                    f"{self.name} with Id: {self.worker_id} encountered an error: {e}. ")
                time.sleep(1)


    def stop(self) -> None:
        """Stop the worker thread."""
        with self.job_scheduler.logger_lock:
            self.running = False
            self.join(timeout=1)
            self.job_scheduler.job_logs.append(
                f"{self.worker_name} Deamon thread stopped at {datetime.now().replace(tzinfo=None)}. ")

    def execute_job(self, job: JobEntity) -> None:
        """Execute a job and handle success/failure."""
        self.current_job = job

        # Log job start
        with self.job_scheduler.logger_lock:
            job.status = JobStatus.RUNNING
            base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")
            self.job_scheduler.job_logs.append(
                f"{self.worker_name} executing Job with Id: {job.job_id} and name: {job.name} with current status: {job.status} and retry_count: {job.retry_count}. ")

            try:
                # Simulate job execution for the specified duration
                time.sleep(job.execution_duration)

                # Simulate random success/failure (70% chance of success)
                if random.random() > 0.3:
                    # Job completed successfully
                    job.status = JobStatus.COMPLETED
                    base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")
                    self.job_scheduler.job_logs.append(
                        f"{self.worker_name} Successfully Completed Job with Id: {job.job_id} and name: {job.name} with current status: {job.status} and retry_count: {job.retry_count}. ")

                    self.job_scheduler.job_complete(job)
                else:
                    # Job failed
                    self.job_scheduler.job_logs.append(
                        f"{self.worker_name} executing Job with Id: {job.job_id} and name: {job.name} with current status: {job.status} and retry_count: {job.retry_count} caught an ExternalError. ")

                    raise Exception("ExternalError")

            except Exception as e:
                # Handle job failure
                job.status = JobStatus.FAILED
                base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")
                self.job_scheduler.job_logs.append(
                    f"{self.worker_name} Failed executing Job with Id: {job.job_id} and name: {job.name} with current status: {job.status} and retry_count: {job.retry_count}. ")

                # Check if retry is possible
                if job.retry_count < job.max_retries:
                    job.retry_count += 1

                    # Schedule retry after delay
                    retry_time = datetime.now() + timedelta(seconds=job.retry_delay)
                    job.status = JobStatus.PENDING
                    job.start_time = retry_time
                    self.job_scheduler.job_logs.append(
                        f"{self.worker_name} Scheduled Retry for Job with Id: {job.job_id} and name: {job.name} with current status: {job.status} and retry_count: {job.retry_count}. ")

                    self.job_scheduler.schedule_job(job)
                else:
                    # Max retries reached
                    job.status = JobStatus.TERMINATED
                    base_logger.info(f"Worker {self.name} executing job {job.name} with id {job.job_id} and status {job.status}. ")
                    self.job_scheduler.job_logs.append(
                        f"Worker: {self.worker_name} Terminated Job with Id: {job.job_id} and name: {job.name} with current status: {job.status} and retry_count: {job.retry_count} == {job.max_retries}. ")

                    self.job_scheduler.job_complete(job)

        # Clear current job
        self.current_job = None
