"""Bonus Task: LLM-Assisted Document Classification.

Uses an LLM to classify messy doc_type values into standardized categories.
"""

import json
import logging
import random
from collections import Counter
from pathlib import Path
from typing import Dict, List, Any, Optional

from utils import setup_logging, stream_jsonl


STANDARD_CATEGORIES = [
    "SALE_DEED",
    "MORTGAGE",
    "DEED_OF_TRUST",
    "RELEASE",
    "LIEN",
    "PLAT",
    "EASEMENT",
    "LEASE",
    "MISC"
]


def sample_doc_types_strategically(jsonl_path: str, sample_size: int = 200) -> List[str]:
    """
    Sample doc_type values strategically from the dataset.
    
    Strategy:
    1. Get all unique doc_types with their frequencies
    2. Sample proportionally - more common types get more samples
    3. Ensure we get rare types too (at least one of each)
    
    Args:
        jsonl_path: Path to JSONL file
        sample_size: Number of doc_types to sample
        
    Returns:
        List of unique doc_type values to classify
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    doc_type_counter = Counter()
    total_records = 0
    
    logger.info(f"Analyzing doc_types in {jsonl_path}")
    
    for record in stream_jsonl(jsonl_path):
        total_records += 1
        doc_type = record.get('doc_type')
        if doc_type:
            doc_type_counter[doc_type] += 1
    
    logger.info(f"Found {len(doc_type_counter)} unique doc_types in {total_records} records")
    
    unique_doc_types = list(doc_type_counter.keys())
    
    if len(unique_doc_types) <= sample_size:
        logger.info(f"All {len(unique_doc_types)} doc_types will be sampled")
        return unique_doc_types
    
    sampled = []
    
    sorted_types = sorted(doc_type_counter.items(), key=lambda x: x[1], reverse=True)
    
    top_n = min(50, len(sorted_types))
    for doc_type, count in sorted_types[:top_n]:
        sampled.append(doc_type)
    
    remaining = [dt for dt in unique_doc_types if dt not in sampled]
    
    if len(sampled) < sample_size:
        additional_needed = sample_size - len(sampled)
        additional = random.sample(remaining, min(additional_needed, len(remaining)))
        sampled.extend(additional)
    
    logger.info(f"Sampled {len(sampled)} doc_types for classification")
    return sampled


def classify_with_llm(doc_types: List[str], api_key: Optional[str] = None) -> Dict[str, str]:
    """
    Use LLM to classify doc_type values into standardized categories.
    
    Args:
        doc_types: List of doc_type values to classify
        api_key: Optional OpenAI API key (if None, uses environment variable)
        
    Returns:
        Dictionary mapping original doc_type to standardized category
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        import openai
    except ImportError:
        logger.error("openai package not installed. Install with: pip install openai")
        raise
    
    if not api_key:
        import os
        api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        logger.warning("No OpenAI API key provided. Using fallback classification.")
        return fallback_classification(doc_types)
    
    client = openai.OpenAI(api_key=api_key)
    
    mapping = {}
    
    categories_description = ", ".join(STANDARD_CATEGORIES)
    
    prompt = f"""You are a data classification expert. Classify the following document types from property records into one of these standardized categories:

Categories: {categories_description}

Rules:
- SALE_DEED: Any type of deed (Warranty Deed, Quitclaim Deed, General Warranty Deed, etc.)
- MORTGAGE: Mortgage documents, mortgage assignments, mortgage modifications
- DEED_OF_TRUST: Deed of Trust, Trust Deed, D/T, DT, D-TR
- RELEASE: Release, Partial Release, Release of Lien, Satisfaction, Cancellation
- LIEN: Lien, Mechanic's Lien, Tax Lien, Judgment Lien
- PLAT: Plat, Map, Map Plat, Subdivision Plat
- EASEMENT: Easement, Right of Way
- LEASE: Lease, Lease Agreement
- MISC: Everything else that doesn't fit the above categories

For each document type, respond with ONLY the category name, nothing else.

Document types to classify:
"""
    
    batch_size = 50
    total_cost = 0
    
    for i in range(0, len(doc_types), batch_size):
        batch = doc_types[i:i+batch_size]
        batch_prompt = prompt + "\n".join([f"{j+1}. {dt}" for j, dt in enumerate(batch)])
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise classification assistant. Respond with only category names, one per line."},
                    {"role": "user", "content": batch_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            result = response.choices[0].message.content.strip()
            lines = result.split('\n')
            
            for j, doc_type in enumerate(batch):
                if j < len(lines):
                    category = lines[j].strip().upper()
                    if category in STANDARD_CATEGORIES:
                        mapping[doc_type] = category
                    else:
                        mapping[doc_type] = "MISC"
                else:
                    mapping[doc_type] = "MISC"
            
            tokens_used = response.usage.total_tokens
            cost = (tokens_used / 1000) * 0.00015
            total_cost += cost
            
            logger.info(f"Classified batch {i//batch_size + 1} ({len(batch)} doc_types). Cost: ${cost:.4f}")
            
        except Exception as e:
            logger.error(f"Error classifying batch: {e}")
            for doc_type in batch:
                mapping[doc_type] = fallback_classification([doc_type])[doc_type]
    
    logger.info(f"Total classification cost: ${total_cost:.4f}")
    return mapping


def fallback_classification(doc_types: List[str]) -> Dict[str, str]:
    """
    Fallback classification using rule-based approach when LLM is not available.
    
    Args:
        doc_types: List of doc_type values to classify
        
    Returns:
        Dictionary mapping original doc_type to standardized category
    """
    mapping = {}
    
    for doc_type in doc_types:
        dt_lower = doc_type.lower().strip()
        dt_original = doc_type.strip()
        
        if dt_lower in ['dt', 'd/t', 'd-t', 'd-tr', 'd-trust', 'sub tr', 'subst tr', 'substitution trustee']:
            mapping[doc_type] = "DEED_OF_TRUST"
        elif 'trust' in dt_lower and ('deed' in dt_lower or dt_lower.startswith('trust')):
            mapping[doc_type] = "DEED_OF_TRUST"
        elif any(keyword in dt_lower for keyword in ['mortgage', 'mtge', 'mtg', 'morg']):
            mapping[doc_type] = "MORTGAGE"
        elif any(keyword in dt_lower for keyword in ['satisfaction', 'sat', 'certificate of satisfaction']):
            mapping[doc_type] = "RELEASE"
        elif any(keyword in dt_lower for keyword in ['cancellation', 'can', 'cancel']):
            mapping[doc_type] = "RELEASE"
        elif any(keyword in dt_lower for keyword in ['release', 'rel', 'partial release', 'rel deed']):
            mapping[doc_type] = "RELEASE"
        elif 'lien' in dt_lower or dt_lower in ['judgment', 'judgement']:
            mapping[doc_type] = "LIEN"
        elif any(keyword in dt_lower for keyword in ['plat', 'map plat', 'map/r', 'map', 'subdivision plat']):
            mapping[doc_type] = "PLAT"
        elif 'lease' in dt_lower:
            mapping[doc_type] = "LEASE"
        elif any(keyword in dt_lower for keyword in ['substitute trustee', 'substitution trustee', 'sub tr', 'subst tr']):
            mapping[doc_type] = "DEED_OF_TRUST"
        elif 'easement' in dt_lower or 'right of way' in dt_lower:
            mapping[doc_type] = "EASEMENT"
        elif any(keyword in dt_lower for keyword in ['deed', 'warranty', 'quitclaim', 'grant', 'conveyance']):
            if 'trust' in dt_lower or 'trustee' in dt_lower:
                mapping[doc_type] = "DEED_OF_TRUST"
            elif 'easement' in dt_lower:
                mapping[doc_type] = "EASEMENT"
            else:
                mapping[doc_type] = "SALE_DEED"
        elif any(keyword in dt_lower for keyword in ['assignment', 'asign', 'assign']):
            if 'mortgage' in dt_lower or 'mtg' in dt_lower:
                mapping[doc_type] = "MORTGAGE"
            elif 'trust' in dt_lower or 'trustee' in dt_lower:
                mapping[doc_type] = "DEED_OF_TRUST"
            else:
                mapping[doc_type] = "MISC"
        elif any(keyword in dt_lower for keyword in ['power of attorney', 'poa']):
            mapping[doc_type] = "MISC"
        elif any(keyword in dt_lower for keyword in ['notice', 'request notice', 'see instrument']):
            mapping[doc_type] = "MISC"
        else:
            mapping[doc_type] = "MISC"
    
    return mapping


def create_mapping(jsonl_path: str, output_path: str, use_llm: bool = True, api_key: Optional[str] = None):
    """
    Create doc_type mapping using LLM classification.
    
    Args:
        jsonl_path: Path to input JSONL file
        output_path: Path to output mapping JSON file
        use_llm: Whether to use LLM (if False, uses fallback)
        api_key: Optional OpenAI API key
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting doc_type classification")
    
    sampled_doc_types = sample_doc_types_strategically(jsonl_path, sample_size=200)
    
    if use_llm:
        logger.info("Using LLM for classification")
        try:
            mapping = classify_with_llm(sampled_doc_types, api_key)
        except Exception as e:
            logger.warning(f"LLM classification failed: {e}. Using fallback.")
            mapping = fallback_classification(sampled_doc_types)
    else:
        logger.info("Using rule-based fallback classification")
        mapping = fallback_classification(sampled_doc_types)
    
    doc_type_counter = Counter()
    for record in stream_jsonl(jsonl_path):
        doc_type = record.get('doc_type')
        if doc_type:
            doc_type_counter[doc_type] += 1
    
    complete_mapping = {}
    for doc_type in doc_type_counter.keys():
        if doc_type in mapping:
            complete_mapping[doc_type] = mapping[doc_type]
        else:
            complete_mapping[doc_type] = fallback_classification([doc_type])[doc_type]
    
    output_path_obj = Path(output_path)
    output_path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(complete_mapping, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Mapping complete. {len(complete_mapping)} doc_types classified.")
    logger.info(f"Output saved to {output_path}")
    
    category_counts = Counter(complete_mapping.values())
    logger.info("Category distribution:")
    for category, count in sorted(category_counts.items()):
        logger.info(f"  {category}: {count}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Classify doc_types using LLM")
    parser.add_argument("--input", "-i", default="nc_records_assessment.jsonl",
                       help="Path to input JSONL file")
    parser.add_argument("--output", "-o", default="outputs/doc_type_mapping.json",
                       help="Path to output mapping JSON file")
    parser.add_argument("--no-llm", action="store_true",
                       help="Use rule-based classification instead of LLM")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    
    args = parser.parse_args()
    
    create_mapping(args.input, args.output, use_llm=not args.no_llm, api_key=args.api_key)
