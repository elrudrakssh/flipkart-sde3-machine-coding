from __future__ import annotations
from typing import Protocol, Dict, List, Tuple, Union, overload, Optional, Any
from datetime import datetime
from threading import Thread, Lock, RLock

from kink import inject, di

from worker import ConcurrentWorker as Worker
from job_entity import JobEntity
from logger import base_logger
from job_status import JobStatus
import time
import heapq


class Scheduler(Protocol):
    def start(self): ...

    def stop(self): ...

    def executor(self): ...

    def get_job(self, job_id: int): ...

    def get_job_logs(self, job_id: int): ...

    def schedule_job(self, job_id: JobEntity): ...


@inject
class JobScheduler(Scheduler):
    """Job scheduler class."""
    def __init__(self, num_workers: int):
        self.jobs: Dict[str, JobEntity] = dict()
        self.workers: List[Worker] = []
        self.job_queue: List[Tuple[datetime, int, str]] = []  # handling the job based or highest priority to be optional
        self.running: bool = True
        self.job_lock: Lock = Lock()  # to maintain concurrency on scheduled job execution
        self.logger_lock: RLock = RLock()  # re-entrant lock to perform logging with nested locking
        self.queue_lock: RLock = RLock()
        self.job_logs: List[str] = []


        # initialize workers for scheduler
        self.workers = [Worker(f"Worker:{i+1}", self) for i in range(num_workers)]

    def start(self) -> None:
        """Start the scheduler and worker threads."""
        _scheduler = di["Executor"]
        _scheduler.start()
        for worker in self.workers:
            worker.start()


    def stop(self) -> None:
        """Stop the scheduler and worker threads."""
        self.running = False
        for worker in self.workers:
            worker.stop()


        # Wait for scheduler thread to finish
        _scheduler = di["Executor"]
        _scheduler.join(timeout=1)

    def _exe_loop_scheduler(self):
        """main handler method to move the scheduled jobs from pending to running."""
        base_logger.info("> Starting Job Scheduler in main thread.")
        while self.running:
            try:
                with self.queue_lock:
                    # Check for are any jobs ready to be scheduled
                    now = datetime.now().replace(tzinfo=None)
                    to_schedule, remaining = [], []

                    for start_time, priority, job_id in self.job_queue:
                        if start_time <= now:
                            to_schedule.append((start_time, priority, job_id))
                        else:
                            remaining.append((start_time, priority, job_id))

                    # Update queue with remaining jobs
                    self.job_queue = remaining

                    # Schedule jobs that are ready
                    for _, _, job_id in to_schedule:
                        with self.job_lock:
                            # job to be picked by any concurrent worker thread
                            if job_id in self.jobs:
                                job = self.jobs[job_id]
                                job.status = JobStatus.SCHEDULED
                                with self.logger_lock:
                                    self.job_logs.append(f"Job with Id: {job.job_id} and name: {job.name} scheduled at {now} successfully with current status: {job.status} and retry_count: {job.retry_count}. ")

                # Sleep briefly to avoid tight loop
                time.sleep(0.1)

            except Exception as e:
                base_logger.error(f"Scheduler error: {e}")
                time.sleep(1)

    @overload
    def register_job(self, job_data: None) -> None:
        ...

    @overload
    def register_job(self, job_data: Dict[str, Union[str, int, float]]) -> JobEntity:
        ...

    def register_job(self, job_data: Union[None, Dict[str, Union[str, int, float]]]) -> Union[None, JobEntity]:
        """Register a new job to JobScheduler Kitchen Manager."""
        job = JobEntity(
            name=job_data["name"], # type: ignore
            execution_duration=job_data["execution_duration"], # type: ignore
            max_retries=job_data.get("nax_entries"), # type: ignore
            retry_delay=job_data.get("retry_delay"), # type: ignore
            job_start_time=datetime.fromisoformat(job_data["start_time"]).replace(tzinfo=None), # type: ignore
            priority=job_data.get("priority", 10), # type: ignore # if value not provided least priority is assumed
            recurrence=job_data.get("recurrence"), # type: ignore
            job_end_time=datetime.fromisoformat(job_data["end_time"]).replace(tzinfo=None) # type: ignore
            if "endTime" in job_data else None
        ) # type: ignore

        with self.job_lock:
            self.jobs[job.job_id] = job
            self.schedule_job(job)

        # Log the job creation
        with self.logger_lock:
            self.job_logs.append(f"Job with Id: {job.job_id} and name: {job.name} successfully created at {job.job_start_time} with current status: {job.status} and retry_count: {job.retry_count}. ")

        return job

    def fetch_next_job(self) -> Optional[JobEntity]:
        """Get the next job that's in SCHEDULED state for a worker to execute."""
        with self.job_lock:
            scheduled_jobs = [job for job in self.jobs.values() if job.job_status == JobStatus.SCHEDULED]
            # try sorting the jobs by priority prop
            scheduled_jobs.sort(key=lambda j: j.priority)

            if scheduled_jobs:
                with self.logger_lock:
                    job = scheduled_jobs[0]
                    self.job_logs.append(f"Job with Id: {job.job_id} and name: {job.name} successfully fetched with current status: {job.status} and retry_count: {job.retry_count}. ")

                return job

        return None

    def update_job(self, job_id: str, update_data: Dict[str, Any]) -> Optional[JobEntity]:
        """Update a pending job."""
        with self.job_lock:
            if job_id not in self.jobs:
                return None

            job = self.jobs[job_id]
            if job.job_status != JobStatus.PENDING:
                return None

            # Update job attributes if provided
            if "name" in update_data:
                job.name = update_data["name"]
            if "execution_duration" in update_data:
                job.execution_duration = update_data["execution_duration"]
            if "max_retries" in update_data:
                job.max_retries = update_data["max_retries"]
            if "retry_delay" in update_data:
                job.retry_delay = update_data["retry_delay"]
            if "start_time" in update_data:
                job.start_time = datetime.fromisoformat(update_data["start_time"]).replace(tzinfo=None)
            if "priority" in update_data:
                job.priority = update_data["priority"]
            if "recurrence" in update_data:
                job.recurrence = update_data["recurrence"]
            if "end_time" in update_data:
                job.end_time = datetime.fromisoformat(update_data["end_time"]).replace(tzinfo=None) \
                    if update_data["end_time"] else None

            with self.queue_lock:
                # Remove existing job from queue if present
                self.job_queue = [(t, p, job_id) for t, p, job_id in self.job_queue if job_id != job_id]

                with self.queue_lock:
                    # Add updated job back to queue
                    self.job_logs.append(f"Job with Id: {job.job_id} and name: {job.name} successfully added to Priority queue at {job.job_start_time} with current status: {job.status} and retry_count: {job.retry_count}. ")
                    self.schedule_job(job)

            return job

    def job_complete(self, job: JobEntity) -> None:
        # If job is recurring, schedule the next occurrence
        if job.recurrence and job.job_status == JobStatus.COMPLETED:
            next_job = job.register_next_occurrence()
            if next_job:
                with self.job_lock:
                    self.jobs[next_job.job_id] = next_job
                    with self.logger_lock:
                        self.job_logs.append(
                            f"Next Job with Id: {next_job.job_id} and name: {next_job.name} scheduled at {next_job.job_start_time} with current status: {next_job.status} and retry_count: {next_job.retry_count}. ")
                        self.schedule_job(next_job)

    def schedule_job(self, job: JobEntity) -> None:
        """Add a job to the scheduling queue."""
        with self.queue_lock:
            heapq.heappush(self.job_queue, (job.job_start_time, job.priority, job.job_id))

    def __call__(self):
        self._scheduler = Thread(target=self._exe_loop_scheduler)
        return self._scheduler

    def executor(self): #type: ignore
        """Execute method that interact for interface compilation and execution for all jobs."""
        # the __call__ to execute Jobs within the scheduler
        return self()

    @property
    def get_all_jobs(self) -> List[JobEntity]:
        """Get all jobs."""
        return list(self.jobs.values())

    @property
    def get_all_job_logs(self) -> List[str]:
        """Get all job logs."""
        return self.job_logs
