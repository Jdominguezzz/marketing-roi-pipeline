.PHONY: setup ingest transform test pipeline dagster sample ci

setup:            ## install everything
	uv sync

ingest:           ## land all sources and load DuckDB raw.*
	uv run python -m marketing_pipeline.extract.kaggle_files
	uv run python -m marketing_pipeline.extract.fx_api
	uv run python -m marketing_pipeline.extract.spend_simulator
	uv run python -m marketing_pipeline.load.duckdb_loader

transform:        ## dbt models + tests
	cd transform && uv run dbt build --profiles-dir .

test:             ## Python unit tests
	uv run pytest -v

pipeline: ingest transform   ## the whole pipeline, end to end

dagster:          ## orchestrator UI on http://127.0.0.1:3000
	uv run dagster dev

sample:           ## rebuild the small CI sample from the real data
	uv run python scripts/make_sample.py

ci: export LANDING_DIR = $(CURDIR)/data/sample/landing
ci: export DUCKDB_PATH = $(CURDIR)/data/ci.duckdb
ci:               ## exactly what GitHub Actions runs, on the committed sample
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest -q
	uv run python -m marketing_pipeline.extract.spend_simulator
	uv run python -m marketing_pipeline.load.duckdb_loader
	cd transform && uv run dbt build --profiles-dir .
