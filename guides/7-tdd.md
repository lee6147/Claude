# 가이드 07: 테스트 주도 개발 (TDD)

> AI와 함께 테스트를 먼저 작성하고, 코드가 테스트를 통과하도록 구현하는 워크플로

## 핵심 원칙

> **TDD의 핵심:** 테스트 먼저 → 구현 → 리팩토링. 이 순서를 절대 바꾸지 마세요.

Claude Code로 TDD할 때 가장 흔한 실수:
- ❌ "이 기능 만들어줘" → AI가 테스트 없이 구현부터 작성
- ✅ "이 기능의 테스트를 먼저 작성해줘" → 테스트 기반 구현

## Step 1: 사용자 시나리오 정의

```bash
claude "검색 기능의 사용자 시나리오를 정의해줘.
형식: As a [역할], I want to [행동], so that [이유]
시나리오 3-5개만."
```

예시 출력:

```
1. 사용자가 키워드로 검색하면 관련 결과가 표시된다
2. 빈 검색어를 입력하면 에러 없이 빈 결과를 반환한다
3. 검색 결과가 없으면 "결과 없음" 메시지가 표시된다
```

## Step 2: 테스트 작성 (코드 작성 전)

```bash
claude "위 시나리오에 대한 테스트를 작성해줘.
- Jest/Vitest 사용
- 구현 코드는 작성하지 마
- 테스트만 먼저 작성"
```

```typescript
// search.test.ts
describe("Search", () => {
  it("returns relevant results for keyword", async () => {
    const results = await search("typescript");
    expect(results.length).toBeGreaterThan(0);
    expect(results[0].title).toContain("typescript");
  });

  it("returns empty array for empty query", async () => {
    const results = await search("");
    expect(results).toEqual([]);
  });

  it("returns empty with message for no matches", async () => {
    const results = await search("xyznonexistent");
    expect(results).toEqual([]);
  });
});
```

## Step 3: 테스트 실행 (실패 확인)

```bash
npm test
# ❌ FAIL — 아직 search() 함수가 없어서 실패해야 정상
```

> 테스트가 실패하는 것이 맞아요. 실패하지 않으면 테스트가 의미 없어요.

## Step 4: 최소 구현

```bash
claude "search.test.ts의 테스트를 통과하도록 search 함수를 구현해줘.
- 테스트를 통과하는 최소한의 코드만
- 과도한 최적화 금지"
```

## Step 5: 테스트 통과 확인

```bash
npm test
# ✅ PASS — 모든 테스트 통과
```

## Step 6: 리팩토링

```bash
claude "테스트가 통과하는 상태에서 search 함수를 리팩토링해줘.
- 테스트는 수정하지 마
- 중복 제거, 네이밍 개선만
- 리팩토링 후 테스트 재실행"
```

## 테스트 유형별 가이드

### 단위 테스트 (함수/컴포넌트)

```typescript
// 사용자가 보는 것을 테스트
expect(screen.getByText("Count: 5")).toBeInTheDocument();

// ❌ 내부 구현을 테스트하지 마세요
expect(component.state.count).toBe(5);
```

### API 통합 테스트

```typescript
describe("POST /api/orders", () => {
  it("creates order with valid data", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ items: [{ id: 1, qty: 2 }] });

    expect(res.status).toBe(201);
    expect(res.body.id).toBeDefined();
  });

  it("rejects invalid data", async () => {
    const res = await request(app)
      .post("/api/orders")
      .send({ items: [] });

    expect(res.status).toBe(400);
  });
});
```

### E2E 테스트 (Playwright)

```typescript
test("user can search products", async ({ page }) => {
  await page.goto("/");
  await page.fill('[placeholder="Search"]', "laptop");
  await page.waitForSelector('[data-testid="result-card"]');

  const results = page.locator('[data-testid="result-card"]');
  await expect(results.first()).toContainText("laptop");
});
```

## 커버리지 기준

| 레벨 | 목표 | 용도 |
|------|------|------|
| 단위 테스트 | 80%+ | 함수, 유틸리티, 컴포넌트 |
| 통합 테스트 | 주요 API 100% | 엔드포인트, DB 연동 |
| E2E | 핵심 플로우 | 회원가입, 결제, 검색 |

## 체크리스트

```
□ 테스트를 먼저 작성했는가
□ 테스트가 실패하는 것을 확인했는가
□ 최소한의 코드로 테스트를 통과시켰는가
□ 리팩토링 후 테스트가 여전히 통과하는가
□ 엣지 케이스 (빈 값, 에러, 경계값)를 테스트했는가
□ 각 테스트가 독립적인가 (순서 의존성 없음)
□ 커버리지 80% 이상 달성했는가
```

## 주의사항

- 테스트가 **구현 세부사항**이 아닌 **동작**을 검증하도록 작성해요
- `.css-class`보다 `[data-testid="..."]` 또는 `button:has-text()`를 사용해요
- 각 테스트는 독립적이어야 해요 — 이전 테스트 결과에 의존하면 안 돼요
- `--watch` 모드로 개발하면 파일 변경 시 테스트가 자동 실행돼요

---

📬 매주 AI 코딩 팁을 받아보세요 → [maily.so/tenbuilder](https://maily.so/tenbuilder)
