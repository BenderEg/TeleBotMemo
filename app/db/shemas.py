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

from db.db import Base

uuid_pk = Annotated[uuid.UUID, mapped_column(
    primary_key=True,
    server_default=expression.text(
        "uuid_generate_v4()"))]


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid_pk]
    email: Mapped[str_255] = mapped_column(unique=True)
    password: Mapped[str_255]
    salt: Mapped[Optional[str_50]]
    first_name: Mapped[Optional[str_50]]
    last_name: Mapped[Optional[str_50]]
    created: Mapped[timestamp]
    modified: Mapped[timestamp_upd]
    user_data: Mapped['UserData'] = relationship(lazy='selectin')
    user_auths: Mapped[list['AuthHistory']] = relationship(lazy='selectin')
    user_roles: Mapped[list['Role']] = relationship(secondary=users_roles,
                                                    lazy='selectin')
    social_accounts: Mapped[list['SocialAccount']] = relationship(lazy='selectin')

    def __init__(self, email: str, password: str):
        self.email = email
        self.salt = self.salt_generator()
        self.password = self.hash_password(password)

    def __repr__(self) -> str:
        return f'<User {self.email}>'