import sys
from typing import Dict, Any

def tty_progress(msg: str, **kwargs):
    print(f"[PROGRESS] {msg}", file=sys.stderr)

def tty_info(msg: str, **kwargs):
    print(f"[INFO] {msg}", file=sys.stderr)

def tty_warn(msg: str, **kwargs):
    print(f"[WARN] {msg}", file=sys.stderr)

def tty_error(msg: str, **kwargs):
    print(f"[ERROR] {msg}", file=sys.stderr)
