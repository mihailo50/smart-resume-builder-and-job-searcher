"""
Base service class for Supabase operations.
"""
import time
import logging
from datetime import date, datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from supabase import Client
from config.supabase import supabase

logger = logging.getLogger(__name__)


def execute_with_retry(query, max_retries: int = 3, delay: float = 0.5):
    """Execute a Supabase query with retry logic for Windows socket issues."""
    last_exception = None
    for attempt in range(max_retries):
        try:
            return query.execute()
        except Exception as e:
            last_exception = e
            error_str = str(e).lower()
            # Retry on Windows socket errors or connection issues
            if 'winerror 10035' in error_str or 'socket' in error_str or 'connection' in error_str:
                if attempt < max_retries - 1:
                    logger.warning(f"Retry {attempt + 1}/{max_retries} after socket error: {e}")
                    time.sleep(delay * (attempt + 1))  # Exponential backoff
                    continue
            raise
    raise last_exception


class BaseSupabaseService:
    """Base class for all Supabase service operations."""
    
    def __init__(self, table_name: str, client: Optional[Client] = None):
        """
        Initialize service with table name.
        
        Args:
            table_name: Name of the Supabase table
            client: Optional Supabase client (uses singleton if not provided)
        """
        self.table_name = table_name
        self.client = client or supabase()
    
    def _serialize_value(self, value: Any) -> Any:
        """Convert datetime/date objects to ISO strings for JSON serialization."""
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        if isinstance(value, dict):
            return self._prepare_data(value)
        return value
    
    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data by serializing date/datetime values to strings."""
        prepared: Dict[str, Any] = {}
        for key, value in data.items():
            prepared[key] = self._serialize_value(value)
        return prepared
    
    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new record.
        
        Args:
            data: Dictionary of data to insert
            
        Returns:
            Dict: Created record
        """
        prepared_data = self._prepare_data(data)
        query = self.client.table(self.table_name).insert(prepared_data)
        response = execute_with_retry(query)
        if response.data:
            return response.data[0]
        return {}
    
    def get_by_id(self, record_id: Any) -> Optional[Dict[str, Any]]:
        """
        Get a record by ID.
        
        Args:
            record_id: ID of the record
            
        Returns:
            Dict: Record data or None if not found
        """
        query = self.client.table(self.table_name).select('*').eq('id', record_id)
        response = execute_with_retry(query)
        if response.data:
            return response.data[0]
        return None
    
    def get_all(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all records with optional filtering.
        
        Args:
            filters: Dictionary of filters (e.g., {'status': 'active'})
            order_by: Column to order by (e.g., 'created_at.desc')
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List: List of records
        """
        query = self.client.table(self.table_name).select('*')
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        if order_by:
            # Handle multiple columns (e.g., 'order.asc,start_date.desc')
            # Split by comma and apply each order
            if ',' in order_by:
                order_parts = [part.strip() for part in order_by.split(',')]
                for order_part in order_parts:
                    # Parse column.direction format
                    if '.' in order_part:
                        col, direction = order_part.rsplit('.', 1)
                        if direction.lower() == 'desc':
                            query = query.order(col, desc=True)
                        else:
                            query = query.order(col, desc=False)
                    else:
                        # Default to ascending if no direction specified
                        query = query.order(order_part, desc=False)
            else:
                # Single column with optional direction
                if '.' in order_by:
                    col, direction = order_by.rsplit('.', 1)
                    if direction.lower() == 'desc':
                        query = query.order(col, desc=True)
                    else:
                        query = query.order(col, desc=False)
                else:
                    query = query.order(order_by, desc=False)
        
        if limit:
            query = query.limit(limit)
        
        if offset:
            query = query.offset(offset)
        
        response = execute_with_retry(query)
        return response.data or []
    
    def update(self, record_id: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a record.
        
        Args:
            record_id: ID of the record to update
            data: Dictionary of data to update
            
        Returns:
            Dict: Updated record or None if not found
        """
        prepared_data = self._prepare_data(data)
        query = self.client.table(self.table_name).update(prepared_data).eq('id', record_id)
        response = execute_with_retry(query)
        if response.data:
            return response.data[0]
        return None
    
    def delete(self, record_id: Any) -> bool:
        """
        Delete a record.
        
        Args:
            record_id: ID of the record to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        query = self.client.table(self.table_name).delete().eq('id', record_id)
        response = execute_with_retry(query)
        return response.data is not None
    
    def search(
        self,
        search_term: str,
        search_columns: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search records across multiple columns.
        
        Args:
            search_term: Term to search for
            search_columns: List of column names to search in
            filters: Optional additional filters
            
        Returns:
            List: List of matching records
        """
        # Supabase text search using ilike (case-insensitive)
        query = self.client.table(self.table_name).select('*')
        
        # Add search conditions (OR across columns)
        search_conditions = []
        for column in search_columns:
            search_conditions.append(f"{column}.ilike.%{search_term}%")
        
        # Note: Supabase doesn't support OR directly, so we'll use a different approach
        # For now, search in the first column - can be enhanced with RPC calls
        if search_columns:
            query = query.ilike(search_columns[0], f"%{search_term}%")
        
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)
        
        response = query.execute()
        return response.data or []



