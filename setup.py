#!/usr/bin/env python3
"""
Setup script for AI Team package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read version from package
version = {}
with open("ai_team/__init__.py") as fp:
    for line in fp:
        if line.startswith("__version__"):
            exec(line, version)
            break

setup(
    name="ai-team",
    version=version.get("__version__", "2.0.0"),
    author="AI Team Contributors",
    description="Tmux-based AI agent orchestration framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-team",
    packages=find_packages(exclude=["tests", "tests.*", "scripts", "docs"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - uses only standard library
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-xdist>=3.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "bandit>=1.7.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ai-team=ai_team.cli.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)