#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Python is installed
if ! command_exists python; then
    echo -e "${RED}Python is not installed or not in PATH${NC}"
    exit 1
fi

# Check if pip is installed
if ! command_exists pip; then
    echo -e "${RED}pip is not installed or not in PATH${NC}"
    exit 1
fi

echo -e "${GREEN}Starting build process...${NC}"

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to install dependencies${NC}"
    exit 1
fi

# Run unit tests
echo -e "${YELLOW}Running unit tests...${NC}"
python -m pytest test_weather_collector.py -v
if [ $? -ne 0 ]; then
    echo -e "${RED}Unit tests failed${NC}"
    exit 1
fi

# Run coverage report
echo -e "${YELLOW}Generating coverage report...${NC}"
python -m pytest --cov=weather_collector test_weather_collector.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Coverage report generation failed${NC}"
    exit 1
fi

# Test the main script
echo -e "${YELLOW}Testing main script...${NC}"
python weather_collector.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Main script test failed${NC}"
    exit 1
fi

echo -e "${GREEN}Build completed successfully!${NC}" 