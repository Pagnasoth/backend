#!/usr/bin/env python
import os
import sys

os.chdir(os.path.dirname(__file__))
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, '.')
from app import analyze, AnalyzeRequest

# Test the analyze function directly
try:
    req = AnalyzeRequest(code='print("hello world")', language='python')
    result = analyze(req)
    print("=== RESULT ===")
    print(result)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

# Check if logs were written
if os.path.exists('gemini_debug.log'):
    print("\n=== GEMINI DEBUG LOG ===")
    with open('gemini_debug.log') as f:
        content = f.read()
        print(content)
else:
    print("\ngemini_debug.log not found")
