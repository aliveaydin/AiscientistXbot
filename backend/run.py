import uvicorn
import os
import sys

# Add backend directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    is_docker = os.path.exists("/.dockerenv")

    if is_docker:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            workers=1,
        )
    else:
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=port,
            reload=True,
            reload_dirs=[os.path.dirname(__file__)],
        )
