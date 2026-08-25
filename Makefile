.PHONY: install install-cuda data preprocess train train-synthetic baseline test lint docker-build clean zip
PYTHON ?= python

install:
	pip install -e . --break-system-packages

install-cuda:
	pip install -e ".[cuda]" --break-system-packages

data:
	$(PYTHON) -m grama.data.download

data-check:
	$(PYTHON) -m grama.data.download --check

preprocess:
	bash scripts/run_preprocess.sh

train-synthetic:
	$(PYTHON) scripts/run_federated_train.py --synthetic --rounds 5

train:
	$(PYTHON) scripts/run_federated_train.py

baseline:
	$(PYTHON) scripts/run_baseline_cnn_bigru.py

test:
	pytest -v --cov=src/grama tests/

lint:
	ruff check src/ tests/ scripts/

docker-build:
	docker build -t grama:latest .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov

zip:
	@echo "Creating grama.zip..."
	@zip -r grama.zip . \
		-x ".git/*" \
		-x "*.pyc" \
		-x "__pycache__/*" \
		-x "*/__pycache__/*" \
		-x ".pytest_cache/*" \
		-x "htmlcov/*" \
		-x ".coverage" \
		-x "*.egg-info/*" \
		-x "venv/*" \
		-x ".venv/*" \
		-x "data/*" \
		-x "*.ckpt" \
		-x "*.pt" \
		-x "*.pth" \
		-x ".DS_Store" \
		-x "grama.zip"
	@echo "Done: grama.zip"