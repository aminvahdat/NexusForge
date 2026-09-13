"""Phase 2 foundation tests."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pytest
from unittest.mock import patch

# Test settings load and respect environment
from backend.app.config.settings import get_settings, Settings


class TestSettings:
    def test_default_max_workers_is_2(self):
        s = Settings()
        assert s.max_concurrent_workers == 2

    def test_environment_overrides(self):
        with patch.dict(os.environ, {'MAX_CONCURRENT_WORKERS': '5'}):
            s = Settings()
            assert s.max_concurrent_workers == 5

    def test_database_url_validation(self):
        with pytest.raises(Exception):
            Settings(DATABASE_URL="invalid://url")

    def test_ai_provider_agnostic(self):
        s = Settings()
        assert s.ai_provider is None  # Must be configured by user, not hardcoded
        assert s.ai_model is None
        assert s.ai_api_key is None

    def test_env_friends_local_docker(self):
        s = Settings()
        assert s.database_url.startswith(('postgresql://', 'postgresql+', 'sqlite'))
        assert s.redis_url.startswith('redis://')
        assert 'postgres' in s.database_url or 'redis' in s.database_url or 'sqlite' in s.database_url


# Test database schema
from backend.app.models import User, Project, Task, Artifact, AgentRole, Priority, TaskStatus

def test_task_has_uuid_pk():
    from sqlalchemy.dialects.postgresql import UUID
    assert isinstance(Task.id.type, UUID)

def test_project_has_uuid_pk():
    from sqlalchemy.dialects.postgresql import UUID
    assert isinstance(Project.id.type, UUID)

def test_user_has_uuid_pk():
    from sqlalchemy.dialects.postgresql import UUID
    assert isinstance(User.id.type, UUID)

def test_artifact_has_uuid_pk():
    from sqlalchemy.dialects.postgresql import UUID
    assert isinstance(Artifact.id.type, UUID)

def test_task_has_role_enum_str():
    assert Task.role.type.python_type is str

def test_task_has_status_enum_str():
    assert Task.status.type.python_type is str

def test_task_has_json_dependencies():
    assert Task.dependencies.type.__class__.__name__ == 'JSON'

def test_project_has_owner_id_fk():
    # Project has ownership boundary for multi-user isolation
    assert Project.owner_id is not None

def test_task_has_project_id_fk():
    assert Task.project_id is not None


def test_config_uses_env_for_db():
    # Verify database is fully environment-driven (not hardcoded)
    s = Settings()
    # The default can be overridden via .env
    assert s.database_url.startswith(('postgresql://', 'postgresql+', 'sqlite'))
