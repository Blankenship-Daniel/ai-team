#!/usr/bin/env python3
"""
Secure Context Injector - Bulletproof shell escaping for context injection
Architectural approach to preventing injection vulnerabilities in agent briefings
"""

import shlex
import html
import json
import re
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from logging_config import setup_logging

logger = setup_logging(__name__)


class EscapingLevel(Enum):
    """Security levels for context escaping"""

    MINIMAL = "minimal"  # Basic shell escaping only
    STANDARD = "standard"  # Shell + HTML escaping
    PARANOID = "paranoid"  # Full multi-layer escaping + validation


class SecurityContext(Enum):
    """Different security contexts for escaped content"""

    SHELL_COMMAND = "shell_command"
    TMUX_MESSAGE = "tmux_message"
    MARKDOWN_TEXT = "markdown_text"
    JSON_VALUE = "json_value"
    AGENT_BRIEFING = "agent_briefing"


@dataclass
class EscapingResult:
    """Result of escaping operation with security metadata"""

    escaped_content: str
    original_length: int
    escaped_length: int
    security_level: EscapingLevel
    security_context: SecurityContext
    potential_threats_found: List[str]
    escaping_applied: List[str]


class SecureContextEscaper:
    """
    Multi-layer security escaping for all context injection scenarios.

    Architecture:
    1. Input validation and threat detection
    2. Context-specific escaping strategies
    3. Multi-layer defense (shell + markup + encoding)
    4. Verification and integrity checking
    """

    # Threat detection patterns
    SHELL_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",  # Shell metacharacters
        r"\$\(",  # Command substitution
        r"`[^`]*`",  # Backtick execution
        r">\s*/dev/",  # Device redirection
        r"curl\s+[^\s]+\s*\|\s*bash",  # Remote execution
        r"rm\s+-rf?\s+/",  # Destructive commands
        r"sudo\s+",  # Privilege escalation
        r"\|\s*sh\b",  # Pipe to shell
        r"eval\s+",  # Dynamic evaluation
    ]

    TMUX_INJECTION_PATTERNS = [
        r"send-keys\s+-t",  # Tmux command injection
        r"new-session\s+",  # Session manipulation
        r"kill-session\s+",  # Session destruction
        r"display-message\s+",  # Message injection
        r"\x1b\[[0-9;]*[a-zA-Z]",  # ANSI escape sequences
    ]

    MARKDOWN_INJECTION_PATTERNS = [
        r"!\[[^\]]*\]\([^)]*\)",  # Image injection
        r"\[[^\]]*\]\([^)]*javascript:",  # JavaScript links
        r"<script[^>]*>",  # Script tags
        r"<iframe[^>]*>",  # Frame injection
    ]

    def __init__(self, security_level: EscapingLevel = EscapingLevel.STANDARD):
        self.security_level = security_level
        self.threat_detector = ThreatDetector()
        self.integrity_verifier = IntegrityVerifier()

    def escape_for_context(
        self, content: str, context: SecurityContext, custom_escaping: Optional[Dict[str, Any]] = None
    ) -> EscapingResult:
        """
        Main escaping entry point with context-aware security.

        Args:
            content: Raw content to escape
            context: Security context (shell, tmux, markdown, etc.)
            custom_escaping: Custom escaping rules for specific use cases

        Returns:
            EscapingResult with escaped content and security metadata
        """
        logger.debug(f"Escaping {len(content)} chars for context {context.value}")

        # 1. Input validation and threat detection
        threats = self.threat_detector.detect_threats(content, context)
        if threats and self.security_level == EscapingLevel.PARANOID:
            raise SecurityException(f"Potential threats detected: {threats}")

        # 2. Context-specific escaping
        escaping_strategy = self._select_escaping_strategy(context)
        escaped_content = escaping_strategy.escape(content, self.security_level)

        # 3. Apply custom escaping rules if provided
        if custom_escaping:
            escaped_content = self._apply_custom_escaping(escaped_content, custom_escaping)

        # 4. Multi-layer defense based on security level
        if self.security_level in [EscapingLevel.STANDARD, EscapingLevel.PARANOID]:
            escaped_content = self._apply_multi_layer_escaping(escaped_content, context)

        # 5. Integrity verification
        if self.security_level == EscapingLevel.PARANOID:
            self.integrity_verifier.verify_escaping_integrity(content, escaped_content, context)

        escaping_applied = escaping_strategy.get_applied_escaping()

        return EscapingResult(
            escaped_content=escaped_content,
            original_length=len(content),
            escaped_length=len(escaped_content),
            security_level=self.security_level,
            security_context=context,
            potential_threats_found=threats,
            escaping_applied=escaping_applied,
        )

    def _select_escaping_strategy(self, context: SecurityContext) -> "EscapingStrategy":
        """Select appropriate escaping strategy for context"""

        strategies = {
            SecurityContext.SHELL_COMMAND: ShellEscapingStrategy(),
            SecurityContext.TMUX_MESSAGE: TmuxEscapingStrategy(),
            SecurityContext.MARKDOWN_TEXT: MarkdownEscapingStrategy(),
            SecurityContext.JSON_VALUE: JsonEscapingStrategy(),
            SecurityContext.AGENT_BRIEFING: AgentBriefingEscapingStrategy(),
        }

        return strategies.get(context, DefaultEscapingStrategy())

    def _apply_multi_layer_escaping(self, content: str, context: SecurityContext) -> str:
        """Apply multiple layers of escaping for defense in depth"""

        # Layer 1: Basic shell escaping (always applied)
        escaped = shlex.quote(content) if not content.startswith("'") else content

        # Layer 2: HTML entity encoding for markup contexts
        if context in [SecurityContext.MARKDOWN_TEXT, SecurityContext.AGENT_BRIEFING]:
            escaped = html.escape(escaped, quote=True)

        # Layer 3: Unicode normalization to prevent bypass attempts
        if self.security_level == EscapingLevel.PARANOID:
            import unicodedata

            escaped = unicodedata.normalize("NFKC", escaped)

        return escaped

    def _apply_custom_escaping(self, content: str, custom_rules: Dict[str, Any]) -> str:
        """Apply custom escaping rules for specific scenarios"""

        escaped = content

        for rule_name, rule_config in custom_rules.items():
            if rule_name == "path_normalization":
                escaped = str(Path(escaped).resolve())
            elif rule_name == "regex_replacement":
                pattern = rule_config.get("pattern")
                replacement = rule_config.get("replacement", "")
                escaped = re.sub(pattern, replacement, escaped)
            elif rule_name == "length_limit":
                max_length = rule_config.get("max_length", 1000)
                escaped = escaped[:max_length]

        return escaped


class EscapingStrategy:
    """Base class for context-specific escaping strategies"""

    def __init__(self):
        self.applied_escaping = []

    def escape(self, content: str, security_level: EscapingLevel) -> str:
        raise NotImplementedError

    def get_applied_escaping(self) -> List[str]:
        return self.applied_escaping.copy()


class ShellEscapingStrategy(EscapingStrategy):
    """Escaping for shell command contexts"""

    def escape(self, content: str, security_level: EscapingLevel) -> str:
        self.applied_escaping = []

        # Always use shlex.quote for shell safety
        escaped = shlex.quote(content)
        self.applied_escaping.append("shlex_quote")

        if security_level == EscapingLevel.PARANOID:
            # Additional shell-specific escaping
            escaped = self._escape_shell_metacharacters(escaped)
            self.applied_escaping.append("metacharacter_escaping")

        return escaped

    def _escape_shell_metacharacters(self, content: str) -> str:
        """Additional escaping for shell metacharacters"""
        dangerous_chars = {
            "$": "\\$",
            "`": "\\`",
            "!": "\\!",
            '"': '\\"',
            "\\": "\\\\",
        }

        escaped = content
        for char, replacement in dangerous_chars.items():
            escaped = escaped.replace(char, replacement)

        return escaped


class TmuxEscapingStrategy(EscapingStrategy):
    """Escaping for tmux message contexts"""

    def escape(self, content: str, security_level: EscapingLevel) -> str:
        self.applied_escaping = []

        # Escape tmux-specific control sequences
        escaped = content.replace("\x1b", "\\x1b")  # ANSI escapes
        escaped = escaped.replace("\n", "\\n")  # Newlines
        escaped = escaped.replace("\r", "\\r")  # Carriage returns
        self.applied_escaping.append("tmux_control_sequences")

        # Use shell escaping as base layer
        escaped = shlex.quote(escaped)
        self.applied_escaping.append("shlex_quote")

        if security_level == EscapingLevel.PARANOID:
            # Prevent tmux command injection
            escaped = self._prevent_tmux_injection(escaped)
            self.applied_escaping.append("tmux_injection_prevention")

        return escaped

    def _prevent_tmux_injection(self, content: str) -> str:
        """Prevent tmux command injection patterns"""
        # Replace dangerous tmux command patterns
        dangerous_patterns = [
            (r"send-keys", "send_keys_ESCAPED"),
            (r"new-session", "new_session_ESCAPED"),
            (r"kill-session", "kill_session_ESCAPED"),
        ]

        escaped = content
        for pattern, replacement in dangerous_patterns:
            escaped = re.sub(pattern, replacement, escaped, flags=re.IGNORECASE)

        return escaped


class AgentBriefingEscapingStrategy(EscapingStrategy):
    """Escaping specifically for agent briefing context injection"""

    def escape(self, content: str, security_level: EscapingLevel) -> str:
        self.applied_escaping = []

        # Agent briefings are markdown-like but need special handling
        escaped = content

        # 1. Escape potential markdown injection
        escaped = self._escape_markdown_injection(escaped)
        self.applied_escaping.append("markdown_injection_prevention")

        # 2. Ensure code blocks are properly escaped
        escaped = self._escape_code_blocks(escaped)
        self.applied_escaping.append("code_block_escaping")

        # 3. Path and environment variable escaping
        escaped = self._escape_environment_variables(escaped)
        self.applied_escaping.append("environment_variable_escaping")

        if security_level == EscapingLevel.PARANOID:
            # 4. Additional briefing-specific protections
            escaped = self._apply_briefing_protections(escaped)
            self.applied_escaping.append("briefing_specific_protections")

        return escaped

    def _escape_markdown_injection(self, content: str) -> str:
        """Prevent markdown injection attacks"""
        # Escape dangerous markdown patterns
        escaped = content.replace("](javascript:", "](BLOCKED_javascript:")
        escaped = escaped.replace("<script", "&lt;script")
        escaped = escaped.replace("<iframe", "&lt;iframe")
        return escaped

    def _escape_code_blocks(self, content: str) -> str:
        """Ensure code blocks in briefings are properly escaped"""
        # Prevent code block escape sequences
        escaped = content.replace("```", "\\`\\`\\`")
        escaped = escaped.replace("~~~", "\\~\\~\\~")
        return escaped

    def _escape_environment_variables(self, content: str) -> str:
        """Escape environment variables and paths safely"""
        # This is critical for lines 164-165 in the vulnerable code

        # If content looks like a path, normalize and escape it
        if "/" in content and len(content) < 500:  # Reasonable path length
            try:
                # Normalize path to prevent traversal
                normalized = str(Path(content).resolve())
                # Shell-escape the normalized path
                escaped = shlex.quote(normalized)
                return escaped
            except (OSError, ValueError):
                # Not a valid path, fall back to general escaping
                pass

        # General environment variable escaping
        escaped = content.replace("$", "\\$")
        escaped = escaped.replace("`", "\\`")
        return escaped

    def _apply_briefing_protections(self, content: str) -> str:
        """Apply additional protections for agent briefings"""
        # Prevent tool injection through briefing
        dangerous_tools = ["rm", "sudo", "curl", "wget", "nc", "telnet"]

        escaped = content
        for tool in dangerous_tools:
            # Replace with safer alternatives or warnings
            pattern = rf"\b{tool}\b"
            replacement = f"[TOOL_BLOCKED:{tool}]"
            escaped = re.sub(pattern, replacement, escaped, flags=re.IGNORECASE)

        return escaped


class ThreatDetector:
    """Detects potential security threats in content before escaping"""

    def detect_threats(self, content: str, context: SecurityContext) -> List[str]:
        """Detect potential security threats in content"""
        threats = []

        # Check for shell injection patterns
        for pattern in SecureContextEscaper.SHELL_INJECTION_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                threats.append(f"shell_injection:{pattern}")

        # Check for tmux injection patterns if in tmux context
        if context == SecurityContext.TMUX_MESSAGE:
            for pattern in SecureContextEscaper.TMUX_INJECTION_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    threats.append(f"tmux_injection:{pattern}")

        # Check for markdown injection patterns
        if context in [SecurityContext.MARKDOWN_TEXT, SecurityContext.AGENT_BRIEFING]:
            for pattern in SecureContextEscaper.MARKDOWN_INJECTION_PATTERNS:
                if re.search(pattern, content, re.IGNORECASE):
                    threats.append(f"markdown_injection:{pattern}")

        return threats


class IntegrityVerifier:
    """Verifies escaping integrity and prevents bypass attempts"""

    def verify_escaping_integrity(self, original: str, escaped: str, context: SecurityContext):
        """Verify that escaping was applied correctly and cannot be bypassed"""

        # Verify length increase (escaped should generally be longer)
        if len(escaped) < len(original):
            logger.warning("Escaped content shorter than original - potential bypass")

        # Verify critical characters are escaped
        dangerous_chars = ["$", "`", ";", "|", "&", "<", ">"]
        for char in dangerous_chars:
            if char in original and char in escaped:
                # Character present in both - verify it's properly escaped
                if not self._is_properly_escaped(char, escaped):
                    raise SecurityException(f"Character '{char}' not properly escaped")

        # Context-specific integrity checks
        if context == SecurityContext.SHELL_COMMAND:
            self._verify_shell_escaping_integrity(original, escaped)
        elif context == SecurityContext.TMUX_MESSAGE:
            self._verify_tmux_escaping_integrity(original, escaped)

    def _is_properly_escaped(self, char: str, content: str) -> bool:
        """Check if a character is properly escaped in content"""
        # Check if character is inside quotes or escaped with backslash
        return (content.startswith("'") and content.endswith("'")) or f"\\{char}" in content

    def _verify_shell_escaping_integrity(self, original: str, escaped: str):
        """Verify shell escaping integrity"""
        # Escaped shell content should be quoted or have backslash escapes
        if not (escaped.startswith("'") or "\\" in escaped):
            raise SecurityException("Shell content not properly escaped")

    def _verify_tmux_escaping_integrity(self, original: str, escaped: str):
        """Verify tmux escaping integrity"""
        # Check that ANSI sequences are escaped
        if "\x1b" in original and "\\x1b" not in escaped:
            raise SecurityException("ANSI sequences not properly escaped for tmux")


class SecurityException(Exception):
    """Exception raised for security-related escaping failures"""

    pass


# Convenience classes for common scenarios
class MarkdownEscapingStrategy(EscapingStrategy):
    def escape(self, content: str, security_level: EscapingLevel) -> str:
        self.applied_escaping = ["markdown_basic"]
        escaped = html.escape(content, quote=True)
        return escaped


class JsonEscapingStrategy(EscapingStrategy):
    def escape(self, content: str, security_level: EscapingLevel) -> str:
        self.applied_escaping = ["json_encode"]
        return json.dumps(content)


class DefaultEscapingStrategy(EscapingStrategy):
    def escape(self, content: str, security_level: EscapingLevel) -> str:
        self.applied_escaping = ["shlex_quote"]
        return shlex.quote(content)


if __name__ == "__main__":
    # Example usage
    escaper = SecureContextEscaper(EscapingLevel.PARANOID)

    # Test dangerous path injection (test data only)
    dangerous_path = "/tmp; rm -rf /"  # nosec B108
    result = escaper.escape_for_context(dangerous_path, SecurityContext.AGENT_BRIEFING)

    print(f"Original: {dangerous_path}")
    print(f"Escaped: {result.escaped_content}")
    print(f"Threats found: {result.potential_threats_found}")
    print(f"Escaping applied: {result.escaping_applied}")
