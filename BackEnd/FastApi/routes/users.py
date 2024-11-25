from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from auth.authenticate import authenticate
from models.users import Page, User, UserSignIn, UserSignUp
from database.connection import get_session
from sqlmodel import select
from auth.hash_password import HashPassword
from uuid import uuid4
from datetime import datetime


user_router = APIRouter()
hash_password = HashPassword()


#1.사용자 등록
@user_router.post("/Signup", status_code=status.HTTP_201_CREATED)
async def sign_new_user(data: UserSignUp, session=Depends(get_session)) -> dict:
    statement = select(User).where(User.email == data.email)
    user = session.exec(statement).first()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="동일한 사용자가 존재합니다."
        )

    new_user = User(
        email=data.email,
        # password=data.password,
        password=hash_password.hash_password(data.password),
        username=data.username)
    session.add(new_user)
    session.commit()

    return {"message": "정상적으로 등록되었습니다."}


#2.로그인 처리
@user_router.post("/Signin")
def sign_in(data: UserSignIn, session=Depends(get_session)) -> dict:
    statement = select(User).where(User.email == data.email)
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="일치하는 사용자가 존재하지 않습니다.",
        )

    # if user.password != data.password:
    if hash_password.verify_password(data.password, user.password) == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="패스워드가 일치하지 않습니다.",
        )

    return {"message": "로그인에 성공했습니다."}

#3.페이지 생성
@user_router.post("/pages", response_model=Page)
def create_page(
    page: Page,
    session=Depends(get_session),
    current_user: User = Depends(authenticate)  # 인증된 사용자만 생성 가능
):
    new_page = Page(
        id=str(uuid4()),
        title=page.title,
        content=page.content,
        public=page.public,  # 공개 여부 설정
        created_at=datetime.now(),
        updated_at=None,
    )
    session.add(new_page)
    session.commit()
    session.refresh(new_page)
    return new_page

#4.모든 페이지 조회
@user_router.get("/pages", response_model=List[Page])
def get_pages(session=Depends(get_session)):
    pages = session.query(Page).all()  # 모든 페이지 조회
    return pages

#5.특정 페이지 조회
@user_router.get("/pages/{page_id}", response_model=Page)
def get_page(
    page_id: str,
    session=Depends(get_session),
    current_user: Optional[User] = Depends(authenticate)
):
    page = session.get(Page, page_id)
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    if not page.public and not current_user:
        raise HTTPException(status_code=403, detail="Not authorized to access this page")
    
    return page

#6.페이지 수정
@user_router.put("/pages/{page_id}", response_model=Page)
def update_page(page_id: str, updated_page: Page, session=Depends(get_session)):
    page = session.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    page.title = updated_page.title
    page.content = updated_page.content
    page.tags = updated_page.tags
    page.updated_at = datetime.now()

    session.commit()
    session.refresh(page)
    return page


#7.페이지 삭제
@user_router.delete("/pages/{page_id}")
def delete_page(page_id: str, session=Depends(get_session)):
    page = session.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    session.delete(page)
    session.commit()
    return {"message" : "페이지가 삭제되었습니다."}