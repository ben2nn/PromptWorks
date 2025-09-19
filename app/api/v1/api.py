from fastapi import APIRouter

from app.api.v1.endpoints import llms, prompts, test_prompt


api_router = APIRouter()
api_router.include_router(llms.router, prefix="/llms", tags=["llms"])
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(
    test_prompt.router, prefix="/test_prompt", tags=["test_prompt"]
)
