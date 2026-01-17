# Social Backend API

"클라우드 커뮤니티" 서비스의 백엔드 API 서버를 구현합니다.

지난주에 각자 작성한 **REST API Docs**를 기반으로 실제 동작하는 서버를 개발합니다.

수행 방법에 대한 상세는 노션 페이지 [4주차 과제](https://www.notion.so/ej31/4-2e3954dac75580e9a969e082171fbd59) 에서 확인해주세요!

## 개발 환경 설정

### 1. 의존성 설치

```bash
  uv sync
```

### 2. 환경변수 설정

`.env` 파일 생성:

```bash
  SECRET_KEY=your-secret-key-here
  PASSWORD_PEPPER=your-pepper-key-here
```

키 생성 방법:
```bash
  python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. 테스트 데이터 생성

```bash
  python scripts/seed.py
```

### 4. 서버 실행

```bash
  fastapi dev main.py
```

Swagger UI: <http://127.0.0.1:8000/docs>

## 테스트 계정

| email | password | 설명 |
|-------|----------|------|
| test@example.com | Test1234! | 기본 테스트 계정 |
| test2@example.com | Test1234! | 보조 테스트 계정 |

> 테스트 계정은 `python scripts/seed.py` 실행 후 사용 가능합니다.
