"""
considering this to be Kitchen-Manager & Chef problem -- job -- orders to cook
JobScheduler - KitchenManager Class
Job dto -- to handle Job class entity
Worker Class -- Chef worker handling
Job Status -- String Enum
Constants -- value objects specific to class hanfling
Job logger -- definition on logging pattern

"""
from __future__ import annotations
import time
from datetime import datetime, timedelta

from logger import base_logger
from src.job_scheduler import JobScheduler, Scheduler
from kink import Container, di


def bootstrap(di: Container) -> None:
    di[Scheduler] = JobScheduler(num_workers=3).executor()


class TestDriver:
    """Test driver for the job scheduler."""
    def __init__(self, workers: int = 5) -> None:
        self.scheduler = JobScheduler(num_workers=workers)
        self.scheduler.start()

    def __call__(self, *args, **kwargs):
        self.run_test()

    def run_test(self) -> None:
        """Run a test of the job scheduler."""
        try:
            # Register jobs
            job1 = self.scheduler.register_job({
                "name": "myScheduledJob1",
                "execution_duration": 30,
                "max_retries": 1,
                "retry_delay": 10,
                "start_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "priority": 1,
                "recurrence": 120
            })

            # Add a slight delay before registering the second job
            time.sleep(1)

            job2 = self.scheduler.register_job({
                "name": "myScheduledJob2",
                "execution_duration": 60,
                "retry_delay": 3,
                "retryDelay": 10,
                "start_time": (datetime.now() + timedelta(seconds=35)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "priority": 1,
                "recurrence": 300
            })

            # Execute jobs
            _ = di[Scheduler]

            # Wait for jobs to complete
            time.sleep(6)  # Wait for 5 minutes to see recurring jobs

            # TODO: need to print the Thread execution logs

        finally:
            # Stop the scheduler
            self.scheduler.stop()


if __name__ == "__main__":
    num_workers = 3
    job_driver_handler = TestDriver(workers=num_workers)
    job_driver_handler()
