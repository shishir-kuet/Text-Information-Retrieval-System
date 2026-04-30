#!/usr/bin/env bash
# Start the backend using Gunicorn. Use PORT from environment (Render provides $PORT).
set -euo pipefail

: ${PORT:=5000}

exec gunicorn -w 4 -b 0.0.0.0:${PORT} backend.run:app
