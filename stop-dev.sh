#!/bin/bash

echo "Stopping all optical designer services..."

# Kill backend
pkill -f "python main.py"
pkill -f "uvicorn"

# Kill frontend  
pkill -f "vite"
pkill -f "npm run dev"

echo "✅ All services stopped"
