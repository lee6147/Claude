타입 체크와 기본 검증을 실행하세요.

1. `python -m py_compile src/main.py` 로 문법 오류 확인
2. `python -m py_compile src/bot/handlers.py` 로 핸들러 문법 확인
3. `python -m py_compile src/claude/executor.py` 로 실행기 문법 확인
4. `python -m py_compile src/db/database.py` 로 DB 문법 확인
5. `python -m py_compile src/db/models.py` 로 모델 문법 확인
6. `python -m py_compile src/projects/manager.py` 로 매니저 문법 확인
7. mypy가 설치되어 있다면 `python -m mypy src/ --ignore-missing-imports` 실행

오류가 있으면 수정하고, 없으면 "모든 파일 검증 통과" 라고 보고하세요.
