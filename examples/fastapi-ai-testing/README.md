# FastAPI + AI 테스팅 실전 예제

> AI로 FastAPI 테스트를 자동 생성하고 커버리지를 높이는 단계별 가이드

## 이 예제에서 배울 수 있는 것

- FastAPI 프로젝트에서 Claude Code로 테스트를 자동 생성하는 방법
- pytest + httpx로 비동기 API 테스트를 작성하는 패턴
- CLAUDE.md 설정으로 테스트 품질을 높이는 실전 팁

## 프로젝트 구조

```
fastapi-ai-testing/
├── CLAUDE.md              # Claude Code 프로젝트 설정
├── app/
│   ├── main.py            # FastAPI 앱 진입점
│   ├── models.py          # Pydantic 모델
│   ├── database.py        # DB 연결 설정
│   └── routers/
│       ├── users.py       # 사용자 API
│       └── posts.py       # 게시글 API
├── tests/
│   ├── conftest.py        # 테스트 픽스처
│   ├── test_users.py      # 사용자 API 테스트
│   └── test_posts.py      # 게시글 API 테스트
├── pyproject.toml
└── requirements.txt
```

## 시작하기

### Step 1: 프로젝트 셋업

```bash
mkdir fastapi-ai-testing && cd fastapi-ai-testing
python -m venv .venv && source .venv/bin/activate

pip install fastapi uvicorn sqlalchemy pydantic
pip install pytest pytest-asyncio httpx  # 테스트 도구
```

### Step 2: CLAUDE.md 작성

프로젝트 루트에 `CLAUDE.md`를 만들어서 테스트 생성 규칙을 명확하게 잡아요.

```markdown
# CLAUDE.md

## Project
- FastAPI 0.115+ / Python 3.12
- SQLAlchemy 2.0 (async)
- Pydantic v2

## Testing Rules
- pytest + pytest-asyncio + httpx 사용
- 모든 테스트는 async def로 작성
- httpx.AsyncClient로 API 호출
- conftest.py에 공통 픽스처 정의
- 각 테스트는 독립적으로 실행 가능해야 함
- 엣지케이스(빈 값, 중복, 권한 없음) 반드시 포함
```

이렇게 규칙을 정해두면 Claude Code가 일관된 스타일로 테스트를 만들어요.

### Step 3: FastAPI 앱 작성

```python
# app/models.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    name: str
    email: EmailStr

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr

class PostCreate(BaseModel):
    title: str
    content: str
    author_id: int

class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author_id: int
```

```python
# app/main.py
from fastapi import FastAPI, HTTPException
from app.models import UserCreate, UserResponse, PostCreate, PostResponse

app = FastAPI(title="AI Testing Demo")

# 인메모리 저장소 (예제용)
users_db: dict[int, dict] = {}
posts_db: dict[int, dict] = {}
next_user_id = 1
next_post_id = 1

@app.post("/users", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate):
    global next_user_id
    # 이메일 중복 체크
    for u in users_db.values():
        if u["email"] == user.email:
            raise HTTPException(status_code=409, detail="Email already exists")
    user_data = {"id": next_user_id, **user.model_dump()}
    users_db[next_user_id] = user_data
    next_user_id += 1
    return user_data

@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int):
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    return users_db[user_id]

@app.post("/posts", response_model=PostResponse, status_code=201)
def create_post(post: PostCreate):
    global next_post_id
    if post.author_id not in users_db:
        raise HTTPException(status_code=404, detail="Author not found")
    post_data = {"id": next_post_id, **post.model_dump()}
    posts_db[next_post_id] = post_data
    next_post_id += 1
    return post_data

@app.get("/posts", response_model=list[PostResponse])
def list_posts(author_id: int | None = None):
    if author_id:
        return [p for p in posts_db.values() if p["author_id"] == author_id]
    return list(posts_db.values())
```

## 핵심 코드: 테스트 작성

### conftest.py — 공통 픽스처

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app, users_db, posts_db

@pytest.fixture(autouse=True)
def reset_db():
    """각 테스트 전에 DB를 초기화해요."""
    import app.main as m
    users_db.clear()
    posts_db.clear()
    m.next_user_id = 1
    m.next_post_id = 1
    yield

@pytest.fixture
async def client():
    """비동기 테스트 클라이언트를 만들어요."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def sample_user(client: AsyncClient):
    """테스트용 사용자를 미리 생성해요."""
    response = await client.post("/users", json={
        "name": "테스트유저",
        "email": "test@example.com"
    })
    return response.json()
```

**왜 이렇게 했나요?**

`autouse=True`로 DB를 매번 초기화하면 테스트 간 의존성이 사라져요. `sample_user` 픽스처를 따로 만들면 게시글 테스트에서 사용자 생성 코드를 반복하지 않아도 돼요.

### test_users.py — 사용자 API 테스트

```python
# tests/test_users.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(mode="auto")

async def test_create_user(client: AsyncClient):
    """사용자 생성이 정상 동작하는지 확인해요."""
    response = await client.post("/users", json={
        "name": "홍길동",
        "email": "hong@example.com"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "홍길동"
    assert data["email"] == "hong@example.com"
    assert "id" in data

async def test_create_user_duplicate_email(client: AsyncClient, sample_user):
    """이메일 중복 시 409를 반환하는지 확인해요."""
    response = await client.post("/users", json={
        "name": "다른사람",
        "email": "test@example.com"  # sample_user와 같은 이메일
    })
    assert response.status_code == 409

async def test_get_user_not_found(client: AsyncClient):
    """존재하지 않는 사용자 조회 시 404를 반환하는지 확인해요."""
    response = await client.get("/users/999")
    assert response.status_code == 404

async def test_create_user_invalid_email(client: AsyncClient):
    """잘못된 이메일 형식 시 422를 반환하는지 확인해요."""
    response = await client.post("/users", json={
        "name": "홍길동",
        "email": "not-an-email"
    })
    assert response.status_code == 422
```

### test_posts.py — 게시글 API 테스트

```python
# tests/test_posts.py
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio(mode="auto")

async def test_create_post(client: AsyncClient, sample_user):
    """게시글 생성이 정상 동작하는지 확인해요."""
    response = await client.post("/posts", json={
        "title": "첫 번째 글",
        "content": "AI로 테스트 자동 생성하기",
        "author_id": sample_user["id"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "첫 번째 글"
    assert data["author_id"] == sample_user["id"]

async def test_create_post_invalid_author(client: AsyncClient):
    """존재하지 않는 작성자로 게시글 생성 시 404를 반환하는지 확인해요."""
    response = await client.post("/posts", json={
        "title": "실패할 글",
        "content": "작성자가 없어요",
        "author_id": 999
    })
    assert response.status_code == 404

async def test_list_posts_filter_by_author(client: AsyncClient, sample_user):
    """작성자별 게시글 필터링이 동작하는지 확인해요."""
    # 게시글 2개 생성
    await client.post("/posts", json={
        "title": "글 A", "content": "내용 A", "author_id": sample_user["id"]
    })
    await client.post("/posts", json={
        "title": "글 B", "content": "내용 B", "author_id": sample_user["id"]
    })

    # 필터링 조회
    response = await client.get(f"/posts?author_id={sample_user['id']}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

async def test_list_posts_empty(client: AsyncClient):
    """게시글이 없을 때 빈 리스트를 반환하는지 확인해요."""
    response = await client.get("/posts")
    assert response.status_code == 200
    assert response.json() == []
```

## AI 활용 포인트

| 상황 | 프롬프트 예시 |
|------|-------------|
| 테스트 자동 생성 | `이 API 라우터의 테스트를 만들어줘. 정상 케이스 + 엣지케이스 포함` |
| 커버리지 올리기 | `coverage report 보고 빠진 브랜치에 대한 테스트 추가해줘` |
| 픽스처 정리 | `conftest.py에 공통 픽스처 정리해줘. 중복 제거하고` |
| 에러 시나리오 | `이 엔드포인트에서 발생할 수 있는 에러 케이스 전부 테스트해줘` |
| 성능 테스트 | `이 API에 대한 부하 테스트 코드 만들어줘. locust 사용` |

## 실행하기

```bash
# 테스트 실행
pytest tests/ -v

# 커버리지 리포트
pytest tests/ --cov=app --cov-report=term-missing

# 특정 테스트만 실행
pytest tests/test_users.py -v -k "duplicate"
```

## 자주 하는 실수 & 해결

| 실수 | 해결 |
|------|------|
| `async def` 빼먹음 | `pytestmark = pytest.mark.asyncio(mode="auto")` 파일 상단에 추가 |
| DB 상태가 테스트 간 공유됨 | `autouse=True` 픽스처로 매 테스트 전 초기화 |
| `httpx.AsyncClient` import 에러 | `pip install httpx` 확인. `requests`가 아닌 `httpx` 사용 |
| 422 에러인데 원인 모름 | `response.json()["detail"]`로 Pydantic 검증 에러 확인 |
| 픽스처 순서 문제 | `conftest.py`에 정의하면 자동으로 모든 테스트에서 사용 가능 |

---

**더 자세한 가이드:** [claude-code/playbooks](../claude-code/playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
