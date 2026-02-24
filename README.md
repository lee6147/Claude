# Obsidian HTML Viewer

Obsidian에서 React 기반 인터랙티브 HTML 가이드를 열어볼 수 있는 환경입니다.

---

## 구조

```
obsidian-html-guide/
├── html/                          # HTML 가이드 파일
│   └── lib/                       # React/Babel CDN 로컬 캐시
├── JSX_Obsidian_변환프롬프트_v4.4.md  # JSX→HTML 변환 프롬프트
├── CLAUDE.md                      # Claude Code 지시사항
└── README.md
```

---

## 핵심 플러그인

| 플러그인 | 역할 | 필수 여부 |
|---------|------|----------|
| **obsidian-html-plugin** (HTML Reader) | `.html` 파일을 파일 탐색기에서 인식 | 필수 |
| **obsidian-custom-frames** | `file:///` 경로로 HTML을 WebView 렌더링 | 필수 |

> React CDN 기반 HTML은 HTML Reader만으로 렌더링되지 않습니다. **Custom Frames에 등록해야** 정상적으로 열립니다.

### 왜 Custom Frames가 필요한가?

HTML Reader 플러그인은 보안상 **모든 JavaScript를 차단**합니다. React/Babel 기반 HTML은 JS가 화면을 그리는 구조이므로, HTML Reader로 열면 **빈 화면**만 나옵니다.

| | 파일 탐색기 (HTML Reader) | Custom Frames (리본) |
|---|---|---|
| 열리는 방식 | 플러그인이 HTML 파싱 | 내장 브라우저(WebView) |
| JavaScript | **차단됨** | **정상 실행** |
| React 앱 | 빈 화면 | 정상 작동 |
| 클릭/애니메이션 | 안 됨 | 됨 |
| 접근 방법 | 파일 탐색기에서 클릭 | 리본 아이콘 또는 `Ctrl+P` |

---

## 동작 원리

- Custom Frames의 `forceIframe: false` 설정으로 **Electron WebView**를 사용
- `file:///` 절대경로로 로컬 HTML 파일을 직접 로드
- WebView이므로 React/Babel CDN 스크립트 실행 가능
- **별도 서버 불필요** (localhost 서버 없이 동작)

---

## 시작하기

### 1. 커뮤니티 플러그인 설치

1. **설정** > **커뮤니티 플러그인** > **제한 모드 해제** > **찾아보기**
2. `HTML Reader`, `Custom Frames` 두 개 모두 설치 및 활성화

### 2. HTML 파일 열기

Custom Frames에 등록된 파일은 리본(좌측 사이드바) 아이콘을 클릭하거나, `Ctrl + P` 명령어 팔레트에서 검색하여 열 수 있습니다.

---

## Custom Frames에 새 HTML 등록하기

HTML 파일을 새로 만들면 **반드시 Custom Frames에 등록**해야 Obsidian에서 열 수 있습니다.

`.obsidian/plugins/obsidian-custom-frames/data.json`의 `frames` 배열에 추가:

```json
{
    "url": "file:///C:/Users/user/obsidian-html-guide/html/파일명.html",
    "displayName": "표시 이름",
    "icon": "아이콘명",
    "hideOnMobile": true,
    "addRibbonIcon": true,
    "openInCenter": true,
    "zoomLevel": 1,
    "forceIframe": false,
    "customCss": "body { overflow-x: hidden; }",
    "customJs": ""
}
```

등록 후 **Obsidian 재시작** 필요.

> 한글 파일명은 URL 인코딩 필요: `센터` → `%EC%84%BC%ED%84%B0`

---

## HTML 가이드 만들기

JSX/TSX 파일을 Obsidian에서 실행 가능한 단일 HTML로 변환할 수 있습니다.
AI에게 [`JSX_Obsidian_변환프롬프트_v4.4.md`](./JSX_Obsidian_변환프롬프트_v4.4.md)를 붙여넣고 JSX 파일을 주면 자동으로 변환해줍니다.

---

## 트러블슈팅

### 빈 페이지가 뜨는 경우

**1단계: 실제 열린 볼트 확인**

Obsidian 볼트가 여러 개일 때, 엉뚱한 볼트의 `data.json`을 수정하는 실수가 흔합니다. 실제로 열린 볼트를 확인하려면:

```
%AppData%\obsidian\obsidian.json
```

```json
{
  "vaults": {
    "94c91c9f3ae756e0": {
      "path": "C:\\Users\\user\\Desktop\\Claud\\Obsidian",
      "open": true   // ← 이 볼트가 실제로 열림
    }
  }
}
```

해당 볼트의 `.obsidian/plugins/obsidian-custom-frames/data.json` URL이 유효한지 점검하세요.

**2단계: URL 경로 확인**

- `file:///` 절대경로가 실제 파일 위치와 일치하는지 확인
- 파일을 옮겼다면 Custom Frames 설정의 URL도 새 경로로 수정 필요
- 한글 파일명은 퍼센트 인코딩 확인: `센터` → `%EC%84%BC%ED%84%B0`

**3단계: HTML 파일 자체 점검**

URL이 맞는데도 빈 페이지라면, HTML 파일이 불완전할 수 있습니다:

- 파일 끝에 `ReactDOM.createRoot(document.getElementById("root")).render(React.createElement(App));` 호출이 있는지 확인
- JSX 변환 중 코드가 잘린 경우 React 컴포넌트가 DOM에 마운트되지 않아 빈 화면이 됩니다

---

## 참고 자료

- [obsidian-html-plugin (GitHub)](https://github.com/nuthrash/obsidian-html-plugin) — HTML Reader 플러그인
- [obsidian-custom-frames (GitHub)](https://github.com/Ellpeck/ObsidianCustomFrames) — Custom Frames 플러그인
