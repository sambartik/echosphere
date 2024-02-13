import asyncio
from contextlib import asynccontextmanager


@asynccontextmanager
async def ConcurentTasksGroup():
    """
      When one of the tasks from group exits, exit the others as well.
    """
    tasks = []

    class TaskGroup:
        @staticmethod
        def create_task(*args, **kwargs):
            task = asyncio.create_task(*args, **kwargs)
            tasks.append(task)
            return task

    yield TaskGroup
    if len(tasks) == 0:
        return

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    # Cancel all tasks that are still running
    for task in pending:
        task.cancel()
        try:
            await task  # Await task to execute its cancellation
        except asyncio.CancelledError:
            pass  # Ignore the error since cancellation is expected

    for task in done:
        err = task.exception()
        if err:
            raise err
