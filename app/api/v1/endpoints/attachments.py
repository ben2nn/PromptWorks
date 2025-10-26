"""附件管理 API 端点

提供附件的上传、下载、列表、删除等 RESTful API 接口。
支持文件上传、缩略图获取、附件信息查询等功能。
"""

from typing import Sequence

from fastapi import (
    APIRouter, 
    Depends, 
    File, 
    HTTPException, 
    Query, 
    Response, 
    UploadFile,
    status
)
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.attachment import PromptAttachment
from app.models.prompt import MediaType
from app.schemas.attachment import (
    AttachmentListResponse,
    AttachmentRead, 
    AttachmentUpdate,
    AttachmentUploadResponse
)
from app.services.attachment import attachment_service
from app.services.file_storage import file_storage_service

router = APIRouter()


def _get_attachment_or_404(db: Session, attachment_id: int) -> PromptAttachment:
    """获取附件或返回 404 错误"""
    attachment = attachment_service.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="附件不存在"
        )
    return attachment


@router.post(
    "/prompts/{prompt_id}/attachments",
    response_model=AttachmentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传附件",
    description="为指定提示词上传附件文件，支持图片、文档、音频、视频等格式"
)
async def upload_attachment(
    prompt_id: int,
    file: UploadFile = File(..., description="要上传的文件"),
    media_type: MediaType | None = Query(None, description="指定媒体类型（可选）"),
    db: Session = Depends(get_db)
) -> AttachmentUploadResponse:
    """上传附件到指定提示词"""
    
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件名不能为空"
        )
    
    # 上传附件
    attachment = await attachment_service.upload_attachment(
        db=db,
        prompt_id=prompt_id,
        file=file,
        media_type=media_type
    )
    
    # 转换为响应模式
    attachment_read = attachment_service.to_attachment_read(attachment)
    
    return AttachmentUploadResponse(
        attachment=attachment_read,
        message="文件上传成功"
    )


@router.get(
    "/prompts/{prompt_id}/attachments",
    response_model=AttachmentListResponse,
    summary="获取附件列表",
    description="获取指定提示词的附件列表，支持分页"
)
def list_prompt_attachments(
    prompt_id: int,
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(50, ge=1, le=200, description="返回的最大记录数"),
    db: Session = Depends(get_db)
) -> AttachmentListResponse:
    """获取提示词的附件列表"""
    
    # 获取附件列表
    attachments = attachment_service.get_prompt_attachments(
        db=db,
        prompt_id=prompt_id,
        skip=skip,
        limit=limit
    )
    
    # 获取总数
    total = attachment_service.count_prompt_attachments(db, prompt_id)
    
    # 转换为响应模式
    attachment_reads = [
        attachment_service.to_attachment_read(attachment)
        for attachment in attachments
    ]
    
    return AttachmentListResponse(
        items=attachment_reads,
        total=total
    )


@router.get(
    "/attachments/{attachment_id}",
    response_model=AttachmentRead,
    summary="获取附件信息",
    description="根据 ID 获取附件的详细信息"
)
def get_attachment(
    attachment_id: int,
    db: Session = Depends(get_db)
) -> AttachmentRead:
    """获取单个附件信息"""
    
    attachment = _get_attachment_or_404(db, attachment_id)
    return attachment_service.to_attachment_read(attachment)


@router.get(
    "/attachments/{attachment_id}/download",
    response_class=FileResponse,
    summary="下载附件",
    description="下载指定的附件文件"
)
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db)
) -> FileResponse:
    """下载附件文件"""
    
    attachment = _get_attachment_or_404(db, attachment_id)
    
    # 获取文件的完整路径
    file_path = file_storage_service.get_file_path(attachment.file_path)
    
    # 检查文件是否存在
    if not file_storage_service.file_exists(attachment.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文件不存在或已被删除"
        )
    
    return FileResponse(
        path=file_path,
        filename=attachment.original_filename,
        media_type=attachment.mime_type
    )


@router.get(
    "/attachments/{attachment_id}/thumbnail",
    response_class=FileResponse,
    summary="获取缩略图",
    description="获取附件的缩略图（仅适用于图片类型）"
)
def get_attachment_thumbnail(
    attachment_id: int,
    db: Session = Depends(get_db)
) -> FileResponse:
    """获取附件缩略图"""
    
    attachment = _get_attachment_or_404(db, attachment_id)
    
    # 检查是否有缩略图
    if not attachment.thumbnail_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="该附件没有缩略图"
        )
    
    # 获取缩略图的完整路径
    thumbnail_path = file_storage_service.get_file_path(attachment.thumbnail_path)
    
    # 检查缩略图文件是否存在
    if not file_storage_service.file_exists(attachment.thumbnail_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="缩略图文件不存在或已被删除"
        )
    
    return FileResponse(
        path=thumbnail_path,
        media_type="image/jpeg"  # 缩略图统一为 JPEG 格式
    )


@router.put(
    "/attachments/{attachment_id}",
    response_model=AttachmentRead,
    summary="更新附件信息",
    description="更新附件的元数据信息"
)
def update_attachment(
    attachment_id: int,
    payload: AttachmentUpdate,
    db: Session = Depends(get_db)
) -> AttachmentRead:
    """更新附件信息"""
    
    attachment = _get_attachment_or_404(db, attachment_id)
    
    # 更新文件名
    if payload.filename is not None:
        attachment.filename = payload.filename
    
    # 更新元数据
    if payload.file_metadata is not None:
        updated_attachment = attachment_service.update_attachment_metadata(
            db=db,
            attachment_id=attachment_id,
            metadata=payload.file_metadata
        )
        if not updated_attachment:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新附件元数据失败"
            )
        attachment = updated_attachment
    else:
        # 如果只更新文件名，直接提交
        db.commit()
        db.refresh(attachment)
    
    return attachment_service.to_attachment_read(attachment)


@router.delete(
    "/attachments/{attachment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="删除附件",
    description="删除指定的附件及其物理文件"
)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db)
) -> Response:
    """删除附件"""
    
    # 验证附件是否存在
    _get_attachment_or_404(db, attachment_id)
    
    # 删除附件
    success = attachment_service.delete_attachment(db, attachment_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除附件失败"
        )
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/prompts/{prompt_id}/attachments",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="删除提示词的所有附件",
    description="删除指定提示词的所有附件及其物理文件"
)
def delete_prompt_attachments(
    prompt_id: int,
    db: Session = Depends(get_db)
) -> Response:
    """删除提示词的所有附件"""
    
    # 删除所有附件
    deleted_count = attachment_service.delete_prompt_attachments(db, prompt_id)
    
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={"X-Deleted-Count": str(deleted_count)}
    )


@router.get(
    "/statistics",
    summary="获取存储统计",
    description="获取附件存储的统计信息"
)
def get_storage_statistics(
    db: Session = Depends(get_db)
) -> dict:
    """获取存储统计信息"""
    
    return attachment_service.get_storage_statistics(db)