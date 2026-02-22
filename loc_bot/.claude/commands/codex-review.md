Codex CLI를 사용한 코드 리뷰를 실행합니다.

## 단계

1. 변경된 파일 목록을 파악합니다.
   - `$ARGUMENTS`가 있으면 해당 파일들을 대상으로 합니다.
   - 없으면 `git diff --name-only`로 변경 파일을 찾거나, 최근 작업한 파일을 대상으로 합니다.

2. `.agents/claude/review-request-latest.md` 파일을 작성합니다:
   - 변경 파일 목록
   - 변경 사유 (커밋 메시지나 컨텍스트에서 추론)
   - 주의 사항

3. Codex CLI를 실행합니다:
   ```bash
   cd C:\Users\sehye\Desktop\loc_bot && codex.cmd exec --full-auto "Read .agents/claude/review-request-latest.md and review all listed files for: syntax errors, type safety, security vulnerabilities, error handling, code duplication. Write detailed results to .agents/codex/review-result-$(date +%Y%m%d-%H%M%S).md with PASS or FAIL verdict."
   ```
   > 주의: Windows에서 Python subprocess는 `codex`(POSIX script)를 실행할 수 없으므로 반드시 `codex.cmd`를 사용해야 합니다.

4. `.agents/codex/` 디렉토리에서 최신 리뷰 결과를 읽고 사용자에게 요약합니다.

5. 결과에 따라:
   - **PASS**: "Codex 리뷰 통과. 커밋 가능합니다." 보고
   - **FAIL**: 수정 필요 사항을 목록으로 보고
