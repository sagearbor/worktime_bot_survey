import os
import sys

# Ensure the src directory is on the Python path for tests
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ROOT_DIR, 'src')
sys.path.insert(0, SRC_DIR)
