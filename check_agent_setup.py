"""
Diagnostic Script for ReAct Agent Setup
Run this to verify all agent files and dependencies are properly installed
"""

import sys
import os
from pathlib import Path

def check_files():
    """Check if all required agent files exist."""
    print("="*80)
    print("CHECKING AGENT FILES")
    print("="*80)
    
    current_dir = Path(__file__).parent.absolute()
    print(f"\nCurrent directory: {current_dir}\n")
    
    required_files = [
        'llm_adapter.py',
        'agent_tools.py',
        'query_router.py',
        'react_agent.py',
        'prompts.py',
        'agent_state.py',
        'test_agent.py',
        'kg_retriever.py',
        'knowledge_graph.py',
    ]
    
    all_present = True
    for filename in required_files:
        filepath = current_dir / filename
        exists = filepath.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {filename:30s} {'FOUND' if exists else 'MISSING'}")
        if not exists:
            all_present = False
    
    return all_present

def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n" + "="*80)
    print("CHECKING DEPENDENCIES")
    print("="*80 + "\n")
    
    dependencies = [
        ('streamlit', 'streamlit'),
        ('langgraph', 'langgraph'),
        ('langchain', 'langchain'),
        ('langchain_core', 'langchain-core'),
        ('networkx', 'networkx'),
        ('pdfplumber', 'pdfplumber'),
    ]
    
    all_installed = True
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {package_name:30s} INSTALLED")
        except ImportError:
            print(f"✗ {package_name:30s} MISSING - Install with: pip install {package_name}")
            all_installed = False
    
    return all_installed

def check_imports():
    """Try to import all agent modules."""
    print("\n" + "="*80)
    print("CHECKING MODULE IMPORTS")
    print("="*80 + "\n")
    
    # Add current directory to path
    current_dir = Path(__file__).parent.absolute()
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    modules = [
        'llm_adapter',
        'agent_tools',
        'query_router',
        'react_agent',
        'prompts',
        'agent_state',
        'kg_retriever',
        'knowledge_graph',
    ]
    
    all_imported = True
    import_errors = {}
    
    for module_name in modules:
        try:
            __import__(module_name)
            print(f"✓ {module_name:30s} IMPORTED")
        except Exception as e:
            print(f"✗ {module_name:30s} IMPORT ERROR")
            print(f"  Error: {str(e)}")
            all_imported = False
            import_errors[module_name] = str(e)
    
    return all_imported, import_errors

def check_python_path():
    """Check Python path configuration."""
    print("\n" + "="*80)
    print("PYTHON PATH CONFIGURATION")
    print("="*80 + "\n")
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"\nPython path (first 5 entries):")
    for i, path in enumerate(sys.path[:5], 1):
        print(f"  {i}. {path}")

def main():
    """Run all diagnostic checks."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "AGENT SETUP DIAGNOSTIC TOOL" + " "*31 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    # Check 1: Files
    files_ok = check_files()
    
    # Check 2: Dependencies
    deps_ok = check_dependencies()
    
    # Check 3: Imports
    imports_ok, import_errors = check_imports()
    
    # Check 4: Python path
    check_python_path()
    
    # Summary
    print("\n" + "="*80)
    print("DIAGNOSTIC SUMMARY")
    print("="*80 + "\n")
    
    print(f"Files Present:        {'✓ YES' if files_ok else '✗ NO - Some files missing'}")
    print(f"Dependencies:         {'✓ YES' if deps_ok else '✗ NO - Install missing packages'}")
    print(f"Imports Working:      {'✓ YES' if imports_ok else '✗ NO - Check errors above'}")
    
    print("\n" + "-"*80 + "\n")
    
    if files_ok and deps_ok and imports_ok:
        print("✓ ALL CHECKS PASSED - Agent setup is complete!")
        print("\nYou can now run:")
        print("  streamlit run app.py")
        print("\nAnd enable Agent Mode in the sidebar.")
    else:
        print("✗ ISSUES DETECTED\n")
        
        if not files_ok:
            print("1. Missing files - Ensure you've pulled the latest code:")
            print("   git pull origin main\n")
        
        if not deps_ok:
            print("2. Missing dependencies - Install with:")
            print("   pip install -r requirements.txt\n")
        
        if not imports_ok:
            print("3. Import errors detected:")
            for module, error in import_errors.items():
                print(f"   - {module}: {error[:100]}")
            print("\n   Try:")
            print("   - Check for syntax errors in the files")
            print("   - Ensure all dependencies are installed")
            print("   - Restart your Python environment\n")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()

