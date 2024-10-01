#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up AI File Translator project...${NC}"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv .venv

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs

# Create .env file for API key
echo -e "${YELLOW}Creating .env file for API key...${NC}"
if [ ! -f .env ]; then
    echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
    echo -e "${GREEN}Created .env file. Please edit it to add your Anthropic API key.${NC}"
else
    echo -e "${GREEN}.env file already exists. Please ensure it contains your Anthropic API key.${NC}"
fi

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To activate the virtual environment, run:${NC}"
echo -e "${GREEN}source .venv/bin/activate${NC}"
echo -e "${YELLOW}To run the script, use:${NC}"
echo -e "${GREEN}python main.py --path /path/to/files --model claude-3-haiku-20240307 --default-lang en${NC}"

