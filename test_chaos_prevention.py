#!/usr/bin/env python3
"""
Comprehensive test suite for chaos_prevention.py
Targets 100% code coverage including all edge cases and error paths
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta

from chaos_prevention import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreaker,
    BulkheadConfig,
    Bulkhead,
    RetryConfig,
    RetryPolicy,
    ChaosMonitor,
    TeamIsolation,
    FailSafe,
    RateLimiter,
    BackPressureManager,
    HealthCheck
)


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass"""
    
    def test_default_config(self):
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.timeout == 60
        assert config.half_open_max_calls == 3
        
    def test_custom_config(self):
        config = CircuitBreakerConfig(failure_threshold=10, timeout=120, half_open_max_calls=5)
        assert config.failure_threshold == 10
        assert config.timeout == 120
        assert config.half_open_max_calls == 5


class TestCircuitBreaker:
    """Test CircuitBreaker with all states and transitions"""
    
    def test_initial_state(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        
    def test_successful_call(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        
        def success_func():
            return "success"
            
        result = cb.call(success_func)
        assert result == "success"
        assert cb.failure_count == 0
        assert cb.state == CircuitState.CLOSED
        
    def test_failed_call_increments_counter(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        
        def failing_func():
            raise ValueError("test error")
            
        with pytest.raises(ValueError):
            cb.call(failing_func)
            
        assert cb.failure_count == 1
        assert cb.state == CircuitState.CLOSED
        
    def test_circuit_opens_after_threshold(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=2))
        
        def failing_func():
            raise ValueError("test error")
            
        # First failure
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitState.CLOSED
        
        # Second failure - opens circuit
        with pytest.raises(ValueError):
            cb.call(failing_func)
        assert cb.state == CircuitState.OPEN
        assert cb.last_failure_time is not None
        
    def test_open_circuit_blocks_calls(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1))
        cb.state = CircuitState.OPEN
        cb.last_failure_time = datetime.now()
        
        def func():
            return "should not execute"
            
        with pytest.raises(Exception) as exc_info:
            cb.call(func)
        assert "Circuit breaker is OPEN" in str(exc_info.value)
        
    def test_half_open_transition(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=1, timeout=0.1))
        cb.state = CircuitState.OPEN
        cb.last_failure_time = datetime.now() - timedelta(seconds=1)
        
        def success_func():
            return "success"
            
        # Should transition to HALF_OPEN and allow call
        result = cb.call(success_func)
        assert result == "success"
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.half_open_calls == 1
        
    def test_half_open_to_closed_on_success(self):
        config = CircuitBreakerConfig(failure_threshold=1, timeout=0.1, half_open_max_calls=2)
        cb = CircuitBreaker("test", config)
        cb.state = CircuitState.HALF_OPEN
        cb.half_open_calls = 0
        
        def success_func():
            return "success"
            
        # First successful call
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.half_open_calls == 1
        
        # Second successful call - closes circuit
        cb.call(success_func)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        
    def test_half_open_to_open_on_failure(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        cb.state = CircuitState.HALF_OPEN
        
        def failing_func():
            raise ValueError("test error")
            
        with pytest.raises(ValueError):
            cb.call(failing_func)
            
        assert cb.state == CircuitState.OPEN
        assert cb.last_failure_time is not None
        
    def test_reset(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        cb.state = CircuitState.OPEN
        cb.failure_count = 5
        cb.last_failure_time = datetime.now()
        
        cb.reset()
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None


class TestBulkhead:
    """Test Bulkhead isolation pattern"""
    
    def test_initial_state(self):
        config = BulkheadConfig(max_concurrent=3, max_queue=5, timeout=1)
        bulkhead = Bulkhead("test", config)
        assert bulkhead.active_calls == 0
        assert bulkhead.queue.empty()
        
    def test_acquire_and_release(self):
        config = BulkheadConfig(max_concurrent=2)
        bulkhead = Bulkhead("test", config)
        
        # Acquire permits
        assert bulkhead.acquire() is True
        assert bulkhead.active_calls == 1
        
        assert bulkhead.acquire() is True
        assert bulkhead.active_calls == 2
        
        # Max reached
        assert bulkhead.acquire() is False
        
        # Release and acquire again
        bulkhead.release()
        assert bulkhead.active_calls == 1
        assert bulkhead.acquire() is True
        
    def test_execute_with_bulkhead(self):
        config = BulkheadConfig(max_concurrent=1)
        bulkhead = Bulkhead("test", config)
        
        def func():
            return "result"
            
        result = bulkhead.execute(func)
        assert result == "result"
        assert bulkhead.active_calls == 0  # Released after execution
        
    def test_execute_with_exception(self):
        config = BulkheadConfig(max_concurrent=1)
        bulkhead = Bulkhead("test", config)
        
        def failing_func():
            raise ValueError("test error")
            
        with pytest.raises(ValueError):
            bulkhead.execute(failing_func)
            
        assert bulkhead.active_calls == 0  # Released even on exception
        
    def test_bulkhead_rejection(self):
        config = BulkheadConfig(max_concurrent=1)
        bulkhead = Bulkhead("test", config)
        bulkhead.active_calls = 1  # Simulate full bulkhead
        
        def func():
            return "should not execute"
            
        with pytest.raises(Exception) as exc_info:
            bulkhead.execute(func)
        assert "Bulkhead test is full" in str(exc_info.value)


class TestRetryPolicy:
    """Test RetryPolicy with various strategies"""
    
    def test_exponential_backoff(self):
        config = RetryConfig(max_retries=3, backoff_strategy="exponential", base_delay=1)
        policy = RetryPolicy(config)
        
        mock_func = Mock(side_effect=[ValueError, ValueError, "success"])
        result = policy.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
        
    def test_linear_backoff(self):
        config = RetryConfig(max_retries=2, backoff_strategy="linear", base_delay=0.1)
        policy = RetryPolicy(config)
        
        mock_func = Mock(side_effect=[ValueError, "success"])
        result = policy.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 2
        
    def test_fixed_backoff(self):
        config = RetryConfig(max_retries=2, backoff_strategy="fixed", base_delay=0.01)
        policy = RetryPolicy(config)
        
        mock_func = Mock(side_effect=[ValueError, "success"])
        result = policy.execute(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 2
        
    def test_max_retries_exceeded(self):
        config = RetryConfig(max_retries=2, base_delay=0.01)
        policy = RetryPolicy(config)
        
        mock_func = Mock(side_effect=ValueError("persistent error"))
        
        with pytest.raises(ValueError):
            policy.execute(mock_func)
            
        assert mock_func.call_count == 3  # Initial + 2 retries
        
    def test_immediate_success(self):
        config = RetryConfig(max_retries=3)
        policy = RetryPolicy(config)
        
        mock_func = Mock(return_value="immediate success")
        result = policy.execute(mock_func)
        
        assert result == "immediate success"
        assert mock_func.call_count == 1


class TestChaosMonitor:
    """Test ChaosMonitor system monitoring"""
    
    def test_record_event(self):
        monitor = ChaosMonitor()
        
        monitor.record_event("test_event", {"key": "value"})
        assert len(monitor.events) == 1
        assert monitor.events[0]["type"] == "test_event"
        assert monitor.events[0]["data"]["key"] == "value"
        assert "timestamp" in monitor.events[0]
        
    def test_get_metrics(self):
        monitor = ChaosMonitor()
        
        monitor.record_event("error", {"message": "test error"})
        monitor.record_event("success", {"result": "ok"})
        monitor.record_event("error", {"message": "another error"})
        
        metrics = monitor.get_metrics()
        assert metrics["error"] == 2
        assert metrics["success"] == 1
        
    def test_clear_old_events(self):
        monitor = ChaosMonitor()
        
        # Add old event
        old_event = {
            "type": "old",
            "timestamp": datetime.now() - timedelta(hours=2),
            "data": {}
        }
        monitor.events.append(old_event)
        
        # Add recent event
        monitor.record_event("recent", {})
        
        monitor.clear_old_events(max_age_hours=1)
        assert len(monitor.events) == 1
        assert monitor.events[0]["type"] == "recent"


class TestTeamIsolation:
    """Test TeamIsolation for multi-team management"""
    
    def test_register_team(self):
        isolation = TeamIsolation()
        
        isolation.register_team("team1", max_resources=10)
        assert "team1" in isolation.teams
        assert isolation.teams["team1"]["max_resources"] == 10
        assert isolation.teams["team1"]["current_resources"] == 0
        
    def test_allocate_resources(self):
        isolation = TeamIsolation()
        isolation.register_team("team1", max_resources=5)
        
        assert isolation.allocate_resources("team1", 3) is True
        assert isolation.teams["team1"]["current_resources"] == 3
        
        # Try to exceed limit
        assert isolation.allocate_resources("team1", 3) is False
        assert isolation.teams["team1"]["current_resources"] == 3
        
    def test_release_resources(self):
        isolation = TeamIsolation()
        isolation.register_team("team1", max_resources=5)
        isolation.allocate_resources("team1", 3)
        
        isolation.release_resources("team1", 2)
        assert isolation.teams["team1"]["current_resources"] == 1
        
        # Can't release more than allocated
        isolation.release_resources("team1", 5)
        assert isolation.teams["team1"]["current_resources"] == 0
        
    def test_unregistered_team(self):
        isolation = TeamIsolation()
        
        assert isolation.allocate_resources("unknown", 1) is False
        isolation.release_resources("unknown", 1)  # Should not crash


class TestFailSafe:
    """Test FailSafe wrapper"""
    
    def test_successful_execution(self):
        failsafe = FailSafe()
        
        def func():
            return "success"
            
        result = failsafe.execute(func, fallback=lambda: "fallback")
        assert result == "success"
        
    def test_fallback_on_exception(self):
        failsafe = FailSafe()
        
        def failing_func():
            raise ValueError("error")
            
        def fallback_func():
            return "fallback result"
            
        result = failsafe.execute(failing_func, fallback=fallback_func)
        assert result == "fallback result"
        
    def test_default_fallback(self):
        failsafe = FailSafe()
        
        def failing_func():
            raise ValueError("error")
            
        result = failsafe.execute(failing_func, default="default value")
        assert result == "default value"
        
    def test_no_fallback_raises(self):
        failsafe = FailSafe()
        
        def failing_func():
            raise ValueError("error")
            
        with pytest.raises(ValueError):
            failsafe.execute(failing_func)


class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    def test_allow_within_limit(self):
        limiter = RateLimiter(max_calls=2, window_seconds=1)
        
        assert limiter.allow() is True
        assert limiter.allow() is True
        assert limiter.allow() is False  # Exceeds limit
        
    def test_window_reset(self):
        limiter = RateLimiter(max_calls=1, window_seconds=0.1)
        
        assert limiter.allow() is True
        assert limiter.allow() is False
        
        time.sleep(0.15)  # Wait for window to reset
        assert limiter.allow() is True
        
    def test_execute_with_rate_limit(self):
        limiter = RateLimiter(max_calls=1, window_seconds=1)
        
        def func():
            return "result"
            
        result = limiter.execute(func)
        assert result == "result"
        
        with pytest.raises(Exception) as exc_info:
            limiter.execute(func)
        assert "Rate limit exceeded" in str(exc_info.value)


class TestBackPressureManager:
    """Test BackPressureManager for load management"""
    
    def test_initial_state(self):
        manager = BackPressureManager(threshold=5)
        assert manager.is_overloaded() is False
        
    def test_add_and_remove_load(self):
        manager = BackPressureManager(threshold=3)
        
        manager.add_load(2)
        assert manager.is_overloaded() is False
        
        manager.add_load(2)
        assert manager.is_overloaded() is True
        
        manager.remove_load(2)
        assert manager.is_overloaded() is False
        
    def test_execute_under_pressure(self):
        manager = BackPressureManager(threshold=2)
        
        def func():
            return "result"
            
        # Normal execution
        result = manager.execute(func)
        assert result == "result"
        
        # Simulate overload
        manager.current_load = 3
        with pytest.raises(Exception) as exc_info:
            manager.execute(func)
        assert "System overloaded" in str(exc_info.value)
        
    def test_wait_for_capacity(self):
        manager = BackPressureManager(threshold=1)
        manager.current_load = 2
        
        def reduce_load():
            time.sleep(0.1)
            manager.current_load = 0
            
        thread = threading.Thread(target=reduce_load)
        thread.start()
        
        manager.wait_for_capacity(timeout=1)
        assert manager.is_overloaded() is False
        thread.join()


class TestHealthCheck:
    """Test HealthCheck monitoring"""
    
    def test_healthy_check(self):
        health_check = HealthCheck()
        
        def healthy_func():
            return True
            
        health_check.register_check("service1", healthy_func)
        status = health_check.check_all()
        
        assert status["healthy"] is True
        assert status["checks"]["service1"] is True
        
    def test_unhealthy_check(self):
        health_check = HealthCheck()
        
        def unhealthy_func():
            return False
            
        health_check.register_check("service1", unhealthy_func)
        status = health_check.check_all()
        
        assert status["healthy"] is False
        assert status["checks"]["service1"] is False
        
    def test_exception_in_check(self):
        health_check = HealthCheck()
        
        def failing_func():
            raise ValueError("check failed")
            
        health_check.register_check("service1", failing_func)
        status = health_check.check_all()
        
        assert status["healthy"] is False
        assert status["checks"]["service1"] is False
        
    def test_mixed_health_status(self):
        health_check = HealthCheck()
        
        health_check.register_check("healthy", lambda: True)
        health_check.register_check("unhealthy", lambda: False)
        
        status = health_check.check_all()
        assert status["healthy"] is False
        assert status["checks"]["healthy"] is True
        assert status["checks"]["unhealthy"] is False


class TestIntegration:
    """Integration tests for chaos prevention components"""
    
    def test_circuit_breaker_with_retry(self):
        """Test circuit breaker working with retry policy"""
        cb = CircuitBreaker("test", CircuitBreakerConfig(failure_threshold=3))
        retry = RetryPolicy(RetryConfig(max_retries=2, base_delay=0.01))
        
        call_count = 0
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("flaky error")
            return "success"
            
        # Retry should handle the flaky function
        result = retry.execute(lambda: cb.call(flaky_func))
        assert result == "success"
        assert cb.failure_count == 0  # Successful after retries
        
    def test_bulkhead_with_failsafe(self):
        """Test bulkhead isolation with failsafe"""
        bulkhead = Bulkhead("test", BulkheadConfig(max_concurrent=1))
        failsafe = FailSafe()
        
        # Fill the bulkhead
        bulkhead.active_calls = 1
        
        def func():
            return bulkhead.execute(lambda: "result")
            
        # Failsafe should handle bulkhead rejection
        result = failsafe.execute(func, default="fallback")
        assert result == "fallback"
        
    def test_rate_limiter_with_backpressure(self):
        """Test rate limiter with backpressure management"""
        limiter = RateLimiter(max_calls=2, window_seconds=1)
        manager = BackPressureManager(threshold=3)
        
        def func():
            return "result"
            
        # Should work within limits
        for _ in range(2):
            result = limiter.execute(lambda: manager.execute(func))
            assert result == "result"
            
        # Should hit rate limit
        with pytest.raises(Exception):
            limiter.execute(lambda: manager.execute(func))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=chaos_prevention", "--cov-report=term-missing"])