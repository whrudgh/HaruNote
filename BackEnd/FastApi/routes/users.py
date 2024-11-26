from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from auth.authenticate import authenticate
from auth.jwt_handler import create_jwt_token
from models.users import Page, User, UserSignIn, UserSignUp
from database.connection import get_session
from sqlmodel import select
from auth.hash_password import HashPassword
from uuid import uuid4
from datetime import datetime
from sqlalchemy.orm import Session


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
        password=hash_password.hash_password(data.password),
        username=data.username
    )
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

    access_token = create_jwt_token(email=user.email, user_id=user.id)
    return {"message": "로그인에 성공했습니다.", "access_token": access_token}

#3.페이지 생성
@user_router.post("/pages", response_model=Page)
def create_page(
    page: Page,
    session=Depends(get_session),
    current_user: User = Depends(authenticate)  # 인증된 사용자만 생성 가능

):
    # 현재 시간을 가져온 뒤 replace()로 수정
    now = datetime.now()
    updated_at_date = now.replace(hour=0, minute=0, second=0, microsecond=0)  # 시간 부분을 00:00:00으로 설정

    new_page = Page(
        id=str(uuid4()),
        title=page.title,
        content=page.content,
        public=page.public,  # 공개 여부 설정
        created_at=datetime.now(),
        updated_at=updated_at_date  # replace()로 수정된 시간 저장
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
@user_router.get("/pages/", response_model=Page)
def get_page_by_title(
    title: str = Query(..., description="조회할 페이지의 제목"),
    session: Session = Depends(get_session),
    current_user: Optional[User] = Depends(authenticate)
):
    # 데이터베이스에서 제목으로 페이지 조회
    page = session.query(Page).filter(Page.title == title).first()
    
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    # 페이지가 비공개(public=False)이고 사용자가 인증되지 않은 경우 접근 제한
    if not page.public and not current_user:
        raise HTTPException(status_code=403, detail="Not authorized to access this page")
    
    return page

#6.날짜별로 그룹화
@user_router.get("/pages/calendar-view", response_model=List[dict])
def get_calendar_view(
    start_date: datetime,
    end_date: datetime,
    session=Depends(get_session),
):
    # 지정된 기간 내의 페이지 가져오기
    pages = (
        session.query(Page)
        .filter(Page.updated_at.between(start_date, end_date))
        .order_by(Page.updated_at.asc())
        .all()
    )
    calendar_data = {}
    for page in pages:
        date_key = page.updated_at.date()  # 날짜만 추출
        if date_key not in calendar_data:
            calendar_data[date_key] = []
        calendar_data[date_key].append({
            "id": page.id,
            "title": page.title,
            "content": page.content,
            "public": page.public,
        })

    return [{"date": key, "pages": value} for key, value in calendar_data.items()]


#7.페이지 수정
@user_router.put("/pages/{page_id}", response_model=Page)
def update_page(page_id: str, updated_page: Page, session=Depends(get_session)):
    page = session.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    page.title = updated_page.title
    page.content = updated_page.content
    page.public = updated_page.public
    page.created_at = datetime.now()

    session.commit()
    session.refresh(page)
    return page


#8.페이지 삭제
@user_router.delete("/pages/{page_id}")
def delete_page(page_id: str, session=Depends(get_session)):
    page = session.query(Page).filter(Page.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    session.delete(page)
    session.commit()
    return {"message" : "페이지가 삭제되었습니다."}


#9.페이지 리스트(제목으로만)로 정렬
@user_router.get("/pages/titles", response_model=List[str])
def get_sorted_page_titles(
    order_by: str = Query("asc", enum=["asc", "desc"], description="정렬 순서: asc(오름차순) 또는 desc(내림차순)"),
    session: Session = Depends(get_session)):
    statement = select(Page.title)
    result = session.exec(statement).all()

    # 정렬
    if order_by == "asc":
        sorted_titles = sorted(result)
    else:
        sorted_titles = sorted(result, reverse=True)

    return sorted_titles
