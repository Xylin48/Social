"""Passenger entry point for cPanel / Spaceship (Python 3.9)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app as application, init_db

# Initialize tables when Passenger starts the application.
init_db()
