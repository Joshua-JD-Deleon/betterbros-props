.PHONY: dev run backtest test clean lint format

dev:
	pip install -r requirements.txt

run:
	streamlit run app/main.py

backtest:
	python scripts/run_week.py --mode backtest

test:
	pytest tests/ -v --cov=src --cov-report=html

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov/

lint:
	ruff check src/ tests/ app/

format:
	black src/ tests/ app/
	ruff check --fix src/ tests/ app/

install-dev: dev
	pip install black ruff mypy pytest-cov

help:
	@echo "Available targets:"
	@echo "  dev       - Install dependencies"
	@echo "  run       - Run Streamlit app"
	@echo "  backtest  - Run backtesting"
	@echo "  test      - Run tests with coverage"
	@echo "  clean     - Remove cache files"
	@echo "  lint      - Run linting"
	@echo "  format    - Format code"
