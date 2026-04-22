PYTHON ?= python

.PHONY: migrate reset-db wait-db test smoke smoke-matrix export-openapi docker-up docker-test-postgres

migrate:
	$(PYTHON) scripts/migrate.py

reset-db:
	$(PYTHON) scripts/reset_db.py --migrate

wait-db:
	$(PYTHON) scripts/wait_for_db.py

test:
	pytest -q

smoke:
	$(PYTHON) scripts/smoke_test.py

smoke-matrix:
	$(PYTHON) scripts/smoke_test_matrix.py

export-openapi:
	$(PYTHON) scripts/export_openapi.py

docker-up:
	docker compose up --build api

docker-test-postgres:
	docker compose run --rm test-runner
