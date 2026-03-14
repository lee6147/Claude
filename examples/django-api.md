# CLAUDE.md 예시: Django REST API

> Django 5.x + DRF + PostgreSQL + Celery 기반 API 서버용 CLAUDE.md 템플릿

## 프로젝트 개요

```markdown
# CLAUDE.md

## Project
- Django 5.x + Django REST Framework
- PostgreSQL + Redis (cache/queue)
- Celery (비동기 작업)
- Python 3.12+
- Package Manager: uv (or pip)
```

## Python 컨벤션

```markdown
## Python Rules
- Type hints on all function signatures
- Docstrings: Google style
- Imports: isort (profile=black)
- Formatting: ruff format
- Linting: ruff check
- Max line length: 88

## Django Rules
- Fat models, thin views
- Business logic in services/ (not views)
- No raw SQL in views — use ORM or managers
- Always use select_related/prefetch_related for FK/M2M
```

### 서비스 레이어 패턴

```python
# apps/orders/services.py
from django.db import transaction
from .models import Order, OrderItem

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order(user, items: list[dict]) -> Order:
        """주문 생성 — 서비스 레이어에서 비즈니스 로직 처리"""
        order = Order.objects.create(
            user=user,
            status="pending",
        )

        order_items = [
            OrderItem(
                order=order,
                product_id=item["product_id"],
                quantity=item["quantity"],
                price=item["price"],
            )
            for item in items
        ]
        OrderItem.objects.bulk_create(order_items)

        order.total = sum(i.price * i.quantity for i in order_items)
        order.save(update_fields=["total"])

        return order
```

> **핵심 패턴:** View → Service → Model. 비즈니스 로직은 Service에 집중해요.

### Serializer 패턴

```python
# apps/orders/serializers.py
from rest_framework import serializers

class OrderCreateSerializer(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.DictField(), min_length=1
    )

    def validate_items(self, value):
        for item in value:
            if item.get("quantity", 0) < 1:
                raise serializers.ValidationError(
                    "Quantity must be at least 1"
                )
        return value
```

### N+1 방지

```python
# ❌ N+1 쿼리 발생
orders = Order.objects.all()
for order in orders:
    print(order.user.email)  # 매번 DB 호출

# ✅ select_related로 JOIN
orders = Order.objects.select_related("user").all()

# ✅ prefetch_related (M2M)
orders = Order.objects.prefetch_related("items__product").all()
```

## 디렉토리 구조

```markdown
## File Structure
project/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── local.py
│   │   └── production.py
│   ├── urls.py
│   └── celery.py
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── services.py      # Business logic
│   │   ├── tests/
│   │   │   ├── test_models.py
│   │   │   ├── test_views.py
│   │   │   └── factories.py  # Factory Boy
│   │   └── urls.py
│   └── orders/
├── common/
│   ├── models.py             # TimeStampedModel
│   ├── permissions.py
│   └── pagination.py
└── requirements/
    ├── base.txt
    ├── local.txt
    └── production.txt
```

## 테스트 패턴

```python
# apps/orders/tests/factories.py
import factory
from apps.users.tests.factories import UserFactory

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "orders.Order"

    user = factory.SubFactory(UserFactory)
    status = "pending"
    total = factory.Faker("pydecimal", left_digits=4, right_digits=2)

# apps/orders/tests/test_views.py
from rest_framework.test import APITestCase

class OrderViewTest(APITestCase):
    def setUp(self):
        self.user = UserFactory()
        self.client.force_authenticate(self.user)

    def test_create_order(self):
        data = {"items": [{"product_id": 1, "quantity": 2, "price": "10.00"}]}
        response = self.client.post("/api/v1/orders/", data, format="json")
        self.assertEqual(response.status_code, 201)
```

## 명령어

```markdown
## Commands
- `python manage.py runserver` — dev server
- `python manage.py test` — run tests
- `python manage.py test --parallel` — parallel tests
- `celery -A config worker -l info` — Celery worker
- `ruff check .` — linting
- `ruff format .` — formatting
```

## 실전 팁

| 상황 | 패턴 |
|------|------|
| 인증 | JWT (`djangorestframework-simplejwt`) |
| 권한 | `IsAuthenticated` + 커스텀 Permission 클래스 |
| 페이지네이션 | `CursorPagination` (대용량) 또는 `PageNumberPagination` |
| 비동기 작업 | Celery task + `@shared_task` 데코레이터 |
| 캐싱 | `django.core.cache` + Redis backend |
| 마이그레이션 | `makemigrations` → 리뷰 → `migrate` (수동 SQL 금지) |

---

📬 매주 AI 코딩 팁을 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
