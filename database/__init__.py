# Database module initialization
from database.connection import get_db, close_db

__all__ = ["get_db", "close_db"]