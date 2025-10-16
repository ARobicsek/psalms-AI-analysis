"""
Comprehensive Logging System for Psalms AI Commentary Pipeline

Provides structured logging for all agent activities including:
- Research requests from Scholar agent
- Queries executed by librarian agents
- Results returned by librarians
- Performance metrics

Logs are stored in logs/ directory with timestamp-based filenames.
"""

import logging
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class LogLevel(Enum):
    """Log levels for the system."""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class AgentLogger:
    """
    Structured logger for agent activities in the Psalms AI pipeline.

    Features:
    - Separate log files for each run (timestamped)
    - JSON-structured logs for machine parsing
    - Human-readable console output
    - Configurable log levels
    """

    def __init__(self,
                 name: str,
                 log_dir: str = "logs",
                 console_level: LogLevel = LogLevel.INFO,
                 file_level: LogLevel = LogLevel.DEBUG):
        """
        Initialize the agent logger.

        Args:
            name: Name of the logger (e.g., "bdb_librarian", "scholar_researcher")
            log_dir: Directory to store log files
            console_level: Minimum level for console output
            file_level: Minimum level for file output
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"{name}_{timestamp}.log"
        self.json_log_file = self.log_dir / f"{name}_{timestamp}.json"

        # Set up Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()  # Remove any existing handlers

        # Console handler (human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_level.value)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (detailed)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(file_level.value)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # JSON log entries (for structured analysis)
        self.json_entries = []

    def _log_json(self, entry: Dict[str, Any]):
        """Log structured JSON entry."""
        entry['timestamp'] = datetime.now().isoformat()
        entry['agent'] = self.name
        self.json_entries.append(entry)

        # Write to JSON file
        with open(self.json_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.json_entries, f, ensure_ascii=False, indent=2)

    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message)
        if kwargs:
            self._log_json({'level': 'DEBUG', 'message': message, **kwargs})

    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message)
        if kwargs:
            self._log_json({'level': 'INFO', 'message': message, **kwargs})

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message)
        if kwargs:
            self._log_json({'level': 'WARNING', 'message': message, **kwargs})

    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message)
        if kwargs:
            self._log_json({'level': 'ERROR', 'message': message, **kwargs})

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message)
        if kwargs:
            self._log_json({'level': 'CRITICAL', 'message': message, **kwargs})

    # Specialized logging methods for agent activities

    def log_research_request(self, psalm_chapter: int, request: Dict[str, Any]):
        """
        Log a research request from Scholar agent.

        Args:
            psalm_chapter: Psalm number being researched
            request: Complete research request JSON
        """
        self.info(
            f"Research request received for Psalm {psalm_chapter}",
            event_type='research_request',
            psalm_chapter=psalm_chapter,
            request=request
        )

    def log_librarian_query(self,
                           librarian_type: str,
                           query: str,
                           params: Dict[str, Any]):
        """
        Log a query executed by a librarian agent.

        Args:
            librarian_type: Type of librarian ("bdb", "concordance", "figurative")
            query: Query string or search term
            params: Query parameters (scope, level, filters, etc.)
        """
        self.info(
            f"{librarian_type.capitalize()} Librarian query: {query}",
            event_type='librarian_query',
            librarian_type=librarian_type,
            query=query,
            params=params
        )

    def log_librarian_results(self,
                             librarian_type: str,
                             query: str,
                             result_count: int,
                             sample_results: Optional[List[Dict[str, Any]]] = None):
        """
        Log results returned by a librarian agent.

        Args:
            librarian_type: Type of librarian
            query: Original query
            result_count: Number of results found
            sample_results: Sample of results (first 3-5) for verification
        """
        message = f"{librarian_type.capitalize()} Librarian returned {result_count} results for '{query}'"
        self.info(
            message,
            event_type='librarian_results',
            librarian_type=librarian_type,
            query=query,
            result_count=result_count,
            sample_results=sample_results or []
        )

    def log_phrase_variations(self,
                            original_phrase: str,
                            variations: List[str],
                            variation_count: int):
        """
        Log automatic phrase variation generation.

        Args:
            original_phrase: Original Hebrew phrase
            variations: List of generated variations
            variation_count: Total number of variations
        """
        self.debug(
            f"Generated {variation_count} variations for '{original_phrase}'",
            event_type='phrase_variations',
            original_phrase=original_phrase,
            variations=variations,
            variation_count=variation_count
        )

    def log_performance_metric(self,
                               operation: str,
                               duration_ms: float,
                               metadata: Optional[Dict[str, Any]] = None):
        """
        Log performance metrics.

        Args:
            operation: Name of operation measured
            duration_ms: Duration in milliseconds
            metadata: Additional context (record count, API calls, etc.)
        """
        self.debug(
            f"{operation} completed in {duration_ms:.2f}ms",
            event_type='performance_metric',
            operation=operation,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )

    def log_api_call(self,
                    api_name: str,
                    endpoint: str,
                    status_code: int,
                    response_time_ms: float):
        """
        Log external API calls (e.g., Sefaria API).

        Args:
            api_name: Name of API (e.g., "Sefaria")
            endpoint: API endpoint called
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
        """
        self.debug(
            f"{api_name} API call: {endpoint} -> {status_code} ({response_time_ms:.2f}ms)",
            event_type='api_call',
            api_name=api_name,
            endpoint=endpoint,
            status_code=status_code,
            response_time_ms=response_time_ms
        )

    def log_error_detail(self,
                        operation: str,
                        error_type: str,
                        error_message: str,
                        stack_trace: Optional[str] = None):
        """
        Log detailed error information.

        Args:
            operation: Operation that failed
            error_type: Type of error (e.g., "APIError", "DatabaseError")
            error_message: Error message
            stack_trace: Optional stack trace
        """
        self.error(
            f"{operation} failed: {error_type} - {error_message}",
            event_type='error_detail',
            operation=operation,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace
        )

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of logged activity.

        Returns:
            Dictionary with counts by event type, log level, etc.
        """
        summary = {
            'total_entries': len(self.json_entries),
            'by_level': {},
            'by_event_type': {}
        }

        for entry in self.json_entries:
            # Count by level
            level = entry.get('level', 'UNKNOWN')
            summary['by_level'][level] = summary['by_level'].get(level, 0) + 1

            # Count by event type
            event_type = entry.get('event_type', 'general')
            summary['by_event_type'][event_type] = summary['by_event_type'].get(event_type, 0) + 1

        return summary


# Global logger registry
_loggers: Dict[str, AgentLogger] = {}


def get_logger(name: str,
               log_dir: str = "logs",
               console_level: LogLevel = LogLevel.INFO,
               file_level: LogLevel = LogLevel.DEBUG) -> AgentLogger:
    """
    Get or create an agent logger.

    Args:
        name: Logger name
        log_dir: Log directory
        console_level: Console log level
        file_level: File log level

    Returns:
        AgentLogger instance
    """
    if name not in _loggers:
        _loggers[name] = AgentLogger(name, log_dir, console_level, file_level)
    return _loggers[name]


def get_all_summaries() -> Dict[str, Dict[str, Any]]:
    """
    Get summaries from all active loggers.

    Returns:
        Dictionary mapping logger name to summary
    """
    return {name: logger.get_summary() for name, logger in _loggers.items()}


# Example usage
if __name__ == '__main__':
    # Ensure UTF-8 for Hebrew output on Windows
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    # Create logger
    logger = get_logger('test_agent')

    # Test various log types
    logger.info("Logger initialized")

    logger.log_research_request(23, {
        'lexicon': [{'word': 'רעה', 'notes': 'shepherd/evil'}],
        'concordance': [{'query': 'רעה', 'scope': 'Psalms'}]
    })

    logger.log_librarian_query(
        'concordance',
        'רעה',
        {'scope': 'Psalms', 'level': 'consonantal'}
    )

    logger.log_phrase_variations(
        'רעה',
        ['רעה', 'והרעה', 'הרעה', 'ברעה'],
        20
    )

    logger.log_librarian_results(
        'concordance',
        'רעה',
        15,
        [
            {'reference': 'Psalms 23:1', 'matched_word': 'רֹעִי'},
            {'reference': 'Psalms 49:15', 'matched_word': 'ירעם'}
        ]
    )

    logger.log_performance_metric(
        'concordance_search',
        45.2,
        {'result_count': 15, 'variations_tried': 20}
    )

    # Print summary
    print("\n=== Log Summary ===")
    summary = logger.get_summary()
    print(json.dumps(summary, indent=2, ensure_ascii=False))

    print(f"\nLogs written to:")
    print(f"  Text: {logger.log_file}")
    print(f"  JSON: {logger.json_log_file}")
