# Keap Exporter Makefile
# Common operations for development and deployment

.PHONY: help install test clean setup-db run-validation sync-all sync-contacts sync-companies sync-tags sync-opportunities sync-tasks sync-notes sync-products sync-orders sync-payments auth-test

# Default target
help:
	@echo "Keap Exporter - Available Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  install          Install Python dependencies"
	@echo "  setup-db         Create database schema and ETL support tables"
	@echo "  clean            Clean up temporary files and caches"
	@echo ""
	@echo "Authentication:"
	@echo "  auth-test         Test Keap API connection and authentication"
	@echo ""
	@echo "Sync Operations:"
	@echo "  sync-all         Run full sync of all entities"
	@echo "  sync-contacts    Sync contacts only"
	@echo "  sync-companies   Sync companies only"
	@echo "  sync-tags        Sync tags only"
	@echo "  sync-opportunities Sync opportunities only"
	@echo "  sync-tasks       Sync tasks only"
	@echo "  sync-notes       Sync notes only"
	@echo "  sync-products    Sync products only"
	@echo "  sync-orders      Sync orders only"
	@echo "  sync-payments     Sync payments only"
	@echo ""
	@echo "Validation & Testing:"
	@echo "  test             Run unit tests"
	@echo "  run-validation   Run database validation queries"
	@echo ""
	@echo "Development:"
	@echo "  lint             Run code linting"
	@echo "  format           Format code with black"
	@echo "  type-check       Run type checking with mypy"

# Installation
install:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

# Database setup
setup-db:
	@echo "Setting up database schema..."
	psql -h $$DB_HOST -U $$DB_USER -d $$DB_NAME -f sql/schema.sql
	psql -h $$DB_HOST -U $$DB_USER -d $$DB_NAME -f sql/keap_etl_support.sql
	psql -h $$DB_HOST -U $$DB_USER -d $$DB_NAME -f sql/keap_validation.sql
	@echo "Database setup complete!"

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/

# Authentication test
auth-test:
	.venv/bin/python src/scripts/sample_connect.py

# Sync operations
sync-all:
	.venv/bin/python src/scripts/sync_all.py

sync-contacts:
	.venv/bin/python src/scripts/sync_contacts.py

sync-companies:
	.venv/bin/python src/scripts/sync_companies.py

sync-tags:
	.venv/bin/python src/scripts/sync_tags.py

sync-opportunities:
	.venv/bin/python src/scripts/sync_opportunities.py

sync-tasks:
	.venv/bin/python src/scripts/sync_tasks.py

sync-notes:
	.venv/bin/python src/scripts/sync_notes.py

sync-products:
	.venv/bin/python src/scripts/sync_products.py

sync-orders:
	.venv/bin/python src/scripts/sync_orders.py

sync-payments:
	.venv/bin/python src/scripts/sync_payments.py

# Validation
run-validation:
	@echo "Running database validation..."
	.venv/bin/python src/scripts/run_validation.py

# Testing
test:
	python -m pytest tests/ -v

# Development tools
lint:
	flake8 src/ tests/
	black --check src/ tests/

format:
	black src/ tests/

type-check:
	mypy src/

# Environment setup
env:
	@echo "Creating .env file from template..."
	cp .env.example .env
	@echo "Please edit .env with your actual credentials"

# Quick start
quickstart: env install setup-db auth-test
	@echo "Quick start complete! Edit .env with your credentials and run 'make auth-test'"

# Full deployment
deploy: install setup-db
	@echo "Deployment complete! Run 'make auth-test' to verify connection"
