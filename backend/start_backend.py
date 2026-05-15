# start_backend.py - 启动后端并记录日志
import os, sys, subprocess, datetime

log_path = os.path.join(os.path.dirname(__file__), "backend.log")
with open(log_path, "a", encoding="utf-8") as f:
    f.write(f"\n\n=== Backend Start: {datetime.datetime.now()} ===\n")

env = os.environ.copy()
env["DISABLE_RATE_LIMIT"] = "1"
env["DATABASE_URL"] = "sqlite:///tushen.db"

proc = subprocess.Popen(
    [sys.executable, "main.py"],
    cwd=os.path.dirname(__file__),
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=False
)

with open(log_path, "a", encoding="utf-8") as f:
    for line in proc.stdout:
        f.write(line.decode("utf-8", errors="replace"))
        f.flush()
