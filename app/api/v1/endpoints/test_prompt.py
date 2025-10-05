from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.models.prompt import Prompt, PromptVersion
from app.models.result import Result
from app.models.test_run import TestRun, TestRunStatus
from app.schemas.result import ResultRead
from app.schemas.test_run import TestRunCreate, TestRunRead, TestRunUpdate
from app.core.task_queue import enqueue_test_run

router = APIRouter()


def _test_run_query():
    return select(TestRun).options(
        joinedload(TestRun.prompt_version)
        .joinedload(PromptVersion.prompt)
        .joinedload(Prompt.prompt_class),
        selectinload(TestRun.results).selectinload(Result.metrics),
    )


@router.get("/", response_model=list[TestRunRead])
def list_test_prompts(
    *,
    db: Session = Depends(get_db),
    status_filter: TestRunStatus | None = Query(default=None, alias="status"),
    prompt_version_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Sequence[TestRun]:
    """按筛选条件列出 Prompt 测试任务。"""

    stmt = (
        _test_run_query()
        .order_by(TestRun.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(TestRun.status == status_filter)
    if prompt_version_id:
        stmt = stmt.where(TestRun.prompt_version_id == prompt_version_id)

    return list(db.execute(stmt).unique().scalars().all())


@router.post("/", response_model=TestRunRead, status_code=status.HTTP_201_CREATED)
def create_test_prompt(
    *, db: Session = Depends(get_db), payload: TestRunCreate
) -> TestRun:
    """为指定 Prompt 版本创建新的测试任务，并将其入队异步执行。"""

    prompt_version = db.get(PromptVersion, payload.prompt_version_id)
    if not prompt_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt 版本不存在"
        )

    data = payload.model_dump(by_alias=True, exclude_none=True)
    test_run = TestRun(**data)
    test_run.prompt_version = prompt_version
    db.add(test_run)
    db.flush()
    db.commit()

    stmt = _test_run_query().where(TestRun.id == test_run.id)
    created_run = db.execute(stmt).unique().scalar_one()

    try:
        enqueue_test_run(test_run.id)
    except Exception as exc:  # pragma: no cover - 防御性兜底
        test_run_ref = db.get(TestRun, test_run.id)
        if test_run_ref:
            test_run_ref.status = TestRunStatus.FAILED
            test_run_ref.last_error = "测试任务入队失败"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="测试任务入队失败",
        ) from exc

    return created_run


@router.get("/{test_prompt_id}", response_model=TestRunRead)
def get_test_prompt(*, db: Session = Depends(get_db), test_prompt_id: int) -> TestRun:
    """根据 ID 获取单个测试任务及其关联数据。"""

    stmt = _test_run_query().where(TestRun.id == test_prompt_id)
    test_run = db.execute(stmt).unique().scalar_one_or_none()
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test run 不存在"
        )

    return test_run


@router.patch("/{test_prompt_id}", response_model=TestRunRead)
def update_test_prompt(
    *,
    db: Session = Depends(get_db),
    test_prompt_id: int,
    payload: TestRunUpdate,
) -> TestRun:
    """根据 ID 更新测试任务属性，可修改状态。"""

    test_run = db.get(TestRun, test_prompt_id)
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test run 不存在"
        )

    update_data = payload.model_dump(exclude_unset=True)
    status_value = update_data.pop("status", None)
    for key, value in update_data.items():
        setattr(test_run, key, value)
    if status_value is not None:
        test_run.status = status_value

    db.commit()
    db.refresh(test_run)
    return test_run


@router.get("/{test_prompt_id}/results", response_model=list[ResultRead])
def list_results_for_test_prompt(
    *, db: Session = Depends(get_db), test_prompt_id: int
) -> Sequence[Result]:
    """列出指定测试任务的所有结果。"""

    stmt = (
        select(Result)
        .where(Result.test_run_id == test_prompt_id)
        .options(selectinload(Result.metrics))
        .order_by(Result.run_index.asc())
    )
    return list(db.scalars(stmt))


@router.post("/{test_prompt_id}/retry", response_model=TestRunRead)
def retry_test_prompt(*, db: Session = Depends(get_db), test_prompt_id: int) -> TestRun:
    """重新入队执行失败的测试任务。"""

    test_run = db.get(TestRun, test_prompt_id)
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test run 不存在"
        )

    if test_run.status != TestRunStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="仅失败状态的测试任务可重试"
        )

    test_run.status = TestRunStatus.PENDING
    test_run.last_error = None
    db.flush()
    db.commit()

    stmt = _test_run_query().where(TestRun.id == test_run.id)
    refreshed = db.execute(stmt).unique().scalar_one()

    try:
        enqueue_test_run(test_run.id)
    except Exception as exc:  # pragma: no cover - 防御性兜底
        failed_run = db.get(TestRun, test_run.id)
        if failed_run:
            failed_run.status = TestRunStatus.FAILED
            failed_run.last_error = "测试任务重新入队失败"
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="测试任务重新入队失败",
        ) from exc

    return refreshed
