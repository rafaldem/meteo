#!/usr/bin/env python3
"""
Enhanced Version Management Utility with Comprehensive Logging.

This module provides robust version management capabilities with enterprise-grade
logging, monitoring, and observability features for backend and frontend components.
"""

import argparse
import json
import logging
import logging.handlers
import os
import re
import sys
import time
import traceback
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Any, Union
from uuid import uuid4


class LogLevel(Enum):
    """Enhanced log levels with structured definitions."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogFormat(Enum):
    """Supported log output formats."""
    CONSOLE = "console"
    JSON = "json"
    STRUCTURED = "structured"


@dataclass
class LoggingConfig:
    """Comprehensive logging configuration with security and operational features."""

    # Core configuration
    level: str = "INFO"
    format_type: LogFormat = LogFormat.STRUCTURED
    output_file: Optional[str] = "version_updater.log"
    console_output: bool = True

    # Advanced features
    enable_rotation: bool = True
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_structured_logging: bool = True
    enable_performance_tracking: bool = True

    # Security and compliance
    sanitize_sensitive_data: bool = True
    enable_audit_trail: bool = True

    # Operational settings
    operation_id_enabled: bool = True
    correlation_id_enabled: bool = True

    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create configuration from environment variables."""
        return cls(
            level=os.getenv('LOG_LEVEL', 'INFO').upper(),
            format_type=LogFormat(os.getenv('LOG_FORMAT', 'structured')),
            output_file=os.getenv('LOG_FILE', 'version_updater.log'),
            console_output=os.getenv('LOG_CONSOLE', 'true').lower() == 'true',
            enable_rotation=os.getenv('LOG_ROTATION', 'true').lower() == 'true',
            max_file_size=int(os.getenv('LOG_MAX_SIZE', str(10 * 1024 * 1024))),
            backup_count=int(os.getenv('LOG_BACKUP_COUNT', '5')),
            sanitize_sensitive_data=os.getenv('LOG_SANITIZE', 'true').lower() == 'true',
            enable_audit_trail=os.getenv('LOG_AUDIT', 'true').lower() == 'true'
        )


class StructuredLogger:
    """Enterprise-grade structured logging implementation with security and observability features."""

    def __init__(self, config: LoggingConfig):
        """Initialize the structured logger with comprehensive configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.operation_id = str(uuid4()) if config.operation_id_enabled else None
        self.correlation_id = str(uuid4()) if config.correlation_id_enabled else None

        # Performance tracking
        self._operation_times = {}
        self._call_counts = {}

        self._setup_logging()
        self._log_initialization()

    def _setup_logging(self) -> None:
        """Configure comprehensive logging infrastructure."""
        # Clear existing handlers to prevent duplicates
        self.logger.handlers.clear()
        self.logger.setLevel(getattr(logging, self.config.level))

        # Configure formatters based on output type
        formatters = self._create_formatters()

        # Setup console handler
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.config.level))
            console_handler.setFormatter(formatters['console'])
            self.logger.addHandler(console_handler)

        # Setup file handler with rotation
        if self.config.output_file:
            if self.config.enable_rotation:
                file_handler = logging.handlers.RotatingFileHandler(
                    self.config.output_file,
                    maxBytes=self.config.max_file_size,
                    backupCount=self.config.backup_count,
                    encoding='utf-8'
                )
            else:
                file_handler = logging.FileHandler(
                    self.config.output_file,
                    encoding='utf-8'
                )

            file_handler.setLevel(logging.DEBUG)  # Always capture debug in files
            file_handler.setFormatter(formatters['file'])
            self.logger.addHandler(file_handler)

        # Prevent propagation to root logger
        self.logger.propagate = False

    def _create_formatters(self) -> Dict[str, logging.Formatter]:
        """Create appropriate formatters for different output destinations."""
        formatters = {}

        if self.config.format_type == LogFormat.JSON:
            # JSON formatter for machine processing
            formatters['console'] = JsonFormatter()
            formatters['file'] = JsonFormatter()
        elif self.config.format_type == LogFormat.STRUCTURED:
            # Structured format balancing human and machine readability
            console_format = (
                "%(asctime)s | %(levelname)-8s | %(operation_id)s | "
                "%(module)s.%(funcName)s:%(lineno)d | %(message)s"
            )
            file_format = (
                "%(asctime)s | %(levelname)-8s | %(operation_id)s | %(correlation_id)s | "
                "%(module)s.%(funcName)s:%(lineno)d | %(duration_ms)s | %(message)s"
            )
            formatters['console'] = StructuredFormatter(console_format)
            formatters['file'] = StructuredFormatter(file_format)
        else:
            # Simple console format
            console_format = "%(asctime)s - %(levelname)s - %(message)s"
            file_format = (
                "%(asctime)s - %(levelname)s - %(operation_id)s - "
                "%(module)s.%(funcName)s:%(lineno)d - %(message)s"
            )
            formatters['console'] = logging.Formatter(console_format)
            formatters['file'] = logging.Formatter(file_format)

        return formatters

    def _log_initialization(self) -> None:
        """Log initialization information for operational visibility."""
        self.info(
            "Structured logger initialized",
            extra={
                'operation_id': self.operation_id,
                'correlation_id': self.correlation_id,
                'config': self._sanitize_config(asdict(self.config)),
                'log_level': self.config.level,
                'output_destinations': self._get_output_destinations()
            }
        )

    def _sanitize_config(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize configuration data for logging."""
        if not self.config.sanitize_sensitive_data:
            return config_dict

        # Create a copy and sanitize sensitive fields
        sanitized = config_dict.copy()
        sensitive_fields = ['output_file', 'correlation_id']

        for field in sensitive_fields:
            if field in sanitized and sanitized[field]:
                sanitized[field] = f"***{str(sanitized[field])[-4:]}"

        return sanitized

    def _get_output_destinations(self) -> list:
        """Get list of configured output destinations."""
        destinations = []
        if self.config.console_output:
            destinations.append('console')
        if self.config.output_file:
            destinations.append(f"file:{self.config.output_file}")
        return destinations

    def _create_log_record(self, level: int, message: str, **kwargs) -> Dict[str, Any]:
        """Create comprehensive log record with metadata."""
        extra = kwargs.get('extra', {})

        # Add operation context
        if self.operation_id:
            extra['operation_id'] = self.operation_id
        if self.correlation_id:
            extra['correlation_id'] = self.correlation_id

        # Add performance metrics if enabled
        if self.config.enable_performance_tracking:
            caller_name = extra.get('caller', 'unknown')
            if caller_name in self._operation_times:
                extra['duration_ms'] = f"{self._operation_times[caller_name]:.2f}ms"
            extra['call_count'] = self._call_counts.get(caller_name, 0)

        return extra

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message with enhanced context."""
        extra = self._create_log_record(logging.DEBUG, message, **kwargs)
        self.logger.debug(message, extra=extra)

    def info(self, message: str, **kwargs) -> None:
        """Log info message with enhanced context."""
        extra = self._create_log_record(logging.INFO, message, **kwargs)
        self.logger.info(message, extra=extra)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message with enhanced context."""
        extra = self._create_log_record(logging.WARNING, message, **kwargs)
        self.logger.warning(message, extra=extra)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs) -> None:
        """Log error message with comprehensive exception context."""
        extra = self._create_log_record(logging.ERROR, message, **kwargs)

        if exception:
            extra.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'stack_trace': traceback.format_exc() if sys.exc_info()[0] else None
            })

        self.logger.error(message, extra=extra)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical message with enhanced context."""
        extra = self._create_log_record(logging.CRITICAL, message, **kwargs)
        self.logger.critical(message, extra=extra)

    def audit(self, action: str, resource: str, status: str, **kwargs) -> None:
        """Log audit events for compliance and security monitoring."""
        if not self.config.enable_audit_trail:
            return

        extra = self._create_log_record(logging.INFO, f"AUDIT: {action}", **kwargs)
        extra.update({
            'audit_action': action,
            'audit_resource': resource,
            'audit_status': status,
            'audit_timestamp': time.time()
        })

        self.logger.info(f"AUDIT: {action} on {resource} - {status}", extra=extra)

    @contextmanager
    def performance_tracking(self, operation_name: str):
        """Context manager for tracking operation performance."""
        start_time = time.time()
        self._call_counts[operation_name] = self._call_counts.get(operation_name, 0) + 1

        try:
            self.debug(
                f"Starting operation: {operation_name}",
                extra={'operation_name': operation_name, 'call_count': self._call_counts[operation_name]}
            )
            yield
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self._operation_times[operation_name] = duration
            self.error(
                f"Operation failed: {operation_name}",
                exception=e,
                extra={'operation_name': operation_name, 'duration_ms': f"{duration:.2f}"}
            )
            raise
        else:
            duration = (time.time() - start_time) * 1000
            self._operation_times[operation_name] = duration
            self.info(
                f"Operation completed: {operation_name}",
                extra={'operation_name': operation_name, 'duration_ms': f"{duration:.2f}"}
            )

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for the current session."""
        return {
            'operation_times_ms': self._operation_times,
            'call_counts': self._call_counts,
            'total_operations': len(self._operation_times),
            'session_id': self.operation_id
        }


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured log output."""

    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in log_data and not key.startswith('_'):
                log_data[key] = value

        return json.dumps(log_data, default=str)


class StructuredFormatter(logging.Formatter):
    """Enhanced structured formatter with comprehensive field support."""

    def format(self, record):
        # Ensure required fields exist
        if not hasattr(record, 'operation_id'):
            record.operation_id = 'N/A'
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'N/A'
        if not hasattr(record, 'duration_ms'):
            record.duration_ms = 'N/A'

        return super().format(record)


def enhanced_logging_decorator(operation_name: str = None):
    """Enhanced decorator for comprehensive function logging with performance tracking."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get logger from first argument (self) or create new one
            logger = None
            if args and hasattr(args[0], 'logger'):
                logger = args[0].logger
            else:
                # Fallback to basic logger
                logger = StructuredLogger(LoggingConfig())

            func_name = operation_name or f"{func.__module__}.{func.__name__}"

            with logger.performance_tracking(func_name):
                try:
                    # Log function entry with sanitized parameters
                    logger.debug(
                        f"Entering function: {func_name}",
                        extra={
                            'function_args_count': len(args),
                            'function_kwargs_count': len(kwargs),
                            'caller': func_name
                        }
                    )

                    result = func(*args, **kwargs)

                    # Log successful completion
                    logger.debug(
                        f"Function completed successfully: {func_name}",
                        extra={
                            'caller': func_name,
                            'result_type': type(result).__name__ if result is not None else 'None'
                        }
                    )

                    return result

                except Exception as e:
                    logger.error(
                        f"Function failed: {func_name}",
                        exception=e,
                        extra={'caller': func_name}
                    )
                    raise

        return wrapper
    return decorator


class BumpType(Enum):
    """Type of version bump operation with enhanced metadata."""
    INCREMENT = "increment"
    SET = "set"


class Component(Enum):
    """Version component to bump with validation support."""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"
    OTHER = "other"


@dataclass
class Version:
    """Enhanced version class with comprehensive validation and logging."""
    major: int
    minor: int
    patch: int

    def __post_init__(self):
        """Validate version components."""
        if any(component < 0 for component in [self.major, self.minor, self.patch]):
            raise ValueError(f"Version components must be non-negative: {self}")

    def __str__(self) -> str:
        """String representation of the version."""
        return f"{self.major}.{self.minor}.{self.patch}"

    def to_dict(self) -> Dict[str, int]:
        """Convert version to dictionary for structured logging."""
        return {'major': self.major, 'minor': self.minor, 'patch': self.patch}


@dataclass
class VersionPattern:
    """Enhanced version patterns with validation support."""
    base: str = r'"(\d+)\.(\d+)\.(\d+)"'
    version_py: str = field(init=False)
    pyproject: str = field(init=False)
    setup: str = field(init=False)

    def __post_init__(self):
        """Initialize composite patterns."""
        self.version_py = r'__version__\s*=\s*' + self.base
        self.pyproject = r'version\s*=\s*' + self.base
        self.setup = r'version\s*=\s*' + self.base


@dataclass
class FileInfo:
    """Enhanced file information with metadata and validation."""
    path: Path
    pattern: str
    description: str = ""

    def __post_init__(self):
        """Initialize file metadata."""
        if not self.description:
            self.description = f"Version file: {self.path.name}"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for structured logging."""
        return {
            'path': str(self.path),
            'pattern': self.pattern,
            'description': self.description,
            'exists': self.path.exists()
        }


@dataclass
class VersionConfig:
    """Enhanced configuration with comprehensive validation and logging support."""
    project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent.parent.resolve())
    patterns: VersionPattern = field(default_factory=VersionPattern)

    def __post_init__(self):
        """Initialize comprehensive file configuration."""
        self.files: Dict[str, Dict[str, FileInfo]] = {
            "backend": {
                "version.py": FileInfo(
                    self.project_root / "backend/version.py",
                    self.patterns.version_py,
                    "Backend version definition file"
                ),
                "pyproject.toml": FileInfo(
                    self.project_root / "backend/pyproject.toml",
                    self.patterns.pyproject,
                    "Backend project configuration file"
                ),
            },
            "frontend": {
                "version.py": FileInfo(
                    self.project_root / "frontend/version.py",
                    self.patterns.version_py,
                    "Frontend version definition file"
                ),
                "pyproject.toml": FileInfo(
                    self.project_root / "frontend/pyproject.toml",
                    self.patterns.pyproject,
                    "Frontend project configuration file"
                ),
            },
            "setup": {
                "setup.py": FileInfo(
                    self.project_root / "setup.py",
                    self.patterns.setup,
                    "Main setup configuration file"
                ),
            },
        }


class VersionManager:
    """Enhanced version manager with comprehensive logging and error handling."""

    def __init__(self, logger: StructuredLogger):
        """Initialize with structured logger."""
        self.logger = logger
        self.logger.info("Version manager initialized")

    @enhanced_logging_decorator("parse_version")
    def parse_version(self, version_string: str) -> Version:
        """Parse version string with comprehensive validation and logging."""
        self.logger.debug(
            "Parsing version string",
            extra={'input_version': version_string if not self.logger.config.sanitize_sensitive_data else f"***{version_string[-4:]}"}
        )

        pattern = VersionPattern().base
        match = re.search(pattern, version_string)

        if not match:
            error_msg = f"Invalid version format: {version_string}"
            self.logger.error(error_msg, extra={'pattern_used': pattern})
            raise ValueError(error_msg)

        try:
            major = int(match.group(1))
            minor = int(match.group(2))
            patch = int(match.group(3))

            version = Version(major, minor, patch)

            self.logger.info(
                "Version parsed successfully",
                extra={
                    'parsed_version': version.to_dict(),
                    'original_string': version_string
                }
            )

            return version

        except (ValueError, IndexError) as e:
            error_msg = f"Error parsing version components from '{version_string}'"
            self.logger.error(error_msg, exception=e, extra={'match_groups': match.groups() if match else None})
            raise ValueError(error_msg) from e

    @enhanced_logging_decorator("bump_version")
    def bump_version(
            self,
            version: Version,
            component: Component,
            bump_type: BumpType,
            value: Optional[int] = None,
    ) -> Version:
        """Bump version with comprehensive logging and validation."""
        self.logger.info(
            "Starting version bump operation",
            extra={
                'current_version': version.to_dict(),
                'component': component.value,
                'bump_type': bump_type.value,
                'target_value': value
            }
        )

        original_version = Version(version.major, version.minor, version.patch)
        major, minor, patch = version.major, version.minor, version.patch

        try:
            if bump_type == BumpType.INCREMENT:
                if component == Component.MAJOR:
                    major += 1
                    minor = 0
                    patch = 0
                    self.logger.debug("Incremented major version, reset minor and patch to 0")
                elif component == Component.MINOR:
                    minor += 1
                    patch = 0
                    self.logger.debug("Incremented minor version, reset patch to 0")
                elif component == Component.PATCH:
                    patch += 1
                    self.logger.debug("Incremented patch version")

            elif bump_type == BumpType.SET and value is not None:
                if value < 0:
                    raise ValueError(f"Version component value must be non-negative: {value}")

                if component == Component.MAJOR:
                    major = value
                    self.logger.debug(f"Set major version to {value}")
                elif component == Component.MINOR:
                    minor = value
                    self.logger.debug(f"Set minor version to {value}")
                elif component == Component.PATCH:
                    patch = value
                    self.logger.debug(f"Set patch version to {value}")
            else:
                error_msg = f"Invalid bump operation: {bump_type} with value {value}"
                self.logger.error(error_msg)
                raise ValueError(error_msg)

            new_version = Version(major, minor, patch)

            self.logger.audit(
                action="version_bump",
                resource=f"version:{original_version}",
                status="success",
                extra={
                    'original_version': original_version.to_dict(),
                    'new_version': new_version.to_dict(),
                    'component': component.value,
                    'bump_type': bump_type.value
                }
            )

            return new_version

        except Exception as e:
            self.logger.error(
                "Version bump operation failed",
                exception=e,
                extra={
                    'original_version': original_version.to_dict(),
                    'component': component.value,
                    'bump_type': bump_type.value,
                    'target_value': value
                }
            )
            raise

    @enhanced_logging_decorator("format_version")
    def format_version(self, version: Version) -> str:
        """Format version with logging."""
        formatted = str(version)
        self.logger.debug(
            "Version formatted",
            extra={'version': version.to_dict(), 'formatted_string': formatted}
        )
        return formatted


class FileUpdater:
    """Enhanced file updater with comprehensive logging and error handling."""

    def __init__(self, version_manager: VersionManager, logger: StructuredLogger):
        """Initialize with enhanced dependencies."""
        self.version_manager = version_manager
        self.logger = logger
        self.logger.info("File updater initialized")

    @enhanced_logging_decorator("read_file")
    def _read_file(self, file_path: Path) -> str:
        """Read file with comprehensive logging and error handling."""
        self.logger.debug(
            "Reading file",
            extra={'file_path': str(file_path), 'file_exists': file_path.exists()}
        )

        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File does not exist: {file_path}")

            with file_path.open("r", encoding="utf-8") as file:
                content = file.read()

            self.logger.info(
                "File read successfully",
                extra={
                    'file_path': str(file_path),
                    'content_length': len(content),
                    'line_count': content.count('\n') + 1
                }
            )

            return content

        except (IOError, UnicodeDecodeError) as e:
            error_msg = f"Failed to read file {file_path}"
            self.logger.error(error_msg, exception=e, extra={'file_path': str(file_path)})
            raise IOError(error_msg) from e

    @enhanced_logging_decorator("write_file")
    def _write_file(self, file_path: Path, content: str) -> None:
        """Write file with comprehensive logging and error handling."""
        self.logger.debug(
            "Writing file",
            extra={
                'file_path': str(file_path),
                'content_length': len(content),
                'backup_created': False
            }
        )

        try:
            # Create backup if file exists
            backup_path = None
            if file_path.exists():
                backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
                file_path.rename(backup_path)
                self.logger.debug(f"Created backup: {backup_path}")

            with file_path.open("w", encoding="utf-8") as file:
                file.write(content)

            self.logger.info(
                "File written successfully",
                extra={
                    'file_path': str(file_path),
                    'content_length': len(content),
                    'backup_path': str(backup_path) if backup_path else None
                }
            )

            self.logger.audit(
                action="file_update",
                resource=str(file_path),
                status="success",
                extra={'backup_created': backup_path is not None}
            )

        except IOError as e:
            error_msg = f"Failed to write file {file_path}"
            self.logger.error(error_msg, exception=e, extra={'file_path': str(file_path)})
            raise IOError(error_msg) from e

    @enhanced_logging_decorator("update_file")
    def update_file(self, file_path: Path, old_version: str, new_version: str) -> None:
        """Update version in file with comprehensive logging."""
        self.logger.info(
            "Starting file update operation",
            extra={
                'file_path': str(file_path),
                'old_version': old_version,
                'new_version': new_version
            }
        )

        if not file_path.exists():
            self.logger.warning(f"File {file_path} does not exist, skipping update")
            return

        with self.logger.performance_tracking(f"update_file_{file_path.name}"):
            original_content = self._read_file(file_path)
            updated_content = original_content.replace(old_version, new_version)

            if original_content == updated_content:
                self.logger.warning(
                    "No version information found in file",
                    extra={'file_path': str(file_path), 'search_string': old_version}
                )
                return

            # Count replacements for verification
            replacement_count = original_content.count(old_version)
            self.logger.info(
                f"Found {replacement_count} version occurrences to update",
                extra={'replacement_count': replacement_count}
            )

            self._write_file(file_path, updated_content)


class VersionUpdater(FileUpdater):
    """Enhanced version updater with comprehensive logging and monitoring."""

    def __init__(
            self,
            version_manager: VersionManager,
            logger: StructuredLogger,
            config: Optional[VersionConfig] = None
    ):
        """Initialize with enhanced configuration."""
        super().__init__(version_manager, logger)
        self.config = config or VersionConfig()

        self.logger.info(
            "Version updater initialized",
            extra={
                'project_root': str(self.config.project_root),
                'component_count': len(self.config.files),
                'total_files': sum(len(files) for files in self.config.files.values())
            }
        )

    @enhanced_logging_decorator("get_current_version")
    def get_current_version(self, version_file_info: FileInfo) -> Version:
        """Get current version with comprehensive logging."""
        self.logger.info(
            "Retrieving current version",
            extra=version_file_info.to_dict()
        )

        try:
            content = self._read_file(version_file_info.path)

            # Search for version pattern
            match = re.search(version_file_info.pattern, content)
            if not match:
                error_msg = f"Could not find version pattern in {version_file_info.path}"
                self.logger.error(
                    error_msg,
                    extra={
                        'pattern': version_file_info.pattern,
                        'content_preview': content[:200] + "..." if len(content) > 200 else content
                    }
                )
                raise ValueError(error_msg)

            # Extract version string
            version_pattern = VersionPattern().base
            version_string_match = re.search(version_pattern, match.group(0))
            if not version_string_match:
                error_msg = f"Could not extract version from matched text: {match.group(0)}"
                self.logger.error(error_msg, extra={'matched_text': match.group(0)})
                raise ValueError(error_msg)

            version_string = version_string_match.group(0)
            version = self.version_manager.parse_version(version_string)

            self.logger.info(
                "Current version retrieved successfully",
                extra={
                    'version': version.to_dict(),
                    'source_file': str(version_file_info.path)
                }
            )

            return version

        except (IOError, ValueError) as e:
            error_msg = f"Failed to get current version from {version_file_info.path}"
            self.logger.error(error_msg, exception=e, extra=version_file_info.to_dict())
            raise

    @enhanced_logging_decorator("update_version")
    def update_version(self, old_version: Version, new_version: Version, component: str) -> None:
        """Update version across component files with comprehensive logging."""
        self.logger.info(
            "Starting component version update",
            extra={
                'component': component,
                'old_version': old_version.to_dict(),
                'new_version': new_version.to_dict()
            }
        )

        old_version_str = self.version_manager.format_version(old_version)
        new_version_str = self.version_manager.format_version(new_version)

        component_files = self.config.files.get(component, {})
        if not component_files:
            self.logger.warning(f"No files defined for component: {component}")
            return

        update_results = {'success': [], 'skipped': [], 'failed': []}

        with self.logger.performance_tracking(f"update_component_{component}"):
            for file_key, file_info in component_files.items():
                try:
                    if file_info.path.exists():
                        self.logger.info(
                            f"Updating {file_key} version",
                            extra={
                                'file_type': file_key,
                                'old_version': old_version_str,
                                'new_version': new_version_str
                            }
                        )

                        self.update_file(file_info.path, old_version_str, new_version_str)
                        update_results['success'].append(file_key)

                    else:
                        self.logger.warning(f"File {file_info.path} does not exist, skipping")
                        update_results['skipped'].append(file_key)

                except Exception as e:
                    self.logger.error(
                        f"Failed to update {file_key}",
                        exception=e,
                        extra={'file_info': file_info.to_dict()}
                    )
                    update_results['failed'].append(file_key)

        # Log summary
        self.logger.info(
            "Component version update completed",
            extra={
                'component': component,
                'update_summary': update_results,
                'total_files': len(component_files),
                'success_count': len(update_results['success'])
            }
        )

        self.logger.audit(
            action="component_version_update",
            resource=f"component:{component}",
            status="completed",
            extra=update_results
        )


class VersionUpdaterCLI:
    """Enhanced command-line interface with comprehensive logging and monitoring."""

    def __init__(self, config: Optional[VersionConfig] = None, logging_config: Optional[LoggingConfig] = None):
        """Initialize CLI with enhanced configuration."""
        self.logging_config = logging_config or LoggingConfig.from_env()
        self.logger = StructuredLogger(self.logging_config)

        self.config = config or VersionConfig()
        self.version_manager = VersionManager(self.logger)
        self.version_updater = VersionUpdater(self.version_manager, self.logger, self.config)

        self.logger.info(
            "Enhanced Version Updater CLI initialized",
            extra={
                'version': "2.0.0",
                'logging_config': self.logging_config.__dict__,
                'project_root': str(self.config.project_root)
            }
        )

    @enhanced_logging_decorator("parse_arguments")
    def parse_arguments(self) -> argparse.Namespace:
        """Parse command line arguments with comprehensive validation."""
        parser = argparse.ArgumentParser(
            description="Enhanced Version Update Utility with Comprehensive Logging",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --component backend --bump-type minor
  %(prog)s --component both --bump-type major --log-level debug
  %(prog)s --component frontend --action set --bump-type patch --value 5
            """
        )

        parser.add_argument(
            "--component",
            choices=["backend", "frontend", "both", "other"],
            default="other",
            help="Which component to update (default: other)"
        )

        parser.add_argument(
            "--bump-type",
            choices=["major", "minor", "patch"],
            default="patch",
            help="Which part of the version to bump (default: patch)"
        )

        parser.add_argument(
            "--action",
            choices=["increment", "set"],
            default="increment",
            help="How to modify the version (default: increment)"
        )

        parser.add_argument(
            "--value",
            type=int,
            help="Value to set (required for set action)"
        )

        parser.add_argument(
            "--log-level",
            choices=["debug", "info", "warning", "error", "critical"],
            default="info",
            help="Logging level (default: info)"
        )

        parser.add_argument(
            "--log-format",
            choices=["console", "json", "structured"],
            default="structured",
            help="Log output format (default: structured)"
        )

        parser.add_argument(
            "--performance-report",
            action="store_true",
            help="Generate performance report at completion"
        )

        return parser.parse_args()

    @enhanced_logging_decorator("run")
    def run(self) -> Union[int, str]:
        """Run the enhanced version update process."""
        session_start = time.time()

        try:
            args = self.parse_arguments()

            self.logger.info(
                "Starting version update session",
                extra={
                    'arguments': vars(args),
                    'session_start': session_start
                }
            )

            # Validate arguments
            bump_type = BumpType.SET if args.action == "set" else BumpType.INCREMENT
            component_enum = getattr(Component, args.bump_type.upper())

            if bump_type == BumpType.SET and args.value is None:
                error = "--value is required for 'set' action"
                self.logger.error(error, extra={'action': args.action, 'value': args.value})
                return error

            # Determine components to process
            component_list = ["setup"]
            if args.component == "both":
                component_list += ["frontend", "backend"]
            elif args.component in ["frontend", "backend"]:
                component_list += [args.component]
            elif args.component == "other":
                pass
            else:
                error = f"Invalid component: {args.component}! Should be one of: backend, frontend, both or setup."
                self.logger.error(error, extra={'provided_component': args.component})
                return error

            self.logger.info(
                "Processing components",
                extra={'components_to_process': component_list}
            )

            # Process each component
            results = {'processed': [], 'skipped': [], 'failed': []}

            for component_name in component_list:
                try:
                    with self.logger.performance_tracking(f"process_component_{component_name}"):
                        if component_name not in self.config.files:
                            self.logger.warning(f"Component {component_name} not found in configuration")
                            results['skipped'].append(component_name)
                            continue

                        # Get appropriate file for version reading
                        component_file_name = "setup.py" if component_name == "setup" else "version.py"
                        component_file_info = self.config.files[component_name][component_file_name]

                        if not component_file_info.path.exists():
                            error_msg = f"{component_name.capitalize()} version file {component_file_info.path} does not exist"
                            self.logger.error(error_msg, extra={'component': component_name})

                            if args.component == component_name:
                                return f"Invalid component: {args.component}! Should be one of: backend, frontend, both or setup."

                            results['failed'].append(component_name)
                            continue

                        # Get current version
                        current_version = self.version_updater.get_current_version(component_file_info)

                        # Configure bump parameters
                        if component_name == "setup":
                            actual_bump_type = BumpType.INCREMENT
                            actual_value = None
                        else:
                            actual_bump_type = bump_type
                            actual_value = args.value

                        # Calculate new version
                        new_version = self.version_manager.bump_version(
                            version=current_version,
                            component=component_enum,
                            bump_type=actual_bump_type,
                            value=actual_value
                        )

                        # Update version files
                        self.version_updater.update_version(current_version, new_version, component_name)

                        self.logger.info(
                            f"Successfully updated {component_name} version",
                            extra={
                                'component': component_name,
                                'old_version': current_version.to_dict(),
                                'new_version': new_version.to_dict()
                            }
                        )

                        results['processed'].append(component_name)

                except Exception as e:
                    error_msg = f"Error updating {component_name} version"
                    self.logger.error(error_msg, exception=e, extra={'component': component_name})

                    if args.component == component_name:
                        return f"Error updating {component_name} version: {e}"

                    results['failed'].append(component_name)

            # Log session summary
            session_duration = time.time() - session_start
            self.logger.info(
                "Version update session completed",
                extra={
                    'session_duration_seconds': f"{session_duration:.2f}",
                    'results_summary': results,
                    'total_components': len(component_list)
                }
            )

            # Generate performance report if requested
            if args.performance_report:
                metrics = self.logger.get_performance_metrics()
                self.logger.info(
                    "Performance Report",
                    extra={'performance_metrics': metrics}
                )

            self.logger.audit(
                action="version_update_session",
                resource="application",
                status="completed",
                extra={
                    'results': results,
                    'session_duration': session_duration
                }
            )

            return 0

        except Exception as e:
            error = f"Unexpected error in version update session: {e}"
            self.logger.critical(error, exception=e)
            return error


if __name__ == "__main__":
    try:
        # Initialize CLI with environment-based configuration
        cli = VersionUpdaterCLI()
        exit_code = cli.run()
        sys.exit(exit_code if isinstance(exit_code, int) else 1)
    except Exception as e:
        # Fallback error handling for critical failures
        print(f"CRITICAL: Failed to initialize version updater: {e}", file=sys.stderr)
        sys.exit(1)
