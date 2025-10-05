from __future__ import annotations

import logging
import threading
import time
from queue import Empty, Queue

from app.db import session as db_session
from app.models.test_run import TestRun, TestRunStatus
from app.services.test_run import TestRunExecutionError, execute_test_run


logger = logging.getLogger("promptworks.task_queue")


class TestRunTaskQueue:
    """简单的内存消息队列，用于串行执行测试任务。"""

    def __init__(self) -> None:
        self._queue: Queue[int] = Queue()
        self._worker = threading.Thread(
            target=self._worker_loop, name="test-run-queue", daemon=True
        )
        self._worker.start()

    def enqueue(self, test_run_id: int) -> None:
        """将测试任务加入待执行队列。"""

        self._queue.put_nowait(test_run_id)
        logger.info("测试任务 %s 已加入执行队列", test_run_id)

    def _worker_loop(self) -> None:
        while True:
            try:
                test_run_id = self._queue.get()
            except Empty:  # pragma: no cover - Queue.get 默认阻塞，不会出现
                continue

            try:
                self._execute_task(test_run_id)
            except Exception:  # pragma: no cover - 防御性兜底
                logger.exception("执行测试任务 %s 过程中发生未捕获异常", test_run_id)
            finally:
                self._queue.task_done()

    def _execute_task(self, test_run_id: int) -> None:
        session = db_session.SessionLocal()
        try:
            test_run = session.get(TestRun, test_run_id)
            if not test_run:
                logger.warning("测试任务 %s 不存在，跳过执行", test_run_id)
                return

            nested_txn = session.begin_nested()
            try:
                execute_test_run(session, test_run)
            except TestRunExecutionError as exc:
                nested_txn.rollback()
                session.expire(test_run)

                failed_run = session.get(TestRun, test_run_id)
                if not failed_run:
                    logger.warning("测试任务 %s 在回滚后不存在", test_run_id)
                    return

                schema = dict(failed_run.schema or {})
                schema["last_error"] = str(exc)
                failed_run.schema = schema
                failed_run.status = TestRunStatus.FAILED
                session.commit()

                logger.warning("测试任务 %s 执行失败: %s", test_run_id, exc)
                return
            except Exception as exc:  # pragma: no cover - 防御性兜底
                nested_txn.rollback()
                session.expire_all()

                failed_run = session.get(TestRun, test_run_id)
                if failed_run:
                    schema = dict(failed_run.schema or {})
                    schema["last_error"] = "执行测试任务失败"
                    failed_run.schema = schema
                    failed_run.status = TestRunStatus.FAILED
                    session.commit()

                logger.exception("测试任务 %s 执行出现未知异常", test_run_id)
                return
            else:
                nested_txn.commit()
                session.commit()
                logger.info("测试任务 %s 执行完成", test_run_id)
        finally:
            session.close()

    def wait_for_idle(self, timeout: float | None = None) -> bool:
        """等待队列清空，供测试或调试使用。"""

        if timeout is None:
            self._queue.join()
            return True

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._queue.unfinished_tasks == 0:
                return True
            time.sleep(0.02)
        return self._queue.unfinished_tasks == 0


task_queue = TestRunTaskQueue()


def enqueue_test_run(test_run_id: int) -> None:
    """对外暴露的入队方法。"""

    task_queue.enqueue(test_run_id)


__all__ = ["enqueue_test_run", "task_queue"]
