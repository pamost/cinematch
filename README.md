# CineMatch - рекомендательная система фильмов с коллаборативной фильтрацией

## Описание feature-based струкутры проекта
    auth - регистрация, логин, JWT
    movies - CRUD фильмов и жанров
    ratings - оценки пользователей
    recommendations - алгоритм коллаборативной фильтрации (главная бизнес-задача)

    cinematch/
    ├── .env
    ├── .gitignore
    ├── .pylintrc
    ├── docker-compose.yml
    ├── requirements.txt
    ├── README.md
    ├── app/
    │   ├── __init__.py
    │   ├── main.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── config.py
    │   │   ├── database.py
    │   │   └── auth.py
    │   └── features/
    │       ├── auth/
    │       │   ├── __init__.py
    │       │   ├── models.py
    │       │   ├── schemas.py
    │       │   ├── service.py
    │       │   └── router.py
    │       ├── movies/   (аналогично)
    │       ├── ratings/  (аналогично)
    │       └── recommendations/ (аналогично)
    └── tests/
        ├── __init__.py
        ├── conftest.py
        └── test_auth.py

    app/core/config.py -  класс настроек с pydantic-settings
    app/core/database.py - движок SQLModel, сессии, зависимость get_db
    app/core/auth.py - хеширование паролей (pwdlib), создание и верификация JWT, зависимость get_current_user

    app/features/auth/models.py - SQLModel-классы (таблицы)
    app/features/auth/schemas.py - Pydantic-схемы (запрос/ответ)
    app/features/auth/service.py - бизнес-логика (работа с БД)
    app/features/auth/router.py - эндпоинты

## Запуск
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    uvicorn app.main:app --reload
    deactivate