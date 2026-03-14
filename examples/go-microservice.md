# CLAUDE.md 예시: Go Microservice

> Go 1.22+ gRPC + sqlc + Wire 기반 마이크로서비스용 CLAUDE.md 템플릿

## 프로젝트 개요

```markdown
# CLAUDE.md

## Project
- Go 1.22+
- gRPC + Connect (HTTP API)
- sqlc (type-safe SQL)
- Wire (DI)
- PostgreSQL
- Docker + Kubernetes
```

## Go 컨벤션

```markdown
## Go Rules
- Follow Effective Go and Go Proverbs
- Accept interfaces, return structs
- Errors are values — handle every error
- No init() functions
- Table-driven tests
- `gofmt` + `golangci-lint`
```

### 에러 처리 패턴

```go
// internal/service/order.go
package service

import (
    "context"
    "fmt"
)

// Sentinel errors — 패키지 레벨에 정의
var (
    ErrOrderNotFound = fmt.Errorf("order not found")
    ErrInvalidInput  = fmt.Errorf("invalid input")
)

func (s *OrderService) GetOrder(ctx context.Context, id string) (*Order, error) {
    order, err := s.repo.FindByID(ctx, id)
    if err != nil {
        // %w로 에러를 감싸서 체이닝
        return nil, fmt.Errorf("get order %s: %w", id, err)
    }
    if order == nil {
        return nil, ErrOrderNotFound
    }
    return order, nil
}
```

> **핵심 패턴:** Sentinel error 정의 → `%w`로 감싸기 → `errors.Is()`로 체크

### 클린 아키텍처 레이어

```go
// Handler → Service → Repository (의존성 방향: 안쪽으로만)

// internal/handler/order.go — HTTP/gRPC 입구
type OrderHandler struct {
    svc *service.OrderService
}

// internal/service/order.go — 비즈니스 로직
type OrderService struct {
    repo OrderRepository  // 인터페이스에 의존
}

// internal/repository/order.go — 데이터 접근
type OrderRepository interface {
    FindByID(ctx context.Context, id string) (*Order, error)
    Create(ctx context.Context, order *Order) error
}
```

### sqlc 쿼리 패턴

```sql
-- query/order.sql
-- name: GetOrder :one
SELECT id, user_id, status, total, created_at
FROM orders
WHERE id = $1;

-- name: CreateOrder :one
INSERT INTO orders (user_id, status, total)
VALUES ($1, $2, $3)
RETURNING *;

-- name: ListOrdersByUser :many
SELECT id, user_id, status, total, created_at
FROM orders
WHERE user_id = $1
ORDER BY created_at DESC
LIMIT $2 OFFSET $3;
```

> sqlc가 타입 안전한 Go 코드를 자동 생성해요. 직접 SQL을 문자열로 작성하지 마세요.

## 디렉토리 구조

```markdown
## File Structure
.
├── cmd/
│   └── server/
│       └── main.go           # 진입점
├── internal/
│   ├── handler/              # HTTP/gRPC 핸들러
│   ├── service/              # 비즈니스 로직
│   ├── repository/           # DB 접근 (sqlc 생성 코드)
│   ├── model/                # 도메인 모델
│   └── config/               # 설정 로딩
├── proto/                    # Protobuf 정의
├── query/                    # sqlc SQL 파일
├── migrations/               # DB 마이그레이션
├── docker-compose.yaml
├── sqlc.yaml
├── buf.yaml                  # Protobuf 관리
└── wire.go                   # DI 설정
```

## 테스트 패턴

```go
// internal/service/order_test.go
func TestOrderService_GetOrder(t *testing.T) {
    tests := []struct {
        name    string
        id      string
        want    *Order
        wantErr error
    }{
        {
            name: "found",
            id:   "order-1",
            want: &Order{ID: "order-1", Status: "pending"},
        },
        {
            name:    "not found",
            id:      "nonexistent",
            wantErr: ErrOrderNotFound,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            svc := NewOrderService(newMockRepo())
            got, err := svc.GetOrder(context.Background(), tt.id)

            if tt.wantErr != nil {
                assert.ErrorIs(t, err, tt.wantErr)
                return
            }
            assert.NoError(t, err)
            assert.Equal(t, tt.want.ID, got.ID)
        })
    }
}
```

> **Table-driven tests:** Go의 표준 테스트 패턴이에요. 케이스 추가가 간편해요.

## 명령어

```markdown
## Commands
- `go run cmd/server/main.go` — dev server
- `go test ./...` — all tests
- `go test -race ./...` — race condition 검사
- `golangci-lint run` — linting
- `sqlc generate` — SQL → Go 코드 생성
- `buf generate` — Proto → Go 코드 생성
- `wire ./...` — DI 코드 생성
```

## 실전 팁

| 상황 | 패턴 |
|------|------|
| DI | Wire로 컴파일 타임 의존성 주입 |
| 에러 전파 | `fmt.Errorf("context: %w", err)` |
| Context | 항상 첫 번째 파라미터로 전달 |
| 로깅 | `slog` (Go 1.21+ 표준 라이브러리) |
| 설정 | 환경변수 → `envconfig` 또는 `viper` |
| 헬스체크 | `/healthz` 엔드포인트 + readiness/liveness probe |

---

📬 매주 AI 코딩 팁을 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
