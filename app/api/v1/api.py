from fastapi import APIRouter

from app.api.v1.endpoints import (
    attachments,
    llms,
    media_types,
    prompt_classes,
    prompt_tags,
    prompts,
    system,
    test_prompt,
    usage,
    prompt_test_tasks,
)


api_router = APIRouter()
api_router.include_router(llms.router, prefix="/llm-providers", tags=["llm_providers"])
api_router.include_router(
    prompt_classes.router, prefix="/prompt-classes", tags=["prompt_classes"]
)
api_router.include_router(prompts.router, prefix="/prompts", tags=["prompts"])
api_router.include_router(
    prompt_tags.router, prefix="/prompt-tags", tags=["prompt_tags"]
)
api_router.include_router(
    test_prompt.router, prefix="/test_prompt", tags=["test_prompt"]
)
api_router.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router.include_router(prompt_test_tasks.router)
# 新增的媒体类型和附件相关路由
api_router.include_router(
    media_types.router, prefix="/media-types", tags=["media_types"]
)
api_router.include_router(attachments.router, tags=["attachments"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
