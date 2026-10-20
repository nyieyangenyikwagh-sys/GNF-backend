.PHONY: claims-isolated claims-integrated claims-failure claims-report claims-dataset

claims-isolated:
	docker compose -f docker-compose.yml -f docker-compose.benchmark.yml up -d --build
	python claims-benchmark/run_claims_benchmark.py

claims-integrated:
	CLAIMS_BENCHMARK_CONFIG=claims-benchmark/config.integrated.json python claims-benchmark/run_claims_benchmark.py

claims-failure:
	python -m pytest claims-benchmark/suites/test_resilience.py -q

claims-report:
	python claims-benchmark/evaluate_claims_results.py $(RUN_DIR)

claims-dataset:
	python claims-benchmark/run_dataset_test.py $(CSV)
