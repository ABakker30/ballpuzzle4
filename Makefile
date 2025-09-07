.PHONY: test solve verify demo

test:
	python -m pytest -q

solve:
	python -m cli.solve tests/data/containers/tiny_4.fcc.json --engine dfs --pieces A=1 --eventlog out/events.jsonl --solution out/solution.json

verify:
	python -m cli.verify out/solution.json tests/data/containers/tiny_4.fcc.json

demo: solve verify
