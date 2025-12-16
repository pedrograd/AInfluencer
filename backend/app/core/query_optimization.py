"""Query optimization utilities for preventing N+1 queries and optimizing database access.

This module provides helper functions and utilities for optimizing database queries,
including eager loading, batch fetching, and query result optimization.
"""

from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from typing import TypeVar, Any

T = TypeVar("T")


async def get_with_relations(
    session: AsyncSession,
    model: type[T],
    filters: dict[str, Any] | None = None,
    relations: list[str] | None = None,
    load_strategy: str = "selectin",
) -> list[T] | T | None:
    """Get model instances with eager-loaded relationships to prevent N+1 queries.
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        filters: Dictionary of filter conditions (e.g., {"id": 123})
        relations: List of relationship names to eager load
        load_strategy: Loading strategy - "selectin" (default), "joined", or "subquery"
        
    Returns:
        Single instance if filters result in one row, list if multiple, None if none
        
    Example:
        ```python
        # Get character with all posts eager-loaded
        character = await get_with_relations(
            db,
            Character,
            filters={"id": character_id},
            relations=["posts", "platform_accounts"]
        )
        ```
    """
    query = select(model)
    
    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(model, key):
                query = query.where(getattr(model, key) == value)
    
    # Add eager loading for relationships
    if relations:
        for relation in relations:
            if hasattr(model, relation):
                if load_strategy == "selectin":
                    query = query.options(selectinload(getattr(model, relation)))
                elif load_strategy == "joined":
                    query = query.options(joinedload(getattr(model, relation)))
                else:
                    query = query.options(selectinload(getattr(model, relation)))
    
    result = await session.execute(query)
    
    if filters and len(filters) == 1:
        # Single result expected
        return result.scalar_one_or_none()
    else:
        # Multiple results
        return list(result.scalars().all())


async def batch_get(
    session: AsyncSession,
    model: type[T],
    ids: list[Any],
    id_field: str = "id",
) -> dict[Any, T]:
    """Batch fetch multiple model instances by IDs in a single query.
    
    Prevents N+1 queries when fetching multiple records.
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        ids: List of IDs to fetch
        id_field: Name of the ID field (default: "id")
        
    Returns:
        Dictionary mapping ID to model instance
        
    Example:
        ```python
        character_ids = ["uuid1", "uuid2", "uuid3"]
        characters = await batch_get(db, Character, character_ids)
        # Returns: {"uuid1": Character(...), "uuid2": Character(...), ...}
        ```
    """
    if not ids:
        return {}
    
    id_attr = getattr(model, id_field)
    query = select(model).where(id_attr.in_(ids))
    result = await session.execute(query)
    instances = result.scalars().all()
    
    return {getattr(inst, id_field): inst for inst in instances}


async def get_paginated(
    session: AsyncSession,
    model: type[T],
    page: int = 1,
    per_page: int = 20,
    filters: dict[str, Any] | None = None,
    order_by: str | None = None,
    descending: bool = True,
) -> tuple[list[T], int]:
    """Get paginated query results with total count.
    
    Args:
        session: Database session
        model: SQLAlchemy model class
        page: Page number (1-indexed)
        per_page: Number of items per page
        filters: Dictionary of filter conditions
        order_by: Field name to order by (default: model's primary key)
        descending: Whether to sort in descending order
        
    Returns:
        Tuple of (items list, total count)
        
    Example:
        ```python
        characters, total = await get_paginated(
            db,
            Character,
            page=1,
            per_page=20,
            order_by="created_at",
            descending=True
        )
        ```
    """
    # Build base query
    query = select(model)
    count_query = select(func.count()).select_from(model)
    
    # Apply filters
    if filters:
        for key, value in filters.items():
            if hasattr(model, key):
                filter_cond = getattr(model, key) == value
                query = query.where(filter_cond)
                count_query = count_query.where(filter_cond)
    
    # Apply ordering
    if order_by and hasattr(model, order_by):
        order_attr = getattr(model, order_by)
        query = query.order_by(order_attr.desc() if descending else order_attr.asc())
    else:
        # Default to primary key
        pk = model.__mapper__.primary_key[0]
        query = query.order_by(pk.desc() if descending else pk.asc())
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.limit(per_page).offset(offset)
    
    # Execute queries
    result = await session.execute(query)
    items = list(result.scalars().all())
    
    count_result = await session.execute(count_query)
    total = count_result.scalar_one()
    
    return items, total

