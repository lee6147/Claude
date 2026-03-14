import asyncio
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)

# httpx 로거가 Telegram API URL(봇 토큰 포함)을 그대로 출력하므로 억제
logging.getLogger("httpx").setLevel(logging.WARNING)

from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, MessageHandler, filters
from telegram.ext import AIORateLimiter
from config.settings import BOT_TOKEN
from src.db.database import init_db, close_db
from src.bot.handlers import (
    cmd_start,
    cmd_projects,
    cmd_register,
    cmd_use,
    cmd_scan,
    cmd_history,
    cmd_status,
    cmd_help,
    cmd_new,
    cmd_stop,
    cmd_stop_all,
    cmd_restart,
    cmd_unknown,
    handle_button_text,
    handle_callback,
    handle_photo,
    load_user_states,
    shutdown_workers,
)


def main():
    if not BOT_TOKEN:
        print("오류: TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
        print(".env 파일을 생성하고 BOT_TOKEN을 설정하세요.")
        sys.exit(1)

    # DB 초기화 + 사용자 상태 로드
    asyncio.run(init_db())
    asyncio.run(load_user_states())

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .rate_limiter(AIORateLimiter(max_retries=2))
        .build()
    )

    # 명령어 등록
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("projects", cmd_projects))
    app.add_handler(CommandHandler("register", cmd_register))
    app.add_handler(CommandHandler("use", cmd_use))
    app.add_handler(CommandHandler("scan", cmd_scan))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("new", cmd_new))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("stop_all", cmd_stop_all))
    app.add_handler(CommandHandler("restart", cmd_restart))

    # 미등록 명령어 처리
    app.add_handler(MessageHandler(filters.COMMAND, cmd_unknown))

    # 인라인 버튼 콜백
    app.add_handler(CallbackQueryHandler(handle_callback))

    # 사진 핸들러
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    # 이미지 문서 핸들러 (Document.ALL → handler 내부에서 mime_type 체크)
    app.add_handler(MessageHandler(filters.Document.ALL, handle_photo))

    # 일반 메시지 → 버튼 텍스트 처리 또는 Claude Code 실행
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_button_text))

    print("loc_bot 시작됨. Ctrl+C로 종료.")
    try:
        app.run_polling(drop_pending_updates=True)
    finally:
        asyncio.run(shutdown_workers())
        asyncio.run(close_db())


if __name__ == "__main__":
    main()
