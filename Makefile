clean: 
	rm -rf __pycache__/

tidy:
	ruff format
	ruff check

db:
	python Cassandra/src/Cassandra.py

produce:
	python Cassandra/src/Cassandra.py
	python Producer/src/FinanceProducer.py

process:
	python Processor/src/SparkProcessor.py

infra:
	docker compose up -d


