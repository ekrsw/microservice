from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.sql import func
from typing import List, Optional, Dict, Any
from uuid import UUID
import datetime

from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate

class PostCRUD:
    async def create(self, db: AsyncSession, *, obj_in: PostCreate, user_id: UUID) -> Post:
        """
        新しい投稿を作成する

        Args:
            db: データベースセッション
            obj_in: 作成する投稿データ
            user_id: 投稿者のユーザーID

        Returns:
            作成された投稿
        """
        db_obj = Post(
            title=obj_in.title,
            content=obj_in.content,
            user_id=user_id,
            is_published=obj_in.is_published,
            published_at=datetime.datetime.now() if obj_in.is_published else None
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get(self, db: AsyncSession, *, id: UUID) -> Optional[Post]:
        """
        IDで投稿を取得する

        Args:
            db: データベースセッション
            id: 投稿ID

        Returns:
            取得した投稿、存在しない場合はNone
        """
        query = select(Post).where(Post.id == id)
        result = await db.execute(query)
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100, published_only: bool = True
    ) -> List[Post]:
        """
        複数の投稿を取得する

        Args:
            db: データベースセッション
            skip: スキップする件数
            limit: 取得する最大件数
            published_only: 公開済みの投稿のみを取得するかどうか

        Returns:
            投稿のリスト
        """
        query = select(Post)
        if published_only:
            query = query.where(Post.is_published == True)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_by_user(
        self, db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 100, published_only: bool = False
    ) -> List[Post]:
        """
        特定ユーザーの投稿を取得する

        Args:
            db: データベースセッション
            user_id: ユーザーID
            skip: スキップする件数
            limit: 取得する最大件数
            published_only: 公開済みの投稿のみを取得するかどうか

        Returns:
            投稿のリスト
        """
        query = select(Post).where(Post.user_id == user_id)
        if published_only:
            query = query.where(Post.is_published == True)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def update(
        self, db: AsyncSession, *, db_obj: Post, obj_in: PostUpdate
    ) -> Post:
        """
        投稿を更新する

        Args:
            db: データベースセッション
            db_obj: 更新する投稿オブジェクト
            obj_in: 更新データ

        Returns:
            更新された投稿
        """
        update_data = obj_in.model_dump(exclude_unset=True)
        
        # 公開状態が変更された場合、published_atを更新
        if "is_published" in update_data and update_data["is_published"] != db_obj.is_published:
            if update_data["is_published"]:
                update_data["published_at"] = datetime.datetime.now()
            else:
                update_data["published_at"] = None
        
        for field in update_data:
            setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def delete(self, db: AsyncSession, *, id: UUID) -> Optional[Post]:
        """
        投稿を削除する

        Args:
            db: データベースセッション
            id: 削除する投稿ID

        Returns:
            削除された投稿、存在しない場合はNone
        """
        post = await self.get(db, id=id)
        if post:
            await db.delete(post)
            await db.commit()
        return post

    async def publish(self, db: AsyncSession, *, db_obj: Post, publish: bool = True) -> Post:
        """
        投稿の公開状態を変更する

        Args:
            db: データベースセッション
            db_obj: 変更する投稿オブジェクト
            publish: 公開する場合はTrue、非公開にする場合はFalse

        Returns:
            更新された投稿
        """
        db_obj.is_published = publish
        db_obj.published_at = datetime.datetime.now() if publish else None
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

# CRUDクラスのインスタンスを作成
post = PostCRUD()
