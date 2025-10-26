"""Check if all required dependencies are installed"""
import sys

required_packages = {
    'flask': 'Flask',
    'flask_cors': 'Flask-CORS',
    'pandas': 'pandas',
    'sklearn': 'scikit-learn',
    'joblib': 'joblib',
    'numpy': 'numpy',
    'nltk': 'nltk',
    'requests': 'requests'
}

print("=" * 60)
print("DEPENDENCY CHECK REPORT")
print("=" * 60)
print(f"Python Version: {sys.version}")
print("-" * 60)

missing = []
installed = []

for module_name, package_name in required_packages.items():
    try:
        __import__(module_name)
        installed.append(package_name)
        print(f"✓ {package_name:20s} - INSTALLED")
    except ImportError:
        missing.append(package_name)
        print(f"✗ {package_name:20s} - MISSING")

print("-" * 60)
print(f"\nInstalled: {len(installed)}/{len(required_packages)}")
print(f"Missing: {len(missing)}/{len(required_packages)}")

if missing:
    print("\n⚠️  MISSING PACKAGES:")
    for pkg in missing:
        print(f"   - {pkg}")
    print("\nTo install missing packages, run:")
    print("   pip install -r requirements.txt")
    sys.exit(1)
else:
    print("\n✓ All required packages are installed!")
    sys.exit(0)
