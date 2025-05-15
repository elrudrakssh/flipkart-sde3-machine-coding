# Flipkart SDE3 Machine Coding Challenge

## Job Scheduler

A robust Job Scheduler system that allows users to register multiple jobs for execution, execute them at scheduled times, with retry mechanisms and comprehensive logging.

## Problem Statement

Design and implement a Job Scheduler that allows users to:
- Register multiple jobs for execution
- Execute the jobs at the scheduled time
- Retry jobs on failure
- Log all execution details

## Requirements

### Must Have Features

1. **Job Registration**
   - Register a job with:
     - name
     - executionDuration (in seconds)
     - max_retries
     - retry_delay
     - start_time
   - Job status can have values: `pending`, `scheduled`, `running`, `completed`, `failed`, `terminated`
   - Jobs are always created in `pending` state
   - Failure/completion of job can be simulated by a random interface locally

2. **Job Operations**
   - Update operations only allowed for jobs in `pending` state

3. **Job Execution**
   - Execute jobs for the specified executionDuration
   - Retry failed jobs with a configured delay

4. **Logging**
   - Maintain logs for each job execution:
     - Timestamp
     - JobName
     - Status (completed/failed)
     - WorkerName
     - Retry count
     - Error (if any)

5. **Parallel Processing**
   - Support parallel execution of jobs by multiple workers
   - Number of workers is initialized during application bootstrap

6. **Execution Interface**
   - Provide an `Execute()` interface which triggers the execution for all jobs

### Bonus Features (Good to Have)

1. **Priority and Preemption**
   - Support job priorities (lower number carries higher precedence)
   - Implement preemption based on priority

2. **Recurring Jobs**
   - Support scheduled recurring jobs until a specified end time

## Example Use Cases

### Worker Setup
```
#Workers = 2  [ Worker1, Worker2 ]
```

### Job Registration Examples

```json
{
  "name": "myScheduledJob1",
  "executionDuration": 30,
  "maxRetries": 1,
  "retryDelay": 10,
  "startTime": "2025-05-15T09:10:00Z",
  "priority": 1,
  "recurrence": 120
}
```

```json
{
  "name": "myScheduledJob2",
  "executionDuration": 60,
  "maxRetries": 3,
  "retryDelay": 10,
  "startTime": "2025-05-15T09:10:35Z",
  "priority": 1,
  "recurrence": 300
}
```

### Sample Log Output

```
Execute()

2025-05-15T09:05:00Z myScheduledJob1 created (pending state)
2025-05-15T09:05:01Z myScheduledJob2 created (pending state)

2025-05-15T09:10:00Z myScheduledJob1 on Worker1 scheduled, 0 retry
2025-05-15T09:10:30Z myScheduledJob1 on Worker1 failed, 0 retry, externalError

2025-05-15T09:10:35Z myScheduledJob2 on Worker1 scheduled, 0 retry

2025-05-15T09:10:40Z myScheduledJob1 on Worker2 scheduled, 1 retry
2025-05-15T09:11:10Z myScheduledJob1 on Worker2 terminated, 1 retry, externalError
2025-05-15T09:11:35Z myScheduledJob2 on Worker1 completed
```

### Experiment Execution Log Output against Testcases

```
Execute()

2025-05-15T20:24:00Z - > Starting Job Scheduler in main thread.
2025-05-15T20:24:02Z - Worker Worker:3 executing job myScheduledJob1 with id 2f3ad706-9f83-404e-bcb7-d5fac23264a8 and status RUNNING. 
2025-05-15T20:24:32Z - Worker Worker:3 executing job myScheduledJob1 with id 2f3ad706-9f83-404e-bcb7-d5fac23264a8 and status COMPLETED. 
2025-05-15T20:24:38Z - Worker Worker:1 executing job myScheduledJob2 with id 23d351ab-b3e4-4a76-924c-146802c21a07 and status RUNNING. 
2025-05-15T20:24:38Z - Worker:1 started with id 014716ca-e524-4af7-9e3d-13cf1e21ccb9. 
2025-05-15T20:24:38Z - Worker:2 started with id ee1409e9-10e9-446b-a4ef-121116a970d1. 
2025-05-15T20:24:38Z - Worker:3 started with id db99d9f8-ecb0-4307-91b6-03cbb1410ce7. 
2025-05-15T20:24:38Z - Job with Id: 2f3ad706-9f83-404e-bcb7-d5fac23264a8 and name: myScheduledJob1 successfully created at 2025-05-15 20:24:02 with current status: PENDING and retry_count: 0. 
2025-05-15T20:24:38Z - Job with Id: 2f3ad706-9f83-404e-bcb7-d5fac23264a8 and name: myScheduledJob1 scheduled at 2025-05-15 20:24:02.089027 successfully with current status: SCHEDULED and retry_count: 0. 
2025-05-15T20:24:38Z - Job with Id: 2f3ad706-9f83-404e-bcb7-d5fac23264a8 and name: myScheduledJob1 successfully fetched with current status: SCHEDULED and retry_count: 0. 
2025-05-15T20:24:38Z - Worker:3 executing Job with Id: 2f3ad706-9f83-404e-bcb7-d5fac23264a8 and name: myScheduledJob1 with current status: RUNNING and retry_count: 0. 
2025-05-15T20:24:38Z - Worker:3 Successfully Completed Job with Id: 2f3ad706-9f83-404e-bcb7-d5fac23264a8 and name: myScheduledJob1 with current status: COMPLETED and retry_count: 0. 
2025-05-15T20:24:38Z - Next Job with Id: 6b22ca0f-d046-4c85-a19c-14c6ef19a315 and name: myScheduledJob1 scheduled at 2025-05-15 20:26:02 with current status: PENDING and retry_count: 0. 
2025-05-15T20:24:38Z - Job with Id: 23d351ab-b3e4-4a76-924c-146802c21a07 and name: myScheduledJob2 successfully created at 2025-05-15 20:24:38 with current status: PENDING and retry_count: 0. 
2025-05-15T20:24:38Z - Job with Id: 23d351ab-b3e4-4a76-924c-146802c21a07 and name: myScheduledJob2 scheduled at 2025-05-15 20:24:38.033921 successfully with current status: SCHEDULED and retry_count: 0. 
2025-05-15T20:24:38Z - Job with Id: 23d351ab-b3e4-4a76-924c-146802c21a07 and name: myScheduledJob2 successfully fetched with current status: SCHEDULED and retry_count: 0. 
2025-05-15T20:24:38Z - Worker:1 executing Job with Id: 23d351ab-b3e4-4a76-924c-146802c21a07 and name: myScheduledJob2 with current status: RUNNING and retry_count: 0. 
2025-05-15T20:25:38Z - Worker Worker:1 executing job myScheduledJob2 with id 23d351ab-b3e4-4a76-924c-146802c21a07 and status FAILED. 
```

## Implementation Guidelines

- **Time Limit**: 120 minutes
- **Code Quality**:
  - Write modular, clean, and demonstrable code
  - Include test cases or runtime execution
  - Create a driver program/main class/test case for evaluation
  - Keep input parsing simple
- **Concurrency**: Handle concurrency where applicable
- **Evaluation Criteria**:
  - Demonstrable & functionally correct code
  - Code readability
  - Proper entity modeling
  - Modularity & extensibility
  - Separation of concerns
  - Appropriate abstractions
  - Exception handling
  - Code comments
  - Appropriate use of design patterns
- **Constraints**:
  - No external databases (use in-memory data structures only)
  - No UX or HTTP API required (standalone application)
  - Focus on bonus features only after completing required features
