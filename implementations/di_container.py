#!/usr/bin/env python3
"""
Dependency Injection Container
Simple but effective DI container following SOLID principles
"""

from typing import Dict, Any, Type, TypeVar, Optional
from interfaces import IDependencyContainer

T = TypeVar("T")


class DependencyContainer:
    """
    Simple dependency injection container implementation.

    Supports both transient and singleton registrations.
    Follows the IDependencyContainer protocol.
    """

    def __init__(self):
        """Initialize empty container"""
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Any] = {}

    def register(self, interface_type: Type[T], implementation: Any) -> None:
        """
        Register transient implementation for interface.

        Args:
            interface_type: The interface/protocol type
            implementation: The implementation class (not instance)
        """
        self._services[interface_type] = implementation

    def register_singleton(self, interface_type: Type[T], implementation: Any) -> None:
        """
        Register singleton implementation for interface.

        Args:
            interface_type: The interface/protocol type
            implementation: Either an instance or a class to instantiate once
        """
        # If it's a class, we'll instantiate on first resolve
        # If it's an instance, store directly
        if isinstance(implementation, type):
            # It's a class, store for lazy instantiation
            self._factories[interface_type] = implementation
        else:
            # It's an instance, store directly
            self._singletons[interface_type] = implementation

    def resolve(self, interface_type: Type[T]) -> T:
        """
        Resolve implementation for interface.

        Args:
            interface_type: The interface/protocol type to resolve

        Returns:
            Implementation instance

        Raises:
            ValueError: If no implementation registered
        """
        # Check singletons first
        if interface_type in self._singletons:
            return self._singletons[interface_type]

        # Check if we need to create a singleton
        if interface_type in self._factories:
            instance = self._factories[interface_type]()
            self._singletons[interface_type] = instance
            del self._factories[interface_type]
            return instance

        # Check transient services
        if interface_type in self._services:
            implementation_class = self._services[interface_type]
            return implementation_class()

        raise ValueError(f"No implementation registered for {interface_type.__name__}")

    def is_registered(self, interface_type: Type) -> bool:
        """Check if interface has implementation registered"""
        return (
            interface_type in self._services or interface_type in self._singletons or interface_type in self._factories
        )
