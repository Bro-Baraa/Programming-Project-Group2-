#!/usr/bin/env python3
"""
Cross-platform startup script for Stage Monitoring Tool.
Starts the backend API + frontend server. Works on Windows, Linux, and macOS.
Usage: python start.py        (from the project root or any directory)
       ./start.py             (on Unix systems if executable)
"""

import atexit
import importlib.util
import os
import platform
import secrets
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_PORT = 8001
FRONTEND_PORT = 8080


class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def print_color(text: str, color: str = Colors.NC) -> None:
    """Print text with ANSI color codes."""
    print(f"{color}{text}{Colors.NC}")


def print_header() -> None:
    print_color("Stage Monitoring Tool — Startscript", Colors.BLUE + Colors.BOLD)
    print("=" * 36)
    print()


def ensure_env_file() -> None:
    """Check if .env exists, auto-create from example with random SECRET_KEY if not."""
    env_file = PROJECT_DIR / "backend" / ".env"
    env_example = PROJECT_DIR / "backend" / ".env.example"

    if env_file.exists():
        return

    if env_example.exists():
        print_color("backend/.env niet gevonden. Auto-aanmaken uit .env.example...", Colors.YELLOW)
        example_text = env_example.read_text(encoding="utf-8")
        random_key = secrets.token_hex(16)
        env_text = ""
        for line in example_text.splitlines(keepends=True):
            if line.startswith("SECRET_KEY="):
                env_text += f"SECRET_KEY={random_key}\n"
            else:
                env_text += line
        env_file.write_text(env_text, encoding="utf-8")
        print_color("backend/.env aangemaakt met een willekeurige SECRET_KEY.", Colors.GREEN)
        print()
    else:
        print_color("Waarschuwing: backend/.env noch backend/.env.example gevonden.", Colors.RED)
        print("SECRET_KEY moet handmatig worden ingesteld.")
        print()


# Keep track of running subprocesses so we can clean them up on exit
_children: list[subprocess.Popen] = []


def cleanup(signum=None, frame=None) -> None:
    """Terminate all spawned child processes gracefully."""
    print()
    print_color("Servers stoppen...", Colors.BLUE)
    for proc in _children:
        if proc.poll() is None:
            try:
                if platform.system() == "Windows":
                    proc.terminate()
                else:
                    proc.terminate()
                    # Give it a moment, then kill if needed
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        proc.kill()
            except Exception:
                pass
    print_color("Gestopt.", Colors.GREEN)
    if signum is not None:
        sys.exit(0)


# Register cleanup for normal exit
atexit.register(cleanup)

# Register signal handlers
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)
if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, cleanup)


def which(cmd: str) -> str | None:
    """Cross-platform `which` equivalent."""
    return shutil.which(cmd)


def detect_python_runner() -> tuple[str, str, bool]:
    """
    Determine how to run Python commands.
    Returns (python_runner, init_runner, use_uv).
    """
    uv_path = which("uv")
    use_uv = uv_path is not None

    if use_uv:
        print_color("uv gedetecteerd", Colors.BLUE)
        venv_dir = PROJECT_DIR / "backend" / ".venv"
        if not venv_dir.exists():
            print_color("Virtuele omgeving niet gevonden. Aanmaken met uv...", Colors.YELLOW)
            subprocess.run([uv_path, "venv"], cwd=PROJECT_DIR / "backend", check=True)
        return "uv run -- python", "uv run -- python", True
    else:
        print_color("uv niet gevonden", Colors.BLUE)
        venv_python = PROJECT_DIR / "backend" / ".venv" / "bin" / "python"
        if platform.system() == "Windows":
            venv_python = PROJECT_DIR / "backend" / ".venv" / "Scripts" / "python.exe"

        if venv_python.exists():
            runner = str(venv_python)
            print_color(f"Gebruik: {runner}", Colors.BLUE)
            return runner, runner, False
        else:
            print_color("Gebruik: python3", Colors.BLUE)
            return "python3", "python3", False


def check_dependencies(python_runner: str, use_uv: bool) -> str:
    """
    Check if uvicorn, fastapi, and sqlalchemy are importable.
    If missing, install them and return the (possibly updated) runner.
    """
    print_color("Controleren of afhankelijkheden geïnstalleerd zijn...", Colors.BLUE)

    runner = python_runner
    # Split the runner string into list for subprocess (handles "uv run -- python")
    base_cmd = runner.split()

    check_script = (
        "import importlib.util, sys; "
        "mods = ['uvicorn', 'fastapi', 'sqlalchemy']; "
        "missing = [m for m in mods if importlib.util.find_spec(m) is None]; "
        "sys.exit(1 if missing else 0)"
    )
    result = subprocess.run(base_cmd + ["-c", check_script], cwd=PROJECT_DIR / "backend")

    if result.returncode == 0:
        return runner

    print_color("Afhankelijkheden ontbreken. Installeren uit requirements.txt...", Colors.YELLOW)
    req_file = PROJECT_DIR / "backend" / "requirements.txt"

    if use_uv:
        uv_path = which("uv")
        subprocess.run([uv_path, "pip", "install", "-r", str(req_file)], cwd=PROJECT_DIR / "backend", check=True)
    else:
        venv_dir = PROJECT_DIR / "backend" / ".venv"
        venv_bin = venv_dir / "bin"
        if platform.system() == "Windows":
            venv_bin = venv_dir / "Scripts"

        if not venv_dir.exists():
            print_color("Virtuele omgeving aanmaken...", Colors.YELLOW)
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], cwd=PROJECT_DIR / "backend", check=True)
            # After creating venv, prefer the venv python
            if platform.system() == "Windows":
                runner = str(venv_dir / "Scripts" / "python.exe")
            else:
                runner = str(venv_dir / "bin" / "python")
            base_cmd = runner.split()

        pip_path = venv_bin / "pip"
        if platform.system() == "Windows":
            pip_path = venv_bin / "pip.exe"

        if pip_path.exists():
            subprocess.run([str(pip_path), "install", "-r", str(req_file)], cwd=PROJECT_DIR / "backend", check=True)
        else:
            print_color("pip niet gevonden in virtuele omgeving. Probeer opnieuw:", Colors.RED)
            print("  rm -rf backend/.venv && python start.py")
            sys.exit(1)

    print_color("Afhankelijkheden geïnstalleerd.", Colors.GREEN)
    return runner


def seed_database_if_empty(init_runner: str) -> None:
    """Check if database is empty and seed with demo data if needed."""
    db_file = PROJECT_DIR / "backend" / "stage_monitoring.db"

    base_cmd = init_runner.split()
    check_script = (
        f"import sqlite3, sys; "
        f"conn = sqlite3.connect('{db_file}'); "
        f"cursor = conn.cursor(); "
        f"cursor.execute('SELECT COUNT(*) FROM users;'); "
        f"count = cursor.fetchone()[0]; "
        f"conn.close(); "
        f"sys.exit(0 if count > 0 else 1)"
    )
    result = subprocess.run(base_cmd + ["-c", check_script], cwd=PROJECT_DIR / "backend")

    if db_file.exists() and result.returncode == 0:
        return

    print_color("Database leeg of niet gevonden. Seeding met demo-data...", Colors.YELLOW)
    seed_script = PROJECT_DIR / "backend" / "seed_complete.py"
    subprocess.run(base_cmd + [str(seed_script)], cwd=PROJECT_DIR / "backend", check=True)
    print_color("Database gevuld!", Colors.GREEN)
    print()


def start_backend(python_runner: str) -> subprocess.Popen:
    """Start the uvicorn backend server."""
    print_color(f"Backend starten op http://localhost:{BACKEND_PORT}", Colors.GREEN)
    base_cmd = python_runner.split()
    cmd = base_cmd + [
        "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--port", str(BACKEND_PORT),
    ]
    return subprocess.Popen(cmd, cwd=PROJECT_DIR / "backend")


def start_frontend() -> subprocess.Popen:
    """Start the frontend HTTP server."""
    print_color(f"Frontend starten op http://localhost:{FRONTEND_PORT}", Colors.GREEN)
    cmd = [sys.executable, "-m", "http.server", str(FRONTEND_PORT)]
    return subprocess.Popen(cmd, cwd=PROJECT_DIR / "frontend")


def wait_for_backend(proc: subprocess.Popen, timeout: int = 10) -> bool:
    """Wait briefly and check whether the backend process is still alive."""
    for _ in range(timeout):
        if proc.poll() is not None:
            return False
        time.sleep(1)
    return proc.poll() is None


def main() -> None:
    print_header()
    ensure_env_file()

    python_runner, init_runner, use_uv = detect_python_runner()
    python_runner = check_dependencies(python_runner, use_uv)
    init_runner = python_runner  # Align after potential venv creation

    seed_database_if_empty(init_runner)

    backend_proc = start_backend(python_runner)
    _children.append(backend_proc)

    if not wait_for_backend(backend_proc):
        print_color("Backend kon niet starten. Controleer of uvicorn geïnstalleerd is:", Colors.RED)
        if use_uv:
            print("  cd backend && uv pip install -r requirements.txt")
        else:
            print("  cd backend && pip install -r requirements.txt")
        sys.exit(1)

    frontend_proc = start_frontend()
    _children.append(frontend_proc)

    time.sleep(1)

    print()
    print("=" * 36)
    print_color("✓ Alles draait!", Colors.GREEN)
    print()
    print(f"  Frontend:  http://localhost:{FRONTEND_PORT}")
    print(f"  Backend:   http://localhost:{BACKEND_PORT}")
    print(f"  API docs:  http://localhost:{BACKEND_PORT}/docs")
    print()
    print("Testaccounts:")
    print("  admin@school.be / admin123")
    print("  student1@school.be / student123")
    print()
    print("Druk Ctrl+C om te stoppen.")
    print()

    # Keep the main thread alive while children run
    try:
        while True:
            backend_alive = backend_proc.poll() is None
            frontend_alive = frontend_proc.poll() is None
            if not backend_alive or not frontend_alive:
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()


if __name__ == "__main__":
    main()
