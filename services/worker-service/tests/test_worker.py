"""
Worker Service — Unit Tests
"""

import pytest


class TestCeleryConfig:
    def test_celery_app_loads(self):
        from app.worker import celery_app
        assert celery_app is not None
        assert celery_app.main == "scalable_ai_worker"

    def test_task_routes_configured(self):
        from app.worker import celery_app
        routes = celery_app.conf.task_routes
        assert "app.worker.tasks.run_inference" in routes
        assert routes["app.worker.tasks.run_inference"]["queue"] == "inference"

    def test_task_serializer_is_json(self):
        from app.worker import celery_app
        assert celery_app.conf.task_serializer == "json"

    def test_acks_late_enabled(self):
        from app.worker import celery_app
        assert celery_app.conf.task_acks_late is True


class TestTasks:
    def test_health_check_task(self):
        from app.worker import health_check
        result = health_check()
        assert result["status"] == "healthy"
        assert "timestamp" in result
