import uuid

from datetime import datetime
from typing import Annotated, Optional

from sqlalchemy import Column, String, \
    ForeignKey, TIMESTAMP, JSON, Table, \
    UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql import expression

from db.postgres import Base

uuid_pk = Annotated[uuid.UUID, mapped_column(
    primary_key=True,
    server_default=expression.text(
        "uuid_generate_v4()"))]
timestamp = Annotated[datetime,
mapped_column(TIMESTAMP(timezone=True),
              server_default=expression.text('now()'),
              nullable=False)]
timestamp_upd = Annotated[datetime,
mapped_column(TIMESTAMP(timezone=True),
              onupdate=func.now(),
              server_default=expression.text('now()'),
              nullable=False)]

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    creation_date: Mapped[timestamp]
    modified: Mapped[timestamp_upd]
    objects: Mapped[list['Object']] = relationship(lazy='selectin')
    categories: Mapped[list['Category']] = relationship(lazy='selectin')

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name

    def __str__(self) -> str:
        return f'<User {self.name}>'

class Object(Base):
    __tablename__ = 'bank'

    id: Mapped[uuid_pk]
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'))
    object: Mapped[str] = mapped_column(nullable=False)
    meaning: Mapped[str] = mapped_column(nullable=False)
    creation_date: Mapped[datetime] = mapped_column(
        server_default=expression.text('CURRENT_DATE'))
    next_date: Mapped[datetime] = mapped_column(
        server_default=expression.text('CURRENT_DATE+1'))
    interval: Mapped[float] = mapped_column(
        server_default='1', nullable=False)
    n: Mapped[int] = mapped_column(
        server_default='1', nullable=False)
    e_factor: Mapped[float] = mapped_column(
        server_default='2.5', nullable=False)
    category: Mapped[str] = mapped_column(nullable=False)
    modified: Mapped[timestamp_upd]

    __table_args__ = (UniqueConstraint(
        'user_id', 'object', 'category',
        name='user_id_object_idx'),
        )

    def __init__(self, object: str, meaning: str,
                 user_id: int, category: str):
        self.object = object
        self.meaning = meaning
        self.user_id = user_id
        self.category = category

    def __str__(self) -> str:
        return f'<Object {self.object}>'


class Category(Base):
    __tablename__ = 'categories'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'))
    name: Mapped[str] = mapped_column(nullable=False)
    creation_date: Mapped[timestamp]
    modified: Mapped[timestamp_upd]

    __table_args__ = (UniqueConstraint(
        'user_id', 'name', name='user_id_category_idx'),
        )

    def __init__(self, user_id: int, name: str):
        self.user_id = user_id
        self.name = name

    def __str__(self) -> str:
        return f'<Category {self.name}>'
