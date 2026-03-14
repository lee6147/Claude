import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
def _parse_user_ids(raw: str) -> list[int]:
    ids = []
    for uid in raw.split(","):
        uid = uid.strip()
        if uid.isdigit():
            ids.append(int(uid))
    return ids

ALLOWED_USER_IDS = _parse_user_ids(os.getenv("ALLOWED_USER_IDS", ""))

# Claude Code CLI
CLAUDE_CLI_PATH = os.getenv("CLAUDE_CLI_PATH", "claude")

# Workspace
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", str(Path.home() / "Desktop"))).expanduser()

# Database
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / os.getenv("DB_PATH", "data/loc_bot.db")

# Limits
MAX_OUTPUT_LENGTH = 4096  # Telegram 메시지 최대 길이
CLAUDE_TIMEOUT = 3600             # 글로벌 타임아웃 (초, 0 = 무제한)
CLAUDE_INACTIVITY_TIMEOUT = 120   # 무출력 경고 기준 (초)
STREAM_UPDATE_INTERVAL = 10       # 텔레그램 편집 간격 (초)
MAX_QUEUE_SIZE = 10               # 프로젝트당 큐 최대 크기
MAX_IMAGE_SIZE = 10 * 1024 * 1024 # 이미지 최대 크기 (10MB)

# agent-engine
def _find_agent_engine() -> str:
    found = shutil.which("agent-engine")
    if found:
        return found
    fallback = Path(__file__).parent.parent.parent / "agent-engine" / ".venv" / "Scripts" / "agent-engine.exe"
    return str(fallback)

AGENT_ENGINE_CLI = os.getenv("AGENT_ENGINE_CLI", _find_agent_engine())
AUTO_REVIEW_ENABLED = os.getenv("AUTO_REVIEW_ENABLED", "true").lower() == "true"
