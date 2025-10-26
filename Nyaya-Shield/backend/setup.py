from setuptools import setup, find_packages

setup(
    name="nyayashield_bot",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'Flask>=2.0.0',
        'Flask-CORS>=3.0.0',
        'pandas>=1.3.0',
        'scikit-learn>=1.0.0',
        'joblib>=1.0.0',
        'numpy>=1.21.0',
        'nltk>=3.6.0',
        'transformers>=4.11.0',
        'torch>=1.9.0',
        'sentence-transformers>=2.0.0',
        'requests>=2.26.0',
    ],
    python_requires='>=3.7',
)
