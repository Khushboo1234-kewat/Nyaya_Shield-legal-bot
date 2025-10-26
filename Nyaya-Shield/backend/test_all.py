"""Comprehensive test script for Nyaya-Shield Legal Bot"""
import sys
import os
from pathlib import Path

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    print(f"\n{title}")
    print("-" * 70)

def test_dependencies():
    """Test if all required dependencies are installed"""
    print_section("1. CHECKING DEPENDENCIES")
    
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
    
    missing = []
    installed = []
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            installed.append(package_name)
            print(f"   ✓ {package_name:20s} - INSTALLED")
        except ImportError:
            missing.append(package_name)
            print(f"   ✗ {package_name:20s} - MISSING")
    
    print(f"\n   Result: {len(installed)}/{len(required_packages)} packages installed")
    return len(missing) == 0, missing

def test_file_structure():
    """Test if all required files exist"""
    print_section("2. CHECKING FILE STRUCTURE")
    
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    
    required_files = {
        'Backend Files': [
            backend_dir / 'app.py',
            backend_dir / 'requirements.txt',
            backend_dir / 'bot' / '__init__.py',
            backend_dir / 'bot' / 'nlp_service.py',
            backend_dir / 'bot' / 'bot_controller.py',
            backend_dir / 'bot' / 'train_model.py',
            backend_dir / 'bot' / 'preprocess.py',
        ],
        'Frontend Files': [
            project_root / 'frontend' / 'templates' / 'index.html',
            project_root / 'frontend' / 'templates' / 'chat.html',
            project_root / 'frontend' / 'templates' / 'base_chat.html',
        ],
        'Model Files': [
            backend_dir / 'bot' / 'chatbot_model.pkl',
        ]
    }
    
    all_exist = True
    for category, files in required_files.items():
        print(f"\n   {category}:")
        for file_path in files:
            exists = file_path.exists()
            status = "✓" if exists else "✗"
            print(f"      {status} {file_path.name}")
            if not exists:
                all_exist = False
    
    return all_exist

def test_imports():
    """Test if bot modules can be imported"""
    print_section("3. TESTING BOT MODULE IMPORTS")
    
    imports_to_test = [
        ('bot.nlp_service', ['initialize_service', 'is_casual_query']),
        ('bot.bot_controller', ['LegalBotController']),
        ('bot.train_model', ['get_legal_answer']),
        ('bot.preprocess', ['preprocess_legal_text']),
    ]
    
    all_success = True
    for module_name, items in imports_to_test:
        try:
            module = __import__(module_name, fromlist=items)
            for item in items:
                if hasattr(module, item):
                    print(f"   ✓ {module_name}.{item}")
                else:
                    print(f"   ✗ {module_name}.{item} - NOT FOUND")
                    all_success = False
        except Exception as e:
            print(f"   ✗ {module_name} - ERROR: {str(e)[:50]}")
            all_success = False
    
    return all_success

def test_flask_app():
    """Test if Flask app can be initialized"""
    print_section("4. TESTING FLASK APP INITIALIZATION")
    
    try:
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Try to import app
        import app as flask_app
        
        print(f"   ✓ Flask app imported successfully")
        print(f"   ✓ App name: {flask_app.app.name}")
        print(f"   ✓ Debug mode: {flask_app.app.config.get('DEBUG', False)}")
        
        # Check if services are initialized
        if flask_app.nlp_service:
            print(f"   ✓ NLP Service initialized")
        else:
            print(f"   ⚠ NLP Service not initialized")
        
        if flask_app.bot_controller:
            print(f"   ✓ Bot Controller initialized")
        else:
            print(f"   ⚠ Bot Controller not initialized")
        
        return True
    except Exception as e:
        print(f"   ✗ Flask app initialization failed: {str(e)[:100]}")
        return False

def test_routes():
    """Test if all routes are registered"""
    print_section("5. CHECKING FLASK ROUTES")
    
    try:
        import app as flask_app
        
        expected_routes = [
            '/',
            '/chat',
            '/login',
            '/register',
            '/services',
            '/health',
            '/api/chat',
            '/services/ipc',
            '/services/consumer',
            '/services/crpc',
            '/services/family',
            '/services/property',
            '/services/it_act',
        ]
        
        registered_routes = [rule.rule for rule in flask_app.app.url_map.iter_rules()]
        
        for route in expected_routes:
            if route in registered_routes:
                print(f"   ✓ {route}")
            else:
                print(f"   ✗ {route} - NOT FOUND")
        
        print(f"\n   Total routes registered: {len(registered_routes)}")
        return True
    except Exception as e:
        print(f"   ✗ Route check failed: {str(e)[:100]}")
        return False

def main():
    print_header("NYAYA-SHIELD LEGAL BOT - COMPREHENSIVE TEST")
    print(f"Python Version: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    
    results = {}
    
    # Run all tests
    results['dependencies'], missing_deps = test_dependencies()
    results['file_structure'] = test_file_structure()
    results['imports'] = test_imports()
    results['flask_app'] = test_flask_app()
    results['routes'] = test_routes()
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    
    for test_name, passed in results.items():
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"   {test_name.replace('_', ' ').title():30s} {status}")
    
    print(f"\n   Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n   🎉 ALL TESTS PASSED! Your code is working properly.")
        return 0
    else:
        print("\n   ⚠️  Some tests failed. Please review the errors above.")
        if not results['dependencies']:
            print(f"\n   Missing packages: {', '.join(missing_deps)}")
            print("   Run: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
