# Obsidian Vault

## HTML 파일 Custom Frames 등록

html/ 폴더에 HTML 파일을 추가하면 `.obsidian/plugins/obsidian-custom-frames/data.json`의 `frames` 배열에 수동 등록해야 한다.

사용자가 "등록해줘"라고 하면 data.json에 직접 프레임을 추가할 것.

### 등록 형식

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

### 주의사항
- 한글 파일명은 URL 퍼센트 인코딩 필요
- 등록 후 Obsidian 재시작 필수
- `forceIframe: false` (WebView 사용) 필수
