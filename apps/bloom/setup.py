"""
Bloom Package Setup

Install Bloom as a Python package for easy imports and CLI usage.
"""

from pathlib import Path
from setuptools import setup, find_packages

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#") and not line.startswith("-e")
    ]

setup(
    name="bloom",
    version="1.0.0",
    description="Bloom Employee Evaluation & Growth Engine - AI-powered performance reviews",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Bloom Team",
    author_email="team@bloom.ai",
    url="https://github.com/yourusername/yelo",
    packages=find_packages(where="."),
    package_dir={"": "."},
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.12.0",
            "black>=23.12.0",
            "ruff>=0.1.0",
            "mypy>=1.8.0",
            "pre-commit>=3.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bloom=bloom.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai, multi-agent, performance-review, evaluation, hr-tech, rag, llm",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/yelo/issues",
        "Source": "https://github.com/yourusername/yelo",
    },
)
