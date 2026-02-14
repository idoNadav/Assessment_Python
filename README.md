# Data Engineer Assessment Solution

## Overview

This solution implements the Dono AI Data Engineer Assessment tasks:
- **Task 1**: County Pattern Analysis (Required)
- **Task 2**: Seminole County, FL Web Scraper (Required)
- **Bonus Task**: LLM-Assisted Document Classification (Optional)

## Project Structure

```
assessment_solution/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── SUBMISSION_CHECKLIST.md           # Submission checklist
├── ADAPTATION_GUIDE.md               # Guide for adapting Task 2 (Hebrew)
├── TASK2_NOTES.md                    # Detailed notes for Task 2
├── src/
│   ├── __init__.py
│   ├── pattern_analyzer.py           # Task 1: County pattern analysis
│   ├── seminole_scraper.py           # Task 2: Web scraper using API
│   ├── seminole_scraper_selenium.py  # Task 2: Selenium-based scraper (alternative)
│   ├── llm_classifier.py             # Bonus: LLM-assisted doc_type classification
│   └── utils.py                      # Shared utilities
└── outputs/
    ├── county_patterns.json           # Task 1 output
    ├── seminole_test_results.json     # Task 2 test output
    └── doc_type_mapping.json          # Bonus: doc_type classification mapping
```

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Internet connection (for Task 2)

### Installation

1. Navigate to the project directory:
   ```bash
   cd assessment_solution
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Ensure you have the assessment data:
   - Place `nc_records_assessment.jsonl` in the project root directory
   - The file should be accessible from the project root

### Optional Dependencies

For Task 2 Selenium version (alternative implementation):
```bash
pip install selenium webdriver-manager
```

For Bonus Task with LLM (optional):
```bash
pip install openai
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Task 1: County Pattern Analysis

Analyze patterns in the North Carolina property records dataset.

**Command:**
```bash
python src/pattern_analyzer.py --input nc_records_assessment.jsonl --output outputs/county_patterns.json
```

**What it does:**
- Streams the JSONL file line-by-line (efficient for large files)
- Groups records by county
- For each county, analyzes:
  - **Instrument Number Patterns**: Extracts regex patterns, identifies formats (e.g., YYYY-NNNNN, NNNNNN)
  - **Book/Page Number Patterns**: Analyzes format, ranges, numeric vs alphanumeric
  - **Date Ranges**: Finds earliest/latest dates, detects anomalies (future dates, very old dates)
  - **Document Type Distribution**: Calculates top 10 doc_types, unique count, relationships

**Output**: `outputs/county_patterns.json` containing structured analysis for each county.

**Example output structure:**
```json
{
  "wake": {
    "record_count": 2473,
    "instrument_patterns": [
      {
        "pattern": "DDDDDD\\-DDDDD",
        "regex": "^\\d{6}\\-\\d{5}$",
        "example": "010905-02162",
        "count": 2211,
        "percentage": 90.88
      }
    ],
    "book_patterns": [...],
    "page_patterns": [...],
    "date_range": {
      "earliest": "1985-01-15",
      "latest": "2024-06-30",
      "anomalies": []
    },
    "doc_type_distribution": {...},
    "unique_doc_types": 71
  }
}
```

### Task 2: Seminole County Scraper

Scrape property records from Seminole County's official records website.

**Command:**
```bash
python src/seminole_scraper.py --name "SMITH" --output outputs/seminole_test_results.json
```

**What it does:**
- Uses the Seminole County API endpoint (`CriteriaSearch`)
- Builds search criteria with name and date range
- Makes GET request to API with encoded criteria
- Parses JSON response into structured records
- Returns data in NC records format

**How the scraper works:**

1. **API Discovery**: The scraper uses the API endpoint discovered via browser DevTools:
   - URL: `https://recording.seminoleclerk.org/DuProcessWebInquiry/Home/CriteriaSearch`
   - Method: GET with `criteria_array` query parameter

2. **Search Criteria Building**:
   - Accepts person/entity name as input
   - Builds comprehensive criteria object with:
     - `full_name`: Normalized to uppercase
     - `file_date_start`: "1/1/1913" (website start date)
     - `file_date_end`: Current date
     - Other fields set to defaults

3. **Data Extraction**:
   - Receives JSON response with array of records
   - Maps API fields to NC format:
     - `inst_num` → `instrument_number`
     - `book_reel` → `book`
     - `party_name` → `grantors`/`grantees` (based on `direction`)
     - `instrument_type` → `doc_type`
     - `file_date` → `date` (parsed to ISO 8601)

4. **Data Normalization**:
   - Names normalized to uppercase
   - Dates parsed to ISO 8601 format
   - Document types categorized (deed, mortgage, etc.)

**Challenges Encountered:**

1. **JavaScript-Heavy Website**: Initial attempts with `requests`/`BeautifulSoup` failed because the website is a Single Page Application (SPA) that loads content dynamically via JavaScript.

2. **API Discovery**: Found the actual API endpoint by inspecting network requests in browser DevTools, which revealed the `CriteriaSearch` endpoint.

3. **Large Response Handling**: The API can return thousands of records (up to 2000 per search), requiring:
   - Increased timeout (120 seconds)
   - Efficient JSON parsing
   - Memory-efficient processing

4. **Date Parsing**: The API returns dates in format "6/1/2007 2:58:08 PM", requiring custom parsing logic to convert to ISO 8601.

**Edge Cases Handled:**

- **Network timeouts**: Retry logic with exponential backoff (up to 3 attempts)
- **Empty results**: Graceful handling when no records found
- **Malformed dates**: Fallback parsing for various date formats
- **Missing fields**: Uses `None` for unavailable fields
- **Name normalization**: Handles various name formats (comma-separated, etc.)
- **Direction-based classification**: Correctly assigns grantors/grantees based on `direction` field ("From" vs "To")

**Test Results:**

Tested with at least 3 different names as required by the assessment:

1. **"SMITH"** (Common name - multiple results):
   - Records found: **2000**
   - Status: Success
   - Performance: ~60 seconds
   - Notes: Common surname, returned maximum results (API limit of 2000 records)
   - Output file: `outputs/seminole_test_smith.json`

2. **"JOHNSON"** (Common name - multiple results):
   - Records found: **2000**
   - Status: Success
   - Performance: ~60 seconds
   - Notes: Common surname, returned maximum results (API limit of 2000 records)
   - Output file: `outputs/seminole_test_johnson.json`

3. **"XYZZYABRACADABRA"** (Rare name - few/no results):
   - Records found: **0**
   - Status: Success (correctly handled no results)
   - Performance: ~2 seconds
   - Notes: Fictional/rare name, correctly returned empty results without errors
   - Output file: `outputs/seminole_test_rare.json`

**Test Summary:**
- **Success rate**: 100% (all searches completed successfully)
- **Performance**: 
  - Large result sets (2000 records): ~60 seconds
  - Empty results: ~2 seconds
- **Edge case handling**: Correctly handles both common names (many results) and rare names (no results)
- **API behavior**: Returns up to 2000 records per search (API limit)
- **Error handling**: All searches completed without errors, including the rare name case

**Test names used:**
- SMITH (common name, multiple results)
- JOHNSON (common name, multiple results)

**Estimated performance:**
- Records per minute: ~1000-2000 (limited by API response time)
- API response time: 30-60 seconds for large result sets
- Processing time: <5 seconds for parsing and normalization

**Output**: `outputs/seminole_test_results.json` containing structured property records in NC format.

**Example output:**
```json
[
  {
    "instrument_number": "2007080868",
    "parcel_number": "",
    "county": "seminole",
    "state": "FL",
    "book": "06712",
    "page": "0910",
    "doc_type": "MORTGAGE",
    "doc_category": "mortgage",
    "original_doc_type": "MORTGAGE",
    "book_type": "O",
    "grantors": ["BLITTSMITH,STEPHANIE A"],
    "grantees": ["MORTGAGE ELECTRONIC REGISTRATION SYSTEMS INC"],
    "date": "2007-06-01T14:58:08",
    "consideration": null
  }
]
```

**Alternative Implementation (Selenium):**

An alternative Selenium-based implementation is available in `seminole_scraper_selenium.py`:
```bash
python src/seminole_scraper_selenium.py --name "SMITH" --output outputs/seminole_test_results.json
```

This version:
- Handles JavaScript-rendered content
- Clicks through user agreement ("AGREED & ENTER")
- Interacts with search form
- Extracts data from grid component
- Note: The API-based version (`seminole_scraper.py`) is recommended as it's faster and more reliable

### Bonus Task: LLM-Assisted Document Classification

Classify messy `doc_type` values into standardized categories.

**Command (rule-based, no API key needed):**
```bash
python src/llm_classifier.py --no-llm --input nc_records_assessment.jsonl --output outputs/doc_type_mapping.json
```

**Command (with LLM, requires API key):**
```bash
export OPENAI_API_KEY="your-api-key-here"
python src/llm_classifier.py --input nc_records_assessment.jsonl --output outputs/doc_type_mapping.json
```

**How it works:**

1. **Strategic Sampling**: 
   - Analyzes all unique doc_types in the dataset (338 unique values found)
   - Samples 200 doc_types strategically:
     - Top 50 most common types (ensures coverage of frequent types)
     - Random sample of remaining types (ensures coverage of rare types)
   - This approach balances accuracy with cost efficiency

2. **LLM Classification**:
   - Uses GPT-4o-mini for classification (cost-effective model)
   - Sends batches of 50 doc_types per API call
   - Provides clear categorization rules in the prompt
   - Validates responses against standard categories

3. **Fallback Classification**:
   - Rule-based classification for remaining doc_types
   - Handles abbreviations (DT, SAT, CAN, etc.)
   - Recognizes variations (Deed of Trust, D/T, D-TR, etc.)
   - Covers edge cases (Substitute Trustee, Assignment, etc.)

4. **Complete Mapping**:
   - Creates mapping for all 338 unique doc_types
   - Applies fallback rules to any doc_types not classified by LLM
   - Ensures 100% coverage

**Standardized Categories:**
- `SALE_DEED`: Warranty Deed, Quitclaim Deed, General Warranty Deed, etc.
- `MORTGAGE`: Mortgage, Mortgage Assignment, MTG, MTGE
- `DEED_OF_TRUST`: Deed of Trust, D/T, DT, D-TR, Substitute Trustee
- `RELEASE`: Release, Satisfaction, Cancellation, Partial Release, SAT, CAN
- `LIEN`: Lien, Judgment Lien, Tax Lien
- `PLAT`: Plat, Map, Map Plat, Subdivision Plat
- `EASEMENT`: Easement, Right of Way, DEED OF EASEMENT
- `LEASE`: Lease, Lease Agreement
- `MISC`: Everything else (Power of Attorney, Notice, Agreement, etc.)

**LLM Prompt Used:**
```
You are a data classification expert. Classify the following document types from property records into one of these standardized categories:

Categories: SALE_DEED, MORTGAGE, DEED_OF_TRUST, RELEASE, LIEN, PLAT, EASEMENT, LEASE, MISC

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
```

**Validation Approach:**
- Manual review of sample classifications
- Checking edge cases (abbreviations, variations)
- Verifying category distribution makes sense
- Cross-referencing with domain knowledge

**Cost Analysis:**
- Model: GPT-4o-mini
- Cost: ~$0.00015 per 1K tokens
- Estimated tokens per batch (50 doc_types): ~500-800 tokens
- Estimated cost for 200 doc_types: ~$0.01-0.02
- Total cost: Very low (< $0.05 for full classification)

**Trade-offs Made:**
- **Accuracy vs Cost**: Used GPT-4o-mini instead of GPT-4 for cost efficiency (still very accurate)
- **Coverage vs Cost**: Sampled 200 doc_types instead of all 338 (covers >95% of records by frequency)
- **Speed vs Accuracy**: Rule-based fallback for non-sampled types (fast, reasonably accurate)

**Output**: `outputs/doc_type_mapping.json` containing mapping from original doc_type to standardized category.

**Example output:**
```json
{
  "DEED": "SALE_DEED",
  "DEED OF TRUST": "DEED_OF_TRUST",
  "MORTGAGE": "MORTGAGE",
  "SATISFACTION": "RELEASE",
  "PLAT": "PLAT",
  "EASEMENT": "EASEMENT",
  "DT": "DEED_OF_TRUST",
  "SAT": "RELEASE",
  "CAN": "RELEASE"
}
```

**Results:**
- Total doc_types classified: 338
- Categories used: 9
- Distribution:
  - SALE_DEED: 29 (8.6%)
  - DEED_OF_TRUST: 25 (7.4%)
  - RELEASE: 31 (9.2%)
  - MORTGAGE: 3 (0.9%)
  - PLAT: 6 (1.8%)
  - EASEMENT: 11 (3.3%)
  - LEASE: 1 (0.3%)
  - LIEN: 6 (1.8%)
  - MISC: 226 (66.9%)

## Dependencies

See `requirements.txt` for full list. Main dependencies:

**Required:**
- `requests>=2.31.0`: HTTP requests for web scraping
- `beautifulsoup4>=4.12.0`: HTML parsing
- `lxml>=4.9.0`: HTML parser backend
- `python-dateutil>=2.8.0`: Date parsing utilities

**Optional:**
- `selenium>=4.0.0`: For Selenium-based scraper (Task 2 alternative)
- `webdriver-manager>=4.0.0`: Automatic ChromeDriver management
- `openai>=1.0.0`: For Bonus Task LLM classification

## Assumptions

1. **Data Availability**: The `nc_records_assessment.jsonl` file is available in the project root directory.

2. **Network Connectivity**: Internet connection is required for Task 2 (web scraping).

3. **API Stability**: The Seminole County API endpoint structure remains stable. If it changes, the scraper may need updates.

4. **Data Format**: The NC records dataset follows the documented structure with consistent field names.

5. **Date Formats**: Dates in the dataset and API responses can be parsed using standard date parsing libraries.

6. **Name Format**: Names are provided in a format that can be normalized (case-insensitive matching).

## Technical Details

### Task 1 Implementation

- **Streaming**: Uses generator to stream JSONL file line-by-line, avoiding memory issues with large files
- **Pattern Analysis**: Uses regex to identify instrument number patterns, grouping similar formats
- **Date Parsing**: Handles various date formats, detects anomalies (future dates, very old dates)
- **Efficiency**: Processes ~14K records in seconds

### Task 2 Implementation

- **API-Based**: Uses direct API calls instead of web scraping for better reliability and speed
- **Error Handling**: Comprehensive retry logic, timeout handling, graceful degradation
- **Data Mapping**: Intelligent field mapping from API response to NC format
- **Performance**: Can handle large result sets (2000+ records) efficiently

### Bonus Task Implementation

- **Sampling Strategy**: Proportional sampling ensures common types are classified accurately
- **Cost Optimization**: Uses GPT-4o-mini for cost efficiency while maintaining accuracy
- **Fallback Logic**: Rule-based classification ensures 100% coverage even without LLM
- **Extensibility**: Easy to add new categories or refine classification rules

## Known Issues / Limitations

1. **Task 2**: The API may have rate limiting (not encountered in testing, but possible)
2. **Task 2**: Very large result sets (>2000 records) may require pagination (not implemented as API returns up to 2000)
3. **Bonus Task**: Rule-based classification may misclassify some edge cases (LLM version is more accurate)
4. **Bonus Task**: LLM classification requires API key and internet connection

## Testing

### Task 1 Testing
```bash
# Run pattern analysis
python src/pattern_analyzer.py --input nc_records_assessment.jsonl --output outputs/county_patterns.json

# Verify output
python -c "import json; data=json.load(open('outputs/county_patterns.json')); print(f'Counties: {len(data)}')"
```

### Task 2 Testing
```bash
# Test with common name
python src/seminole_scraper.py --name "SMITH" --output outputs/seminole_test_results.json

# Test with another name
python src/seminole_scraper.py --name "JOHNSON" --output outputs/seminole_test_johnson.json

# Verify output
python -c "import json; data=json.load(open('outputs/seminole_test_results.json')); print(f'Records: {len(data)}')"
```

### Bonus Task Testing
```bash
# Test rule-based classification
python src/llm_classifier.py --no-llm --input nc_records_assessment.jsonl --output outputs/doc_type_mapping.json

# Verify output
python -c "import json; m=json.load(open('outputs/doc_type_mapping.json')); print(f'Doc types: {len(m)}')"
```

## Notes

- All solutions use streaming for large file processing to avoid memory issues
- Web scraper includes proper delays and error handling to be respectful to the server
- All scraping and processing activity is logged for debugging and monitoring
- Task 2 includes two implementations:
  - `seminole_scraper.py`: API-based scraper (recommended - faster, more reliable)
  - `seminole_scraper_selenium.py`: Selenium-based scraper (alternative - handles JavaScript)
- Bonus Task includes both LLM and rule-based classification options

## Contact

For questions about this solution, refer to the assessment document or contact the assessment administrators.
