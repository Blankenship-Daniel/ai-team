#!/bin/bash
"""
Quality Automation Setup Script
Sets up comprehensive quality checks and automation
"""

set -euo pipefail

echo "🔧 Setting up Quality Automation for Tmux Orchestrator..."

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python version: $PYTHON_VERSION"

# Install quality tools
echo "📦 Installing quality tools..."

# Core quality tools
pip3 install --user \
    black \
    isort \
    flake8 \
    bandit \
    safety \
    coverage \
    pytest \
    pre-commit

# Set up pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "🪝 Installing pre-commit hooks..."
    pre-commit install
    pre-commit install --hook-type commit-msg
    echo "✓ Pre-commit hooks installed"
else
    echo "⚠️  .pre-commit-config.yaml not found"
fi

# Create quality check script
cat > "run_quality_checks.sh" << 'EOF'
#!/bin/bash
# Comprehensive quality check runner

echo "🔍 Running comprehensive quality checks..."

# Format code
echo "🎨 Formatting code..."
black --line-length=100 .
isort --profile=black --line-length=100 .

# Run linting
echo "📏 Running linting..."
flake8 --max-line-length=100 --extend-ignore=E203,W503 .

# Security scan
echo "🔒 Running security scan..."
bandit -r . -f json > security_report.json || echo "Security issues found - check security_report.json"

# Dependency check
echo "🛡️  Checking dependencies..."
safety check --json > dependency_report.json || echo "Dependency issues found - check dependency_report.json"

# Run tests with coverage
echo "🧪 Running tests with coverage..."
coverage run --source=. -m pytest
coverage report
coverage html

# Run custom quality automation
echo "⚙️  Running custom quality checks..."
python3 quality_automation.py

echo "✅ Quality checks complete!"
EOF

chmod +x run_quality_checks.sh

# Create pyproject.toml for tool configuration
cat > "pyproject.toml" << 'EOF'
[tool.black]
line-length = 100
target-version = ['py38']

[tool.isort]
profile = "black"
line_length = 100

[tool.bandit]
exclude_dirs = ["tests", "test_*"]
skips = ["B101", "B601"]

[tool.coverage.run]
source = ["."]
omit = [
    "test_*",
    "*/tests/*",
    "setup.py",
    "*/venv/*",
    "*/.env/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError"
]
EOF

# Create GitHub Actions workflow for CI
mkdir -p .github/workflows
cat > ".github/workflows/quality.yml" << 'EOF'
name: Quality Checks

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  quality:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install black isort flake8 bandit safety coverage pytest
        
    - name: Format check
      run: |
        black --check --line-length=100 .
        isort --check-only --profile=black --line-length=100 .
        
    - name: Lint
      run: flake8 --max-line-length=100 --extend-ignore=E203,W503 .
      
    - name: Security scan
      run: bandit -r . -f json
      
    - name: Dependency check
      run: safety check
      
    - name: Test with coverage
      run: |
        coverage run --source=. -m pytest
        coverage report --fail-under=80
        
    - name: Quality automation
      run: python quality_automation.py
EOF

# Create requirements file for quality tools
cat > "requirements-dev.txt" << 'EOF'
# Development and quality tools
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
bandit>=1.7.0
safety>=2.3.0
coverage>=7.0.0
pytest>=7.0.0
pre-commit>=3.0.0
EOF

echo "✅ Quality automation setup complete!"
echo ""
echo "📋 What was installed:"
echo "  • Code formatters: black, isort"
echo "  • Linters: flake8"
echo "  • Security: bandit, safety"
echo "  • Testing: pytest, coverage"
echo "  • Automation: pre-commit hooks"
echo ""
echo "🚀 Usage:"
echo "  • Run all checks: ./run_quality_checks.sh"
echo "  • Format code: black . && isort ."
echo "  • Manual pre-commit: pre-commit run --all-files"
echo "  • Quality report: python quality_automation.py"
echo ""
echo "🔄 Git hooks are now active - quality checks run on every commit!"