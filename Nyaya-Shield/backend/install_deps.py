#!/usr/bin/env python3
"""
Quick dependency installer for NyayaShield Legal Bot
Run this script in your activated virtual environment
"""

import subprocess
import sys

def install_package(package):
    """Install a package using pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def download_nltk_data():
    """Download required NLTK data"""
    try:
        import nltk
        print("📥 Downloading NLTK data...")
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        print("✅ NLTK data downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download NLTK data: {e}")
        return False

def main():
    """Main installation function"""
    print("🚀 Installing NyayaShield dependencies...")
    
    # Required packages
    packages = [
        "Flask==2.3.3",
        "Flask-CORS==4.0.0", 
        "pandas==2.1.1",
        "scikit-learn==1.3.0",
        "joblib==1.3.2",
        "numpy==1.24.3",
        "nltk==3.8.1"
    ]
    
    # Install packages
    failed_packages = []
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    # Download NLTK data
    if "nltk" not in [p.split("==")[0] for p in failed_packages]:
        download_nltk_data()
    
    # Summary
    if failed_packages:
        print(f"\n❌ Failed to install: {', '.join(failed_packages)}")
        print("Please install these manually using: pip install <package>")
    else:
        print("\n✅ All dependencies installed successfully!")
        print("You can now run: python app.py")

if __name__ == "__main__":
    main()
