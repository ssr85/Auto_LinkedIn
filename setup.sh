#!/bin/bash
# Setup script for LinkedIn Content Automation System

echo "=================================="
echo "LinkedIn Content Automation Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python 3.9 or higher is required"
    echo "Current version: $python_version"
    exit 1
fi

echo "✓ Python version: $python_version"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✓ Pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi
echo ""

# Create logs directory
echo "Creating logs directory..."
if [ ! -d "logs" ]; then
    mkdir logs
    echo "✓ Logs directory created"
else
    echo "⚠️  Logs directory already exists"
fi
echo ""

# Create .env file if it doesn't exist
echo "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ .env file created from template"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your API keys before running!"
    echo ""
else
    echo "⚠️  .env file already exists. Skipping..."
    echo ""
fi

# Make main.py executable
chmod +x main.py
echo "✓ Made main.py executable"
echo ""

echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Set up your Trello board with required lists"
echo "3. Run: python main.py validate"
echo "4. Start using: python main.py research"
echo ""
echo "For help: python main.py --help"
echo ""
