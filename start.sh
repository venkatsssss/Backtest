#!/bin/bash

# SageForge Backtesting Module - Startup Script

echo "🚀 Starting SageForge Backtesting Module..."
echo "======================================"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Python is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8 or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python version: $PYTHON_VERSION"
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_warning "Virtual environment not found. Creating..."
        python3 -m venv venv
        print_status "Virtual environment created."
    fi
}

# Activate virtual environment
activate_venv() {
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    print_status "Virtual environment activated."
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    pip install --quiet -r requirements.txt
    print_status "Dependencies installed successfully!"
}

# Check credentials
check_credentials() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        print_warning "Please update .env file with your Angel One API credentials."
        print_warning "Get credentials from: https://smartapi.angelbroking.com/"
        return 1
    fi
    
    if grep -q "your_.*_here" .env; then
        print_warning "Please update .env file with your actual Angel One API credentials."
        print_warning "Running in demo mode for now..."
        return 1
    fi
    
    print_status "Angel One credentials configured."
    return 0
}

# Start backend server
start_backend() {
    print_header "Starting Backend Server..."
    print_status "Backend will start at: http://localhost:8000"
    print_status "API documentation: http://localhost:8000/docs"
    
    cd backend
    python main.py &
    BACKEND_PID=$!
    cd ..
    
    sleep 3
    
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        print_status "Backend server started successfully! (PID: $BACKEND_PID)"
    else
        print_error "Backend server failed to start. Check the logs above."
        exit 1
    fi
}

# Start frontend server
start_frontend() {
    print_header "Starting Frontend Server..."
    print_status "Frontend will start at: http://localhost:3000"
    
    cd frontend
    
    if command -v python3 &> /dev/null; then
        python3 -m http.server 3000 > /dev/null 2>&1 &
        FRONTEND_PID=$!
        print_status "Frontend server started with Python (PID: $FRONTEND_PID)"
    else
        print_error "Python 3 not found. Cannot start frontend server."
        exit 1
    fi
    
    cd ..
    sleep 2
}

# Open browser
open_browser() {
    sleep 3
    print_status "Opening browser..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        xdg-open http://localhost:3000 > /dev/null 2>&1 &
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        open http://localhost:3000 > /dev/null 2>&1 &
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        start http://localhost:3000 > /dev/null 2>&1 &
    fi
}

# Cleanup function
cleanup() {
    print_header "Shutting down servers..."
    
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        print_status "Backend server stopped."
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        print_status "Frontend server stopped."
    fi
    
    pkill -f "python.*main.py" 2>/dev/null || true
    pkill -f "http.server" 2>/dev/null || true
    
    print_status "Cleanup completed."
    exit 0
}

# Set trap for cleanup on exit
trap cleanup EXIT INT TERM

# Main execution
main() {
    print_header "SageForge Backtesting Module Startup"
    print_header "===================================="
    
    check_python
    check_venv
    activate_venv
    install_dependencies
    
    if ! check_credentials; then
        print_warning "Running in demo mode. You can still use all features with simulated data."
        print_warning "Press Ctrl+C to exit and configure credentials, or wait 5 seconds to continue..."
        sleep 5
    fi
    
    start_backend
    start_frontend
    open_browser
    
    print_header "🎉 SageForge Backtesting Module is running!"
    print_header "========================================="
    print_status "Frontend: http://localhost:3000"
    print_status "Backend:  http://localhost:8000" 
    print_status "API Docs: http://localhost:8000/docs"
    print_header ""
    print_status "Press Ctrl+C to stop all servers"
    print_header ""
    
    while true; do
        sleep 10
        
        if ! curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
            print_error "Backend server stopped unexpectedly!"
            exit 1
        fi
    done
}

