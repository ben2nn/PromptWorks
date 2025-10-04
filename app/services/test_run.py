from __future__ import annotations

from typing import Sequence

from sqlalchemy.orm import Session

from app.models.metric import Metric
from app.models.result import Result
from app.models.test_run import TestRun, TestRunStatus


def complete_with_mock_results(db: Session, test_run: TestRun) -> TestRun:
    """模拟生成测试结果，并将测试任务标记为完成。"""

    if test_run.status != TestRunStatus.PENDING:
        return test_run

    prompt_version = test_run.prompt_version
    results: list[Result] = []
    for index in range(1, test_run.repetitions + 1):
        input_tokens = 420 + index * 35
        output_tokens = 320 + index * 28
        total_tokens = input_tokens + output_tokens
        latency = 1100 + index * 85

        result = Result(
            test_run_id=test_run.id,
            run_index=index,
            output=(
                f"模型 {test_run.model_name} 在第 {index} 次运行的模拟输出。"
                "\n该结果用于前端演示，可替换为真实测试管线的产出。"
            ),
            parsed_output={
                "version": prompt_version.version if prompt_version else None,
                "round": index,
                "summary": "模拟响应内容",
            },
            tokens_used=total_tokens,
            latency_ms=latency,
        )
        result.metrics = [
            Metric(
                is_valid_json=True,
                schema_pass=True,
                numeric_accuracy=0.9,
                boolean_accuracy=0.95,
            )
        ]
        results.append(result)

    test_run.status = TestRunStatus.COMPLETED
    for item in results:
        db.add(item)

    return test_run


def ensure_completed(db: Session, runs: Sequence[TestRun]) -> None:
    for run in runs:
        complete_with_mock_results(db, run)
    db.flush()
