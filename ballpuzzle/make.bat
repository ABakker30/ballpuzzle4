@echo off
if "%1"=="test" (
    python -m pytest -q
) else if "%1"=="solve" (
    python -m cli.solve tests/data/containers/tiny_4.fcc.json --engine dfs --pieces A=1 --eventlog out/events.jsonl --solution out/solution.json
) else if "%1"=="verify" (
    python -m cli.verify out/solution.json tests/data/containers/tiny_4.fcc.json
) else if "%1"=="demo" (
    call .\make.bat solve
    call .\make.bat verify
) else (
    echo Usage: make [test^|solve^|verify^|demo]
)
