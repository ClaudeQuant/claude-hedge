"""
ClaudeHedge Setup Configuration
Production-ready package installation and distribution
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
if requirements_file.exists():
    with open(requirements_file) as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
else:
    requirements = [
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'yfinance>=0.2.28',
        'matplotlib>=3.7.0',
        'scipy>=1.10.0',
    ]

setup(
    name="claudehedge",
    version="1.0.0",
    author="ClaudeHedge Team",
    author_email="contact@claudehedge.ai",
    description="AI-powered systematic futures trading with timezone arbitrage",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ClaudeQuant/claude-hedge",
    project_urls={
        "Homepage": "https://claudehedge.ai",
        "Documentation": "https://docs.claudehedge.ai",
        "Dashboard": "https://dashboard.claudehedge.ai",
        "Bug Reports": "https://github.com/ClaudeQuant/claude-hedge/issues",
        "Source": "https://github.com/ClaudeQuant/claude-hedge",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Natural Language :: English",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.1.0",
            "mypy>=1.5.0",
            "sphinx>=7.1.0",
        ],
        "ml": [
            "scikit-learn>=1.3.0",
            "tensorflow>=2.13.0",
            "torch>=2.0.0",
        ],
        "api": [
            "fastapi>=0.103.0",
            "uvicorn>=0.23.0",
            "websockets>=11.0",
        ],
        "blockchain": [
            "web3>=6.9.0",
            "solana>=0.30.0",
        ],
        "all": [
            "pytest>=7.4.0",
            "scikit-learn>=1.3.0",
            "fastapi>=0.103.0",
            "web3>=6.9.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "claudehedge=claudehedge.cli:main",
            "claudehedge-backtest=claudehedge.scripts.run_backtest:main",
            "claudehedge-report=claudehedge.scripts.generate_report:main",
        ],
    },
    include_package_data=True,
    package_data={
        "claudehedge": [
            "config/*.yaml",
            "data/*.csv",
            "docs/*.md",
        ],
    },
    zip_safe=False,
    keywords=[
        "trading",
        "futures",
        "systematic",
        "algorithmic",
        "quantitative",
        "finance",
        "backtesting",
        "timezone arbitrage",
        "hedge fund",
        "ai trading",
        "machine learning",
        "cryptocurrency",
    ],
)
