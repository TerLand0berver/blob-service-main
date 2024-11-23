"""
Asynchronous task queue for file processing.
"""
import asyncio
import logging
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from app.core.config import config

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class Task:
    """Async task."""
    id: str
    func: Callable[..., Awaitable[Any]]
    args: tuple
    kwargs: Dict[str, Any]
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()

class AsyncTaskQueue:
    """Asynchronous task queue."""
    
    def __init__(self, max_workers: int = 3):
        self.queue: asyncio.Queue[Task] = asyncio.Queue()
        self.tasks: Dict[str, Task] = {}
        self.max_workers = max_workers
        self.workers: list[asyncio.Task] = []
        
    async def start(self):
        """Start task queue workers."""
        for _ in range(self.max_workers):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
            
    async def stop(self):
        """Stop task queue workers."""
        # Cancel all workers
        for worker in self.workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
    async def _worker(self):
        """Task queue worker."""
        while True:
            try:
                # Get task from queue
                task = await self.queue.get()
                
                # Update task status
                task.status = TaskStatus.PROCESSING
                task.updated_at = datetime.now()
                
                try:
                    # Execute task
                    result = await task.func(*task.args, **task.kwargs)
                    
                    # Update task with result
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    
                except Exception as e:
                    # Update task with error
                    logger.error(f"Task {task.id} failed: {e}")
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    
                finally:
                    task.updated_at = datetime.now()
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
                
            except Exception as e:
                logger.error(f"Worker error: {e}")
                continue
                
    async def add_task(
        self,
        task_id: str,
        func: Callable[..., Awaitable[Any]],
        *args,
        **kwargs
    ) -> Task:
        """Add task to queue.
        
        Args:
            task_id: Task ID
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Task instance
        """
        # Create task
        task = Task(
            id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            status=TaskStatus.PENDING
        )
        
        # Add to tasks dict
        self.tasks[task_id] = task
        
        # Add to queue
        await self.queue.put(task)
        
        return task
        
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
        
    async def wait_for_task(self, task_id: str, timeout: float = None) -> Task:
        """Wait for task to complete.
        
        Args:
            task_id: Task ID
            timeout: Timeout in seconds
            
        Returns:
            Completed task
            
        Raises:
            TimeoutError: If task times out
            KeyError: If task not found
        """
        task = self.get_task(task_id)
        if not task:
            raise KeyError(f"Task {task_id} not found")
            
        start_time = datetime.now()
        while task.status in (TaskStatus.PENDING, TaskStatus.PROCESSING):
            if timeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    raise TimeoutError(f"Task {task_id} timed out")
                    
            await asyncio.sleep(0.1)
            
        return task

# Global task queue instance
task_queue = AsyncTaskQueue(max_workers=config.MAX_WORKERS)
