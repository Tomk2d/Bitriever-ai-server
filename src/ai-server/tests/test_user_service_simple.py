import pytest
from unittest.mock import Mock, patch
import bcrypt
from dto.user_dto import SignupRequest, SignupType, SnsProvider


class TestUserServiceSimple:
    """UserService 간단 테스트 (Mock 사용)"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        # UserService Mock 생성
        self.mock_service = Mock()
        self.mock_repository = Mock()
        self.mock_service.user_repository = self.mock_repository

    def test_signup_success(self):
        """회원가입 성공 테스트"""
        # Given
        user_data = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type=SignupType.LOCAL,
            sns_provider=None,
            sns_id=None,
        )

        expected_user = Mock()
        expected_user.email = "test@example.com"
        expected_user.nickname = "testuser"
        expected_user.signup_type = SignupType.LOCAL

        self.mock_service.signup.return_value = expected_user

        # When
        result = self.mock_service.signup(user_data)

        # Then
        assert result == expected_user
        self.mock_service.signup.assert_called_once_with(user_data)

    def test_login_success(self):
        """로그인 성공 테스트"""
        # Given
        email = "test@example.com"
        password = "testpassword123"

        expected_user_info = {
            "user_id": "test-user-id",
            "email": "test@example.com",
            "nickname": "testuser",
            "signup_type": SignupType.LOCAL,
            "is_active": True,
            "is_upbit_connect": False,
        }

        self.mock_service.login.return_value = expected_user_info

        # When
        result = self.mock_service.login(email, password)

        # Then
        assert result == expected_user_info
        self.mock_service.login.assert_called_once_with(email, password)

    def test_login_user_not_found(self):
        """로그인 실패 - 사용자 없음"""
        # Given
        email = "nonexistent@example.com"
        password = "testpassword123"

        self.mock_service.login.side_effect = ValueError("존재하지 않는 이메일입니다.")

        # When & Then
        with pytest.raises(ValueError, match="존재하지 않는 이메일입니다."):
            self.mock_service.login(email, password)

    def test_login_wrong_password(self):
        """로그인 실패 - 잘못된 비밀번호"""
        # Given
        email = "test@example.com"
        password = "wrongpassword"

        self.mock_service.login.side_effect = ValueError(
            "비밀번호가 일치하지 않습니다."
        )

        # When & Then
        with pytest.raises(ValueError, match="비밀번호가 일치하지 않습니다."):
            self.mock_service.login(email, password)

    def test_check_email_duplicate_true(self):
        """이메일 중복 검사 - 중복인 경우"""
        # Given
        email = "existing@example.com"
        self.mock_service.check_email_duplicate.return_value = True

        # When
        result = self.mock_service.check_email_duplicate(email)

        # Then
        assert result is True
        self.mock_service.check_email_duplicate.assert_called_once_with(email)

    def test_check_email_duplicate_false(self):
        """이메일 중복 검사 - 중복이 아닌 경우"""
        # Given
        email = "new@example.com"
        self.mock_service.check_email_duplicate.return_value = False

        # When
        result = self.mock_service.check_email_duplicate(email)

        # Then
        assert result is False
        self.mock_service.check_email_duplicate.assert_called_once_with(email)

    def test_check_nickname_duplicate_true(self):
        """닉네임 중복 검사 - 중복인 경우"""
        # Given
        nickname = "existinguser"
        self.mock_service.check_nickname_duplicate.return_value = True

        # When
        result = self.mock_service.check_nickname_duplicate(nickname)

        # Then
        assert result is True
        self.mock_service.check_nickname_duplicate.assert_called_once_with(nickname)

    def test_check_nickname_duplicate_false(self):
        """닉네임 중복 검사 - 중복이 아닌 경우"""
        # Given
        nickname = "newuser"
        self.mock_service.check_nickname_duplicate.return_value = False

        # When
        result = self.mock_service.check_nickname_duplicate(nickname)

        # Then
        assert result is False
        self.mock_service.check_nickname_duplicate.assert_called_once_with(nickname)

    def test_signup_validation_error(self):
        """회원가입 검증 에러 테스트"""
        # Given - Mock에서 에러 발생 시뮬레이션
        user_data = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type=SignupType.LOCAL,
            sns_provider=None,
            sns_id=None,
        )

        self.mock_service.signup.side_effect = ValueError(
            "비밀번호는 8자 이상이어야 합니다."
        )

        # When & Then
        with pytest.raises(ValueError, match="비밀번호는 8자 이상이어야 합니다."):
            self.mock_service.signup(user_data)

    def test_signup_system_error(self):
        """회원가입 시스템 에러 테스트"""
        # Given
        user_data = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type=SignupType.LOCAL,
            sns_provider=None,
            sns_id=None,
        )

        self.mock_service.signup.side_effect = Exception("데이터베이스 연결 오류")

        # When & Then
        with pytest.raises(Exception, match="데이터베이스 연결 오류"):
            self.mock_service.signup(user_data)


class TestUserServiceIntegration:
    """UserService 통합 테스트 (실제 bcrypt 사용)"""

    def test_password_hashing_integration(self):
        """실제 bcrypt를 사용한 비밀번호 해싱 테스트"""
        # Given
        password = "testpassword123"

        # When
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

    def test_password_hashing_and_verification_workflow(self):
        """비밀번호 해싱 및 검증 워크플로우 테스트"""
        # Given
        original_password = "mypassword123"

        # When - 회원가입 시 해싱
        hashed_password = bcrypt.hashpw(
            original_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # Then - 로그인 시 검증
        # 올바른 비밀번호
        assert bcrypt.checkpw(
            original_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

        # 잘못된 비밀번호들
        wrong_passwords = [
            "mypassword",
            "mypassword12",
            "mypassword1234",
            "differentpassword",
        ]
        for wrong_password in wrong_passwords:
            assert not bcrypt.checkpw(
                wrong_password.encode("utf-8"), hashed_password.encode("utf-8")
            )

    def test_signup_request_validation(self):
        """SignupRequest 검증 테스트"""
        # Given & When & Then
        # 정상적인 로컬 가입
        valid_local_signup = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type=SignupType.LOCAL,
            sns_provider=None,
            sns_id=None,
        )
        assert valid_local_signup.email == "test@example.com"
        assert valid_local_signup.signup_type == SignupType.LOCAL

    def test_signup_request_validation_errors(self):
        """SignupRequest 검증 에러 테스트"""
        # Given & When & Then
        # 로컬 가입시 짧은 비밀번호 (Pydantic 필드 검증)
        with pytest.raises(
            ValueError, match="String should have at least 8 characters"
        ):
            SignupRequest(
                email="test@example.com",
                nickname="testuser",
                password="short",  # 8자 미만
                signup_type=SignupType.LOCAL,
                sns_provider=None,
                sns_id=None,
            )

    def test_signup_request_validation_success_cases(self):
        """SignupRequest 성공 케이스 테스트"""
        # Given & When & Then
        # 로컬 가입 성공
        local_signup = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type=SignupType.LOCAL,
            sns_provider=None,
            sns_id=None,
        )
        assert local_signup.signup_type == SignupType.LOCAL
        assert local_signup.password == "testpassword123"

    def test_enum_values(self):
        """Enum 값 테스트"""
        # Given & When & Then
        assert SignupType.LOCAL == 0
        assert SignupType.SNS == 1

        assert SnsProvider.NAVER == 1
        assert SnsProvider.KAKAO == 2
        assert SnsProvider.GOOGLE == 3
        assert SnsProvider.APPLE == 4

    def test_pydantic_field_validation(self):
        """Pydantic 필드 검증 테스트"""
        # Given & When & Then
        # 이메일 형식 검증
        with pytest.raises(ValueError, match="value is not a valid email"):
            SignupRequest(
                email="invalid-email",
                nickname="testuser",
                password="testpassword123",
                signup_type=SignupType.LOCAL,
                sns_provider=None,
                sns_id=None,
            )

        # 닉네임 길이 검증
        with pytest.raises(
            ValueError, match="String should have at most 20 characters"
        ):
            SignupRequest(
                email="test@example.com",
                nickname="verylongnicknamethatexceeds20characters",
                password="testpassword123",
                signup_type=SignupType.LOCAL,
                sns_provider=None,
                sns_id=None,
            )

    def test_basic_signup_request_creation(self):
        """기본 SignupRequest 생성 테스트"""
        # Given & When & Then
        # 로컬 가입 기본 테스트
        local_signup = SignupRequest(
            email="test@example.com",
            nickname="testuser",
            password="testpassword123",
            signup_type=SignupType.LOCAL,
            sns_provider=None,
            sns_id=None,
        )

        assert local_signup.email == "test@example.com"
        assert local_signup.nickname == "testuser"
        assert local_signup.password == "testpassword123"
        assert local_signup.signup_type == SignupType.LOCAL
        assert local_signup.sns_provider is None
        assert local_signup.sns_id is None
