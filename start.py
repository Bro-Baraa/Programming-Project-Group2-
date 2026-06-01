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
import traceback
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
BACKEND_PORT = 8001
FRONTEND_PORT = 8080

# Setup logging to file + console
LOG_FILE = PROJECT_DIR / "startup.log"
log_handle = open(LOG_FILE, "w", encoding="utf-8", buffering=1)


def log(text: str, color: str | None = None) -> None:
    """Print to console and write to log file."""
    if color:
        print(f"{color}{text}\033[0m")
    else:
        print(text)
    log_handle.write(f"{text}\n")
    log_handle.flush()


def log_command(cmd: list[str], cwd: Path | None = None) -> None:
    log(f"[CMD] {cwd or Path.cwd()} > {' '.join(cmd)}")


def log_result(result: subprocess.CompletedProcess) -> None:
    log(f"[EXIT] code={result.returncode}")
    if result.stdout:
        log(f"[STDOUT] {result.stdout.decode('utf-8', errors='replace').strip()}")
    if result.stderr:
        log(f"[STDERR] {result.stderr.decode('utf-8', errors='replace').strip()}")


def log_env() -> None:
    log("=" * 50)
    log(f"Platform:     {platform.platform()}")
    log(f"Python:       {sys.executable} ({sys.version})")
    log(f"Project dir:  {PROJECT_DIR}")
    log(f"uv available: {shutil.which('uv') or 'NO'}")
    log(f"Working dir:  {os.getcwd()}")
    log("=" * 50)
    log("")


class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    NC = "\033[0m"


def print_color(text: str, color: str = Colors.NC) -> None:
    """Print text with ANSI color codes."""
    log(text, color)


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
_cleanup_done = False


def cleanup(signum=None, frame=None) -> None:
    """Terminate all spawned child processes gracefully."""
    global _cleanup_done
    if _cleanup_done:
        return
    _cleanup_done = True
    log("")
    log("Servers stoppen...")
    for proc in _children:
        if proc.poll() is None:
            try:
                log(f"  Terminating process PID={proc.pid}")
                if platform.system() == "Windows":
                    try:
                        proc.send_signal(signal.CTRL_BREAK_EVENT)
                    except (ValueError, OSError):
                        proc.terminate()
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        log(f"  Killing PID={proc.pid} (didn't terminate)")
                        proc.kill()
                else:
                    proc.terminate()
                    try:
                        proc.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        log(f"  Killing PID={proc.pid} (didn't terminate)")
                        proc.kill()
            except Exception as e:
                log(f"  Error stopping PID={proc.pid}: {e}")
    log("Gestopt.")
    if signum is not None:
        log("Exiting due to signal")
        log_handle.close()
        sys.exit(0)


# Register cleanup for normal exit
atexit.register(cleanup)

# Register signal handlers
signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)
if hasattr(signal, "SIGBREAK"):
    signal.signal(signal.SIGBREAK, cleanup)


def log_fatal_error(msg: str) -> None:
    """Print a fatal error, log it, and wait for keypress on Windows."""
    log("")
    log("=" * 50)
    log(f"FATAL ERROR: {msg}")
    log("=" * 50)
    log(f"Full log written to: {LOG_FILE}")
    log("")
    if platform.system() == "Windows":
        log("Press Enter to exit...")
        log_handle.flush()
        try:
            input()
        except EOFError:
            pass
    log_handle.close()
    sys.exit(1)


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
        log("uv gedetecteerd")
        venv_dir = PROJECT_DIR / "backend" / ".venv"
        if not venv_dir.exists():
            log("Virtuele omgeving niet gevonden. Aanmaken met uv...")
            cmd = [uv_path, "venv"]
            log_command(cmd, PROJECT_DIR / "backend")
            try:
                result = subprocess.run(cmd, cwd=PROJECT_DIR / "backend", capture_output=True)
                log_result(result)
                if result.returncode != 0:
                    log_fatal_error(f"uv venv failed with exit code {result.returncode}")
            except Exception as e:
                log_fatal_error(f"uv venv failed: {e}\n{traceback.format_exc()}")
        return "uv run -- python", "uv run -- python", True
    else:
        log("uv niet gevonden")
        venv_python = PROJECT_DIR / "backend" / ".venv" / "bin" / "python"
        if platform.system() == "Windows":
            venv_python = PROJECT_DIR / "backend" / ".venv" / "Scripts" / "python.exe"

        if venv_python.exists():
            runner = str(venv_python)
            log(f"Gebruik: {runner}")
            return runner, runner, False
        else:
            if platform.system() == "Windows":
                runner = sys.executable
            else:
                runner = "python3"
            log(f"Gebruik: {runner}")
            return runner, runner, False


def check_dependencies(python_runner: str, use_uv: bool) -> str:
    """
    Check if uvicorn, fastapi, and sqlalchemy are importable.
    If missing, install them and return the (possibly updated) runner.
    """
    log("Controleren of afhankelijkheden geïnstalleerd zijn...")

    runner = python_runner
    base_cmd = runner.split()

    check_script = (
        "import importlib.util, sys; "
        "mods = ['uvicorn', 'fastapi', 'sqlalchemy']; "
        "missing = [m for m in mods if importlib.util.find_spec(m) is None]; "
        "sys.exit(1 if missing else 0)"
    )
    cmd = base_cmd + ["-c", check_script]
    log_command(cmd, PROJECT_DIR / "backend")
    result = subprocess.run(cmd, cwd=PROJECT_DIR / "backend", capture_output=True)
    log_result(result)

    if result.returncode == 0:
        log("Dependencies OK")
        return runner

    log("Afhankelijkheden ontbreken. Installeren uit requirements.txt...")
    req_file = PROJECT_DIR / "backend" / "requirements.txt"

    if use_uv:
        uv_path = which("uv")
        cmd = [uv_path, "pip", "install", "-r", str(req_file)]
        log_command(cmd, PROJECT_DIR / "backend")
        try:
            result = subprocess.run(cmd, cwd=PROJECT_DIR / "backend", capture_output=True)
            log_result(result)
            if result.returncode != 0:
                log_fatal_error(f"uv pip install failed with exit code {result.returncode}")
        except Exception as e:
            log_fatal_error(f"uv pip install failed: {e}\n{traceback.format_exc()}")
    else:
        venv_dir = PROJECT_DIR / "backend" / ".venv"
        venv_bin = venv_dir / "bin"
        if platform.system() == "Windows":
            venv_bin = venv_dir / "Scripts"

        if not venv_dir.exists():
            log("Virtuele omgeving aanmaken...")
            cmd = [sys.executable, "-m", "venv", str(venv_dir)]
            log_command(cmd, PROJECT_DIR / "backend")
            try:
                result = subprocess.run(cmd, cwd=PROJECT_DIR / "backend", capture_output=True)
                log_result(result)
                if result.returncode != 0:
                    log_fatal_error(f"python -m venv failed with exit code {result.returncode}")
            except Exception as e:
                log_fatal_error(f"venv creation failed: {e}\n{traceback.format_exc()}")
            if platform.system() == "Windows":
                runner = str(venv_dir / "Scripts" / "python.exe")
            else:
                runner = str(venv_dir / "bin" / "python")
            log(f"Runner updated to: {runner}")
            base_cmd = runner.split()

        pip_path = venv_bin / "pip"
        if platform.system() == "Windows":
            pip_path = venv_bin / "pip.exe"

        if pip_path.exists():
            cmd = [str(pip_path), "install", "-r", str(req_file)]
            log_command(cmd, PROJECT_DIR / "backend")
            try:
                result = subprocess.run(cmd, cwd=PROJECT_DIR / "backend", capture_output=True)
                log_result(result)
                if result.returncode != 0:
                    log_fatal_error(f"pip install failed with exit code {result.returncode}")
            except Exception as e:
                log_fatal_error(f"pip install failed: {e}\n{traceback.format_exc()}")
        else:
            log_fatal_error("pip niet gevonden in virtuele omgeving. Probeer opnieuw: rm -rf backend/.venv && python start.py")

    log("Afhankelijkheden geïnstalleerd.")
    return runner


def seed_database_if_empty(init_runner: str) -> None:
    """Check if database is empty and seed with demo data if needed."""
    db_file = PROJECT_DIR / "backend" / "stage_monitoring.db"

    base_cmd = init_runner.split()
    # Use raw-string prefix so Windows backslashes don't trigger unicode escapes
    check_script = (
        f"import sqlite3, sys; "
        f"conn = sqlite3.connect(r'{db_file}'); "
        f"cursor = conn.cursor(); "
        f"cursor.execute('SELECT COUNT(*) FROM users;'); "
        f"count = cursor.fetchone()[0]; "
        f"conn.close(); "
        f"sys.exit(0 if count > 0 else 1)"
    )
    cmd = base_cmd + ["-c", check_script]
    log_command(cmd, PROJECT_DIR / "backend")
    result = subprocess.run(cmd, cwd=PROJECT_DIR / "backend", capture_output=True)
    log_result(result)

    if db_file.exists() and result.returncode == 0:
        log("Database OK (users exist)")
        return

    log("Database leeg of niet gevonden. Seeding met demo-data...")
    seed_script = PROJECT_DIR / "backend" / "seed_complete.py"
    cmd = base_cmd + [str(seed_script)]
    log_command(cmd, PROJECT_DIR / "backend")
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR / "backend", capture_output=True)
        log_result(result)
        if result.returncode != 0:
            log_fatal_error(f"seed_complete.py failed with exit code {result.returncode}")
    except Exception as e:
        log_fatal_error(f"seed script failed: {e}\n{traceback.format_exc()}")
    log("Database gevuld!")
    log("")


def start_backend(python_runner: str) -> subprocess.Popen:
    """Start the uvicorn backend server."""
    log(f"Backend starten op http://localhost:{BACKEND_PORT}")
    base_cmd = python_runner.split()
    cmd = base_cmd + [
        "-m", "uvicorn",
        "app.main:app",
        "--reload",
        "--port", str(BACKEND_PORT),
        "--host", "0.0.0.0",
    ]
    log_command(cmd, PROJECT_DIR / "backend")
    log("Starting backend process...")
    kwargs = {
        "cwd": PROJECT_DIR / "backend",
        "stderr": subprocess.PIPE,
        "stdout": subprocess.PIPE,
    }
    if platform.system() == "Windows":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    return subprocess.Popen(cmd, **kwargs)


def start_frontend() -> subprocess.Popen:
    """Start the frontend HTTP server."""
    log(f"Frontend starten op http://localhost:{FRONTEND_PORT}")
    cmd = [sys.executable, "-m", "http.server", str(FRONTEND_PORT)]
    log_command(cmd, PROJECT_DIR / "frontend")
    return subprocess.Popen(cmd, cwd=PROJECT_DIR / "frontend", stderr=subprocess.PIPE, stdout=subprocess.PIPE)


def wait_for_backend(proc: subprocess.Popen, timeout: int = 10) -> bool:
    """Wait briefly and check whether the backend process is still alive."""
    for i in range(timeout):
        if proc.poll() is not None:
            log(f"Backend exited early after {i+1}s with code: {proc.poll()}")
            stderr_data = b""
            try:
                stderr_data, _ = proc.communicate(timeout=2)
            except Exception:
                pass
            if stderr_data:
                log("Backend stderr:")
                log(stderr_data.decode("utf-8", errors="replace").strip())
            return False
        time.sleep(1)
    alive = proc.poll() is None
    log(f"Backend alive after {timeout}s: {alive}")
    return alive


def main() -> None:
    print_header()
    log_env()
    ensure_env_file()

    python_runner, init_runner, use_uv = detect_python_runner()
    python_runner = check_dependencies(python_runner, use_uv)
    init_runner = python_runner  # Align after potential venv creation

    seed_database_if_empty(init_runner)

    backend_proc = start_backend(python_runner)
    _children.append(backend_proc)

    if not wait_for_backend(backend_proc):
        msg = "Backend kon niet starten. Controleer of uvicorn geïnstalleerd is."
        if use_uv:
            msg += "  cd backend && uv pip install -r requirements.txt"
        else:
            msg += "  cd backend && pip install -r requirements.txt"
        log_fatal_error(msg)

    frontend_proc = start_frontend()
    _children.append(frontend_proc)

    time.sleep(1)

    log("")
    log("=" * 36)
    log("✓ Alles draait!")
    log("")
    log(f"  Frontend:  http://localhost:{FRONTEND_PORT}")
    log(f"  Backend:   http://localhost:{BACKEND_PORT}")
    log(f"  API docs:  http://localhost:{BACKEND_PORT}/docs")
    log("")
    log("Testaccounts:")
    log("  admin@school.be / admin123")
    log("  student1@school.be / student123")
    log("")
    log("Druk Ctrl+C om te stoppen.")
    log("")

    # Keep the main thread alive while children run
    try:
        while True:
            backend_alive = backend_proc.poll() is None
            frontend_alive = frontend_proc.poll() is None
            if not backend_alive:
                log("Backend process stopped unexpectedly!")
                try:
                    stderr_data, _ = backend_proc.communicate(timeout=2)
                    if stderr_data:
                        log("Backend stderr:")
                        log(stderr_data.decode("utf-8", errors="replace").strip())
                except Exception:
                    pass
                break
            if not frontend_alive:
                log("Frontend process stopped unexpectedly!")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        log("Ctrl+C pressed")
    finally:
        cleanup()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_fatal_error(f"Unhandled exception: {e}\n{traceback.format_exc()}")
