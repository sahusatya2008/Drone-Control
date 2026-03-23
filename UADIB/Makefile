PY=python

install:
	$(PY) -m pip install -e .[dev]

test:
	pytest

run:
	uvicorn api.server:app --reload --port 8080

lint:
	ruff check .
