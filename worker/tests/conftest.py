import sys
from pathlib import Path

# Получаем путь к корню проекта (worker)
worker_root = Path(__file__).parent.parent

# Путь к src
src_path = worker_root / "src"

# Добавляем оба пути в sys.path
sys.path.insert(0, str(worker_root))  # чтобы видеть worker/
sys.path.insert(0, str(src_path))     # чтобы видеть src/

# Для отладки (опционально)
print(f"Added to path: {worker_root}")
print(f"Added to path: {src_path}")
print(f"sys.path: {sys.path[:3]}")