.PHONY: install test lint format typecheck check

install:
	python -m pip install -e ".[dev]"

test:
	pytest --cov=orbitops --cov-report=term-missing

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src

check:
	ruff check .
	ruff format --check .
	mypy src
	pytest --cov=orbitops --cov-report=term-missing
