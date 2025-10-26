"""Simple verification script for Nyaya-Shield"""
import sys
import os

print("Starting verification...")

# Test 1: Python version
print(f"\n1. Python Version: {sys.version}")

# Test 2: Dependencies
print("\n2. Checking Dependencies:")
deps = ['flask', 'pandas', 'sklearn', 'joblib', 'numpy', 'nltk']
for dep in deps:
    try:
        __import__(dep)
        print(f"   OK: {dep}")
    except:
        print(f"   MISSING: {dep}")

# Test 3: File structure
print("\n3. Checking Files:")
files = ['app.py', 'bot/nlp_service.py', 'bot/bot_controller.py']
for f in files:
    exists = os.path.exists(f)
    print(f"   {'OK' if exists else 'MISSING'}: {f}")

# Test 4: Try importing app
print("\n4. Testing App Import:")
try:
    import app
    print("   OK: app.py imported")
    print(f"   Flask app: {app.app.name}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\nVerification complete!")
