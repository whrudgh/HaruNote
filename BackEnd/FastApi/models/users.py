from pydantic import BaseModel, EmailStr
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
# 순환 참조 방지 
if TYPE_CHECKING:
    from models.events import Event



class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: EmailStr
    password: str
    username: str
    events: Optional[List["Event"]] = Relationship(back_populates="user")


class UserSignUp(SQLModel):
    email: EmailStr
    password: str
    username: str

#
class UserSignIn(SQLModel):
    email: EmailStr
    password: str

class Page(SQLModel, table=True):  # table=True -> DB 테이블로 생성 
    id: str = Field(default=None, primary_key=True)  # 고유 ID (UUID)
    title: str  # 제목
    content: str  # 내용
    tags: List[str] = []  # 태그 목록 (JSON 형태로 저장 가능)
    created_at: datetime = Field(default_factory=datetime.now)  # 생성 시간
    updated_at: Optional[datetime] = None  # 수정 시간