from fastapi import APIRouter

from app.api.v1.endpoints import prompts, test_runs


api_router = APIRouter()
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(test_runs.router, prefix="/test-runs", tags=["test-runs"])
