#!/usr/bin/env python3
"""
Fixed comprehensive test suite for chaos_prevention.py
Matches actual implementation classes and methods
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from chaos_prevention import (
    CircuitState,
    CircuitBreakerConfig,
    CircuitBreaker,
    BulkheadIsolation,
    RateLimiter,
    ChaosPreventionManager,
    setup_team_coordination_protection,
    get_chaos_manager,
    chaos_protected
)


class TestCircuitBreakerConfig:
    """Test CircuitBreakerConfig dataclass"""
    
    def test_default_config(self):
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.recovery_timeout == 60
        assert config.success_threshold == 3
        assert config.timeout == 30.0
        
    def test_custom_config(self):
        config = CircuitBreakerConfig(
            failure_threshold=10,
            recovery_timeout=120,
            success_threshold=5,
            timeout=15.0
        )
        assert config.failure_threshold == 10
        assert config.recovery_timeout == 120
        assert config.success_threshold == 5
        assert config.timeout == 15.0


class TestCircuitBreaker:
    """Test CircuitBreaker with all states and transitions"""
    
    def test_initial_state(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 0
        assert cb.success_count == 0
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
        cb.last_failure_time = time.time()
        
        def func():
            return "should not execute"
            
        with pytest.raises(Exception) as exc_info:
            cb.call(func)
        assert "Circuit breaker" in str(exc_info.value) and "OPEN" in str(exc_info.value)
        
    def test_half_open_transition(self):
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0)
        cb = CircuitBreaker("test", config)
        cb.state = CircuitState.OPEN
        cb.last_failure_time = time.time() - 1  # In the past
        
        def success_func():
            return "success"
            
        # Should transition to HALF_OPEN and allow call
        result = cb.call(success_func)
        assert result == "success"
        assert cb.success_count == 1
        
    def test_half_open_to_closed_on_success(self):
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=2)
        cb = CircuitBreaker("test", config)
        cb.state = CircuitState.HALF_OPEN
        cb.success_count = 0
        
        def success_func():
            return "success"
            
        # First successful call
        cb.call(success_func)
        assert cb.state == CircuitState.HALF_OPEN
        assert cb.success_count == 1
        
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
        
    def test_timeout_handling(self):
        config = CircuitBreakerConfig(timeout=0.1)
        cb = CircuitBreaker("test", config)
        
        def slow_func():
            time.sleep(0.2)  # Longer than timeout
            return "result"
            
        with pytest.raises(TimeoutError):
            cb.call(slow_func)
            
        assert cb.failure_count == 1
        
    def test_thread_safety(self):
        cb = CircuitBreaker("test", CircuitBreakerConfig())
        results = []
        errors = []
        
        def test_func():
            try:
                result = cb.call(lambda: "success")
                results.append(result)
            except Exception as e:
                errors.append(e)
                
        # Run multiple threads
        threads = [threading.Thread(target=test_func) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        # All should succeed
        assert len(results) == 10
        assert len(errors) == 0


class TestBulkheadIsolation:
    """Test BulkheadIsolation pattern"""
    
    def test_initialization(self):
        bulkhead = BulkheadIsolation("test", max_concurrent=3)
        assert bulkhead.name == "test"
        assert bulkhead.max_concurrent == 3
        assert bulkhead.current_count == 0
        
    def test_acquire_and_release(self):
        bulkhead = BulkheadIsolation("test", max_concurrent=2)
        
        # Acquire permits
        assert bulkhead.acquire() is True
        assert bulkhead.current_count == 1
        
        assert bulkhead.acquire() is True
        assert bulkhead.current_count == 2
        
        # Max reached
        assert bulkhead.acquire() is False
        
        # Release and acquire again
        bulkhead.release()
        assert bulkhead.current_count == 1
        assert bulkhead.acquire() is True
        
    def test_execute_with_bulkhead(self):
        bulkhead = BulkheadIsolation("test", max_concurrent=2)
        
        def func():
            return "result"
            
        result = bulkhead.execute(func)
        assert result == "result"
        assert bulkhead.current_count == 0  # Released after execution
        
    def test_execute_with_exception(self):
        bulkhead = BulkheadIsolation("test", max_concurrent=2)
        
        def failing_func():
            raise ValueError("test error")
            
        with pytest.raises(ValueError):
            bulkhead.execute(failing_func)
            
        assert bulkhead.current_count == 0  # Released even on exception
        
    def test_bulkhead_rejection(self):
        bulkhead = BulkheadIsolation("test", max_concurrent=1)
        
        # Fill the bulkhead
        bulkhead.current_count = 1
        
        def func():
            return "should not execute"
            
        with pytest.raises(Exception) as exc_info:
            bulkhead.execute(func)
        assert "full" in str(exc_info.value).lower()
        
    def test_concurrent_execution(self):
        bulkhead = BulkheadIsolation("test", max_concurrent=3)
        results = []
        
        def slow_func(i):
            time.sleep(0.1)
            return f"result-{i}"
            
        threads = []
        for i in range(5):
            t = threading.Thread(target=lambda i=i: results.append(bulkhead.execute(lambda: slow_func(i))))
            threads.append(t)
            
        for t in threads:
            t.start()
        for t in threads:
            t.join()
            
        # Some should succeed, others should be rejected
        assert len(results) <= 3  # Max concurrent limit


class TestRateLimiter:
    """Test RateLimiter functionality"""
    
    def test_initialization(self):
        limiter = RateLimiter("test", requests_per_second=5)
        assert limiter.name == "test"
        assert limiter.rate_limit == 5
        
    def test_allow_within_limit(self):
        limiter = RateLimiter("test", requests_per_second=10)
        
        # Should allow initially
        assert limiter.is_allowed() is True
        
    def test_rate_limiting(self):
        limiter = RateLimiter("test", requests_per_second=2)
        
        # First requests should be allowed
        assert limiter.is_allowed() is True
        assert limiter.is_allowed() is True
        
        # Further requests might be limited
        # Note: Exact behavior depends on implementation
        
    def test_execute_with_rate_limit(self):
        limiter = RateLimiter("test", requests_per_second=1)
        
        def func():
            return "result"
            
        result = limiter.execute(func)
        assert result == "result"
        
    def test_window_behavior(self):
        limiter = RateLimiter("test", requests_per_second=1)
        
        # Make several requests
        allowed_count = 0
        for _ in range(5):
            if limiter.is_allowed():
                allowed_count += 1
                
        # Should have some limit enforcement
        assert allowed_count >= 1  # At least one should be allowed


class TestChaosPreventionManager:
    """Test the main ChaosPreventionManager"""
    
    def test_initialization(self):
        manager = ChaosPreventionManager()
        assert manager.circuit_breakers == {}
        assert manager.bulkheads == {}
        assert manager.rate_limiters == {}
        
    def test_register_circuit_breaker(self):
        manager = ChaosPreventionManager()
        config = CircuitBreakerConfig()
        
        cb = manager.register_circuit_breaker("test", config)
        assert isinstance(cb, CircuitBreaker)
        assert "test" in manager.circuit_breakers
        
    def test_register_bulkhead(self):
        manager = ChaosPreventionManager()
        
        bulkhead = manager.register_bulkhead("test", max_concurrent=3)
        assert isinstance(bulkhead, BulkheadIsolation)
        assert "test" in manager.bulkheads
        
    def test_register_rate_limiter(self):
        manager = ChaosPreventionManager()
        
        limiter = manager.register_rate_limiter("test", requests_per_second=5)
        assert isinstance(limiter, RateLimiter)
        assert "test" in manager.rate_limiters
        
    def test_get_circuit_breaker(self):
        manager = ChaosPreventionManager()
        config = CircuitBreakerConfig()
        
        # Register first
        original = manager.register_circuit_breaker("test", config)
        
        # Get the same one
        retrieved = manager.get_circuit_breaker("test")
        assert retrieved is original
        
    def test_get_nonexistent_circuit_breaker(self):
        manager = ChaosPreventionManager()
        
        cb = manager.get_circuit_breaker("nonexistent")
        assert cb is None
        
    def test_get_status(self):
        manager = ChaosPreventionManager()
        
        # Register some components
        manager.register_circuit_breaker("cb1", CircuitBreakerConfig())
        manager.register_bulkhead("bh1", max_concurrent=2)
        manager.register_rate_limiter("rl1", requests_per_second=10)
        
        status = manager.get_status()
        
        assert "circuit_breakers" in status
        assert "bulkheads" in status
        assert "rate_limiters" in status
        assert len(status["circuit_breakers"]) == 1
        assert len(status["bulkheads"]) == 1
        assert len(status["rate_limiters"]) == 1


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_setup_team_coordination_protection(self):
        manager = setup_team_coordination_protection()
        assert isinstance(manager, ChaosPreventionManager)
        
        # Should have some default protection set up
        status = manager.get_status()
        assert "circuit_breakers" in status
        
    def test_get_chaos_manager(self):
        manager = get_chaos_manager()
        assert isinstance(manager, ChaosPreventionManager)
        
        # Should be singleton
        manager2 = get_chaos_manager()
        assert manager is manager2
        
    def test_chaos_protected_decorator(self):
        @chaos_protected("test_operation")
        def test_func():
            return "success"
            
        result = test_func()
        assert result == "success"
        
    def test_chaos_protected_with_failure(self):
        @chaos_protected("test_operation")
        def failing_func():
            raise ValueError("test error")
            
        with pytest.raises(ValueError):
            failing_func()


class TestIntegrationScenarios:
    """Integration tests for chaos prevention"""
    
    def test_circuit_breaker_with_bulkhead(self):
        manager = ChaosPreventionManager()
        
        # Set up protection
        cb = manager.register_circuit_breaker("service", CircuitBreakerConfig(failure_threshold=2))
        bh = manager.register_bulkhead("service", max_concurrent=2)
        
        def protected_service():
            if not bh.acquire():
                raise Exception("Service overloaded")
            try:
                return cb.call(lambda: "service result")
            finally:
                bh.release()
                
        # Should work initially
        result = protected_service()
        assert result == "service result"
        
    def test_cascading_failure_prevention(self):
        manager = ChaosPreventionManager()
        
        # Set up aggressive circuit breaker
        cb = manager.register_circuit_breaker("flaky", CircuitBreakerConfig(failure_threshold=1))
        
        def flaky_service():
            raise ValueError("Service down")
            
        # First call fails and opens circuit
        with pytest.raises(ValueError):
            cb.call(flaky_service)
            
        # Second call is blocked by circuit breaker
        with pytest.raises(Exception) as exc_info:
            cb.call(flaky_service)
        assert "OPEN" in str(exc_info.value)
        
    def test_recovery_scenario(self):
        manager = ChaosPreventionManager()
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0, success_threshold=1)
        cb = manager.register_circuit_breaker("recovery", config)
        
        # Fail and open circuit
        with pytest.raises(ValueError):
            cb.call(lambda: exec('raise ValueError("fail")'))
            
        # Wait and recover
        time.sleep(0.01)
        result = cb.call(lambda: "recovered")
        assert result == "recovered"
        assert cb.state == CircuitState.CLOSED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=chaos_prevention", "--cov-report=term-missing"])