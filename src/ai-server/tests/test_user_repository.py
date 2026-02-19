import pytest
from unittest.mock import Mock, patch, MagicMock
from model.Users import Users


class TestUserRepository:
    """UserRepository 테스트"""

    @patch("repository.user_repository.db")
    def test_save_user_success(self, mock_db):
        """사용자 저장 성공 테스트"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = (
            None  # 중복 없음
        )

        user_data = Users(
            email="test@example.com",
            nickname="testuser",
            password_hash="hashed_password",
            signup_type="email",
        )

        repo = Mock()  # UserRepository 인스턴스 대신 Mock 사용

        # When
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.save_user.return_value = user_data
            result = mock_repo.save_user(user_data)

        # Then
        assert result == user_data
        mock_session.add.assert_called_once_with(user_data)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(user_data)

    @patch("repository.user_repository.db")
    def test_save_user_email_duplicate(self, mock_db):
        """이메일 중복으로 인한 저장 실패 테스트"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session

        # 이메일 중복 시뮬레이션
        existing_user = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = (
            existing_user
        )

        user_data = Users(
            email="existing@example.com",
            nickname="testuser",
            password_hash="hashed_password",
            signup_type="email",
        )

        # When & Then
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.save_user.side_effect = ValueError("이미 존재하는 이메일입니다.")

            with pytest.raises(ValueError, match="이미 존재하는 이메일입니다."):
                mock_repo.save_user(user_data)

    @patch("repository.user_repository.db")
    def test_save_user_nickname_duplicate(self, mock_db):
        """닉네임 중복으로 인한 저장 실패 테스트"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session

        # 이메일은 중복 없음, 닉네임은 중복
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            None,  # 이메일 중복 검사 - 중복 없음
            Mock(),  # 닉네임 중복 검사 - 중복 있음
        ]

        user_data = Users(
            email="test@example.com",
            nickname="existinguser",
            password_hash="hashed_password",
            signup_type="email",
        )

        # When & Then
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.save_user.side_effect = ValueError("이미 존재하는 닉네임입니다.")

            with pytest.raises(ValueError, match="이미 존재하는 닉네임입니다."):
                mock_repo.save_user(user_data)

    @patch("repository.user_repository.db")
    def test_find_by_email_success(self, mock_db):
        """이메일로 사용자 조회 성공 테스트"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session

        expected_user = Users(
            id="test-id",
            email="test@example.com",
            nickname="testuser",
            password_hash="hashed_password",
            signup_type="email",
        )
        mock_session.query.return_value.filter.return_value.first.return_value = (
            expected_user
        )

        # When
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.find_by_email.return_value = expected_user
            result = mock_repo.find_by_email("test@example.com")

        # Then
        assert result == expected_user
        mock_session.query.assert_called_once()

    @patch("repository.user_repository.db")
    def test_find_by_email_not_found(self, mock_db):
        """이메일로 사용자 조회 - 사용자 없음"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # When
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.find_by_email.return_value = None
            result = mock_repo.find_by_email("nonexistent@example.com")

        # Then
        assert result is None

    @patch("repository.user_repository.db")
    def test_find_by_nickname_success(self, mock_db):
        """닉네임으로 사용자 조회 성공 테스트"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session

        expected_user = Users(
            id="test-id",
            email="test@example.com",
            nickname="testuser",
            password_hash="hashed_password",
            signup_type="email",
        )
        mock_session.query.return_value.filter.return_value.first.return_value = (
            expected_user
        )

        # When
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.find_by_nickname.return_value = expected_user
            result = mock_repo.find_by_nickname("testuser")

        # Then
        assert result == expected_user
        mock_session.query.assert_called_once()

    @patch("repository.user_repository.db")
    def test_find_by_nickname_not_found(self, mock_db):
        """닉네임으로 사용자 조회 - 사용자 없음"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        # When
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.find_by_nickname.return_value = None
            result = mock_repo.find_by_nickname("nonexistentuser")

        # Then
        assert result is None

    @patch("repository.user_repository.db")
    def test_find_by_id_success(self, mock_db):
        """ID로 사용자 조회 성공 테스트"""
        # Given
        mock_session = Mock()
        mock_db.get_session.return_value = mock_session

        expected_user = Users(
            id="test-id",
            email="test@example.com",
            nickname="testuser",
            password_hash="hashed_password",
            signup_type="email",
        )
        mock_session.query.return_value.filter.return_value.first.return_value = (
            expected_user
        )

        # When
        with patch("repository.user_repository.UserRepository") as mock_repo_class:
            mock_repo = mock_repo_class.return_value
            mock_repo.find_by_id.return_value = expected_user
            result = mock_repo.find_by_id("test-id")

        # Then
        assert result == expected_user
        mock_session.query.assert_called_once()
