# job_entity.py

from typing import Optional, Self, Union, overload
from job_status import JobStatus
import datetime
from dataclasses import dataclass, field
from logger import base_logger
import uuid


@dataclass(init=True)
class JobEntity:
    name: str
    execution_duration: int
    retry_delay: int
    job_start_time: datetime
    job_status: str = JobStatus.PENDING
    retry_count: int = 0
    max_retries: Optional[int] = None
    job_end_time: Optional[datetime] = None
    priority: Optional[int] = None
    recurrence: Optional[Union[int, float]] = None  # in seconds
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))  # generate unique id

    def __post_init__(self):
        """Post-initialization of JobEntity."""
        self.max_retries = 3
        self.recurrence = self.recurrence if self.recurrence else 100
        self.name = self.name if self.name else f"{self.job_id} ScheduledJob"
        self._set_job_end_time(self.job_end_time)  # type: ignore

    @overload
    def _set_job_end_time(self, job_end_time: None):
        ...

    @overload
    def _set_job_end_time(self, job_end_time: datetime):
        ...

    def _set_job_end_time(self, job_end_time: Union[datetime, None]):
        self.job_end_time = self.job_start_time + datetime.timedelta(
            seconds=2 * 60) if not job_end_time else job_end_time

    @property
    def status(self):
        return self.job_status

    @status.setter
    def status(self, status: str):
        self.job_status = status

    def __str__(self):
        """String representation of JobEntity."""
        return f"{self.__class__.__name__}(job_id={self.job_id}, job_status={self.status}, job_start_time={self.job_start_time}, job_end_time={self.job_end_time})"

    def __eq__(self, other: "JobEntity"):
        if isinstance(other, JobEntity):
            return self.name == other.name
        return NotImplemented

    def __lt__(self, other: "JobEntity"):
        if isinstance(other, JobEntity):
            return NotImplemented

        while self.job_start_time != other.job_start_time:
            return self.job_start_time < other.job_start_time

        return self.priority < other.priority

    def register_next_occurrence(self) -> Union[None, Self]:
        """Register next occurrence of the job if it is a recurring job oe not past the end time."""

        if not self.recurrence:
            return None

        _next_job_start_time = self.job_start_time + datetime.timedelta(seconds=self.recurrence)
        if self.job_end_time and _next_job_start_time > self.job_end_time:
            base_logger.info(f"Job {self.job_id} has already ended. No more occurrences will be scheduled.")
            return None

        worker_job = JobEntity(
            name=self.name,
            execution_duration=self.execution_duration,
            retry_delay=self.retry_delay,
            job_status=JobStatus.PENDING,
            job_start_time=_next_job_start_time,
            job_end_time=self.job_end_time,
            max_retries=self.max_retries,
            priority=self.priority,
            recurrence=self.recurrence,
        )

        return worker_job

    def to_dict(self):
        """Deserialize JobEntity object to dictionary."""
        return {
            "name": self.name,
            "job_id": self.job_id,
            "execution_duration": self.execution_duration,
            "retry_delay": self.retry_delay,
            "job_status": self.job_status,
            "job_start_time": self.job_start_time,
            "max_retries": self.max_retries,
            "recurrence": self.recurrence,
            "priority": self.priority,
            "job_end_time": self.job_end_time,
        }
