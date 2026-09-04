import os
import sys

# 保证 mdhub 包可导入（pytest 不自动把 rootdir 加进 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
