#!/usr/bin/env python3
"""Seed скрипт для заполнения локальной БД тестовыми данными.

Использование:
    python seed_local.py
"""

import asyncio
import random
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import settings
from app.core.auth import get_password_hash
from app.features.auth.models import User
from app.features.movies.models import Movie, Genre, MovieGenre
from app.features.ratings.models import Rating


async def main():
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        # ── Пользователи ──
        users_data = [
            ("nina", "12345"),
            ("artem", "12345"),
            ("margo", "12345"),
        ]
        users = []
        for username, password in users_data:
            user = User(username=username, hashed_password=get_password_hash(password))
            session.add(user)
            users.append(user)
        await session.commit()
        for u in users:
            await session.refresh(u)
        print(f"✅ Созданы пользователи: {[u.username for u in users]}")

        # ── Жанры ──
        genre_names = ["Комедия", "Драма", "Фантастика", "Боевик", "Ужасы"]
        genres = []
        for name in genre_names:
            g = Genre(name=name)
            session.add(g)
            genres.append(g)
        await session.commit()
        for g in genres:
            await session.refresh(g)
        print(f"✅ Созданы жанры: {[g.name for g in genres]}")

        # ── Фильмы (5 штук) ──
        movies_data = [
            {
                "title": "Зелёная миля",
                "description": "Пол Эджкомб — начальник блока смертников в тюрьме «Холодная гора». Каждый из узников ожидает свою очередь на электрический стул. Однажды в тюрьму поступает огромный заключённый, наделённый невероятным даром.",
                "release_year": 1999,
                "genres": ["Драма", "Ужасы"],
            },
            {
                "title": "Назад в будущее",
                "description": "Подросток Марти Макфлай на машине времени, изобретённой его другом доком Брауном, случайно попадает из 1985 года в 1955-й. Там он знакомится со своими родителями и мешает их знакомству, рискуя исчезнуть.",
                "release_year": 1985,
                "genres": ["Фантастика", "Комедия"],
            },
            {
                "title": "Тёмный рыцарь",
                "description": "Бэтмен объединяется с окружным прокурором Харви Дентом и комиссаром Гордоном, чтобы очистить Готэм от organised crime. На их пути встаёт харизматичный психопат Джокер, сеющий анархию.",
                "release_year": 2008,
                "genres": ["Боевик", "Драма"],
            },
            {
                "title": "Молчание ягнят",
                "description": "Молодая курсантка ФБР Кларисса Старлинг ведёт беседы с гениальным психиатром и серийным убийцей Ганнибалом Лектером, чтобы получить его помощь в поимке другого преступника — «Буффало Билла».",
                "release_year": 1991,
                "genres": ["Ужасы", "Драма"],
            },
            {
                "title": "Матрица",
                "description": "Программист Томас Андерсон узнаёт, что весь окружающий его мир — симуляция, созданная машинами. Он присоединяется к группе повстанцев, чтобы пробудить человечество и сразиться с системой.",
                "release_year": 1999,
                "genres": ["Фантастика", "Боевик"],
            },
        ]

        genre_map = {g.name: g for g in genres}
        movies = []
        for m in movies_data:
            movie = Movie(title=m["title"], description=m["description"], release_year=m["release_year"])
            session.add(movie)
            await session.flush()
            for gname in m["genres"]:
                link = MovieGenre(movie_id=movie.id, genre_id=genre_map[gname].id)
                session.add(link)
            movies.append(movie)

        await session.commit()
        for mv in movies:
            await session.refresh(mv)
        print(f"✅ Создано фильмов: {len(movies)}")

        # ── Рейтинги только от margo ──
        margo = next(u for u in users if u.username == "margo")
        random.seed(42)
        # margo оценивает 3 из 5 фильмов
        rated_movies = random.sample(movies, 3)
        for movie in rated_movies:
            rating_val = random.randint(1, 5)
            session.add(Rating(user_id=margo.id, movie_id=movie.id, rating=rating_val))
        await session.commit()
        print(f"✅ Margo оценила {len(rated_movies)} фильма(ов)")

    await engine.dispose()
    print("\n🎉 Заполнение БД завершено!")


if __name__ == "__main__":
    asyncio.run(main())
