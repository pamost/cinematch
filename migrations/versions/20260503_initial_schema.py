"""Initial schema: create all tables.

Revision ID: 0001_init
Revises:
Create Date: 2026-05-03 20:50:00.000000

Описание:
- users         — пользователи (регистрация, JWT)
- movies        — фильмы
- genres        — жанры
- movie_genres  — связь многие-ко-многим (фильмы ↔ жанры)
- ratings       — оценки пользователей

Все модели определены через SQLModel, миграция создана вручную
как пример работы с Alembic.
"""

# pylint: disable=no-member,invalid-name

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_init"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def table_exists(name: str) -> bool:
    """Проверяет, существует ли таблица в БД."""
    bind = op.get_bind()
    return sa.inspect(bind).has_table(name)


def upgrade() -> None:
    """Создание всех таблиц начальной схемы."""

    # --- users ---
    if not table_exists("users"):
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("username", sa.String(length=50), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("username"),
        )
        op.create_index(op.f("ix_users_username"), "users", ["username"])

    # --- movies ---
    if not table_exists("movies"):
        op.create_table(
            "movies",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("release_year", sa.Integer(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_movies_title"), "movies", ["title"])

    # --- genres ---
    if not table_exists("genres"):
        op.create_table(
            "genres",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("name"),
        )
        op.create_index(op.f("ix_genres_name"), "genres", ["name"])

    # --- movie_genres (many-to-many) ---
    if not table_exists("movie_genres"):
        op.create_table(
            "movie_genres",
            sa.Column("movie_id", sa.Integer(), nullable=False),
            sa.Column("genre_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(
                ["movie_id"], ["movies.id"],
                name="fk_movie_genres_movie_id",
            ),
            sa.ForeignKeyConstraint(
                ["genre_id"], ["genres.id"],
                name="fk_movie_genres_genre_id",
            ),
            sa.PrimaryKeyConstraint("movie_id", "genre_id"),
        )

    # --- ratings ---
    if not table_exists("ratings"):
        op.create_table(
            "ratings",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("movie_id", sa.Integer(), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.ForeignKeyConstraint(
                ["user_id"], ["users.id"],
                name="fk_ratings_user_id",
            ),
            sa.ForeignKeyConstraint(
                ["movie_id"], ["movies.id"],
                name="fk_ratings_movie_id",
            ),
        )


def downgrade() -> None:
    """Удаление всех таблиц (откат миграции)."""

    if table_exists("ratings"):
        op.drop_table("ratings")
    if table_exists("movie_genres"):
        op.drop_table("movie_genres")
    if table_exists("genres"):
        op.drop_index(op.f("ix_genres_name"), table_name="genres")
        op.drop_table("genres")
    if table_exists("movies"):
        op.drop_index(op.f("ix_movies_title"), table_name="movies")
        op.drop_table("movies")
    if table_exists("users"):
        op.drop_index(op.f("ix_users_username"), table_name="users")
        op.drop_table("users")
