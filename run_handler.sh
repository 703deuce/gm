#!/bin/sh
# Run handler.py with the same Python that had pip install run (saved at build time)
exec "$(cat /app/.python3_path)" -u /app/handler.py
