# 플레이북 07: 성능 최적화

> AI를 활용해 성능 병목을 찾고 최적화하는 단계별 가이드

## 언제 쓰나요?

- API 응답 시간이 느려졌을 때
- 메모리 사용량이 비정상적으로 높을 때
- 데이터베이스 쿼리가 점점 느려질 때
- 배포 후 성능이 떨어졌을 때

## 소요 시간

15-30분

## 사전 준비

- 프로파일링 도구 설치 (Chrome DevTools, `clinic.js`, `py-spy` 등)
- 성능 기준치(baseline) 측정값
- 재현 가능한 시나리오

## Step 1: 병목 지점 발견

성능 문제의 80%는 전체 코드의 20%에서 발생합니다. AI에게 프로파일링 결과를 넘기면 빠르게 핵심을 짚어줍니다.

```bash
# Node.js 프로파일링 결과를 Claude에게 분석 요청
node --prof app.js
node --prof-process isolate-*.log > profile.txt
claude "이 프로파일링 결과에서 가장 시간을 많이 쓰는 함수 Top 5와 최적화 방안을 알려줘" < profile.txt

# Python 프로파일링
py-spy record -o profile.svg -- python app.py
claude "이 코드의 성능 병목을 찾아줘. CPU 사용량이 높은 부분 위주로" < app.py
```

## Step 2: 쿼리 최적화

데이터베이스 쿼리는 가장 흔한 병목입니다. 느린 쿼리 로그를 AI에게 전달하세요.

```bash
claude "다음 PostgreSQL 쿼리를 최적화해줘.
현재 실행 시간: 3.2초
EXPLAIN ANALYZE 결과:

Seq Scan on orders  (cost=0.00..15420.00 rows=500000)
  Filter: (created_at > '2025-01-01')
  Rows Removed by Filter: 450000

테이블 크기: 500만 행
자주 사용하는 필터: created_at, status, user_id"
```

**AI가 제안하는 일반적인 최적화:**

| 문제 | 해결 방법 |
|------|----------|
| Full Table Scan | 인덱스 추가 (`CREATE INDEX idx_orders_created ON orders(created_at)`) |
| N+1 쿼리 | JOIN 또는 배치 쿼리로 전환 |
| 불필요한 컬럼 조회 | `SELECT *` → 필요한 컬럼만 지정 |
| 대량 데이터 반환 | 페이지네이션 또는 커서 기반 조회 |
| 복잡한 서브쿼리 | CTE 또는 임시 테이블 활용 |

## Step 3: 코드 레벨 최적화

```bash
claude "이 함수의 시간 복잡도를 분석하고 개선해줘.
현재 10만 건 처리에 38초 걸립니다.
목표: 5초 이내

$(cat src/services/processor.ts)"
```

**자주 발견되는 패턴:**

```typescript
// ❌ 배열 내부에서 반복 검색 — O(n²)
const results = items.map(item => {
  const match = allData.find(d => d.id === item.refId);
  return { ...item, data: match };
});

// ✅ Map으로 변환 후 조회 — O(n)
const dataMap = new Map(allData.map(d => [d.id, d]));
const results = items.map(item => ({
  ...item,
  data: dataMap.get(item.refId),
}));
```

```python
# ❌ 동기 루프에서 API 호출 — 순차 실행
results = []
for url in urls:
    resp = requests.get(url)
    results.append(resp.json())

# ✅ 비동기 병렬 처리 — 동시 실행
import asyncio, aiohttp

async def fetch_all(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [session.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]
```

## Step 4: 메모리 최적화

```bash
# 메모리 스냅샷을 Claude에게 전달
node --inspect app.js
# Chrome DevTools에서 힙 스냅샷 캡처 후

claude "메모리 사용량이 2GB까지 증가합니다.
의심 코드:

$(cat src/services/cache.ts)

1. 메모리 누수 가능성이 있는 부분을 찾아줘
2. 개선 방안을 코드와 함께 제시해줘"
```

**메모리 누수 흔한 원인:**

| 원인 | 증상 | 해결 |
|------|------|------|
| 이벤트 리스너 미해제 | 시간이 지날수록 메모리 증가 | `removeEventListener` 또는 `AbortController` 사용 |
| 전역 캐시 무제한 | 재시작 전까지 계속 증가 | LRU 캐시로 교체, TTL 설정 |
| 클로저가 큰 객체 참조 | 특정 함수 호출 후 메모리 유지 | 참조 해제 또는 WeakRef 사용 |
| 스트림 미종료 | 연결 수에 비례하여 증가 | `stream.destroy()` 보장 |

## Step 5: 결과 검증

최적화 후 반드시 전후 비교를 수행합니다.

```bash
claude "다음 벤치마크 결과를 분석해줘.

[Before]
- API 응답: 평균 3.2초, p95 8.1초
- 메모리: 1.8GB (피크)
- DB 쿼리: 평균 450ms

[After]
- API 응답: 평균 0.4초, p95 1.2초
- 메모리: 420MB (피크)
- DB 쿼리: 평균 12ms

개선율을 계산하고 추가로 개선할 부분이 있는지 알려줘"
```

## 체크리스트

- [ ] 프로파일링으로 실제 병목 확인 (추측으로 최적화하지 않기)
- [ ] 쿼리에 적절한 인덱스 설정
- [ ] N+1 쿼리 제거
- [ ] 불필요한 메모리 할당 정리
- [ ] 비동기 처리 가능한 부분 병렬화
- [ ] 최적화 전후 벤치마크 비교
- [ ] 기능 테스트 통과 확인 (최적화 후 동작 동일)

## 다음 단계

→ [AI 배포 플레이북](./08-deployment.md)

---

**더 자세한 가이드:** [claude-code/playbooks](../playbooks/)

**뉴스레터:** [maily.so/tenbuilder](https://maily.so/tenbuilder)
