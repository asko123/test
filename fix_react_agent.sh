#!/bin/bash
# Quick fix script for react_agent.py syntax error

echo "Fixing react_agent.py syntax error..."

# Check if file exists
if [ ! -f "react_agent.py" ]; then
    echo "ERROR: react_agent.py not found in current directory"
    echo "Please run this script from the directory containing react_agent.py"
    exit 1
fi

# Create backup
cp react_agent.py react_agent.py.backup
echo "Created backup: react_agent.py.backup"

# Fix the typo on line 361
# This replaces 'self_agent' with 'self.agent' and ensures 'is not None' is complete
sed -i.tmp 's/return self_agent is not$/return self.agent is not None/g' react_agent.py

# Remove temp file
rm -f react_agent.py.tmp react_agent.py.tmp.backup

# Verify fix
if grep -q "return self.agent is not None" react_agent.py; then
    echo "✓ Fix applied successfully!"
    echo ""
    echo "Verifying syntax..."
    if python -m py_compile react_agent.py 2>/dev/null; then
        echo "✓ Syntax check passed!"
        echo ""
        echo "You can now run: streamlit run app.py"
    else
        echo "✗ Syntax check failed"
        echo "Restoring backup..."
        mv react_agent.py.backup react_agent.py
        exit 1
    fi
else
    echo "✗ Fix may not have applied correctly"
    echo "Please check react_agent.py manually"
fi

