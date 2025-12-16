# Alembic Database Migrations

This directory contains database migration scripts managed by Alembic.

## Usage

### Create a new migration
```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migrations
```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

### View current migration status
```bash
alembic current
alembic history
```

## Notes

- Migrations use async SQLAlchemy with asyncpg driver
- All models must be imported in `alembic/env.py` for autogenerate to work
- The database URL is read from `app.core.config.settings.database_url`

