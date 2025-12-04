"""
Location Detection Service.

Supports IP-based geolocation and browser geolocation.
"""
import os
import logging
from typing import Dict, Optional, Any
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class LocationService:
    """Service for detecting user location."""
    
    # Free IP geolocation APIs
    IP_API_SERVICE = 'ipapi.co'  # Free tier: 1000 requests/day
    FALLBACK_API_SERVICE = 'ip-api.com'  # Free tier: 45 requests/minute
    
    def __init__(self):
        """Initialize location service."""
        self.api_key = os.getenv('IP_GEOLOCATION_API_KEY')  # Optional
    
    def get_location_from_ip(self, ip_address: str) -> Dict[str, Any]:
        """
        Get location information from IP address.
        
        Args:
            ip_address: IP address string
            
        Returns:
            Dict: Location information with city, country, etc.
        """
        # Handle localhost/development IPs
        localhost_ips = ['127.0.0.1', '::1', '::ffff:127.0.0.1', 'localhost']
        
        if not ip_address or ip_address in localhost_ips or ip_address.startswith('::'):
            return {
                'success': False,
                'error': 'Localhost IP address detected. Please provide location manually or use browser geolocation.',
                'city': None,
                'country': None,
                'country_code': None,
                'region': None,
                'is_localhost': True,
                'message': 'For development on localhost, please use browser geolocation or enter your location manually.',
            }
        
        # Try ipapi.co first (free tier: 1000 requests/day)
        location = self._get_from_ipapi_co(ip_address)
        
        if not location.get('success'):
            # Fallback to ip-api.com
            location = self._get_from_ip_api_com(ip_address)
        
        return location
    
    def _get_from_ipapi_co(self, ip_address: str) -> Dict[str, Any]:
        """Get location from ipapi.co."""
        try:
            url = f"https://ipapi.co/{ip_address}/json/"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for error in response
                if 'error' in data:
                    return {
                        'success': False,
                        'error': data.get('reason', 'Unknown error'),
                        'city': None,
                        'country': None,
                        'country_code': None,
                        'region': None,
                    }
                
                return {
                    'success': True,
                    'city': data.get('city'),
                    'country': data.get('country_name'),
                    'country_code': data.get('country_code'),
                    'region': data.get('region'),
                    'latitude': data.get('latitude'),
                    'longitude': data.get('longitude'),
                    'timezone': data.get('timezone'),
                    'source': 'ipapi.co'
                }
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"ipapi.co request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'city': None,
                'country': None,
                'country_code': None,
                'region': None,
            }
    
    def _get_from_ip_api_com(self, ip_address: str) -> Dict[str, Any]:
        """Get location from ip-api.com (fallback)."""
        try:
            url = f"http://ip-api.com/json/{ip_address}"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'fail':
                    return {
                        'success': False,
                        'error': data.get('message', 'Unknown error'),
                        'city': None,
                        'country': None,
                        'country_code': None,
                        'region': None,
                    }
                
                return {
                    'success': True,
                    'city': data.get('city'),
                    'country': data.get('country'),
                    'country_code': data.get('countryCode'),
                    'region': data.get('regionName'),
                    'latitude': data.get('lat'),
                    'longitude': data.get('lon'),
                    'timezone': data.get('timezone'),
                    'source': 'ip-api.com'
                }
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"ip-api.com request failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'city': None,
                'country': None,
                'country_code': None,
                'region': None,
            }
    
    def get_client_ip(self, request) -> str:
        """
        Extract client IP address from Django request.
        
        Args:
            request: Django request object
            
        Returns:
            str: IP address
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        
        if x_forwarded_for:
            # Get the first IP in case of proxy chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        
        return ip
    
    def reverse_geocode(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to location (browser geolocation).
        
        Args:
            latitude: Latitude
            longitude: Longitude
            
        Returns:
            Dict: Location information
        """
        try:
            # Use OpenStreetMap Nominatim API (free, no key required)
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': latitude,
                'lon': longitude,
                'format': 'json',
                'addressdetails': 1,
            }
            
            headers = {
                'User-Agent': 'ResumeAI-Pro/1.0'  # Required by Nominatim
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                return {
                    'success': True,
                    'city': address.get('city') or address.get('town') or address.get('village'),
                    'country': address.get('country'),
                    'country_code': address.get('country_code', '').upper(),
                    'region': address.get('state') or address.get('region'),
                    'latitude': latitude,
                    'longitude': longitude,
                    'postcode': address.get('postcode'),
                    'full_address': data.get('display_name'),
                    'source': 'openstreetmap'
                }
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Reverse geocoding failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'city': None,
                'country': None,
                'country_code': None,
                'region': None,
            }
    
    def normalize_location_string(self, location: Dict[str, Any]) -> str:
        """
        Create a normalized location string from location data.
        
        Args:
            location: Location dictionary
            
        Returns:
            str: Location string (e.g., "New York, NY, US")
        """
        parts = []
        
        if location.get('city'):
            parts.append(location['city'])
        
        if location.get('region'):
            parts.append(location['region'])
        elif location.get('country_code'):
            # If no region, use country code
            pass
        
        if location.get('country'):
            parts.append(location['country'])
        elif location.get('country_code'):
            parts.append(location['country_code'])
        
        return ', '.join(parts) if parts else 'Unknown Location'

