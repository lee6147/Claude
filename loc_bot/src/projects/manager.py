from pathlib import Path
from config.settings import WORKSPACE_ROOT
from src.db.models import add_project, get_project, list_projects


async def register_project(name: str, path: str | None = None, description: str = "") -> str:
    """프로젝트를 등록한다. path가 없으면 WORKSPACE_ROOT/name 사용."""
    if await get_project(name):
        return f"이미 등록된 프로젝트입니다: {name}"

    project_path = Path(path) if path else WORKSPACE_ROOT / name
    if not project_path.exists():
        return f"디렉토리가 존재하지 않습니다: {project_path}"

    await add_project(name, str(project_path), description)
    return f"프로젝트 등록 완료: {name} → {project_path}"


async def get_project_path(name: str) -> Path | None:
    """프로젝트의 작업 디렉토리 경로를 반환한다."""
    proj = await get_project(name)
    if not proj:
        return None
    return Path(proj["path"])


async def list_all_projects() -> str:
    """등록된 프로젝트 목록을 포맷팅하여 반환한다."""
    projects = await list_projects()
    if not projects:
        return "등록된 프로젝트가 없습니다."

    lines = ["📂 등록된 프로젝트:"]
    for p in projects:
        lines.append(f"  • {p['name']} → {p['path']}")
    return "\n".join(lines)


def scan_workspace() -> list[str]:
    """WORKSPACE_ROOT에서 디렉토리 목록을 스캔한다."""
    if not WORKSPACE_ROOT.exists():
        return []
    return [
        d.name
        for d in WORKSPACE_ROOT.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
