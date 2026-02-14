"""Shared utilities for data processing."""

import json
import logging
from typing import Iterator, Dict, Any, Optional
from datetime import datetime


def setup_logging(level=logging.INFO):
    """Configure logging for the application."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def stream_jsonl(filepath: str) -> Iterator[Dict[Any, Any]]:
    """
    Stream JSONL file line-by-line.
    
    Args:
        filepath: Path to JSONL file
        
    Yields:
        Dictionary representing each record
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                logging.warning(f"Error parsing line {line_num}: {e}")
                continue


def normalize_name(name: str) -> str:
    """
    Normalize name to uppercase format.
    
    Args:
        name: Name string to normalize
        
    Returns:
        Uppercase normalized name
    """
    if not name:
        return ""
    return name.strip().upper()


def parse_date(date_str: str) -> Optional[str]:
    """
    Parse and format date to ISO 8601.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        ISO 8601 formatted date string, or None if parsing fails
    """
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%m/%d/%Y",
        "%m/%d/%Y %I:%M:%S %p",  # e.g., "6/1/2007 2:58:08 PM"
        "%m/%d/%Y %I:%M:%S %p",  # e.g., "6/1/2007 2:58:08 PM"
        "%m/%d/%Y %H:%M:%S",     # e.g., "6/1/2007 14:58:08"
        "%m/%d/%Y %I:%M %p",     # e.g., "6/1/2007 2:58 PM"
        "%m/%d/%Y %H:%M",        # e.g., "6/1/2007 14:58"
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    
    try:
        from dateutil import parser
        dt = parser.parse(date_str)
        return dt.isoformat()
    except (ImportError, ValueError):
        logging.warning(f"Could not parse date: {date_str}")
        return None


def validate_record(record: Dict[Any, Any]) -> bool:
    """
    Validate record structure.
    
    Args:
        record: Record dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not isinstance(record, dict):
        return False
    if 'county' not in record:
        return False
    return True
