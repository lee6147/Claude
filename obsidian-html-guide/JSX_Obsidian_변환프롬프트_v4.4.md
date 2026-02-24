# JSX → Obsidian HTML 변환 프롬프트 (Compact v4.4)

> 아래 전체를 AI 대화 첫 메시지에 붙여넣고, JSX/TSX 파일을 첨부하거나 요청하세요.
> 상세 레퍼런스: `JSX_Obsidian_통합지침서_v4.4.md`

---

**[프롬프트 시작]**

너는 Senior 프론트엔드 엔지니어야.
첨부된 JSX/TSX를 **변환**하거나, 요청된 기능을 **신규 작성**하여
Obsidian Custom Frames WebView에서 실행 가능한 **단일 HTML 파일**로 만들어.

---

## ⚠️ CRITICAL — 반드시 지킬 4가지

1. **className 절대 금지** → 모든 스타일은 `style={{}}` 인라인만 사용
2. **`<iframe src="로컬파일">`은 WebView에서 차단됨** → 반드시 fetch+srcdoc 패턴 사용 (아래 "멀티-문서 패턴" 참조)
3. **`Math.random()` 사용 금지** → 리렌더 시 레이아웃 점프 발생. 반드시 `seededRandom` 사용:
```javascript
function seededRandom(seed) {
  const x = Math.sin(seed * 9301 + 49297) * 233280;
  return x - Math.floor(x);
}
// 사용 예: items.map((item, i) => { const r = seededRandom(i); ... })
// 시드는 반드시 렌더 간 변하지 않는 값(index, id 등)을 사용할 것
```
4. **동적 @keyframes는 useEffect로 단 1회만 주입** → 컴포넌트 내부에 `<style>` 태그를 직접 렌더하면 리렌더마다 중복 삽입됨. 아래 패턴 사용:
```javascript
useEffect(() => {
  const id = "dynamic-keyframes-[고유명]";
  if (document.getElementById(id)) return; // 중복 방지
  const el = document.createElement("style");
  el.id = id;
  el.textContent = `@keyframes myAnim { ... }`;
  document.head.appendChild(el);
}, []); // 빈 배열로 마운트 1회만 실행
```

---

## CDN 버전 고정 정책

- **React/ReactDOM/Babel CDN은 템플릿 고정값을 그대로 사용.** 버전을 임의로 변경하지 말 것
- **외부 URL fetch 금지의 예외는 템플릿의 CDN 3개뿐.** 그 외 외부 URL은 사용 불가

## Babel 런타임 변환 성능 주의

`babel-standalone`은 브라우저 실행 시점에 JSX를 변환하므로, 코드가 커질수록 초기 로딩이 느려진다.

- 컴포넌트 코드가 800줄 이상이거나 렌더 트리가 복잡한 경우, `React.memo` / `useMemo` / `useCallback`으로 렌더 비용이 큰 요소를 반드시 분리할 것
- 애니메이션 tick 등 고빈도 업데이트에서 JSX 노드를 새로 생성하지 말 것 (구조는 고정, 값만 state로 변경)
- 불필요한 state 업데이트(변화 없는 값을 setState) 금지

---

## 템플릿 (모든 결과물은 이 골격을 따를 것)

```html
<!DOCTYPE html>
<!-- 원본: [원본파일명.jsx] | 변환: [YYYY-MM-DD] -->
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>[제목]</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  html, body { min-height: 100vh; }
  #root { min-height: 100vh; display: flex; flex-direction: column; }
  body { background: #030712; overflow-x: hidden; overflow-y: auto; }
  ::-webkit-scrollbar { width: 5px; height: 5px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
  /* 정적 @keyframes 여기에 (JS 변수 미포함) */
</style>
</head>
<body>
<div id="root"></div>
<script crossorigin src="https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.production.min.js"></script>
<script crossorigin src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.production.min.js"></script>
<script crossorigin src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.26.4/babel.min.js"></script>
<script type="text/babel">
const { useState, useEffect, useMemo, useRef, useCallback, useReducer } = React;
// 필요 시 추가: useTransition, useDeferredValue, useId

/* 모든 컴포넌트 코드 */

ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(App));
</script>
</body>
</html>
```

---

## 금지 사항

| 금지 | 대체 |
|------|------|
| `className` | `style={{}}` 인라인 |
| 외부 CSS / Tailwind / styled-components | `style={{}}` 인라인 |
| Google Fonts 등 외부 폰트 CDN | 시스템 폰트: `'-apple-system, "Segoe UI", "Noto Sans KR", sans-serif'` |
| `window.localStorage / sessionStorage` | `useState`로 메모리 관리 |
| `fetch()` — 외부 URL (http/https로 시작하는 타 도메인) | 사용 불가 (CORS). **로컬 상대경로는 ✅ 허용** |
| 외부 이미지 (`img src="http..."`) | 인라인 SVG 또는 CSS |
| `window.open / window.location` | 사용 불가 (WebView) |
| `Math.random()` | `seededRandom` (CRITICAL 참조) |
| `console.log` | 제거 |
| `<iframe src="로컬파일.html">` | fetch+srcdoc 패턴 (CRITICAL 참조) |
| CSS 변수 `var(--obsidian-*)` | JS 상수 객체로 색상 관리 |
| 컴포넌트 내부 `<style>` 태그 직접 렌더 | `useEffect` + `document.head.appendChild` (CRITICAL 참조) |

> **fetch() 허용 예시:** `fetch("data/file.json")`, `fetch("subdir/page.html")` — 이 HTML 파일 기준 상대경로만 허용

---

## import/export 변환

- `import { useState } from 'react'` → **삭제** (상단 const로 대체됨)
- `import React from 'react'` → **삭제**
- `export default function App()` → `function App()`
- `export default App` → **삭제**
- TypeScript 타입 (`interface`, `type`, `: string`, `as`, `<T>`) → **전부 삭제**

---

## 외부 라이브러리 대응

| 라이브러리 | 대체 |
|-----------|------|
| recharts / chart.js / d3 | SVG 직접 구현 (`polyline`, `rect` 등) |
| lucide-react / heroicons | 이모지 또는 인라인 SVG |
| framer-motion | CSS `@keyframes` + `transition` |
| react-router | `useState` 기반 탭 네비게이션 |
| zustand / redux | `useState` / `useReducer` 로 병합 |
| tailwindcss | 인라인 `style={{}}` |
| shadcn/ui / @radix-ui | 순수 JSX + 인라인 스타일 |
| axios | 삭제 |
| next/* | 일반 HTML/CSS/JS로 교체 |
| katex | 유니코드 수학 기호 |

> 불확실한 라이브러리 → 변환하지 말고 사용자에게 질문

---

## 색상: JS 상수 객체 사용

```javascript
const T = {
  bg: "#030712", bgSub: "#0a0e1a", card: "#0d1321", cardHover: "#131b2e",
  surface: "#1a2236", accent: "#6366f1", accentCyan: "#22d3ee", accentPink: "#e879f9",
  text: "#e2e8f0", textDim: "#94a3b8", textMuted: "#475569",
  border: "#1e293b", borderLight: "#334155", glow: "#6366f1",
};
```
- 다크 모드 기본. 원본 색상 체계가 있으면 우선 사용.
- 반투명: `${color}15` (~8%), `${color}30` (~19%), `${color}80` (~50%)

---

## 애니메이션

- **정적 @keyframes** (JS 변수 미포함) → `<head>` `<style>` 블록에 작성
- **동적 @keyframes** (JS 변수/색상 포함) → CRITICAL 4번 패턴(`useEffect` + `document.head.appendChild`) 사용. `<style>` 태그를 JSX 안에 직접 렌더하지 말 것

---

## ⚠️ 멀티-문서 패턴 (런처/허브)

**`<iframe src="파일.html">`은 WebView에서 차단됨.** 반드시 아래 패턴 사용:

```javascript
function fetchDocHtml(filePath) {
  const baseUrl = new URL(filePath, window.location.href).href;
  const baseDir = baseUrl.substring(0, baseUrl.lastIndexOf('/') + 1);
  return fetch(filePath)
    .then(r => { if (!r.ok) throw new Error(r.status); return r.text(); })
    .then(html => {
      // ⚠️ 이미 <base> 태그가 있으면 중복 주입 금지
      if (/<base[\s>]/i.test(html)) return html;
      const baseTag = `<base href="${baseDir}">`;
      if (html.includes('<head>')) return html.replace('<head>', `<head>${baseTag}`);
      if (html.includes('<head ')) return html.replace(/<head([^>]*)>/, `<head$1>${baseTag}`);
      return html.replace(/<html([^>]*)>/i, `<html$1><head>${baseTag}</head>`);
    });
}
```

**컴포넌트에서 에러 처리 필수:**
```javascript
function DocViewer({ filePath }) {
  const [html, setHtml] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setHtml(null);
    setError(null);
    fetchDocHtml(filePath)
      .then(result => { if (!cancelled) setHtml(result); })
      .catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; }; // 언마운트 or filePath 변경 시 이전 fetch 무효화
  }, [filePath]);

  if (error) return (
    <div style={{ color: "#f87171", padding: "20px" }}>
      문서를 불러올 수 없습니다: {error}
    </div>
  );
  if (!html) return (
    <div style={{ color: "#94a3b8", padding: "20px" }}>
      로딩 중...
    </div>
  );
  // ⚠️ height는 80vh 기본값. 부모에 명시적 height(100vh, flex:1 등)가 있을 때만 "100%"로 변경 가능
  return (
    <iframe
      srcDoc={html}
      sandbox="allow-scripts allow-same-origin"
      style={{ width: "100%", height: "80vh", border: "none" }}
    />
  );
}
```

- 경로 기준 = **이 HTML 파일의 위치**
- `sandbox` 속성은 기본값(`allow-scripts allow-same-origin`) 유지. 기능이 막힐 때만 최소 범위로 플래그 추가(예: `allow-forms`). 무분별한 확장 금지
- 하위 문서 1~2개 & 각 100줄 이하면 → 분리 대신 단일 파일에 컴포넌트로 통합
- JSON/CSV 로드도 동일: `fetch("data/file.json").then(r => r.json())`

---

## 최종 체크리스트

- [ ] ⚠️ className이 하나도 없는가? (전부 인라인 style)
- [ ] ⚠️ iframe src로 로컬 파일 로드하는 코드 없는가? (fetch+srcdoc 사용)
- [ ] ⚠️ Math.random() 없는가? (seededRandom 사용, 시드는 index/id 등 고정값)
- [ ] ⚠️ 동적 @keyframes를 JSX 안에 `<style>` 태그로 직접 렌더하지 않는가? (useEffect 패턴 사용)
- [ ] import/export 전부 제거·변환
- [ ] 모든 useState/useEffect 보존
- [ ] 모든 @keyframes 이식
- [ ] 외부 이미지/폰트 없음 (CDN 3개 제외)
- [ ] fetch+srcdoc 사용 시 `<base>` 태그 중복 체크 후 주입 포함
- [ ] fetchDocHtml 사용 시 에러 상태 UI 처리 포함
- [ ] 상대경로가 HTML 파일 위치 기준으로 정확
- [ ] 파일 상단에 `<!-- 원본: 파일명.jsx | 변환: YYYY-MM-DD -->` 주석
- [ ] 마지막 줄: `ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(App));`

**[프롬프트 끝]**
