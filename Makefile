clean: 
	rm -rf __pycache__/

tidy:
	ruff format
	ruff check

produce:
	poetry run python Producer/src/FinanceProducer.py

process:
	poetry run python Processor/src/SparkProcessor.py

infra:
	docker compose up -d

down:
	docker compose down


