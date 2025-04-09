from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.base import Base
import uuid
from datetime import datetime

class Post(Base):
    __tablename__ = "posts"
    
    # 既存フィールド
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
        )
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, server_default=func.now())