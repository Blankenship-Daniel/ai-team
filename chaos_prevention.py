#!/usr/bin/env python3
"""
Chaos Prevention Toolkit for Multi-Team AI Orchestration
Implements circuit breakers, bulkheads, and fail-safe mechanisms
"""

import time
import threading
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
from logging_config import setup_logging

logger = setup_logging(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, requests blocked
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before trying again
    success_threshold: int = 3  # Successes to close again
    timeout: float = 30.0  # Operation timeout


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures"""

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info(f"Circuit breaker {self.name} moving to HALF_OPEN")
                else:
                    raise Exception(f"Circuit breaker {self.name} is OPEN")

        try:
            # Execute with timeout
            start_time = time.time()
            result = func(*args, **kwargs)

            # Check if operation took too long
            if time.time() - start_time > self.config.timeout:
                raise TimeoutError(f"Operation timeout: {self.config.timeout}s")

            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True

        time_since_failure = time.time() - self.last_failure_time
        return time_since_failure >= self.config.recovery_timeout

    def _on_success(self):
        """Handle successful operation"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    logger.info(f"Circuit breaker {self.name} CLOSED")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0  # Reset failure count on success

    def _on_failure(self):
        """Handle failed operation"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.CLOSED and self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} OPENED after {self.failure_count} failures")
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker {self.name} reopened during testing")


class BulkheadIsolation:
    """Isolate resources to prevent cascading failures"""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.active_operations = 0
        self._lock = threading.Semaphore(max_concurrent)
        self._monitor_lock = threading.Lock()

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute operation with resource isolation"""
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            raise Exception("Resource pool exhausted - operation rejected")

        try:
            with self._monitor_lock:
                self.active_operations += 1

            logger.debug(f"Executing operation (active: {self.active_operations})")
            return func(*args, **kwargs)

        finally:
            with self._monitor_lock:
                self.active_operations -= 1
            self._lock.release()


class RateLimiter:
    """Rate limiting to prevent resource exhaustion"""

    def __init__(self, max_calls: int, time_window: int = 60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
        self._lock = threading.Lock()

    def allow_request(self) -> bool:
        """Check if request is allowed under rate limit"""
        with self._lock:
            now = time.time()

            # Remove old calls outside window
            self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]

            if len(self.calls) >= self.max_calls:
                return False

            self.calls.append(now)
            return True


class ChaosPreventionManager:
    """Central manager for chaos prevention mechanisms"""

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkheads: Dict[str, BulkheadIsolation] = {}
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.health_checks: Dict[str, Callable] = {}
        self._monitoring_active = False
        self._monitor_thread = None

    def create_circuit_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Create a new circuit breaker"""
        breaker = CircuitBreaker(name, config)
        self.circuit_breakers[name] = breaker
        logger.info(f"Created circuit breaker: {name}")
        return breaker

    def create_bulkhead(self, name: str, max_concurrent: int = 3) -> BulkheadIsolation:
        """Create a new bulkhead isolation"""
        bulkhead = BulkheadIsolation(max_concurrent)
        self.bulkheads[name] = bulkhead
        logger.info(f"Created bulkhead: {name} (max_concurrent: {max_concurrent})")
        return bulkhead

    def create_rate_limiter(self, name: str, max_calls: int, time_window: int = 60) -> RateLimiter:
        """Create a new rate limiter"""
        limiter = RateLimiter(max_calls, time_window)
        self.rate_limiters[name] = limiter
        logger.info(f"Created rate limiter: {name} ({max_calls} calls per {time_window}s)")
        return limiter

    def register_health_check(self, name: str, health_func: Callable[[], bool]):
        """Register a health check function"""
        self.health_checks[name] = health_func
        logger.info(f"Registered health check: {name}")

    def protected_execution(self, operation_name: str, func: Callable, *args, **kwargs) -> Any:
        """Execute operation with full chaos protection"""
        # Rate limiting
        if operation_name in self.rate_limiters:
            if not self.rate_limiters[operation_name].allow_request():
                raise Exception(f"Rate limit exceeded for {operation_name}")

        # Circuit breaker protection
        if operation_name in self.circuit_breakers:
            return self.circuit_breakers[operation_name].call(func, *args, **kwargs)

        # Bulkhead isolation
        if operation_name in self.bulkheads:
            return self.bulkheads[operation_name].execute(func, *args, **kwargs)

        # Fallback to direct execution
        return func(*args, **kwargs)

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system protection status"""
        status = {
            "timestamp": datetime.now().isoformat(),
            "circuit_breakers": {},
            "bulkheads": {},
            "rate_limiters": {},
            "health_checks": {},
        }

        # Circuit breaker status
        for name, breaker in self.circuit_breakers.items():
            status["circuit_breakers"][name] = {
                "state": breaker.state.value,
                "failure_count": breaker.failure_count,
                "success_count": breaker.success_count,
            }

        # Bulkhead status
        for name, bulkhead in self.bulkheads.items():
            status["bulkheads"][name] = {
                "active_operations": bulkhead.active_operations,
                "max_concurrent": bulkhead.max_concurrent,
            }

        # Rate limiter status
        for name, limiter in self.rate_limiters.items():
            with limiter._lock:
                status["rate_limiters"][name] = {
                    "current_calls": len(limiter.calls),
                    "max_calls": limiter.max_calls,
                    "time_window": limiter.time_window,
                }

        # Health check status
        for name, health_func in self.health_checks.items():
            try:
                is_healthy = health_func()
                status["health_checks"][name] = {"healthy": is_healthy, "error": None}
            except Exception as e:
                status["health_checks"][name] = {"healthy": False, "error": str(e)}

        return status

    def start_monitoring(self):
        """Start background monitoring of chaos prevention mechanisms"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Chaos prevention monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("Chaos prevention monitoring stopped")

    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                status = self.get_system_status()

                # Log warnings for unhealthy states
                for name, breaker_status in status["circuit_breakers"].items():
                    if breaker_status["state"] != "closed":
                        logger.warning(f"Circuit breaker {name} is {breaker_status['state']}")

                for name, health_status in status["health_checks"].items():
                    if not health_status["healthy"]:
                        logger.warning(f"Health check {name} failed: {health_status.get('error')}")

                time.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                time.sleep(60)


# Pre-configured chaos prevention for common operations
def setup_team_coordination_protection() -> ChaosPreventionManager:
    """Setup chaos prevention for team coordination operations"""
    manager = ChaosPreventionManager()

    # Circuit breakers for critical operations
    team_registration_config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=30, success_threshold=2)
    manager.create_circuit_breaker("team_registration", team_registration_config)

    context_sync_config = CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60, success_threshold=3)
    manager.create_circuit_breaker("context_sync", context_sync_config)

    # Bulkheads for resource-intensive operations
    manager.create_bulkhead("tmux_operations", max_concurrent=2)
    manager.create_bulkhead("file_operations", max_concurrent=3)

    # Rate limiters
    manager.create_rate_limiter("team_messages", max_calls=100, time_window=60)
    manager.create_rate_limiter("resource_reservations", max_calls=50, time_window=60)

    # Health checks
    def tmux_health_check() -> bool:
        # import subprocess

        try:
            result = subprocess.run(["tmux", "list-sessions"], capture_output=True, timeout=5)
            return result.returncode == 0
        except:
            return False

    def disk_space_check() -> bool:
        import shutil

        try:
            _, _, free = shutil.disk_usage(".")
            return free > 1024 * 1024 * 100  # 100MB free
        except:
            return False

    manager.register_health_check("tmux_available", tmux_health_check)
    manager.register_health_check("disk_space", disk_space_check)

    manager.start_monitoring()
    return manager


# Singleton instance
_chaos_manager: Optional[ChaosPreventionManager] = None


def get_chaos_manager() -> ChaosPreventionManager:
    """Get the global chaos prevention manager"""
    global _chaos_manager
    if _chaos_manager is None:
        _chaos_manager = setup_team_coordination_protection()
    return _chaos_manager


# Decorator for protected execution
def chaos_protected(operation_name: str):
    """Decorator to add chaos protection to functions"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_chaos_manager()
            return manager.protected_execution(operation_name, func, *args, **kwargs)

        return wrapper

    return decorator


if __name__ == "__main__":
    # Demo the chaos prevention system
    manager = setup_team_coordination_protection()

    @chaos_protected("demo_operation")
    def risky_operation():
        import random

        if random.random() < 0.3:  # 30% failure rate
            raise Exception("Simulated failure")
        return "Success!"

    # Test the protection
    for i in range(10):
        try:
            result = risky_operation()
            print(f"Attempt {i+1}: {result}")
        except Exception as e:
            print(f"Attempt {i+1}: Failed - {e}")
        time.sleep(1)

    # Show final status
    status = manager.get_system_status()
    print("\nFinal System Status:")
    print(json.dumps(status, indent=2))
