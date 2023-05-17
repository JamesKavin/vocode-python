.PHONY: chat speak listen lint lint_diff help

chat:
	poetry run python playground/streaming/agent/chat.py

transcribe:
	poetry run python playground/streaming/transcriber/transcribe.py

synthesize:
	poetry run python playground/streaming/synthesizer/synthesize.py

PYTHON_FILES=.
lint: PYTHON_FILES=.
lint_diff: PYTHON_FILES=$(shell git diff --name-only --diff-filter=d main | grep -E '\.py$$')

lint lint_diff:
	poetry run black $(PYTHON_FILES)

test:
	poetry run pytest

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  chat        Run chat agent"
	@echo "  transcribe  Transcribe audio to text"
	@echo "  synthesize  Synthesize text into audio"
	@echo "  lint        Lint all Python files"
	@echo "  lint_diff   Lint changed Python files"
	@echo "  test        Run tests"
	@echo "  help        Show this help message"

