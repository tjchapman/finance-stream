clean: 
	rm -rf __pycache__/

tidy:
	ruff format
	ruff check