"""Task 1: County Pattern Analysis.

Analyzes property records to extract patterns for:
- Instrument number formats
- Book/page number patterns
- Date ranges
- Document type distribution
"""

import json
import logging
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils import setup_logging, stream_jsonl, parse_date


def analyze_instrument_patterns(records: list) -> list:
    """
    Analyze instrument number patterns for a county.
    
    Args:
        records: List of records for the county
        
    Returns:
        List of pattern dictionaries
    """
    instrument_numbers = []
    for record in records:
        instr_num = record.get('instrument_number')
        if instr_num and isinstance(instr_num, str):
            instrument_numbers.append(instr_num)
    
    if not instrument_numbers:
        return []
    
    pattern_groups = defaultdict(list)
    
    for instr_num in instrument_numbers:
        if instr_num.startswith('bp'):
            continue
        
        pattern_parts = []
        for char in instr_num:
            if char.isdigit():
                pattern_parts.append('\\d')
            elif char.isalpha():
                pattern_parts.append('[A-Za-z]')
            else:
                if char in ['-', '.', '/', '_', '(', ')', '{', '}', '[', ']', '*', '+', '?', '^', '$', '|', '\\']:
                    pattern_parts.append(f'\\{char}')
                else:
                    pattern_parts.append(char)
        
        pattern = ''.join(pattern_parts)
        
        pattern_groups[pattern].append(instr_num)
    
    result = []
    total_count = len([instr for instr in instrument_numbers if not instr.startswith('bp')])
    
    for pattern, examples in pattern_groups.items():
        count = len(examples)
        percentage = (count / total_count * 100) if total_count > 0 else 0
        
        regex_parts = []
        i = 0
        while i < len(pattern):
            if pattern[i:i+2] == '\\d':
                digit_count = 0
                j = i
                while j < len(pattern) and pattern[j:j+2] == '\\d':
                    digit_count += 1
                    j += 2
                regex_parts.append(f'\\d{{{digit_count}}}')
                i = j
            elif pattern[i:i+9] == '[A-Za-z]':
                letter_count = 0
                j = i
                while j < len(pattern) and pattern[j:j+9] == '[A-Za-z]':
                    letter_count += 1
                    j += 9
                regex_parts.append(f'[A-Za-z]{{{letter_count}}}')
                i = j
            else:
                regex_parts.append(pattern[i])
                i += 1
        
        regex_pattern = '^' + ''.join(regex_parts) + '$'
        
        readable_pattern = pattern.replace('\\d', 'D').replace('[A-Za-z]', 'L')
        
        result.append({
            "pattern": readable_pattern,
            "regex": regex_pattern,
            "example": examples[0] if examples else "",
            "count": count,
            "percentage": round(percentage, 2)
        })
    
    result.sort(key=lambda x: x['count'], reverse=True)
    
    return result


def analyze_book_page_patterns(records: list) -> list:
    """
    Analyze book and page number patterns.
    
    Args:
        records: List of records for the county
        
    Returns:
        List of pattern dictionaries for book and page separately
    """
    books = []
    pages = []
    
    for record in records:
        book = record.get('book')
        page = record.get('page')
        
        if book:
            books.append(str(book))
        if page:
            pages.append(str(page))
    
    result = []
    
    if books:
        book_patterns = {
            "field": "book",
            "is_numeric": all(b.isdigit() for b in books),
            "has_letters": any(not b.isdigit() for b in books),
            "min_value": min(books, key=lambda x: (len(x), x)) if books else None,
            "max_value": max(books, key=lambda x: (len(x), x)) if books else None,
            "unique_count": len(set(books)),
            "total_count": len(books)
        }
        result.append(book_patterns)
    
    if pages:
        page_patterns = {
            "field": "page",
            "is_numeric": all(p.isdigit() for p in pages),
            "has_letters": any(not p.isdigit() for p in pages),
            "min_value": min(pages, key=lambda x: (len(x), x)) if pages else None,
            "max_value": max(pages, key=lambda x: (len(x), x)) if pages else None,
            "unique_count": len(set(pages)),
            "total_count": len(pages)
        }
        result.append(page_patterns)
    
    return result


def analyze_date_ranges(records: list) -> Dict[str, Any]:
    """
    Analyze date ranges and detect anomalies.
    
    Args:
        records: List of records for the county
        
    Returns:
        Dictionary with earliest, latest, and anomalies
    """
    dates = []
    anomalies = []
    today = datetime.now()
    
    for record in records:
        date_str = record.get('date')
        if not date_str:
            continue
        
        parsed_date = parse_date(date_str)
        if not parsed_date:
            continue
        
        try:
            if 'T' in parsed_date:
                dt = datetime.fromisoformat(parsed_date.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(parsed_date)
            
            dates.append(dt)
            
            if dt > today:
                days_ahead = (dt - today).days
                if days_ahead > 1:
                    anomalies.append({
                        "date": parsed_date,
                        "type": "future_date",
                        "days_ahead": days_ahead
                    })
            
            if dt.year < 1800:
                anomalies.append({
                    "date": parsed_date,
                    "type": "very_old_date",
                    "year": dt.year
                })
        
        except (ValueError, AttributeError) as e:
            anomalies.append({
                "date": parsed_date,
                "type": "parse_error",
                "error": str(e)
            })
    
    if not dates:
        return {
            "earliest": None,
            "latest": None,
            "anomalies": anomalies
        }
    
    earliest = min(dates)
    latest = max(dates)
    
    return {
        "earliest": earliest.isoformat(),
        "latest": latest.isoformat(),
        "anomalies": anomalies
    }


def analyze_doc_type_distribution(records: list) -> Dict[str, Any]:
    """
    Analyze document type distribution.
    
    Args:
        records: List of records for the county
        
    Returns:
        Dictionary with distribution and statistics
    """
    doc_types = []
    doc_categories = []
    doc_type_to_category = {}
    
    for record in records:
        doc_type = record.get('doc_type')
        doc_category = record.get('doc_category')
        
        if doc_type:
            doc_types.append(doc_type)
            if doc_category:
                doc_type_to_category[doc_type] = doc_category
                doc_categories.append(doc_category)
    
    doc_type_counter = Counter(doc_types)
    doc_category_counter = Counter(doc_categories)
    
    top_10_doc_types = dict(doc_type_counter.most_common(10))
    
    type_category_relationship = {}
    for doc_type, count in doc_type_counter.items():
        category = doc_type_to_category.get(doc_type, None)
        if category:
            if category not in type_category_relationship:
                type_category_relationship[category] = {}
            type_category_relationship[category][doc_type] = count
    
    return {
        "doc_type_distribution": top_10_doc_types,
        "unique_doc_types": len(doc_type_counter),
        "unique_doc_categories": len(doc_category_counter),
        "total_records": len(records),
        "type_category_relationship": type_category_relationship
    }


def analyze_county_patterns(jsonl_path: str, output_path: str):
    """
    Main function to analyze patterns for all counties.
    
    Args:
        jsonl_path: Path to input JSONL file
        output_path: Path to output JSON file
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting pattern analysis for {jsonl_path}")
    
    county_records = defaultdict(list)
    total_records = 0
    
    for record in stream_jsonl(jsonl_path):
        total_records += 1
        county = record.get('county')
        if county:
            county_records[county].append(record)
    
    logger.info(f"Processed {total_records} total records across {len(county_records)} counties")
    
    results = {}
    
    for county, records in county_records.items():
        logger.info(f"Analyzing {len(records)} records for county: {county}")
        
        instrument_patterns = analyze_instrument_patterns(records)
        book_page_patterns = analyze_book_page_patterns(records)
        date_range = analyze_date_ranges(records)
        doc_type_dist = analyze_doc_type_distribution(records)
        
        results[county] = {
            "record_count": len(records),
            "instrument_patterns": instrument_patterns,
            "book_patterns": [bp for bp in book_page_patterns if bp.get('field') == 'book'],
            "page_patterns": [bp for bp in book_page_patterns if bp.get('field') == 'page'],
            "date_range": date_range,
            "doc_type_distribution": doc_type_dist.get("doc_type_distribution", {}),
            "unique_doc_types": doc_type_dist.get("unique_doc_types", 0)
        }
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Analysis complete. Output saved to {output_path}")
    logger.info(f"Analyzed {len(county_records)} counties")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze county patterns from property records")
    parser.add_argument("--input", "-i", default="nc_records_assessment.jsonl",
                       help="Path to input JSONL file")
    parser.add_argument("--output", "-o", default="outputs/county_patterns.json",
                       help="Path to output JSON file")
    
    args = parser.parse_args()
    
    analyze_county_patterns(args.input, args.output)
