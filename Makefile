# GraMa. `make help` lists the targets.
#
# Works without installing the package: src/ is put on PYTHONPATH here.

PYTHON ?= python3
PROFILE ?= quick
export PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

.PHONY: help setup setup-cuda check-data data smoke quick full full-background report test lint notebook pack clean

help:
	@echo "make setup            install the dependencies (once)"
	@echo "make setup-cuda       also build the mamba-ssm CUDA kernel (optional, slow to build)"
	@echo "make check-data       check that CIC-IoV2024 is in data/raw"
	@echo "make data             build the processed dataset for PROFILE (default: quick)"
	@echo "make smoke            whole pipeline on synthetic data, a few minutes on a CPU"
	@echo "make quick            real data, short runs (about 30 min on a GPU)"
	@echo "make full             the paper runs (hours); see also full-background"
	@echo "make full-background  the paper runs, detached, logging to results/full.log"
	@echo "make report           rebuild tables and figures for PROFILE from saved runs"
	@echo "make notebook         run GraMa.ipynb top to bottom without opening it"
	@echo "make pack             zip results/PROFILE for download"
	@echo "make test             unit tests"

setup:
	$(PYTHON) -m pip install -q -r requirements.txt
	$(PYTHON) -m pip install -q pytest ruff

setup-cuda: setup
	$(PYTHON) -m pip install --no-build-isolation causal-conv1d mamba-ssm

check-data:
	$(PYTHON) -m grama.data.download

data:
	$(PYTHON) scripts/build_dataset.py --profile $(PROFILE)

smoke:
	$(PYTHON) scripts/run_experiments.py --profile smoke

quick:
	$(PYTHON) scripts/run_experiments.py --profile quick

full:
	$(PYTHON) scripts/run_experiments.py --profile full

full-background:
	@mkdir -p results
	nohup $(PYTHON) scripts/run_experiments.py --profile full --no-progress > results/full.log 2>&1 &
	@echo "Started. Follow it with: tail -f results/full.log"

report:
	$(PYTHON) -m grama.experiments.report results/$(PROFILE)

notebook:
	$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace GraMa.ipynb --ExecutePreprocessor.timeout=-1

pack:
	cd results && zip -qr ../results_$(PROFILE).zip $(PROFILE) -x "$(PROFILE)/models/*"
	@echo "Wrote results_$(PROFILE).zip"

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests scripts

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
