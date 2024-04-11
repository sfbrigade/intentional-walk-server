.PHONY: test coverage

test:
	@echo "Running tests"
	@poetry run pytest

coverage:
	@echo "Running tests with coverage"
	@poetry run scripts/coverage_html.py

lint:
	@echo "Running linter"
	@poetry run black .
	@poetry run flake8