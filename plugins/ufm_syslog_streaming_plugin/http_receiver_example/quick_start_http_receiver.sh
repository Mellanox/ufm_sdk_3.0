#!/bin/bash
#
# Quick start script for HTTP receiver
# This script helps you quickly set up and test the HTTP receiver
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================="
echo "HTTP Receiver Quick Start"
echo "=========================================="
echo ""

# Function to check if Python3 is installed
check_python() {
    if ! command -v python3 &> /dev/null; then
        echo "Error: python3 is not installed"
        exit 1
    fi
    echo "✓ Python3 is installed: $(python3 --version)"
}

# Function to check if pip3 is installed
check_pip() {
    if ! command -v pip3 &> /dev/null; then
        echo "Error: pip3 is not installed"
        exit 1
    fi
    echo "✓ pip3 is installed"
}

# Function to install dependencies
install_dependencies() {
    echo ""
    echo "Installing dependencies..."
    if [ -f "http_receiver_requirements.txt" ]; then
        pip3 install -r http_receiver_requirements.txt
        echo "✓ Dependencies installed"
    else
        echo "Installing Flask manually..."
        pip3 install Flask==2.3.3 Werkzeug==2.3.7
        echo "✓ Flask installed"
    fi
}

# Function to start the receiver
start_receiver() {
    echo ""
    echo "=========================================="
    echo "Starting HTTP Receiver"
    echo "=========================================="
    echo ""
    echo "The receiver will start on http://0.0.0.0:24226"
    echo "Endpoint: /api/logs"
    echo ""
    echo "Press Ctrl+C to stop the receiver"
    echo ""
    
    python3 http_receiver.py \
        --host 0.0.0.0 \
        --port 24226 \
        --endpoint /api/logs
}

# Main menu
show_menu() {
    echo ""
    echo "What would you like to do?"
    echo ""
    echo "1) Install dependencies"
    echo "2) Start the receiver"
    echo "3) Install and start the receiver"
    echo "4) View documentation"
    echo "5) Exit"
    echo ""
    read -p "Enter your choice [1-5]: " choice
    
    case $choice in
        1)
            check_python
            check_pip
            install_dependencies
            show_menu
            ;;
        2)
            start_receiver
            ;;
        3)
            check_python
            check_pip
            install_dependencies
            start_receiver
            ;;
        4)
            if [ -f "HTTP_RECEIVER_README.md" ]; then
                echo ""
                echo "Opening documentation..."
                if command -v less &> /dev/null; then
                    less HTTP_RECEIVER_README.md
                else
                    cat HTTP_RECEIVER_README.md
                fi
            else
                echo "Documentation not found!"
            fi
            show_menu
            ;;
        5)
            echo ""
            echo "Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid choice. Please try again."
            show_menu
            ;;
    esac
}

# Check basic requirements
check_python
check_pip

# Show menu
show_menu

