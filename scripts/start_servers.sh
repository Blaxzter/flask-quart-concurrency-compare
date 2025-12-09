#!/bin/bash
# Convenience script to start all servers for benchmarking

echo "Starting IO Benchmark Test Environment"
echo "======================================="
echo ""

# Check if we're in the right directory
if [ ! -f "fastapi_server.py" ]; then
    echo "Error: Please run this script from the 00_scripts/io_benchmark directory"
    exit 1
fi

# Start FastAPI test server in background
echo "1. Starting FastAPI test server on port 8001..."
python fastapi_server.py > fastapi_server.log 2>&1 &
FASTAPI_PID=$!
echo "   PID: $FASTAPI_PID"

# Give it a moment to start
sleep 2

# Start Flask comparison server in background
echo "2. Starting Flask comparison server on port 8002..."
python flask_comparison_server.py > flask_server.log 2>&1 &
FLASK_PID=$!
echo "   PID: $FLASK_PID"

# Give it a moment to start
sleep 2

echo ""
echo "Servers started!"
echo "================"
echo "FastAPI Test Server:    http://localhost:8001 (PID: $FASTAPI_PID)"
echo "Flask Comparison:       http://localhost:8002 (PID: $FLASK_PID)"
echo ""
echo "Now start your Quart application (main Respeak backend) and run:"
echo "  python benchmark.py"
echo ""
echo "To stop the servers:"
echo "  kill $FASTAPI_PID $FLASK_PID"
echo ""
echo "Or run: pkill -f 'python fastapi_server.py' && pkill -f 'python flask_comparison_server.py'"

