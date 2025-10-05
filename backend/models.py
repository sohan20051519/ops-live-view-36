from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID, uuid4

class Workspace(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    owner_id: UUID

class UserProfile(BaseModel):
    id: UUID
    workspace_id: Optional[UUID] = None

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class Project(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    repo_url: str
    workspace_id: UUID
    language: Optional[str] = None
    dockerfile_path: Optional[str] = None

class Secret(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    key: str
    value: str  # In a production system, this value should be encrypted.
    workspace_id: UUID