import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from model.Users import Users
from dto.user_dto import SignupRequest


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_user_service():
    """UserService 모킹"""
    with patch("api.user_api.get_user_service") as mock:
        service = Mock()
        mock.return_value = service
        yield service


@pytest.fixture
def sample_user_data():
    """테스트용 사용자 데이터"""
    return {
        "email": "test@example.com",
        "nickname": "testuser",
        "password": "testpassword123",
        "signup_type": "email",
        "sns_provider": None,
        "sns_id": None,
    }


@pytest.fixture
def sample_user():
    """테스트용 Users 모델 인스턴스"""
    return Users(
        id="test-user-id",
        email="test@example.com",
        nickname="testuser",
        password_hash="hashed_password",
        signup_type="email",
        sns_provider=None,
        sns_id=None,
    )
