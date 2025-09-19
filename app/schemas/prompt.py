from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PromptClassBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None


class PromptClassRead(PromptClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptVersionBase(BaseModel):
    version: str = Field(..., max_length=50)
    content: str


class PromptVersionCreate(PromptVersionBase):
    prompt_id: int


class PromptVersionRead(PromptVersionBase):
    id: int
    prompt_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    author: str | None = Field(default=None, max_length=100)


class PromptCreate(PromptBase):
    class_id: int | None = Field(default=None, ge=1)
    class_name: str | None = Field(default=None, max_length=255)
    class_description: str | None = None
    version: str = Field(..., max_length=50)
    content: str

    @model_validator(mode="after")
    def validate_class_reference(self):
        if self.class_id is None and not (self.class_name and self.class_name.strip()):
            raise ValueError("class_id 或 class_name 至少需要提供一个")
        return self


class PromptUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    author: str | None = Field(default=None, max_length=100)
    class_id: int | None = Field(default=None, ge=1)
    class_name: str | None = Field(default=None, max_length=255)
    class_description: str | None = None
    version: str | None = Field(default=None, max_length=50)
    content: str | None = None
    activate_version_id: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_version_payload(self):
        if (self.version is None) != (self.content is None):
            raise ValueError("更新版本时必须同时提供 version 与 content")
        return self

    @model_validator(mode="after")
    def validate_class_reference(self):
        if (
            self.class_id is None
            and self.class_name is not None
            and not self.class_name.strip()
        ):
            raise ValueError("class_name 不能为空字符串")
        return self


class PromptRead(PromptBase):
    id: int
    prompt_class: PromptClassRead
    current_version: PromptVersionRead | None = None
    versions: list[PromptVersionRead] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
