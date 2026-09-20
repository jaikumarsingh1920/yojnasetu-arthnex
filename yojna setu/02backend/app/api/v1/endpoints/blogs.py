from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.blog import FinancialBlog
from app.models.user import User, UserRole
from app.schemas.blog import FinancialBlogInput, FinancialBlogResponse

router = APIRouter()


def serialize(blog: FinancialBlog, db: Session) -> dict:
    author = db.query(User).filter(User.user_id == blog.author_id).first()
    return {
        "blog_id": blog.blog_id, "title": blog.title, "summary": blog.summary,
        "content": blog.content, "author_name": (author.full_name if author and author.full_name else "YojnaSetu Editorial Team"),
        "created_at": blog.created_at, "updated_at": blog.updated_at,
    }


@router.get("", response_model=List[FinancialBlogResponse], summary="Read financial literacy blogs")
def list_financial_blogs(db: Session = Depends(get_db)):
    """Public, read-only endpoint. FinancialBlog stores only financial blog posts."""
    blogs = db.query(FinancialBlog).order_by(FinancialBlog.created_at.desc()).all()
    return [serialize(blog, db) for blog in blogs]


@router.get("/{blog_id}", response_model=FinancialBlogResponse, summary="Read a financial blog")
def get_financial_blog(blog_id: str, db: Session = Depends(get_db)):
    blog = db.query(FinancialBlog).filter(FinancialBlog.blog_id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found.")
    return serialize(blog, db)


admin_router = APIRouter()


@admin_router.post("", response_model=FinancialBlogResponse, status_code=status.HTTP_201_CREATED)
def create_financial_blog(data: FinancialBlogInput, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))):
    blog = FinancialBlog(**data.model_dump(), author_id=current_user.user_id)
    db.add(blog)
    db.commit()
    db.refresh(blog)
    return serialize(blog, db)


@admin_router.put("/{blog_id}", response_model=FinancialBlogResponse)
def update_financial_blog(blog_id: str, data: FinancialBlogInput, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))):
    blog = db.query(FinancialBlog).filter(FinancialBlog.blog_id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found.")
    for field, value in data.model_dump().items():
        setattr(blog, field, value)
    db.commit()
    db.refresh(blog)
    return serialize(blog, db)


@admin_router.delete("/{blog_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_financial_blog(blog_id: str, db: Session = Depends(get_db), current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN))):
    blog = db.query(FinancialBlog).filter(FinancialBlog.blog_id == blog_id).first()
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found.")
    db.delete(blog)
    db.commit()
