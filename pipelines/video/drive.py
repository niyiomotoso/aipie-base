"""Google Drive transfer via rclone.

The Drive MCP connector caps downloads at 10MB, which no footage file respects,
so every media transfer goes through rclone. Moves and renames inside Drive are
server-side - never download-and-reupload a 400MB file.
"""
import subprocess
import sys

from . import config as C


def _run(args: list, what: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["rclone"] + args, capture_output=True, text=True)
    if r.returncode != 0:
        tail = " | ".join(r.stderr.strip().splitlines()[-4:])
        raise RuntimeError(f"rclone {what} failed: {tail}")
    return r


def have_remote() -> bool:
    try:
        r = _run(["listremotes"], "listremotes")
    except (RuntimeError, FileNotFoundError):
        return False
    return f"{C.REMOTE}:" in r.stdout


def list_projects() -> list:
    """Project folders under Videos Unedited."""
    r = _run(["lsf", "--dirs-only", C.UNEDITED], "list projects")
    return [p.rstrip("/") for p in r.stdout.split() if p.strip()]


def list_files(project: str, edited: bool = False) -> list:
    base = C.EDITED if edited else C.UNEDITED
    try:
        r = _run(["lsf", f"{base}/{project}"], "list files")
    except RuntimeError:
        return []
    return [p for p in r.stdout.splitlines() if p.strip() and not p.endswith("/")]


def pull(project: str, dest, include: list = None) -> list:
    """Download a project's source files. Returns local paths."""
    args = ["copy", f"{C.UNEDITED}/{project}", str(dest),
            "--stats-one-line", "--stats", "20s"]
    for pat in include or []:
        args += ["--include", pat]
    print(f"pulling {project} from Drive...")
    _run(args, "pull")
    files = sorted(p for p in dest.iterdir() if p.is_file() and not p.name.startswith("."))
    for f in files:
        print(f"  {f.name}  {f.stat().st_size/1e6:.1f} MB")
    return files


def push(project: str, paths: list) -> None:
    """Upload outputs into Videos Edited/<project>/, creating it if absent."""
    dest = f"{C.EDITED}/{project}"
    _run(["mkdir", dest], "mkdir")
    for p in paths:
        if not p.exists():
            print(f"  skipped (missing): {p.name}")
            continue
        _run(["copy", str(p), dest, "--stats-one-line", "--stats", "20s"], "push")
        print(f"  uploaded {p.name}  {p.stat().st_size/1e6:.1f} MB")


def ensure_mirror(project: str) -> str:
    """Output folder mirrors the source folder name exactly."""
    if project not in list_projects():
        raise SystemExit(
            f"no project '{project}' under Videos Unedited. "
            f"Available: {', '.join(list_projects()) or '(none)'}")
    _run(["mkdir", f"{C.EDITED}/{project}"], "mkdir edited")
    return f"{C.EDITED}/{project}"


if __name__ == "__main__":
    if not have_remote():
        sys.exit(f"rclone remote '{C.REMOTE}:' not configured - run: rclone config")
    print("projects:", ", ".join(list_projects()) or "(none)")
