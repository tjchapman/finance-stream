clean: 
	rm -rf __pycache__/

tidy:
	ruff format
	ruff check

setup-sql:
	python Cassandra/src/Cassandra.py

produce:
	python Producer/src/FinanceProducer.py

process:
	python Processor/src/SparkProcessor.py

