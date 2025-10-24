from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime
from queue import Empty, Queue

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db import session as db_session
from app.models.prompt_test import (
    PromptTestExperiment,
    PromptTestExperimentStatus,
    PromptTestTask,
    PromptTestTaskStatus,
    PromptTestUnit,
)
from app.services.prompt_test_engine import (
    PromptTestExecutionError,
    execute_prompt_test_experiment,
)

logger = logging.getLogger("promptworks.prompt_test_queue")


class PromptTestTaskQueue:
    """Prompt 测试任务的串行执行队列。"""

    def __init__(self) -> None:
        self._queue: Queue[int] = Queue()
        self._worker = threading.Thread(
            target=self._worker_loop, name="prompt-test-task-queue", daemon=True
        )
        self._worker.start()

    @staticmethod
    def _update_task_last_error(task: PromptTestTask, message: str | None) -> None:
        if message:
            base = dict(task.config) if isinstance(task.config, dict) else {}
            base["last_error"] = message
            task.config = base
            return

        if isinstance(task.config, dict) and "last_error" in task.config:
            cleaned = dict(task.config)
            cleaned.pop("last_error", None)
            task.config = cleaned

    def enqueue(self, task_id: int) -> None:
        """将任务加入待执行队列。"""

        self._queue.put_nowait(task_id)
        logger.info("Prompt 测试任务 %s 已加入执行队列", task_id)

    def wait_for_idle(self, timeout: float | None = None) -> bool:
        """等待队列清空，便于测试或调试。"""

        if timeout is None:
            self._queue.join()
            return True

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._queue.unfinished_tasks == 0:
                return True
            time.sleep(0.02)
        return self._queue.unfinished_tasks == 0

    def _worker_loop(self) -> None:
        while True:
            try:
                task_id = self._queue.get()
            except Empty:  # pragma: no cover - Queue.get 默认阻塞
                continue

            try:
                self._execute_task(task_id)
            except Exception:  # pragma: no cover - 防御性兜底
                logger.exception(
                    "执行 Prompt 测试任务 %s 过程中发生未捕获异常", task_id
                )
            finally:
                self._queue.task_done()

    def _execute_task(self, task_id: int) -> None:
        session = db_session.SessionLocal()
        try:
            task = session.execute(
                select(PromptTestTask)
                .where(PromptTestTask.id == task_id)
                .options(selectinload(PromptTestTask.units))
            ).scalar_one_or_none()
            if not task:
                logger.warning("Prompt 测试任务 %s 不存在，跳过执行", task_id)
                return
            if task.is_deleted:
                logger.info("Prompt 测试任务 %s 已被标记删除，跳过执行", task_id)
                return

            if not task.units:
                task.status = PromptTestTaskStatus.COMPLETED
                self._update_task_last_error(task, None)
                session.commit()
                logger.info(
                    "Prompt 测试任务 %s 无最小测试单元，自动标记为完成", task_id
                )
                return

            task.status = PromptTestTaskStatus.RUNNING
            self._update_task_last_error(task, None)
            session.commit()

            for unit in task.units:
                if not isinstance(unit, PromptTestUnit):
                    continue

                sequence = (
                    session.scalar(
                        select(func.max(PromptTestExperiment.sequence)).where(
                            PromptTestExperiment.unit_id == unit.id
                        )
                    )
                    or 0
                ) + 1

                experiment = PromptTestExperiment(
                    unit_id=unit.id,
                    sequence=sequence,
                    status=PromptTestExperimentStatus.PENDING,
                )
                session.add(experiment)
                session.flush()

                try:
                    execute_prompt_test_experiment(session, experiment)
                except PromptTestExecutionError as exc:
                    session.refresh(experiment)
                    experiment.status = PromptTestExperimentStatus.FAILED
                    experiment.error = str(exc)
                    experiment.finished_at = datetime.now(UTC)
                    task.status = PromptTestTaskStatus.FAILED
                    self._update_task_last_error(task, str(exc))
                    session.commit()
                    logger.warning(
                        "Prompt 测试任务 %s 的最小单元 %s 执行失败: %s",
                        task_id,
                        unit.id,
                        exc,
                    )
                    return
                except Exception as exc:  # pragma: no cover - 防御性兜底
                    session.refresh(experiment)
                    experiment.status = PromptTestExperimentStatus.FAILED
                    experiment.error = "执行测试任务失败"
                    experiment.finished_at = datetime.now(UTC)
                    task.status = PromptTestTaskStatus.FAILED
                    self._update_task_last_error(task, "执行测试任务失败")
                    session.commit()
                    logger.exception(
                        "Prompt 测试任务 %s 的最小单元 %s 执行出现未知异常",
                        task_id,
                        unit.id,
                    )
                    return

                session.commit()

            task.status = PromptTestTaskStatus.COMPLETED
            self._update_task_last_error(task, None)
            session.commit()
            logger.info("Prompt 测试任务 %s 执行完成", task_id)
        finally:
            session.close()


task_queue = PromptTestTaskQueue()


def enqueue_prompt_test_task(task_id: int) -> None:
    """对外暴露的入队方法。"""

    task_queue.enqueue(task_id)


__all__ = ["enqueue_prompt_test_task", "task_queue"]
