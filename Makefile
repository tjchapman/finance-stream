clean: 
	rm -rf __pycache__/

tidy:
	ruff format
	ruff check

setup-cassandra:
	python Cassandra/src/Cassandra.py

produce-kafka:
	python Producer/src/FinanceProducer.py

process-spark:
	python Processor/src/SparkProcessor.py

