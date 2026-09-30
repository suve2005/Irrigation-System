# profile_server.py
"""
Same server as main.py, but every request is logged with
timing + RSS delta. main.py is NOT modified.
"""
import uvicorn

from main import app                       # noqa: F401  (import side effects only)
from benchmark import BenchmarkMiddleware

# Attach middleware *after* import. Since main.py defines no other middleware,
# ordering is not a concern here.
app.add_middleware(BenchmarkMiddleware)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)