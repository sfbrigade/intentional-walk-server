.PHONY: test coverage

test:
	@echo "Running tests"
	@poetry run pytest

coverage:
	@echo "Running tests with coverage"
	@poetry run scripts/coverage_html.py