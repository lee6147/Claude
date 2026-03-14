# EP03: AI 에이전트 A to Z — 나만의 에이전트를 처음부터 만들어보자

> AI 에이전트의 핵심 개념부터 실제 동작하는 에이전트까지, 코드로 직접 만들어보는 실전 가이드

## 📺 영상

**[YouTube에서 보기](https://youtube.com/@ten-builder)**

## 이 에피소드에서 다루는 것

- AI 에이전트가 정확히 뭔지, 챗봇과 뭐가 다른지
- ReAct 패턴으로 "생각 → 행동 → 관찰" 루프 만들기
- 도구(Tool)를 직접 정의하고 에이전트에 연결하기
- 메모리를 붙여서 대화 맥락을 유지하는 방법

## AI 에이전트 vs 챗봇

챗봇은 질문에 답만 해요. 에이전트는 **스스로 판단하고 행동**해요.

| 구분 | 챗봇 | 에이전트 |
|------|------|----------|
| 입력 | 사용자 메시지 | 사용자 목표 |
| 처리 | 한 번 응답 | 루프를 돌며 여러 번 행동 |
| 도구 사용 | ❌ | ✅ 검색, API 호출, 파일 읽기 등 |
| 자율성 | 낮음 | 높음 — 중간 단계를 스스로 결정 |

핵심 차이는 **루프**에요. 에이전트는 목표를 달성할 때까지 "생각 → 행동 → 결과 확인"을 반복해요.

## 사전 준비

- Python 3.11+
- `pip install anthropic` (Claude API)
- Anthropic API 키 설정: `export ANTHROPIC_API_KEY=your_key`

## 핵심 코드 & 설정

### 프로젝트 구조

```
ai-agent-demo/
├── agent.py            # 메인 에이전트 루프
├── tools.py            # 도구 정의
├── memory.py           # 대화 메모리
├── prompts.py          # 시스템 프롬프트
└── requirements.txt
```

### Step 1: ReAct 에이전트 루프 만들기

에이전트의 핵심은 ReAct(Reasoning + Acting) 패턴이에요. LLM이 먼저 생각하고, 어떤 도구를 쓸지 결정하고, 결과를 보고 다시 생각하는 루프를 만들어요.

#### `agent.py`

```python
import anthropic
from tools import TOOLS, execute_tool
from memory import ConversationMemory

client = anthropic.Anthropic()
memory = ConversationMemory(max_turns=20)

SYSTEM_PROMPT = """당신은 유능한 AI 에이전트입니다.
사용자의 요청을 달성하기 위해 제공된 도구를 사용하세요.
한 번에 하나의 도구를 사용하고, 결과를 확인한 뒤 다음 행동을 결정하세요.
목표를 달성하면 최종 답변을 제공하세요."""


def run_agent(user_input: str) -> str:
    memory.add_user_message(user_input)
    messages = memory.get_messages()

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        # 도구 호출이 없으면 최종 답변
        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            memory.add_assistant_message(final_text)
            return final_text

        # 도구 호출 처리
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"🔧 도구 실행: {block.name}({block.input})")
                result = execute_tool(block.name, block.input)
                print(f"📋 결과: {result[:200]}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        # 대화에 결과 추가하고 다시 루프
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})
```

### Step 2: 도구 정의하기

에이전트에게 줄 수 있는 도구를 정의해요. Claude API의 tool use 스펙에 맞춰서 JSON Schema로 작성해요.

#### `tools.py`

```python
import json
import subprocess
import urllib.request

TOOLS = [
    {
        "name": "web_search",
        "description": "웹에서 정보를 검색합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "검색할 키워드",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_file",
        "description": "로컬 파일의 내용을 읽습니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "읽을 파일 경로",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "run_command",
        "description": "셸 명령어를 실행합니다",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "실행할 명령어",
                }
            },
            "required": ["command"],
        },
    },
]


def execute_tool(name: str, params: dict) -> str:
    if name == "web_search":
        # 간단한 검색 구현 (실제로는 Tavily 등 사용)
        url = f"https://api.tavily.com/search"
        # ... API 호출 구현
        return f"'{params['query']}' 검색 결과를 반환합니다"

    elif name == "read_file":
        try:
            with open(params["path"], "r") as f:
                return f.read()[:5000]
        except FileNotFoundError:
            return f"파일을 찾을 수 없어요: {params['path']}"

    elif name == "run_command":
        result = subprocess.run(
            params["command"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout or result.stderr

    return f"알 수 없는 도구: {name}"
```

### Step 3: 대화 메모리 붙이기

에이전트가 이전 대화를 기억하게 해줘요. 간단한 슬라이딩 윈도우 방식으로 구현해요.

#### `memory.py`

```python
class ConversationMemory:
    def __init__(self, max_turns: int = 20):
        self.messages: list[dict] = []
        self.max_turns = max_turns

    def add_user_message(self, text: str):
        self.messages.append({"role": "user", "content": text})
        self._trim()

    def add_assistant_message(self, text: str):
        self.messages.append({"role": "assistant", "content": text})
        self._trim()

    def get_messages(self) -> list[dict]:
        return list(self.messages)

    def _trim(self):
        # 최근 N턴만 유지
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-self.max_turns * 2 :]
```

### Step 4: 실행해보기

```bash
# requirements.txt
# anthropic>=0.40.0

pip install -r requirements.txt

python -c "
from agent import run_agent
result = run_agent('현재 디렉토리에 있는 Python 파일 목록을 보여줘')
print(result)
"
```

실행하면 에이전트가 이렇게 동작해요:

```
🔧 도구 실행: run_command({'command': 'ls *.py'})
📋 결과: agent.py
tools.py
memory.py
prompts.py
```

에이전트가 알아서 `ls` 명령어를 선택하고 실행한 거예요.

## 에이전트 아키텍처 패턴

실전에서 자주 쓰이는 패턴 3가지를 정리했어요.

| 패턴 | 설명 | 적합한 상황 |
|------|------|------------|
| **ReAct** | 생각 → 행동 → 관찰 루프 | 단일 에이전트, 범용 작업 |
| **Swarm** | 여러 에이전트가 동적으로 핸드오프 | 역할이 명확히 나뉘는 복잡한 작업 |
| **Plan-Execute** | 먼저 계획 → 순서대로 실행 | 단계가 많은 프로젝트성 작업 |

이번 에피소드에서 만든 건 ReAct 패턴이에요. 가장 기본이면서도 실용적인 패턴이에요.

## AI 활용 포인트

| 상황 | 프롬프트 예시 |
|------|-------------|
| 도구 추가 | `에이전트에 데이터베이스 조회 도구를 추가해줘` |
| 에러 처리 | `도구 실행 실패 시 재시도 로직을 넣어줘` |
| 패턴 변경 | `ReAct 대신 Plan-Execute 패턴으로 바꿔줘` |
| 성능 개선 | `도구 호출 결과를 캐싱하는 기능을 추가해줘` |

## 더 알아보기

- [Anthropic 공식 Tool Use 문서](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [에이전트 팀즈 에피소드](../EP02-agent-teams/)
- [Claude Code 플레이북](../../claude-code/playbooks/)

---

**구독하기:** [@ten-builder](https://youtube.com/@ten-builder) | [뉴스레터](https://maily.so/tenbuilder)
