import os
import sys

# Forward to scripts/common/sync_catalog.py
common_path = os.path.join(os.path.dirname(__file__), 'common')
sys.path.insert(0, common_path)
from sync_catalog import sync_catalog

if __name__ == '__main__':
    sync_catalog()
