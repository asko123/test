# Troubleshooting Agent Import Errors

## Diagnostic Results

Run the diagnostic script to identify issues:
```bash
python check_agent_setup.py
```

## Common Issues & Solutions

### Issue 1: "No module named 'langgraph'"

**Cause:** LangGraph dependency not installed

**Solution:**
```bash
pip install langgraph
# or install all dependencies
pip install -r requirements.txt
```

### Issue 2: "No module named 'goldmansachs'"

**Cause:** Goldman Sachs internal package not available in current environment

**This is EXPECTED if you're running on a server without Goldman Sachs package access.**

**Solutions:**

#### Option A: Use a Compatible Environment
```bash
# Activate environment with goldmansachs package
source /path/to/gs-venv/bin/activate

# Then run Streamlit
streamlit run app.py
```

#### Option B: Run Where GS Package is Available
The `goldmansachs.awm_genai` package is only available in Goldman Sachs environments. Run the app:
- On a GS workstation
- In a GS-approved environment
- With proper GS credentials configured

### Issue 3: Import errors for react_agent, llm_adapter

**Cause:** These modules depend on other packages that aren't installed

**Solution:**
1. Install ALL dependencies first:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify goldmansachs package is accessible:
   ```python
   python -c "from goldmansachs.awm_genai import LLM; print('GS LLM available!')"
   ```

3. If still failing, check for syntax errors:
   ```bash
   python -m py_compile react_agent.py
   python -m py_compile llm_adapter.py
   ```

## Running Diagnostic

### Step 1: Check Setup
```bash
python check_agent_setup.py
```

### Step 2: Review Output

**All Checks Pass:**
```
✓ Files Present:        YES
✓ Dependencies:         YES  
✓ Imports Working:      YES

✓ ALL CHECKS PASSED - Agent setup is complete!
```

**Issues Detected:**
The script will show exactly what's missing and how to fix it.

### Step 3: Install Missing Items

**If dependencies missing:**
```bash
pip install -r requirements.txt
```

**If files missing:**
```bash
git pull origin main
```

### Step 4: Verify
```bash
python check_agent_setup.py
```

Should now show all checks passing.

## Path Issues

### The app.py now includes automatic path handling:

```python
# Ensure current directory is in Python path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
```

This means the app will automatically find modules in the same directory.

### If you're still getting import errors:

1. **Check working directory:**
   ```bash
   pwd
   # Should be: /path/to/test
   ```

2. **Run from correct directory:**
   ```bash
   cd /Users/Tawfiq/Desktop/test
   streamlit run app.py
   ```

3. **Check file permissions:**
   ```bash
   ls -la *.py | grep agent
   # All files should be readable
   ```

## Environment-Specific Notes

### Running on Goldman Sachs Infrastructure

**Required:**
- Valid App ID
- Proper environment (UAT or PROD)
- Access to `goldmansachs.awm_genai` package

**Configuration in `config.py`:**
```python
APP_ID = "your_app_id"
ENV = "uat"  # or "prod"
```

### Running on External Servers

**Note:** The `goldmansachs.awm_genai` package is proprietary and only available in GS environments. 

**If you see:**
```
ModuleNotFoundError: No module named 'goldmansachs'
```

This means you're running in an environment without access to GS packages. You need to:
1. Move to a GS-approved environment
2. Configure proper credentials
3. Use an environment with the GS package installed

## Quick Fix Checklist

- [ ] All agent files present (`python check_agent_setup.py`)
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Running from correct directory (`cd /Users/Tawfiq/Desktop/test`)
- [ ] Goldman Sachs package accessible (check with your IT team)
- [ ] App ID and environment configured in `config.py`
- [ ] Restart Streamlit after installing dependencies

## Still Having Issues?

### Check these files exist:
```bash
ls -1 *agent*.py *adapter*.py *router*.py prompts.py
```

Expected output:
```
agent_state.py
agent_tools.py
check_agent_setup.py
llm_adapter.py
query_router.py
react_agent.py
test_agent.py
prompts.py
```

### Verify Python can see the modules:
```python
python -c "import sys; sys.path.insert(0, '.'); import react_agent; print('OK!')"
```

### Check for circular imports:
```bash
python -c "import react_agent"
python -c "import llm_adapter"
python -c "import agent_tools"
```

If any fail, the error message will show the specific issue.

## Contact Support

If none of these solutions work:

1. Run diagnostic: `python check_agent_setup.py > diagnostic_output.txt`
2. Share the output with your team
3. Include your Python version and environment details

## Workaround: Disable Agent Mode

If you need to run the app immediately without agent capabilities:

**Edit `config.py`:**
```python
ENABLE_AGENT_MODE = False  # Disable agent features
```

This will let you use the Knowledge Graph features without the agent while you troubleshoot the import issues.

