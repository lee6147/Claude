# Obsidian Vault

## HTML 파일 Custom Frames 등록

html/ 폴더에 HTML 파일을 넣고 `register_html.py`를 실행하면 Custom Frames에 자동 등록된다.

```bash
python register_html.py          # 등록 + Obsidian 재시작
python register_html.py --dry    # 미리보기
```

사용자가 "등록해줘"라고 하면 위 스크립트를 실행할 것.

### 스크립트 동작
- html/ 폴더의 *.html 스캔
- <title> 태그에서 표시 이름 추출
- .obsidian/plugins/obsidian-custom-frames/data.json에 등록
- Obsidian 재시작
