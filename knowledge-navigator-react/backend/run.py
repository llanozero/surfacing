"""后端启动入口：python backend/run.py（端口 8171）。"""

import sys
from pathlib import Path

import uvicorn

# 允许以脚本方式直接运行（python backend/run.py）
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8171, reload=False)
