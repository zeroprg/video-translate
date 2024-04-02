#!/bin/bash

# Start FastAPI using Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8081 &

# Start Gradio
python main.py
