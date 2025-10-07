#!/bin/bash

echo "Setting up Document Chat Bot..."
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install goldmansachs.awm_genai -U
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    echo "Please edit .env file with your credentials"
fi

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit config.py with your App ID and credentials"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run Streamlit app: streamlit run app.py"
echo "   OR"
echo "   Run Jupyter notebook: jupyter notebook chatbot.ipynb"
echo ""

