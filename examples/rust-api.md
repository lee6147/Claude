# CLAUDE.md 예시: Rust API

> Rust + Axum + SQLx + PostgreSQL 기반 API 서버용 CLAUDE.md 템플릿

## 프로젝트 개요

```markdown
# CLAUDE.md

## Project
- Rust (latest stable)
- Axum (web framework)
- SQLx (async, compile-time checked SQL)
- PostgreSQL
- tokio (async runtime)
- Tower (middleware)
```

## Rust 컨벤션

```markdown
## Rust Rules
- Use `thiserror` for library errors, `anyhow` for application errors
- Prefer compile-time checks (SQLx query macros)
- No unwrap() in production code — use ? or proper error handling
- Clippy warnings = errors in CI
- Format with rustfmt
```

### 에러 처리 패턴

```rust
// src/error.rs
use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("not found: {0}")]
    NotFound(String),

    #[error("validation error: {0}")]
    Validation(String),

    #[error("unauthorized")]
    Unauthorized,

    #[error(transparent)]
    Database(#[from] sqlx::Error),

    #[error(transparent)]
    Internal(#[from] anyhow::Error),
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let status = match &self {
            AppError::NotFound(_) => StatusCode::NOT_FOUND,
            AppError::Validation(_) => StatusCode::BAD_REQUEST,
            AppError::Unauthorized => StatusCode::UNAUTHORIZED,
            _ => StatusCode::INTERNAL_SERVER_ERROR,
        };

        (status, self.to_string()).into_response()
    }
}
```

> **핵심 패턴:** `thiserror`로 에러 타입 정의 → `IntoResponse`로 HTTP 응답 변환

### 핸들러 → 서비스 → 리포지토리

```rust
// src/handler/order.rs
async fn get_order(
    State(state): State<AppState>,
    Path(id): Path<Uuid>,
) -> Result<Json<OrderResponse>, AppError> {
    let order = state.order_service
        .find_by_id(id)
        .await?;

    Ok(Json(OrderResponse::from(order)))
}

// src/service/order.rs
impl OrderService {
    pub async fn find_by_id(&self, id: Uuid) -> Result<Order, AppError> {
        self.repo.find_by_id(id).await?
            .ok_or_else(|| AppError::NotFound(format!("order {id}")))
    }
}

// src/repository/order.rs
impl OrderRepository {
    pub async fn find_by_id(&self, id: Uuid) -> Result<Option<Order>, sqlx::Error> {
        sqlx::query_as!(
            Order,
            "SELECT id, user_id, status, total, created_at FROM orders WHERE id = $1",
            id
        )
        .fetch_optional(&self.pool)
        .await
    }
}
```

> `sqlx::query_as!`는 컴파일 타임에 SQL을 검증해요. 런타임 에러가 줄어요.

## 디렉토리 구조

```markdown
## File Structure
src/
├── main.rs               # 진입점 + router 설정
├── config.rs             # 환경변수 로딩
├── error.rs              # AppError 정의
├── handler/
│   ├── mod.rs
│   ├── order.rs
│   └── health.rs
├── service/
│   ├── mod.rs
│   └── order.rs
├── repository/
│   ├── mod.rs
│   └── order.rs
├── model/
│   ├── mod.rs
│   └── order.rs          # DB 모델 + Response DTO
└── middleware/
    ├── mod.rs
    └── auth.rs

migrations/               # SQLx 마이그레이션
tests/
└── integration/          # 통합 테스트
    └── order_test.rs
```

## 테스트 패턴

```rust
// tests/integration/order_test.rs
#[tokio::test]
async fn test_create_order() {
    let app = spawn_test_app().await;

    let response = app.client
        .post(&format!("{}/api/orders", app.address))
        .json(&json!({
            "items": [{"product_id": 1, "quantity": 2}]
        }))
        .header("Authorization", format!("Bearer {}", app.token))
        .send()
        .await
        .expect("Failed to execute request");

    assert_eq!(response.status(), 201);

    let order: OrderResponse = response.json().await.unwrap();
    assert_eq!(order.status, "pending");
}

// 테스트 헬퍼 — 격리된 DB + 서버 인스턴스
async fn spawn_test_app() -> TestApp {
    let db = create_test_database().await;
    let app = build_app(db.pool.clone()).await;
    // ...
}
```

## 명령어

```markdown
## Commands
- `cargo run` — dev server
- `cargo test` — all tests
- `cargo clippy -- -D warnings` — lint (warnings = errors)
- `cargo fmt --check` — format check
- `sqlx migrate run` — apply migrations
- `cargo sqlx prepare` — offline mode preparation (CI용)
```

## 실전 팁

| 상황 | 패턴 |
|------|------|
| 상태 공유 | `State<AppState>` (Arc 내부) |
| 미들웨어 | Tower Layer + Service |
| 인증 | extractor 패턴 (`FromRequestParts`) |
| 직렬화 | `serde` Serialize/Deserialize |
| 환경 설정 | `dotenvy` + `config` crate |
| CI SQL 체크 | `cargo sqlx prepare` → `.sqlx/` 디렉토리 커밋 |

---

📬 매주 AI 코딩 팁을 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
