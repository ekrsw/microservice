from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_user_post
from app.db.session import get_db
from app.crud.post import post
from app.schemas.post import Post, PostCreate, PostUpdate

router = APIRouter()

@router.get("/", response_model=List[Post])
async def get_posts(
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    published_only: bool = Query(True, description="公開済みの投稿のみを取得するかどうか")
):
    """
    投稿一覧を取得する
    
    - **認証**: 必須
    - **権限**: 認証されたユーザーであれば誰でも可能
    """
    posts = await post.get_multi(
        db, skip=skip, limit=limit, published_only=published_only
    )
    return posts

@router.post("/", response_model=Post, status_code=status.HTTP_201_CREATED)
async def create_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_in: PostCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    新しい投稿を作成する
    
    - **認証**: 必須
    - **権限**: 認証されたユーザーであれば誰でも可能
    """
    post_obj = await post.create(db, obj_in=post_in, user_id=current_user["user_id"])
    return post_obj

@router.get("/{post_id}", response_model=Post)
async def get_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    特定の投稿を取得する
    
    - **認証**: 必須
    - **権限**: 認証されたユーザーであれば誰でも可能
    """
    post_obj = await post.get(db, id=post_id)
    if post_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投稿が見つかりません"
        )
    
    # 非公開の投稿は所有者のみ閲覧可能
    if not post_obj.is_published and post_obj.user_id != current_user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="この投稿を閲覧する権限がありません"
        )
    
    return post_obj

@router.put("/{post_id}", response_model=Post)
async def update_post(
    *,
    post_id: UUID,
    post_in: PostUpdate,
    db: AsyncSession = Depends(get_db),
    post_obj: Post = Depends(get_user_post)  # 所有権チェック
):
    """
    投稿を更新する
    
    - **認証**: 必須
    - **権限**: 投稿の所有者のみ
    """
    updated_post = await post.update(db, db_obj=post_obj, obj_in=post_in)
    return updated_post

@router.delete("/{post_id}", response_model=Post)
async def delete_post(
    *,
    post_id: UUID,
    db: AsyncSession = Depends(get_db),
    post_obj: Post = Depends(get_user_post)  # 所有権チェック
):
    """
    投稿を削除する
    
    - **認証**: 必須
    - **権限**: 投稿の所有者のみ
    """
    deleted_post = await post.delete(db, id=post_id)
    return deleted_post

@router.get("/user/{user_id}", response_model=List[Post])
async def get_user_posts(
    *,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100,
    published_only: bool = Query(None, description="公開済みの投稿のみを取得するかどうか")
):
    """
    特定ユーザーの投稿一覧を取得する
    
    - **認証**: 必須
    - **権限**: 認証されたユーザーであれば誰でも可能
    - **注意**: 自分以外のユーザーの場合は公開済みの投稿のみ取得可能
    """
    # 自分の投稿を取得する場合は、published_onlyのデフォルト値をFalseにする
    # 他のユーザーの投稿を取得する場合は、published_onlyのデフォルト値をTrueにする
    if published_only is None:
        published_only = user_id != current_user["user_id"]
    
    posts = await post.get_by_user(
        db, user_id=user_id, skip=skip, limit=limit, published_only=published_only
    )
    return posts
