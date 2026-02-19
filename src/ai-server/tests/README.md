# User API 테스트 가이드

## 테스트 구조

```
tests/
├── __init__.py
├── conftest.py              # pytest 설정 및 공통 fixture
├── test_user_api.py         # User API 엔드포인트 테스트
├── test_user_service.py     # UserService 테스트
├── test_user_repository.py  # UserRepository 테스트
└── README.md               # 이 파일
```

## 테스트 실행 방법

### 1. 필요한 패키지 설치
```bash
# pytest와 관련 패키지 설치
poetry add pytest pytest-asyncio httpx --group dev
```

### 2. 테스트 실행
```bash
# 모든 테스트 실행
cd src/app-server
pytest tests/ -v

# 특정 테스트 파일 실행
pytest tests/test_user_api.py -v

# 특정 테스트 클래스 실행
pytest tests/test_user_api.py::TestUserSignupAPI -v

# 특정 테스트 메서드 실행
pytest tests/test_user_api.py::TestUserSignupAPI::test_signup_success -v
```

### 3. 테스트 커버리지 확인
```bash
# 커버리지 패키지 설치
poetry add pytest-cov --group dev

# 커버리지와 함께 테스트 실행
pytest tests/ --cov=service --cov=repository --cov=api --cov-report=html
```

## 테스트 종류

### 1. API 테스트 (`test_user_api.py`)
- **회원가입 API** (`/api/signup`)
  - 성공 케이스
  - 검증 에러 케이스
  - 시스템 에러 케이스

- **이메일 중복 검사 API** (`/api/check-email`)
  - 중복인 경우
  - 중복이 아닌 경우
  - 에러 케이스

- **닉네임 중복 검사 API** (`/api/check-nickname`)
  - 중복인 경우
  - 중복이 아닌 경우
  - 에러 케이스

### 2. 서비스 테스트 (`test_user_service.py`)
- **회원가입 로직**
  - 성공 케이스
  - 빈 비밀번호 검증
  - 공백 비밀번호 검증
  - 리포지토리 에러 처리

- **중복 검사 로직**
  - 이메일 중복 검사 (중복/비중복)
  - 닉네임 중복 검사 (중복/비중복)
  - 에러 처리

- **비밀번호 해싱**
  - bcrypt 해싱 테스트
  - 비밀번호 검증 테스트

### 3. 리포지토리 테스트 (`test_user_repository.py`)
- **사용자 저장**
  - 성공 케이스
  - 이메일 중복 에러
  - 닉네임 중복 에러

- **사용자 조회**
  - 이메일로 조회 (성공/실패)
  - 닉네임으로 조회 (성공/실패)
  - ID로 조회

## Mock 사용법

### 1. 의존성 주입 Mock
```python
@pytest.fixture
def mock_user_service():
    with patch('api.user_api.get_user_service') as mock:
        service = Mock()
        mock.return_value = service
        yield service
```

### 2. 데이터베이스 Mock
```python
@patch('repository.user_repository.db')
def test_save_user_success(self, mock_db):
    mock_session = Mock()
    mock_db.get_session.return_value = mock_session
    # 테스트 로직...
```

### 3. 서비스 Mock
```python
def test_signup_success(self, client, mock_user_service):
    mock_user_service.signup.return_value = expected_user
    response = client.post("/api/signup", json=user_data)
    # 검증...
```

## 테스트 데이터

### 1. 공통 Fixture
```python
@pytest.fixture
def sample_user_data():
    return {
        "email": "test@example.com",
        "nickname": "testuser",
        "password": "testpassword123",
        "signup_type": "email",
        "sns_provider": None,
        "sns_id": None
    }
```

### 2. Users 모델 Fixture
```python
@pytest.fixture
def sample_user():
    return Users(
        id="test-user-id",
        email="test@example.com",
        nickname="testuser",
        password_hash="hashed_password",
        signup_type="email"
    )
```

## 테스트 실행 시 주의사항

1. **환경 변수**: 테스트 실행 전 필요한 환경 변수가 설정되어 있는지 확인
2. **데이터베이스**: 테스트용 데이터베이스 사용 권장
3. **Mock 사용**: 실제 데이터베이스 연결 없이 테스트 가능
4. **격리**: 각 테스트는 독립적으로 실행되어야 함

## 테스트 결과 해석

### 성공 케이스
- HTTP 상태 코드: 200
- 응답 구조: `SuccessResponse` 형태
- 데이터 검증: 예상된 필드 값 확인

### 에러 케이스
- HTTP 상태 코드: 500 (현재 구현)
- 응답 구조: `ErrorResponse` 형태
- 에러 메시지: 적절한 에러 메시지 확인

## 추가 테스트 케이스 제안

1. **입력 검증 테스트**
   - 이메일 형식 검증
   - 비밀번호 길이 검증
   - 닉네임 길이 검증

2. **보안 테스트**
   - SQL 인젝션 방지
   - XSS 방지
   - 비밀번호 강도 검증

3. **성능 테스트**
   - 대량 사용자 처리
   - 동시 요청 처리

4. **통합 테스트**
   - 실제 데이터베이스 연결
   - 전체 플로우 테스트 