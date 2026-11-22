import os
import sys

# Forward to scripts/common/export_handoff.py
common_path = os.path.join(os.path.dirname(__file__), 'common')
sys.path.insert(0, common_path)
from export_handoff import export_handoff

if __name__ == '__main__':
    export_handoff()
