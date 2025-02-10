.PHONY: install lint test format run clean

install:
	conda env update --file environment.yml --prune

lint:
	flake8 src tests

format:
	black src tests
	isort src tests

test:
	pytest tests

run:
	python src/modified_dijkstra.py networks/sample_graph.txt 1 10

clean:
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -name "*.pyc" -delete
