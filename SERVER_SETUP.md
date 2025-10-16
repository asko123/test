# Server Setup Guide for Agent Integration

## Quick Diagnosis

If you're getting import errors on your server, run this first:

```bash
cd /Users/Tawfiq/Desktop/test
python check_agent_setup.py
```

This will show you exactly what's missing.

---

## Installation Steps for Server

### Step 1: Verify Python Environment

```bash
# Check Python version (needs 3.8+)
python --version

# Check if you're in the right directory
pwd
# Should output: /Users/Tawfiq/Desktop/test
```

### Step 2: Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt
```

**Expected packages:**
- streamlit
- pdfplumber
- networkx
- matplotlib
- langgraph ← **NEW**
- langchain ← **NEW**
- langchain-core ← **NEW**
- goldmansachs.awm_genai (must be pre-installed in your environment)

### Step 3: Verify Installation

```bash
# Run diagnostic
python check_agent_setup.py
```

**Expected output:**
```
✓ Files Present:        YES
✓ Dependencies:         YES  
✓ Imports Working:      YES

✓ ALL CHECKS PASSED
```

### Step 4: Run Streamlit

```bash
streamlit run app.py
```

The app will automatically:
- Detect if agent modules are available
- Show appropriate error messages if not
- Fall back to simple mode gracefully

---

## Troubleshooting Server-Specific Issues

### Issue: "No module named 'goldmansachs'"

**This package is only available in Goldman Sachs environments.**

**Check:**
1. Are you running in a GS-approved environment?
2. Is the package installed in your Python environment?

**Verify:**
```bash
python -c "from goldmansachs.awm_genai import LLM; print('Available!')"
```

**If not available:**
- Contact your IT team for access
- Use a GS workstation
- Configure proper credentials

### Issue: "No module named 'langgraph'"

**Solution:**
```bash
pip install langgraph langchain langchain-core
```

**If pip install fails:**
```bash
# Try with --user flag
pip install --user langgraph langchain langchain-core

# Or upgrade pip first
pip install --upgrade pip
pip install langgraph langchain langchain-core
```

### Issue: Import works locally but not on server

**Cause:** Different Python environments

**Solution:**
```bash
# On server, check which Python you're using
which python
which pip

# Make sure you're installing to the right Python
/full/path/to/python -m pip install -r requirements.txt

# Then run with that Python
/full/path/to/python -m streamlit run app.py
```

### Issue: "ModuleNotFoundError" even after install

**Solution:**
```bash
# 1. Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -name "*.pyc" -delete

# 2. Reinstall dependencies
pip uninstall langgraph langchain langchain-core -y
pip install langgraph langchain langchain-core

# 3. Restart Streamlit
streamlit run app.py
```

---

## Server Environment Checklist

### Before Running

- [ ] Python 3.8+ installed
- [ ] In correct directory (`/Users/Tawfiq/Desktop/test`)
- [ ] `goldmansachs.awm_genai` package accessible
- [ ] All files present (check with `ls *.py | grep agent`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Diagnostic passes (`python check_agent_setup.py`)

### First Run

- [ ] Run: `streamlit run app.py`
- [ ] Check sidebar for "ReAct Agent" section
- [ ] If error shown, read the error message carefully
- [ ] Follow troubleshooting steps in error message

### If Agent Not Working

The app will gracefully degrade:
- ✅ Knowledge Graph features still work
- ✅ Simple chat mode works
- ❌ Agent mode disabled (with clear error message)

You can still use the app with KG enhancement even if agent doesn't initialize!

---

## Quick Commands Reference

### Diagnosis
```bash
python check_agent_setup.py
```

### Installation
```bash
pip install -r requirements.txt
```

### Run App
```bash
streamlit run app.py
```

### Test Imports Manually
```bash
python -c "import react_agent; print('OK')"
python -c "import llm_adapter; print('OK')"
python -c "import agent_tools; print('OK')"
```

### Check File Locations
```bash
ls -la | grep -E "(agent|adapter|router|prompts)"
```

---

## Understanding the Error Messages

### In Streamlit Sidebar

If you see a red error box under "ReAct Agent":

```
Agent modules not available

Error: No module named 'langgraph'

Troubleshooting:
1. Ensure all agent files exist in: /Users/Tawfiq/Desktop/test
2. Required files: [list of files]
3. Install dependencies: pip install langgraph langchain langchain-core
4. Restart the Streamlit app
```

**This is helpful!** It tells you:
- What's missing
- Where it's looking
- How to fix it
- What to do next

### In Terminal/Console

When starting the app, you might see:

```
[WARNING] Agent modules not available: No module named 'langgraph'
[INFO] Current directory: /Users/Tawfiq/Desktop/test
[INFO] Python path: ['/Users/Tawfiq/Desktop/test', ...]
```

**This is diagnostic output** showing:
- What went wrong
- Where the app is running from
- Where it's searching for modules

---

## Working Configuration

Once everything is set up correctly, you should see:

### In Sidebar:
```
✓ ReAct Agent
  [✓] Enable Agent Mode
  [✓] Show Reasoning Trace
```

### After Processing Documents:
```
Successfully processed 2 documents! Agent mode ready!
```

### In Chat:
```
Ready to chat! 2 documents loaded.
KG: 145 entities, 312 relationships
```

---

## Fallback Mode

**Even if agent fails to initialize, the app still works!**

The app will:
1. Show clear error message in sidebar
2. Disable agent checkbox
3. Continue with Knowledge Graph enhancement
4. Provide full functionality except agent mode

You still get:
- ✅ Document upload and extraction
- ✅ Knowledge Graph entity extraction
- ✅ Relationship detection
- ✅ Enhanced context retrieval
- ✅ Chat interface
- ❌ ReAct Agent multi-step reasoning (disabled)

---

## Summary

**The app is designed to be resilient:**

1. **Automatic path handling** - Finds modules in same directory
2. **Graceful degradation** - Works even if agent fails
3. **Clear error messages** - Shows exactly what's wrong
4. **Diagnostic script** - Helps you identify issues
5. **Fallback mode** - KG features still work

**Run the diagnostic script** to get started:
```bash
python check_agent_setup.py
```

It will tell you exactly what needs to be fixed!

