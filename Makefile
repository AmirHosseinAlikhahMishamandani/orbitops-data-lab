.PHONY: install install-base test lint format typecheck check benchmark-spark

install:
	python -m pip install -e ".[dev]"

install-base:
	python -m pip install -e .

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

benchmark-spark:
	python benchmarks/benchmark_transformers.py --records $${RECORDS:-100000}
