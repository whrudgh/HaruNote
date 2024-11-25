from pydantic import BaseModel, EmailStr
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship
# 순환 참조 방지 
if TYPE_CHECKING:
    from models.events import Event


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: EmailStr
    password: str
    username: str
    events: Optional[List["Event"]] = Relationship(back_populates="user")

# 사용자 등록 시 사용할 모델
class UserSignUp(SQLModel):
    email: EmailStr
    password: str
    username: str

class UserSignIn(SQLModel):
    email: EmailStr
    password: str
