import pytest
from unittest.mock import Mock, patch, MagicMock
import bcrypt
from model.Users import Users
from dto.user_dto import SignupRequest


class TestUserService:
    """UserService 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        with patch("service.user_service.UserService") as mock_service_class:
            self.mock_service = mock_service_class.return_value
            self.mock_repository = Mock()
            self.mock_service.user_repository = self.mock_repository

    def test_signup_success(self):
        """회원가입 성공 테스트"""
        # Given
        user_data = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type="email",
            sns_provider=None,
            sns_id=None,
        )

        expected_user = Users(
            id="test-id",
            email="test@example.com",
            nickname="testuser",
            password_hash="hashed_password",
            signup_type="email",
        )

        self.mock_repository.save_user.return_value = expected_user

        # When
        result = self.mock_service.signup(user_data)

        # Then
        assert result == expected_user
        self.mock_repository.save_user.assert_called_once()

        # Users 객체가 올바른 파라미터로 생성되었는지 확인
        call_args = self.mock_repository.save_user.call_args[0][0]
        assert call_args.email == user_data.email
        assert call_args.nickname == user_data.nickname
        assert call_args.signup_type == user_data.signup_type

    def test_signup_empty_password(self):
        """빈 비밀번호로 회원가입 시도 시 에러"""
        # Given
        user_data = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="",  # 빈 비밀번호
            signup_type="email",
            sns_provider=None,
            sns_id=None,
        )

        self.mock_service.signup.side_effect = ValueError("비밀번호는 필수입니다.")

        # When & Then
        with pytest.raises(ValueError, match="비밀번호는 필수입니다."):
            self.mock_service.signup(user_data)

    def test_signup_whitespace_password(self):
        """공백만 있는 비밀번호로 회원가입 시도 시 에러"""
        # Given
        user_data = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="   ",  # 공백만 있는 비밀번호
            signup_type="email",
            sns_provider=None,
            sns_id=None,
        )

        self.mock_service.signup.side_effect = ValueError("비밀번호는 필수입니다.")

        # When & Then
        with pytest.raises(ValueError, match="비밀번호는 필수입니다."):
            self.mock_service.signup(user_data)

    def test_signup_repository_error(self):
        """리포지토리 에러 시 처리"""
        # Given
        user_data = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type="email",
            sns_provider=None,
            sns_id=None,
        )

        self.mock_service.signup.side_effect = Exception("데이터베이스 연결 오류")

        # When & Then
        with pytest.raises(Exception, match="데이터베이스 연결 오류"):
            self.mock_service.signup(user_data)

    def test_check_email_duplicate_true(self):
        """이메일 중복 검사 - 중복인 경우"""
        # Given
        email = "existing@example.com"
        existing_user = Mock()
        self.mock_repository.find_by_email.return_value = existing_user

        # When
        result = self.mock_service.check_email_duplicate(email)

        # Then
        assert result is True
        self.mock_repository.find_by_email.assert_called_once_with(email)

    def test_check_email_duplicate_false(self):
        """이메일 중복 검사 - 중복이 아닌 경우"""
        # Given
        email = "new@example.com"
        self.mock_repository.find_by_email.return_value = None

        # When
        result = self.mock_service.check_email_duplicate(email)

        # Then
        assert result is False
        self.mock_repository.find_by_email.assert_called_once_with(email)

    def test_check_email_duplicate_error(self):
        """이메일 중복 검사 중 에러 발생"""
        # Given
        email = "test@example.com"
        self.mock_repository.find_by_email.side_effect = Exception("데이터베이스 오류")

        # When & Then
        with pytest.raises(Exception, match="데이터베이스 오류"):
            self.mock_service.check_email_duplicate(email)

    def test_check_nickname_duplicate_true(self):
        """닉네임 중복 검사 - 중복인 경우"""
        # Given
        nickname = "existinguser"
        existing_user = Mock()
        self.mock_repository.find_by_nickname.return_value = existing_user

        # When
        result = self.mock_service.check_nickname_duplicate(nickname)

        # Then
        assert result is True
        self.mock_repository.find_by_nickname.assert_called_once_with(nickname)

    def test_check_nickname_duplicate_false(self):
        """닉네임 중복 검사 - 중복이 아닌 경우"""
        # Given
        nickname = "newuser"
        self.mock_repository.find_by_nickname.return_value = None

        # When
        result = self.mock_service.check_nickname_duplicate(nickname)

        # Then
        assert result is False
        self.mock_repository.find_by_nickname.assert_called_once_with(nickname)

    def test_check_nickname_duplicate_error(self):
        """닉네임 중복 검사 중 에러 발생"""
        # Given
        nickname = "testuser"
        self.mock_repository.find_by_nickname.side_effect = Exception(
            "데이터베이스 오류"
        )

        # When & Then
        with pytest.raises(Exception, match="데이터베이스 오류"):
            self.mock_service.check_nickname_duplicate(nickname)

    def test_hash_password(self):
        """비밀번호 해싱 테스트"""
        # Given
        password = "testpassword123"

        # When
        with patch("service.user_service.bcrypt") as mock_bcrypt:
            mock_bcrypt.hashpw.return_value = b"hashed_password_bytes"
            mock_bcrypt.gensalt.return_value = b"salt_bytes"

            result = self.mock_service._hash_password(password)

        # Then
        mock_bcrypt.hashpw.assert_called_once_with(
            password.encode("utf-8"), mock_bcrypt.gensalt.return_value
        )
        mock_bcrypt.gensalt.assert_called_once()


class TestUserServiceIntegration:
    """UserService 통합 테스트 (실제 bcrypt 사용)"""

    def test_password_hashing_integration(self):
        """실제 bcrypt를 사용한 비밀번호 해싱 테스트"""
        # Given
        password = "testpassword123"

        # When
        with patch("service.user_service.UserService") as mock_service_class:
            service = mock_service_class.return_value

            # 실제 bcrypt 사용
            hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
                "utf-8"
            )

            # Then
            assert hashed != password
            assert len(hashed) > len(password)

            # 해시된 비밀번호 검증
            assert bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    def test_password_verification(self):
        """해시된 비밀번호 검증 테스트"""
        # Given
        original_password = "testpassword123"
        hashed_password = bcrypt.hashpw(
            original_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # When & Then
        # 올바른 비밀번호 검증
        assert bcrypt.checkpw(
            original_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

        # 잘못된 비밀번호 검증
        wrong_password = "wrongpassword"
        assert not bcrypt.checkpw(
            wrong_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
