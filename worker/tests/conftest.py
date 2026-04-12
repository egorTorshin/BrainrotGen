import sys
from pathlib import Path

worker_root = Path(__file__).parent.parent
src_path = worker_root / "src"

sys.path.insert(0, str(worker_root))
sys.path.insert(0, str(src_path))

print(f"Added to path: {worker_root}")
print(f"Added to path: {src_path}")
print(f"sys.path: {sys.path[:3]}")
