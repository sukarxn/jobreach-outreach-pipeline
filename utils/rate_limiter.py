import time
import random
from utils.logger import log


def random_sleep(min_seconds: float = 2.0, max_seconds: float = 5.0):
    """Sleep a random duration between min and max seconds."""
    delay = random.uniform(min_seconds, max_seconds)
    log.debug(f"Rate limit sleep: {delay:.2f}s")
    time.sleep(delay)


def check_cap(current_count: int, max_count: int) -> bool:
    """Return True if still under cap, False if cap reached."""
    if current_count >= max_count:
        log.warning(f"Daily cap reached: {current_count}/{max_count} — stopping.")
        return False
    return True
