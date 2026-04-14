#!/bin/bash

# Results Viewer Startup Script

echo "🚀 Starting Results Viewer WebApp..."
echo "=================================="

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
elif [ -d "results_env" ]; then
    echo "✓ Activating results environment..."
    source results_env/bin/activate
else
    echo "⚠ No virtual environment found. Using system Python."
fi

# Install dependencies if requirements file exists
if [ -f "results_viewer_requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r results_viewer_requirements.txt
fi

# Start the webapp
echo "🌐 Starting web server on http://localhost:5001"
echo "Press Ctrl+C to stop"
echo ""

python results_viewer.py