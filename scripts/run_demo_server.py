from pathlib import Path
import os
import sys

import uvicorn


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))
    port = int(os.environ.get("PORT", "8001"))
    log_path = root / "uvicorn.log"
    log_file = log_path.open("a", encoding="utf-8", buffering=1)
    sys.stdout = log_file
    sys.stderr = log_file
    print(f"Starting demo server on http://127.0.0.1:{port}/demo/")
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="info")
