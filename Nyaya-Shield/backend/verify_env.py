import sys
import os

def main():
    print("=== Environment Verification ===")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    print("\n=== Testing Imports ===")
    
    # Test basic imports
    try:
        import flask
        print("✓ Flask:", flask.__version__)
    except ImportError as e:
        print("✗ Flask import failed:", str(e))
    
    try:
        import torch
        print(f"✓ PyTorch: {torch.__version__}")
        print(f"  CUDA available: {torch.cuda.is_available()}")
    except ImportError as e:
        print("✗ PyTorch import failed:", str(e))
    
    try:
        from transformers import pipeline
        print("✓ Transformers:", pipeline.__module__.split('.')[0])
    except ImportError as e:
        print("✗ Transformers import failed:", str(e))
    
    try:
        from sentence_transformers import SentenceTransformer
        print("✓ Sentence Transformers: Installed")
    except ImportError as e:
        print("✗ Sentence Transformers import failed:", str(e))

if __name__ == "__main__":
    main()
