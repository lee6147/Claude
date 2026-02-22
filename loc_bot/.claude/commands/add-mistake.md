실수 패턴을 수동으로 기록합니다.

사용자가 제공하는 정보:
- 파일 경로: $ARGUMENTS의 첫 번째 인자
- 패턴 설명: $ARGUMENTS의 나머지 부분

다음을 수행하세요:

1. `.claude/cache/mistake-candidates.jsonl` 에 아래 형식으로 추가:
   ```json
   {"file":"<파일경로>","pattern":"<패턴설명>","type":"manual","time":"<ISO시간>"}
   ```

2. 이 실수 패턴을 향후 같은 파일 수정 시 주의사항으로 기억하세요.

3. 기록 완료 메시지를 출력하세요.

예시: /add-mistake src/bot/handlers.py auth_required 데코레이터 빠뜨림
