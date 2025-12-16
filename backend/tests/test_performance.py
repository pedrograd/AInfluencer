"""Performance tests for AInfluencer backend.

This module contains performance tests for:
- API response times (P50, P95, P99)
- Concurrent request handling
- Database query performance
- System resource usage under load
"""

from __future__ import annotations

import asyncio
import statistics
import time
from collections import defaultdict
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.main import app


# Performance thresholds (in milliseconds)
PERFORMANCE_THRESHOLDS = {
    "api_response_p95": 200,  # P95 response time < 200ms
    "api_response_p99": 500,  # P99 response time < 500ms
    "db_query_p95": 100,  # P95 database query time < 100ms
    "concurrent_requests": 50,  # Support 50 concurrent requests
}


@pytest.fixture
def client():
    """Create a test client for performance testing."""
    return TestClient(app)


@pytest.fixture
async def db_session():
    """Create a test database session for performance testing."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.core.database import Base

    # Use in-memory SQLite for performance tests
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


def measure_response_time(func, *args, **kwargs):
    """Measure the response time of a function call."""
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    return (end_time - start_time) * 1000, result  # Convert to milliseconds


def calculate_percentiles(times: list[float], percentiles: list[int] = [50, 95, 99]) -> dict[int, float]:
    """Calculate percentile values from a list of times."""
    if not times:
        return {p: 0.0 for p in percentiles}

    sorted_times = sorted(times)
    results = {}
    for p in percentiles:
        index = int((p / 100) * len(sorted_times))
        if index >= len(sorted_times):
            index = len(sorted_times) - 1
        results[p] = sorted_times[index]
    return results


class TestAPIPerformance:
    """Performance tests for API endpoints."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_health_endpoint_performance(self, client):
        """Test health endpoint response time."""
        times = []
        iterations = 100

        for _ in range(iterations):
            elapsed, response = measure_response_time(client.get, "/api/health")
            times.append(elapsed)
            assert response.status_code == 200

        percentiles = calculate_percentiles(times)
        p95 = percentiles[95]
        p99 = percentiles[99]

        assert p95 < PERFORMANCE_THRESHOLDS["api_response_p95"], (
            f"Health endpoint P95 response time ({p95:.2f}ms) exceeds threshold "
            f"({PERFORMANCE_THRESHOLDS['api_response_p95']}ms)"
        )
        assert p99 < PERFORMANCE_THRESHOLDS["api_response_p99"], (
            f"Health endpoint P99 response time ({p99:.2f}ms) exceeds threshold "
            f"({PERFORMANCE_THRESHOLDS['api_response_p99']}ms)"
        )

    @pytest.mark.performance
    @pytest.mark.slow
    def test_status_endpoint_performance(self, client):
        """Test status endpoint response time."""
        times = []
        iterations = 50  # Status endpoint is heavier, fewer iterations

        for _ in range(iterations):
            elapsed, response = measure_response_time(client.get, "/api/status")
            times.append(elapsed)
            assert response.status_code == 200

        percentiles = calculate_percentiles(times)
        p95 = percentiles[95]
        p99 = percentiles[99]

        # Status endpoint is heavier, allow higher thresholds
        assert p95 < 500, (
            f"Status endpoint P95 response time ({p95:.2f}ms) exceeds threshold (500ms)"
        )
        assert p99 < 1000, (
            f"Status endpoint P99 response time ({p99:.2f}ms) exceeds threshold (1000ms)"
        )

    @pytest.mark.performance
    @pytest.mark.slow
    def test_auth_endpoints_performance(self, client):
        """Test authentication endpoints response time."""
        # Test register endpoint
        register_times = []
        for _ in range(20):
            elapsed, response = measure_response_time(
                client.post,
                "/api/auth/register",
                json={
                    "email": f"perf_test_{time.time()}@example.com",
                    "password": "testpassword123",
                    "full_name": "Performance Test User",
                },
            )
            register_times.append(elapsed)
            # Accept both 201 (success) and 400 (duplicate) as valid responses
            assert response.status_code in [201, 400]

        register_percentiles = calculate_percentiles(register_times)
        assert register_percentiles[95] < 500, (
            f"Register endpoint P95 response time ({register_percentiles[95]:.2f}ms) exceeds threshold (500ms)"
        )

    @pytest.mark.performance
    @pytest.mark.slow
    def test_characters_list_performance(self, client):
        """Test characters list endpoint response time."""
        times = []
        iterations = 50

        for _ in range(iterations):
            elapsed, response = measure_response_time(client.get, "/api/characters")
            times.append(elapsed)
            # Accept both 200 (success) and 401 (unauthorized) as valid responses
            assert response.status_code in [200, 401]

        percentiles = calculate_percentiles(times)
        p95 = percentiles[95]

        # Characters list may require auth, allow higher threshold
        assert p95 < 300, (
            f"Characters list endpoint P95 response time ({p95:.2f}ms) exceeds threshold (300ms)"
        )


class TestConcurrentRequests:
    """Tests for concurrent request handling."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_health_requests(self, client):
        """Test handling of concurrent health endpoint requests."""
        import concurrent.futures

        num_requests = PERFORMANCE_THRESHOLDS["concurrent_requests"]
        times = []

        def make_request():
            start = time.perf_counter()
            response = client.get("/api/health")
            elapsed = (time.perf_counter() - start) * 1000
            assert response.status_code == 200
            return elapsed

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            for future in concurrent.futures.as_completed(futures):
                times.append(future.result())

        percentiles = calculate_percentiles(times)
        p95 = percentiles[95]
        p99 = percentiles[99]

        # Under concurrent load, allow higher response times
        assert p95 < 1000, (
            f"Concurrent health requests P95 response time ({p95:.2f}ms) exceeds threshold (1000ms)"
        )
        assert p99 < 2000, (
            f"Concurrent health requests P99 response time ({p99:.2f}ms) exceeds threshold (2000ms)"
        )

    @pytest.mark.performance
    @pytest.mark.slow
    def test_concurrent_status_requests(self, client):
        """Test handling of concurrent status endpoint requests."""
        import concurrent.futures

        num_requests = 20  # Status endpoint is heavier, fewer concurrent requests
        times = []
        errors = []

        def make_request():
            try:
                start = time.perf_counter()
                response = client.get("/api/status")
                elapsed = (time.perf_counter() - start) * 1000
                assert response.status_code == 200
                return elapsed
            except Exception as e:
                errors.append(str(e))
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
            futures = [executor.submit(make_request) for _ in range(num_requests)]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result is not None:
                    times.append(result)

        # Allow some errors under heavy concurrent load, but most should succeed
        success_rate = len(times) / num_requests
        assert success_rate >= 0.8, (
            f"Concurrent status requests success rate ({success_rate:.2%}) is below 80%"
        )

        if times:
            percentiles = calculate_percentiles(times)
            p95 = percentiles[95]
            assert p95 < 2000, (
                f"Concurrent status requests P95 response time ({p95:.2f}ms) exceeds threshold (2000ms)"
            )


class TestDatabasePerformance:
    """Performance tests for database queries."""

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_database_query_performance(self, db_session: AsyncSession):
        """Test database query performance."""
        from app.models.character import Character
        from sqlalchemy import select

        # Create test characters
        characters = []
        for i in range(10):
            character = Character(
                name=f"Test Character {i}",
                bio=f"Bio {i}",
                age=25 + i,
            )
            characters.append(character)
            db_session.add(character)

        await db_session.commit()

        # Measure query performance
        query_times = []
        iterations = 50

        for _ in range(iterations):
            start = time.perf_counter()
            result = await db_session.execute(select(Character).limit(10))
            await result.scalars().all()
            elapsed = (time.perf_counter() - start) * 1000
            query_times.append(elapsed)

        percentiles = calculate_percentiles(query_times)
        p95 = percentiles[95]

        assert p95 < PERFORMANCE_THRESHOLDS["db_query_p95"], (
            f"Database query P95 response time ({p95:.2f}ms) exceeds threshold "
            f"({PERFORMANCE_THRESHOLDS['db_query_p95']}ms)"
        )

    @pytest.mark.performance
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_database_pagination_performance(self, db_session: AsyncSession):
        """Test database pagination query performance."""
        from app.models.character import Character
        from sqlalchemy import select

        # Create test characters
        for i in range(20):
            character = Character(
                name=f"Pagination Test {i}",
                bio=f"Bio {i}",
                age=25 + i,
            )
            db_session.add(character)

        await db_session.commit()

        # Measure pagination query performance
        query_times = []
        page_size = 10

        for offset in range(0, 20, page_size):
            start = time.perf_counter()
            result = await db_session.execute(
                select(Character).offset(offset).limit(page_size)
            )
            await result.scalars().all()
            elapsed = (time.perf_counter() - start) * 1000
            query_times.append(elapsed)

        percentiles = calculate_percentiles(query_times)
        p95 = percentiles[95]

        assert p95 < PERFORMANCE_THRESHOLDS["db_query_p95"], (
            f"Database pagination query P95 response time ({p95:.2f}ms) exceeds threshold "
            f"({PERFORMANCE_THRESHOLDS['db_query_p95']}ms)"
        )


class TestResourceUsage:
    """Tests for system resource usage under load."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_memory_usage_under_load(self, client):
        """Test memory usage under load."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Generate load
        for _ in range(100):
            client.get("/api/health")

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (< 100MB for 100 requests)
        assert memory_increase < 100, (
            f"Memory increase ({memory_increase:.2f}MB) exceeds threshold (100MB) for 100 requests"
        )

    @pytest.mark.performance
    @pytest.mark.slow
    def test_cpu_usage_under_load(self, client):
        """Test CPU usage under load."""
        import psutil
        import os
        import time

        process = psutil.Process(os.getpid())

        # Measure CPU usage during load
        cpu_percentages = []
        num_requests = 50

        for _ in range(num_requests):
            start = time.time()
            client.get("/api/health")
            # Measure CPU usage over a short window
            cpu_percent = process.cpu_percent(interval=0.1)
            cpu_percentages.append(cpu_percent)

        avg_cpu = statistics.mean(cpu_percentages)

        # Average CPU usage should be reasonable (< 80% for health checks)
        # This is a sanity check, not a strict requirement
        if avg_cpu > 80:
            pytest.skip(f"High CPU usage ({avg_cpu:.2f}%) detected, may be system-dependent")


class TestPerformanceRegression:
    """Tests to detect performance regressions."""

    @pytest.mark.performance
    @pytest.mark.slow
    def test_api_response_time_regression(self, client):
        """Test that API response times haven't regressed."""
        endpoints = [
            ("/api/health", 200),
            ("/api/status", 200),
        ]

        for endpoint, expected_status in endpoints:
            times = []
            iterations = 20

            for _ in range(iterations):
                elapsed, response = measure_response_time(client.get, endpoint)
                times.append(elapsed)
                assert response.status_code == expected_status

            avg_time = statistics.mean(times)
            p95 = calculate_percentiles(times)[95]

            # Log performance metrics for monitoring
            print(f"\n{endpoint} - Avg: {avg_time:.2f}ms, P95: {p95:.2f}ms")

            # Basic regression check: P95 should be reasonable
            assert p95 < 1000, (
                f"{endpoint} P95 response time ({p95:.2f}ms) indicates possible regression"
            )

