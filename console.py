from datetime import datetime

R      = "\033[0m"
GREY   = "\033[90m"
WHITE  = "\033[97m"
YELLOW = "\033[93m"

LABELS = {
    "CAPTCHA":  "\033[95m",
    "VERIFIED": "\033[92m",
    "UNLOCKED": "\033[96m",
    "SUCCESS":  "\033[92m",
    "FAILED":   "\033[91m",
    "WAITING":  "\033[90m",
    "PENDING":  "\033[90m",
    "ERROR":    "\033[91m",
    "INPUT":    "\033[93m",
    "INFO":     "\033[94m",
    "SOLVING":  "\033[95m",
}

GRAD = ["\033[38;5;22m", "\033[38;5;28m", "\033[38;5;34m", "\033[38;5;40m", "\033[38;5;46m"]


def ts():
    return f"{GREY}{datetime.now().strftime('%H:%M:%S')}{R}"


def log(label: str, message: str, detail: str = None):
    color = LABELS.get(label, WHITE)
    det = f" {GREY}[{detail}]{R}" if detail else ""
    print(f"{ts()} {color}{label}{R} > {WHITE}{message}{R}{det}")


def gradient_token(token: str) -> str:
    out = ""
    step = max(1, len(token) // len(GRAD))
    for i, ch in enumerate(token):
        out += GRAD[min(i // step, len(GRAD) - 1)] + ch
    return out + R


def overwrite(text: str):
    print(f"\033[1A\033[2K{text}", end="\r\n", flush=True)