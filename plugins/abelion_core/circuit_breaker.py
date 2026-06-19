import time
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class State(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = State.CLOSED
        self.failures = 0
        self.last_failure_time = 0

    def allow_request(self):
        if self.state == State.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = State.HALF_OPEN
                return True
            return False
        return True

    def record_success(self):
        self.failures = 0
        self.state = State.CLOSED

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            self.state = State.OPEN
            logger.error(f"[abelion_orchestrator] Circuit breaker OPENED due to {self.failures} failures.")

_breakers = {}

def get_breaker(name):
    if name not in _breakers:
        _breakers[name] = CircuitBreaker()
    return _breakers[name]
