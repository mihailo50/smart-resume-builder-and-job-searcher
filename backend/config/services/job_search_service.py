"""
Job Search Service for external job APIs.

Supports Adzuna API (free tier: 1000 requests/day).
"""
import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AdzunaJobSearchService:
    """Service for searching jobs using Adzuna API."""
    
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"
    DEFAULT_COUNTRY = "US"
    DEFAULT_PAGE = 1
    DEFAULT_RESULTS_PER_PAGE = 20
    MAX_RESULTS_PER_PAGE = 50
    
    # Country codes supported by Adzuna
    SUPPORTED_COUNTRIES = {
        'US': 'us',
        'GB': 'gb',
        'AU': 'au',
        'CA': 'ca',
        'DE': 'de',
        'AT': 'at',
        'IT': 'it',
        'ES': 'es',
        'PL': 'pl',
        'FR': 'fr',
        'NL': 'nl',
        'BR': 'br',
        'MX': 'mx',
        'IN': 'in',
        'NZ': 'nz',
        'ZA': 'za',
        'SG': 'sg',
        'IE': 'ie',
        'CH': 'ch',
    }
    
    def __init__(self):
        """Initialize Adzuna API client."""
        self.app_id = os.getenv('ADZUNA_APP_ID')
        # Support both ADZUNA_API_KEY and ADZUNA_APP_KEY for backwards compatibility
        self.app_key = os.getenv('ADZUNA_API_KEY') or os.getenv('ADZUNA_APP_KEY')
        
        if not self.app_id or not self.app_key:
            logger.warning(
                "Adzuna API credentials not configured. "
                "Set ADZUNA_APP_ID and ADZUNA_API_KEY in your .env file."
            )
    
    def _get_country_code(self, country: str) -> str:
        """Convert country code to Adzuna format."""
        country_upper = country.upper()
        return self.SUPPORTED_COUNTRIES.get(country_upper, self.SUPPORTED_COUNTRIES[self.DEFAULT_COUNTRY])
    
    def search_jobs(
        self,
        query: str,
        location: Optional[str] = None,
        country: Optional[str] = None,
        job_type: Optional[str] = None,
        remote: Optional[bool] = None,
        max_results: int = 20,
        page: int = 1
    ) -> Dict[str, Any]:
        """
        Search for jobs using Adzuna API.
        
        Args:
            query: Search query (job title, keywords)
            location: Location string (city, state, etc.)
            country: Country code (default: US)
            job_type: Job type (full_time, part_time, contract, internship, freelance)
            remote: Filter remote jobs only
            max_results: Maximum number of results (default: 20, max: 50)
            page: Page number (default: 1)
            
        Returns:
            Dict: Search results with jobs and metadata
        """
        if not self.app_id or not self.app_key:
            return {
                'success': False,
                'error': 'Adzuna API credentials not configured',
                'results': [],
                'count': 0
            }
        
        # Normalize country code
        country_code = self._get_country_code(country or self.DEFAULT_COUNTRY)
        
        # Build API URL
        url = f"{self.BASE_URL}/{country_code}/search/{page}"
        
        # Prepare parameters
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
            'results_per_page': min(max_results, self.MAX_RESULTS_PER_PAGE),
            'what': query,  # Job title/keywords
        }
        
        # Add location filter
        if location:
            params['where'] = location
        
        # Add job type filter
        if job_type:
            # Map internal job types to Adzuna format
            job_type_map = {
                'full-time': 'full_time',
                'part-time': 'part_time',
                'contract': 'contract',
                'internship': 'internship',
                'freelance': 'freelance',
            }
            adzuna_job_type = job_type_map.get(job_type.lower(), job_type.lower())
            params['full_time'] = '1' if adzuna_job_type == 'full_time' else '0'
            params['part_time'] = '1' if adzuna_job_type == 'part_time' else '0'
            params['contract'] = '1' if adzuna_job_type == 'contract' else '0'
            params['internship'] = '1' if adzuna_job_type == 'internship' else '0'
        
        # Remote filter (Adzuna uses location0 for remote)
        if remote:
            params['location0'] = 'us'  # Remote jobs
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Transform Adzuna results to our format
            jobs = []
            for result in data.get('results', []):
                job = self._transform_job(result, country_code)
                jobs.append(job)
            
            return {
                'success': True,
                'results': jobs,
                'count': len(jobs),
                'total_results': data.get('count', len(jobs)),
                'page': page,
                'total_pages': (data.get('count', 0) // max_results) + 1,
                'source': 'adzuna'
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Adzuna API error: {e}")
            return {
                'success': False,
                'error': f'Failed to search jobs: {str(e)}',
                'results': [],
                'count': 0
            }
    
    def _transform_job(self, adzuna_job: Dict[str, Any], country_code: str) -> Dict[str, Any]:
        """
        Transform Adzuna job format to our internal format.
        
        Args:
            adzuna_job: Job data from Adzuna API
            country_code: Country code
            
        Returns:
            Dict: Transformed job data
        """
        # Extract salary information
        salary_min = adzuna_job.get('salary_min')
        salary_max = adzuna_job.get('salary_max')
        salary_is_predicted = adzuna_job.get('salary_is_predicted', False)
        
        # Determine remote type
        location_raw = adzuna_job.get('location', {}).get('display_name', '')
        remote_type = 'remote' if 'remote' in location_raw.lower() else 'onsite'
        
        # Determine job type
        job_type = 'full-time'  # Default
        if adzuna_job.get('contract_time', '').lower() in ['part_time', 'parttime']:
            job_type = 'part-time'
        elif adzuna_job.get('contract_time', '').lower() in ['contract']:
            job_type = 'contract'
        elif adzuna_job.get('contract_time', '').lower() in ['internship']:
            job_type = 'internship'
        
        # Format posted date
        posted_date = None
        created = adzuna_job.get('created')
        if created:
            try:
                posted_date = datetime.strptime(created, '%Y-%m-%dT%H:%M:%SZ').date()
            except (ValueError, TypeError):
                pass
        
        # Extract description (combine description and snippet)
        description_parts = []
        if adzuna_job.get('description'):
            description_parts.append(adzuna_job['description'])
        if adzuna_job.get('snippet'):
            description_parts.append(adzuna_job['snippet'])
        description = ' '.join(description_parts) or ''
        
        return {
            'external_id': str(adzuna_job.get('id', '')),
            'title': adzuna_job.get('title', ''),
            'company': adzuna_job.get('company', {}).get('display_name', 'Unknown Company'),
            'location': location_raw,
            'remote_type': remote_type,
            'job_type': job_type,
            'description': description,
            'requirements': adzuna_job.get('description', ''),  # Use description as requirements if separate not available
            'salary_min': float(salary_min) if salary_min else None,
            'salary_max': float(salary_max) if salary_max else None,
            'currency': adzuna_job.get('salary_currency', 'USD'),
            'application_url': adzuna_job.get('redirect_url', ''),
            'company_url': adzuna_job.get('company', {}).get('url', ''),
            'posted_date': posted_date,
            'source': 'adzuna',
            'source_id': str(adzuna_job.get('id', '')),
            'category': adzuna_job.get('category', {}).get('label', ''),
            'raw_data': adzuna_job  # Store raw data for reference
        }
    
    def get_job_details(self, job_id: str, country: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a specific job.
        
        Args:
            job_id: Adzuna job ID
            country: Country code
            
        Returns:
            Dict: Detailed job information or None if not found
        """
        if not self.app_id or not self.app_key:
            return None
        
        country_code = self._get_country_code(country or self.DEFAULT_COUNTRY)
        url = f"{self.BASE_URL}/{country_code}/jobs/{job_id}"
        
        params = {
            'app_id': self.app_id,
            'app_key': self.app_key,
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return self._transform_job(data, country_code)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Adzuna API error fetching job {job_id}: {e}")
            return None

