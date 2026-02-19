import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from main import app
from dto.user_dto import SignupType, SnsProvider


class TestUserAPI:
    """User API 테스트"""

    @pytest.fixture
    def client(self):
        """FastAPI 테스트 클라이언트"""
        return TestClient(app)

    @pytest.fixture
    def mock_user_service(self):
        """UserService Mock"""
        return Mock()

    @pytest.fixture
    def sample_user_data(self):
        """샘플 사용자 데이터"""
        return {
            "email": "test@example.com",
            "nickname": "testuser",
            "password": "testpassword123",
            "signup_type": SignupType.LOCAL,
            "sns_provider": None,
            "sns_id": None,
        }

    @pytest.fixture
    def sample_login_data(self):
        """샘플 로그인 데이터"""
        return {"email": "test@example.com", "password": "testpassword123"}

    @pytest.fixture
    def sample_user_info(self):
        """샘플 사용자 정보 (로그인 응답용)"""
        return {
            "user_id": "test-user-id",
            "email": "test@example.com",
            "nickname": "testuser",
            "signup_type": SignupType.LOCAL,
            "is_active": True,
            "is_upbit_connect": False,
        }

    @patch("api.user_api.get_user_service")
    def test_signup_success(
        self, mock_get_service, client, mock_user_service, sample_user_data
    ):
        """회원가입 성공 테스트"""
        # Given
        mock_get_service.return_value = mock_user_service

        expected_user = Mock()
        expected_user.id = "test-user-id"
        expected_user.email = "test@example.com"
        expected_user.nickname = "testuser"
        expected_user.signup_type = SignupType.LOCAL
        expected_user.created_at = "2024-01-01T00:00:00"
        expected_user.is_active = True
        expected_user.is_upbit_connect = False

        mock_user_service.signup.return_value = expected_user

        # When
        response = client.post("/user/signup", json=sample_user_data)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "회원가입이 완료되었습니다"
        assert data["data"]["user_id"] == "test-user-id"
        assert data["data"]["email"] == "test@example.com"

        mock_user_service.signup.assert_called_once()

    @patch("api.user_api.get_user_service")
    def test_login_success(
        self,
        mock_get_service,
        client,
        mock_user_service,
        sample_login_data,
        sample_user_info,
    ):
        """로그인 성공 테스트"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.login.return_value = sample_user_info

        # When
        response = client.post("/user/login", json=sample_login_data)

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "로그인이 완료되었습니다"
        assert data["data"]["user_id"] == "test-user-id"
        assert data["data"]["email"] == "test@example.com"
        assert data["data"]["nickname"] == "testuser"
        assert data["data"]["access_token"] == "dummy_access_token_for_now"
        assert data["data"]["token_type"] == "bearer"

        mock_user_service.login.assert_called_once_with(
            "test@example.com", "testpassword123"
        )

    @patch("api.user_api.get_user_service")
    def test_login_user_not_found(
        self, mock_get_service, client, mock_user_service, sample_login_data
    ):
        """로그인 실패 - 사용자 없음"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.login.side_effect = ValueError("존재하지 않는 이메일입니다.")

        # When
        response = client.post("/user/login", json=sample_login_data)

        # Then
        assert response.status_code == 400
        data = response.json()
        assert data["status_code"] == 400
        assert data["error_code"] == "LOGIN_FAILED"
        assert "존재하지 않는 이메일입니다" in data["message"]

    @patch("api.user_api.get_user_service")
    def test_login_wrong_password(
        self, mock_get_service, client, mock_user_service, sample_login_data
    ):
        """로그인 실패 - 잘못된 비밀번호"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.login.side_effect = ValueError(
            "비밀번호가 일치하지 않습니다."
        )

        # When
        response = client.post("/user/login", json=sample_login_data)

        # Then
        assert response.status_code == 400
        data = response.json()
        assert data["status_code"] == 400
        assert data["error_code"] == "LOGIN_FAILED"
        assert "비밀번호가 일치하지 않습니다" in data["message"]

    @patch("api.user_api.get_user_service")
    def test_login_invalid_email_format(
        self, mock_get_service, client, mock_user_service
    ):
        """로그인 실패 - 잘못된 이메일 형식"""
        # Given
        mock_get_service.return_value = mock_user_service
        invalid_login_data = {"email": "invalid-email", "password": "testpassword123"}

        # When
        response = client.post("/user/login", json=invalid_login_data)

        # Then
        assert response.status_code == 422  # Pydantic validation error

    @patch("api.user_api.get_user_service")
    def test_login_empty_password(self, mock_get_service, client, mock_user_service):
        """로그인 실패 - 빈 비밀번호"""
        # Given
        mock_get_service.return_value = mock_user_service
        invalid_login_data = {"email": "test@example.com", "password": ""}

        # When
        response = client.post("/user/login", json=invalid_login_data)

        # Then
        assert response.status_code == 422  # Pydantic validation error

    @patch("api.user_api.get_user_service")
    def test_check_email_duplicate_true(
        self, mock_get_service, client, mock_user_service
    ):
        """이메일 중복 검사 - 중복인 경우"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.check_email_duplicate.return_value = True

        # When
        response = client.get("/user/check-email?email=existing@example.com")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "existing@example.com"
        assert data["data"]["is_duplicate"] is True

        mock_user_service.check_email_duplicate.assert_called_once_with(
            "existing@example.com"
        )

    @patch("api.user_api.get_user_service")
    def test_check_email_duplicate_false(
        self, mock_get_service, client, mock_user_service
    ):
        """이메일 중복 검사 - 중복이 아닌 경우"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.check_email_duplicate.return_value = False

        # When
        response = client.get("/user/check-email?email=new@example.com")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "new@example.com"
        assert data["data"]["is_duplicate"] is False

        mock_user_service.check_email_duplicate.assert_called_once_with(
            "new@example.com"
        )

    @patch("api.user_api.get_user_service")
    def test_check_nickname_duplicate_true(
        self, mock_get_service, client, mock_user_service
    ):
        """닉네임 중복 검사 - 중복인 경우"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.check_nickname_duplicate.return_value = True

        # When
        response = client.get("/user/check-nickname?nickname=existinguser")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["nickname"] == "existinguser"
        assert data["data"]["is_duplicate"] is True

        mock_user_service.check_nickname_duplicate.assert_called_once_with(
            "existinguser"
        )

    @patch("api.user_api.get_user_service")
    def test_check_nickname_duplicate_false(
        self, mock_get_service, client, mock_user_service
    ):
        """닉네임 중복 검사 - 중복이 아닌 경우"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.check_nickname_duplicate.return_value = False

        # When
        response = client.get("/user/check-nickname?nickname=newuser")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["nickname"] == "newuser"
        assert data["data"]["is_duplicate"] is False

        mock_user_service.check_nickname_duplicate.assert_called_once_with("newuser")

    @patch("api.user_api.get_user_service")
    def test_signup_validation_error(self, mock_get_service, client, mock_user_service):
        """회원가입 검증 에러 테스트"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.signup.side_effect = ValueError("비밀번호는 필수입니다.")

        invalid_user_data = {
            "email": "test@example.com",
            "nickname": "testuser",
            "password": "",  # 빈 비밀번호
            "signup_type": SignupType.LOCAL,
            "sns_provider": None,
            "sns_id": None,
        }

        # When
        response = client.post("/user/signup", json=invalid_user_data)

        # Then
        assert response.status_code == 422  # Pydantic validation error

    @patch("api.user_api.get_user_service")
    def test_signup_system_error(
        self, mock_get_service, client, mock_user_service, sample_user_data
    ):
        """회원가입 시스템 에러 테스트"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.signup.side_effect = Exception("데이터베이스 연결 오류")

        # When
        response = client.post("/user/signup", json=sample_user_data)

        # Then
        assert response.status_code == 500
        data = response.json()
        assert data["status_code"] == 500
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"

    @patch("api.user_api.get_user_service")
    def test_login_system_error(
        self, mock_get_service, client, mock_user_service, sample_login_data
    ):
        """로그인 시스템 에러 테스트"""
        # Given
        mock_get_service.return_value = mock_user_service
        mock_user_service.login.side_effect = Exception("데이터베이스 연결 오류")

        # When
        response = client.post("/user/login", json=sample_login_data)

        # Then
        assert response.status_code == 500
        data = response.json()
        assert data["status_code"] == 500
        assert data["error_code"] == "INTERNAL_SERVER_ERROR"

    def test_signup_invalid_email_format(self, client):
        """회원가입 실패 - 잘못된 이메일 형식"""
        # Given
        invalid_user_data = {
            "email": "invalid-email",
            "nickname": "testuser",
            "password": "testpassword123",
            "signup_type": SignupType.LOCAL,
            "sns_provider": None,
            "sns_id": None,
        }

        # When
        response = client.post("/user/signup", json=invalid_user_data)

        # Then
        assert response.status_code == 422  # Pydantic validation error

    def test_signup_short_password(self, client):
        """회원가입 실패 - 짧은 비밀번호"""
        # Given
        invalid_user_data = {
            "email": "test@example.com",
            "nickname": "testuser",
            "password": "short",  # 8자 미만
            "signup_type": SignupType.LOCAL,
            "sns_provider": None,
            "sns_id": None,
        }

        # When
        response = client.post("/user/signup", json=invalid_user_data)

        # Then
        assert response.status_code == 422  # Pydantic validation error

    def test_signup_long_nickname(self, client):
        """회원가입 실패 - 긴 닉네임"""
        # Given
        invalid_user_data = {
            "email": "test@example.com",
            "nickname": "verylongnicknamethatexceeds20characters",
            "password": "testpassword123",
            "signup_type": SignupType.LOCAL,
            "sns_provider": None,
            "sns_id": None,
        }

        # When
        response = client.post("/user/signup", json=invalid_user_data)

        # Then
        assert response.status_code == 422  # Pydantic validation error
