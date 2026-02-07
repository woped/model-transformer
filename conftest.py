"""conftest.

Loads env variables from a .env and adds them to the projects
root dir and to the `sys.path`.
"""
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the root of your project to the sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

print("sys.path:", sys.path)  # For debugging
print("PYTHONPATH:", os.getenv('PYTHONPATH'))  # For debugging
print("Working Directory:", os.getcwd())  # For debugging
print("Project Root:", project_root)  # For debugging
