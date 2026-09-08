import os
from pathlib import Path

from dotenv import load_dotenv


ROOT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(ROOT_DIR / ".env")


def get_int_setting(name: str, default: int) -> int:
    value = os.getenv(name)

    if value is None:
        return default

    return int(value)


def get_bool_setting(name: str, default: bool) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in {
        "1",
        "true",
        "yes",
        "on"
    }


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

OPENAI_MODEL = os.getenv(
    "OPENAI_MODEL",
    "gpt-5.6-sol"
)

HEADLESS = get_bool_setting(
    "HEADLESS",
    True
)

MAX_CONCURRENT_SITES = get_int_setting(
    "MAX_CONCURRENT_SITES",
    4
)

MAX_EXPLORATION_STEPS = get_int_setting(
    "MAX_EXPLORATION_STEPS",
    6
)

NAVIGATION_TIMEOUT_MS = get_int_setting(
    "NAVIGATION_TIMEOUT_MS",
    15_000
)

ACTION_TIMEOUT_MS = get_int_setting(
    "ACTION_TIMEOUT_MS",
    5_000
)

PAGE_SETTLE_TIME_MS = get_int_setting(
    "PAGE_SETTLE_TIME_MS",
    1_200
)

MAX_PAGE_TEXT_CHARS = 18_000

MAX_MODEL_PAGE_CHARS = 6_000

MAX_HTML_CHARS = 250_000

TARGET_FILE = ROOT_DIR / "data" / "targets.txt"

OUTPUT_FILE = ROOT_DIR / "output" / "results.json"

SCREENSHOT_DIR = ROOT_DIR / "output" / "screenshots"