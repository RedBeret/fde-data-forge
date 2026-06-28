.PHONY: install test lint sample-report clean

PYTHON ?= python
FDE ?= $(PYTHON) -m fde.cli

install:
	$(PYTHON) -m pip install -r requirements.txt -e .

test:
	$(PYTHON) -m pytest -q

lint:
	ruff check .
	ruff format --check .

sample-report:
	mkdir -p reports
	$(FDE) report \
		--parts samples/parts_v1.csv \
		--suppliers samples/suppliers_legacy.csv \
		--change-orders samples/change_orders.xlsx \
		--manifest samples/mess_manifest_sample.json \
		--out reports/sample_report.json

clean:
	rm -rf reports
