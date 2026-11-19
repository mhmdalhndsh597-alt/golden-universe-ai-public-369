.PHONY: setup test run-core deploy-prod

setup:
	python3 -m pip install -r core-engine/requirements.txt

test:
	PYTHONPATH=core-engine python3 -m pytest -q core-engine/tests

run-core:
	PYTHONPATH=core-engine python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000

deploy-prod:
	kubectl apply -f deploy/kubernetes/k8s-gpu-worker.yaml
