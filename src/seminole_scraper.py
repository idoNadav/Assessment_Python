"""Task 2: Seminole County, FL Web Scraper.

Scrapes property records from Seminole County's official records website.
"""

import json
import time
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from utils import setup_logging, normalize_name, parse_date


class SeminoleScraper:
    """Scraper for Seminole County property records."""
    
    BASE_URL = "https://recording.seminoleclerk.org/DuProcessWebInquiry/index.html"
    API_URL = "https://recording.seminoleclerk.org/DuProcessWebInquiry/Home/CriteriaSearch"
    SEARCH_URLS = [
        "https://recording.seminoleclerk.org/DuProcessWebInquiry/index.html",
        "https://recording.seminoleclerk.org/DuProcessWebInquiry/search.html",
        "https://recording.seminoleclerk.org/DuProcessWebInquiry/Search.aspx",
    ]
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize the scraper.
        
        Args:
            delay: Delay in seconds between requests
        """
        self.delay = delay
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
    def search_by_name(self, name: str, max_retries: int = 3) -> List[Dict[str, Any]]:
        """
        Search for records by person/entity name using the API endpoint.
        
        Args:
            name: Name to search for
            max_retries: Maximum number of retry attempts for failed requests
            
        Returns:
            List of record dictionaries
        """
        self.logger.info(f"Searching for name: {name}")
        
        for attempt in range(max_retries):
            try:
                from datetime import datetime
                import urllib.parse
                
                today = datetime.now().strftime("%m/%d/%Y")
                
                criteria = {
                    "direction": "",
                    "name_direction": True,
                    "full_name": name.upper(),
                    "file_date_start": "1/1/1913",
                    "file_date_end": today,
                    "inst_type": "",
                    "inst_book_type_id": "",
                    "location_id": "",
                    "book_reel": "",
                    "page_image": "",
                    "greater_than_page": False,
                    "inst_num": "",
                    "description": "",
                    "consideration_value_min": "",
                    "consideration_value_max": "",
                    "parcel_id": "",
                    "legal_section": "",
                    "legal_township": "",
                    "legal_range": "",
                    "legal_square": "",
                    "subdivision_code": "",
                    "block": "",
                    "lot_from": "",
                    "q_NWNW": False,
                    "q_NWNE": False,
                    "q_NWSE": False,
                    "q_NWSW": False,
                    "q_NENW": False,
                    "q_NENE": False,
                    "q_NESW": False,
                    "q_NESE": False,
                    "q_SWNW": False,
                    "q_SWNE": False,
                    "q_SWSW": False,
                    "q_SWSE": False,
                    "q_SENW": False,
                    "q_SENE": False,
                    "q_SESW": False,
                    "q_SESE": False,
                    "q_q_search_type": False,
                    "address_street": "",
                    "address_number": "",
                    "address_parcel": "",
                    "address_ppin": "",
                    "patent_number": ""
                }
                
                criteria_array = json.dumps([criteria])
                encoded_criteria = urllib.parse.quote(criteria_array)
                
                api_url = f"{self.API_URL}?criteria_array={encoded_criteria}"
                self.logger.debug(f"Calling API: {self.API_URL}")
                
                search_response = self._make_request('GET', api_url, timeout=120)
                time.sleep(self.delay)
                
                try:
                    data = search_response.json()
                    self.logger.debug("Received JSON response from API")
                    records = self._parse_api_response(data)
                except (ValueError, json.JSONDecodeError):
                    self.logger.debug("Response is HTML, parsing as HTML")
                    results_soup = BeautifulSoup(search_response.content, 'html.parser')
                    records = self._parse_results_table(results_soup)
                
                all_records = records.copy()
                
                self.logger.info(f"Found {len(all_records)} total records")
                return all_records
                
            except requests.exceptions.Timeout as e:
                self.logger.warning(f"Timeout error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(self.delay * 2)  
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Network error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                time.sleep(self.delay * 2)
                
            except Exception as e:
                self.logger.error(f"Error during search: {e}", exc_info=True)
                if attempt == max_retries - 1:
                    raise
                time.sleep(self.delay)
        
        return []  
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling.
        
        Args:
            method: HTTP method ('GET' or 'POST')
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
        """
        if method.upper() == 'GET':
            response = self.session.get(url, **kwargs)
        else:
            response = self.session.post(url, **kwargs)
        
        response.raise_for_status()
        return response
    
    def _build_search_params(self, name: str, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Build search parameters based on form structure.
        
        Args:
            name: Name to search for
            soup: BeautifulSoup object of the search page
            
        Returns:
            Dictionary of form parameters
        """
        params = {}
        
        name_fields = soup.find_all(['input', 'select'], {
            'name': lambda x: x and ('name' in x.lower() or 'party' in x.lower() or 'search' in x.lower())
        })
        
        if name_fields:
          
            field_name = name_fields[0].get('name')
            params[field_name] = name
        else:
            common_names = ['name', 'searchName', 'partyName', 'grantor', 'grantee', 'party']
            for common_name in common_names:
                if soup.find('input', {'name': common_name}) or soup.find('select', {'name': common_name}):
                    params[common_name] = name
                    break
        
        hidden_inputs = soup.find_all('input', {'type': 'hidden'})
        for hidden in hidden_inputs:
            hidden_name = hidden.get('name')
            hidden_value = hidden.get('value', '')
            if hidden_name:
                params[hidden_name] = hidden_value
        
        if not any('name' in k.lower() or 'party' in k.lower() for k in params.keys()):
            params['name'] = name
            params['searchType'] = 'name'  
        
        return params
    
    def _parse_results_table(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """
        Parse the results table from the HTML.
        
        Args:
            soup: BeautifulSoup object of the results page
            
        Returns:
            List of record dictionaries
        """
        records = []
        
        tables = soup.find_all('table')
        
        if not tables:
            table_divs = soup.find_all('div', class_=lambda x: x and 'table' in x.lower())
            if table_divs:
                self.logger.debug("Found div-based table structure")
        
        rows = []
        for table in tables:
            tbody = table.find('tbody')
            if tbody:
                rows.extend(tbody.find_all('tr'))
            else:
                rows.extend(table.find_all('tr'))
        
        if not rows:
            no_results = soup.find(string=lambda x: x and ('no results' in x.lower() or 'no records' in x.lower()))
            if no_results:
                self.logger.info("No results found")
                return []
            
            self.logger.warning("Could not find results table")
            return []
        
        if rows:
            first_row = rows[0]
            if all(cell.name == 'th' for cell in first_row.find_all(['th', 'td'])):
                rows = rows[1:]
        
        for row in rows:
            try:
                record = self.extract_record_data(row)
                if record:
                    records.append(record)
            except Exception as e:
                self.logger.warning(f"Error extracting record from row: {e}")
                continue
        
        return records
    
    def extract_record_data(self, row) -> Optional[Dict[str, Any]]:
        """
        Extract structured data from a results table row.
        
        Args:
            row: BeautifulSoup element representing a table row
            
        Returns:
            Dictionary with record data in NC format, or None if extraction fails
        """
        cells = row.find_all(['td', 'th'])
        
        if len(cells) < 3:  
            return None
        

        
        record = {
            "instrument_number": None,
            "parcel_number": None,
            "county": "seminole",
            "state": "FL",
            "book": None,
            "page": None,
            "doc_type": None,
            "doc_category": None,
            "original_doc_type": None,
            "book_type": None,
            "grantors": [],
            "grantees": [],
            "date": None,
            "consideration": None
        }
        
        cell_texts = [cell.get_text(strip=True) for cell in cells]
        
        for i, text in enumerate(cell_texts):
            if not text:
                continue
            
            if not record["instrument_number"] and (text.replace('-', '').replace('/', '').isalnum()):
                if len(text) >= 4:  
                    record["instrument_number"] = text
            
            if not record["date"]:
                parsed_date = parse_date(text)
                if parsed_date:
                    record["date"] = parsed_date
            
            if not record["doc_type"] and len(text) < 50 and any(word.isupper() for word in text.split()):
                record["doc_type"] = text.upper()
                record["original_doc_type"] = text

                doc_lower = text.lower()
                if 'deed' in doc_lower:
                    record["doc_category"] = "deed"
                elif 'trust' in doc_lower:
                    record["doc_category"] = "trust"
                elif 'mortgage' in doc_lower:
                    record["doc_category"] = "mortgage"
                elif 'release' in doc_lower or 'satisfaction' in doc_lower:
                    record["doc_category"] = "release"
                elif 'lien' in doc_lower:
                    record["doc_category"] = "lien"
                else:
                    record["doc_category"] = "misc"
            
            if not record["book"] and (text.isdigit() or (len(text) < 10 and text.replace(' ', '').isalnum())):
                record["book"] = text
            
            if not record["page"] and text.isdigit():
                record["page"] = text
            
            if len(text) > 5 and ',' in text:
                if not record["grantors"]:
                    names = [normalize_name(n.strip()) for n in text.split(',')]
                    record["grantors"] = [n for n in names if n]
                elif not record["grantees"]:
                    names = [normalize_name(n.strip()) for n in text.split(',')]
                    record["grantees"] = [n for n in names if n]
            
            if '$' in text or (text.replace(',', '').replace('.', '').isdigit() and len(text) > 3):
                try:
                    amount_str = text.replace('$', '').replace(',', '').strip()
                    if amount_str.replace('.', '').isdigit():
                        record["consideration"] = float(amount_str)
                except (ValueError, AttributeError):
                    pass
        
        if record["instrument_number"] or record["doc_type"] or record["date"]:
            return record
        
        return None
    
    def _parse_api_response(self, data: Any) -> List[Dict[str, Any]]:
        """
        Parse API response (JSON) into record dictionaries.
        
        Args:
            data: JSON response from API (list of records)
            
        Returns:
            List of record dictionaries
        """
        records = []
        
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            if 'data' in data:
                items = data['data']
            elif 'results' in data:
                items = data['results']
            elif 'records' in data:
                items = data['records']
            else:
                items = [v for v in data.values() if isinstance(v, list)]
                items = items[0] if items else []
        else:
            self.logger.warning(f"Unexpected API response format: {type(data)}")
            return []
        
        for item in items:
            if isinstance(item, dict):
                record = self._parse_api_record(item)
                if record:
                    records.append(record)
        
        return records
    
    def _parse_api_record(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse a single record from API response.
        
        API response structure:
        - inst_num: instrument number
        - book_reel: book number
        - page: page number
        - party_name: searched name (grantor or grantee based on direction)
        - cross_party_name: the other party
        - direction: "From" or "To"
        - instrument_type: document type
        - file_date: date filed
        - book_description: book type (e.g., "OFFICIAL RECORDS")
        
        Args:
            item: Dictionary from API response
            
        Returns:
            Record dictionary in NC format, or None
        """
        record = {
            "instrument_number": item.get('inst_num') or item.get('instrument_number'),
            "parcel_number": item.get('parcel_id') or item.get('real_estate_id'),
            "county": "seminole",
            "state": "FL",
            "book": item.get('book_reel') or item.get('book'),
            "page": item.get('page'),
            "doc_type": None,
            "doc_category": None,
            "original_doc_type": item.get('instrument_type') or item.get('instrument_description'),
            "book_type": item.get('book_name') or item.get('book_description'),
            "grantors": [],
            "grantees": [],
            "date": None,
            "consideration": None
        }
        
        if record["original_doc_type"]:
            record["doc_type"] = record["original_doc_type"].upper()
            doc_lower = record["original_doc_type"].lower()
            if 'deed' in doc_lower:
                record["doc_category"] = "deed"
            elif 'mortgage' in doc_lower:
                record["doc_category"] = "mortgage"
            elif 'trust' in doc_lower:
                record["doc_category"] = "trust"
            elif 'judgment' in doc_lower:
                record["doc_category"] = "judgment"
            elif 'order' in doc_lower:
                record["doc_category"] = "order"
            elif 'notice' in doc_lower:
                record["doc_category"] = "notice"
            else:
                record["doc_category"] = "misc"
        
        date_str = item.get('file_date')
        if date_str:
            record["date"] = parse_date(str(date_str))
        
        direction = item.get('direction', '').upper()
        party_name = item.get('party_name')
        cross_party = item.get('cross_party_name')
        
        if party_name:
            name = normalize_name(str(party_name))
            if name:
                if direction == 'FROM':
                    record["grantors"].append(name)
                else:
                    record["grantees"].append(name)
        
        if cross_party:
            name = normalize_name(str(cross_party))
            if name:
                if direction == 'FROM':
                    record["grantees"].append(name)
                else:
                    record["grantors"].append(name)
        
        if record["instrument_number"] or (record["doc_type"] and record["date"]):
            return record
        
        return None
    
    def _handle_pagination(self, soup: BeautifulSoup, search_params: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Handle pagination if multiple pages of results exist.
        
        Args:
            soup: BeautifulSoup object of current results page
            search_params: Original search parameters
            
        Returns:
            List of additional records from subsequent pages
        """
        all_records = []
        
        next_links = soup.find_all('a', string=lambda x: x and ('next' in x.lower() or '>' in x))
        
        page_links = soup.find_all('a', href=lambda x: x and ('page' in x.lower() or 'p=' in x.lower()))
        
        if not next_links and not page_links:
            pagination_divs = soup.find_all(['div', 'span'], class_=lambda x: x and 'pagination' in str(x).lower())
            if pagination_divs:
                for div in pagination_divs:
                    next_links.extend(div.find_all('a', string=lambda x: x and 'next' in x.lower()))
        
        page_num = 2
        max_pages = 10
        
        while page_num <= max_pages:
            pagination_params = search_params.copy()
            pagination_params.update({
                'page': str(page_num),
                'p': str(page_num),
                'pageNum': str(page_num),
                'currentPage': str(page_num)
            })
            
            try:
                self.logger.debug(f"Fetching page {page_num}")
                page_response = self.session.post(
                    self.SEARCH_URL if hasattr(self, 'SEARCH_URL') else self.BASE_URL,
                    data=pagination_params,
                    timeout=30
                )
                page_response.raise_for_status()
                time.sleep(self.delay)
                
                page_soup = BeautifulSoup(page_response.content, 'html.parser')
                page_records = self._parse_results_table(page_soup)
                
                if not page_records:
                    break
                
                all_records.extend(page_records)
                self.logger.debug(f"Found {len(page_records)} records on page {page_num}")
                
                has_next = page_soup.find('a', string=lambda x: x and 'next' in x.lower() if x else False)
                if not has_next:
                    break
                
                page_num += 1
                
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Error fetching page {page_num}: {e}")
                break
            except Exception as e:
                self.logger.warning(f"Error processing page {page_num}: {e}")
                break
        
        return all_records


def scrape_and_save(name: str, output_path: str):
    """
    Scrape records for a name and save to JSON file.
    
    Args:
        name: Name to search for
        output_path: Path to save results
    """
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting scrape for name: {name}")
    
    scraper = SeminoleScraper(delay=1.0)
    
    try:
        records = scraper.search_by_name(name)
        logger.info(f"Found {len(records)} records for '{name}'")
        
        with open(output_path, 'w') as f:
            json.dump(records, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error scraping for '{name}': {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Seminole County property records")
    parser.add_argument("--name", "-n", required=True,
                       help="Name to search for")
    parser.add_argument("--output", "-o", default="outputs/seminole_test_results.json",
                       help="Path to output JSON file")
    
    args = parser.parse_args()
    
    scrape_and_save(args.name, args.output)
