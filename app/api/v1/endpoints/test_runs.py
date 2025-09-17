from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db.session import get_db
from app.models.prompt import Prompt
from app.models.result import Result
from app.models.test_run import TestRun, TestRunStatus
from app.schemas.result import ResultRead
from app.schemas.test_run import TestRunCreate, TestRunRead, TestRunUpdate

router = APIRouter()


@router.get("/", response_model=list[TestRunRead])
def list_test_runs(
    *,
    db: Session = Depends(get_db),
    status_filter: TestRunStatus | None = Query(default=None, alias="status"),
    prompt_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Sequence[TestRun]:
    """按筛选条件分页返回测试运行列表，包含关联提示词和结果。"""

    stmt = (
        select(TestRun)
        .options(
            joinedload(TestRun.prompt),
            selectinload(TestRun.results).selectinload(Result.metrics),
        )
        .order_by(TestRun.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(TestRun.status == status_filter)
    if prompt_id:
        stmt = stmt.where(TestRun.prompt_id == prompt_id)

    return list(db.scalars(stmt))


@router.post("/", response_model=TestRunRead, status_code=status.HTTP_201_CREATED)
def create_test_run(
    *, db: Session = Depends(get_db), payload: TestRunCreate
) -> TestRun:
    """为指定提示词创建新的测试运行，初始状态为待处理。"""

    prompt_exists = db.scalar(select(Prompt.id).where(Prompt.id == payload.prompt_id))
    if not prompt_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt not found"
        )

    test_run = TestRun(**payload.model_dump(), status=TestRunStatus.PENDING)
    db.add(test_run)
    db.commit()
    db.refresh(test_run)
    return test_run


@router.get("/{test_run_id}", response_model=TestRunRead)
def get_test_run(*, db: Session = Depends(get_db), test_run_id: int) -> TestRun:
    """根据 ID 获取单个测试运行及其关联数据，不存在时返回 404。"""

    stmt = (
        select(TestRun)
        .options(
            joinedload(TestRun.prompt),
            selectinload(TestRun.results).selectinload(Result.metrics),
        )
        .where(TestRun.id == test_run_id)
    )
    test_run = db.scalar(stmt)
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found"
        )

    return test_run


@router.patch("/{test_run_id}", response_model=TestRunRead)
def update_test_run(
    *,
    db: Session = Depends(get_db),
    test_run_id: int,
    payload: TestRunUpdate,
) -> TestRun:
    """根据 ID 更新测试运行字段并可修改状态。"""

    test_run = db.get(TestRun, test_run_id)
    if not test_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test run not found"
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


@router.get("/{test_run_id}/results", response_model=list[ResultRead])
def list_results_for_test_run(
    *, db: Session = Depends(get_db), test_run_id: int
) -> Sequence[Result]:
    """列出指定测试运行的所有结果数据，按执行顺序排序。"""

    stmt = (
        select(Result)
        .where(Result.test_run_id == test_run_id)
        .options(selectinload(Result.metrics))
        .order_by(Result.run_index.asc())
    )
    return list(db.scalars(stmt))
