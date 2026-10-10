# GraMa. `make help` lists the targets.
#
# Works without installing the package: src/ is put on PYTHONPATH here.

PYTHON ?= python3
PROFILE ?= quick
SOURCE ?= cic
export PYTHONPATH := $(CURDIR)/src:$(PYTHONPATH)

PAPER1 = new_baselines def_ablation alie_duplicates cic_adaptive_new cic_seeds def_grid clients40 road_new_baselines cantt1_new_baselines
PAPER2 = det_road_central det_road_ablation det_road_fedavg det_cantt1 det_cantt2 det_cantt3 det_cantt4 det_cic

.PHONY: paper1-background paper2-background papers-background queue-status stats-paper1 stats-paper2 help setup setup-cuda check-data data smoke quick full full-background road cantt others-background extra-background report test lint notebook pack hf clean

help:
	@echo "make setup            install the dependencies (once)"
	@echo "make setup-cuda       also build the mamba-ssm CUDA kernel (optional, slow to build)"
	@echo "make check-data       check that CIC-IoV2024 is in data/raw (SOURCE=road or can_train_test for the others)"
	@echo "make data             build the processed dataset for PROFILE (default: quick)"
	@echo "make smoke            whole pipeline on synthetic data, a few minutes on a CPU"
	@echo "make quick            real data, short runs (about 30 min on a GPU)"
	@echo "make full             the paper runs (hours); see also full-background"
	@echo "make full-background  the paper runs, detached, logging to results/full.log"
	@echo "make road             the ROAD runs (about 50, 8-10 hours on an A100)"
	@echo "make cantt            the can-train-and-test runs, sets 1 to 4 (about 100 runs)"
	@echo "make others-background  road then cantt, detached, logging to results/others.log"
	@echo "make extra-background   adaptive attack (CIC, cantt1) and extra road/cantt1 seeds, detached, logging to results/extra.log"
	@echo "make paper1-background   the defence paper's profiles in order, detached (status: results/queue_paper1.status)"
	@echo "make paper2-background   the detector paper's profiles in order, detached (status: results/queue_paper2.status)"
	@echo "make papers-background   both queues at once on the same GPU"
	@echo "make queue-status        last lines of every queue's status file"
	@echo "make stats-paper1        confidence intervals and paired tests for the defence paper (after its runs)"
	@echo "make stats-paper2        the same for the detector paper"
	@echo "make report           rebuild tables and figures for PROFILE from saved runs"
	@echo "make notebook         run GraMa.ipynb top to bottom without opening it"
	@echo "make pack             pack results/PROFILE into results_PROFILE.tar.gz for download"
	@echo "make hf               upload results/PROFILE and weights to the Hugging Face Hub (private repo)"
	@echo "make test             unit tests"

setup:
	$(PYTHON) -m pip install -q -r requirements.txt
	$(PYTHON) -m pip install -q pytest ruff

setup-cuda: setup
	$(PYTHON) -m pip install --no-build-isolation causal-conv1d mamba-ssm

check-data:
	$(PYTHON) -m grama.data.download --source $(SOURCE)

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

road:
	$(PYTHON) scripts/run_experiments.py --profile road

cantt:
	for p in cantt1 cantt2 cantt3 cantt4; do $(PYTHON) scripts/run_experiments.py --profile $$p || exit 1; done

others-background:
	@mkdir -p results
	nohup sh -c '$(PYTHON) scripts/run_experiments.py --profile road --no-progress && \
	  for p in cantt1 cantt2 cantt3 cantt4; do $(PYTHON) scripts/run_experiments.py --profile $$p --no-progress || exit 1; done' \
	  > results/others.log 2>&1 &
	@echo "Started. Follow it with: tail -f results/others.log"

# Each profile runs even if an earlier one fails (e.g. CIC-IoV2024 not in data/raw).
extra-background:
	@mkdir -p results
	nohup sh -c 'for p in cantt1_adaptive cic_adaptive cantt1 road; do \
	  echo "=== $$p ==="; $(PYTHON) scripts/run_experiments.py --profile $$p --no-progress || echo "=== $$p FAILED ==="; done; \
	  echo "=== all done ==="' > results/extra.log 2>&1 &
	@echo "Started. Follow it with: tail -f results/extra.log"

paper1-background:
	nohup sh scripts/run_queue.sh paper1 $(PAPER1) > /dev/null 2>&1 &
	@echo "Started. Follow it with: tail -f results/queue_paper1.status"

paper2-background:
	nohup sh scripts/run_queue.sh paper2 $(PAPER2) > /dev/null 2>&1 &
	@echo "Started. Follow it with: tail -f results/queue_paper2.status"

papers-background: paper1-background paper2-background

queue-status:
	@for f in results/queue_*.status; do echo "== $$f"; tail -n 6 $$f; done

# The 40-vehicle runs share run ids with the 20-vehicle ones, so they get their own file.
stats-paper1:
	$(PYTHON) scripts/stats.py results/full results/new_baselines results/def_ablation results/alie_duplicates results/cic_seeds results/def_grid \
	  --metric final.f1_macro defence.tpr defence.fpr --reference grama_hdbscan --out results/stats/paper1_defence
	$(PYTHON) scripts/stats.py results/clients40 \
	  --metric final.f1_macro defence.tpr defence.fpr --reference grama_hdbscan --out results/stats/paper1_clients40

stats-paper2:
	$(PYTHON) scripts/stats.py results/det_road_central results/det_road_fedavg results/det_road_ablation results/det_cantt1 results/det_cantt2 results/det_cantt3 results/det_cantt4 results/det_cic \
	  --metric final.f1_macro tests.masquerade.f1_macro tests.unknown_vehicle.f1_macro tests.unknown_attack.f1_macro tests.unknown_vehicle_and_attack.f1_macro --reference grama_central --out results/stats/paper2_detector

report:
	$(PYTHON) -m grama.experiments.report results/$(PROFILE)

notebook:
	$(PYTHON) -m jupyter nbconvert --to notebook --execute --inplace GraMa.ipynb --ExecutePreprocessor.timeout=-1

pack:
	tar czf results_$(PROFILE).tar.gz -C results --exclude=$(PROFILE)/models $(PROFILE)
	@echo "Wrote results_$(PROFILE).tar.gz"

hf:
	$(PYTHON) scripts/publish_hf.py --profile $(PROFILE)

test:
	$(PYTHON) -m pytest -q

lint:
	$(PYTHON) -m ruff check src tests scripts

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
