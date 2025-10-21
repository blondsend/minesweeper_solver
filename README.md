# Minesweeper AI Solver

Educational Minesweeper project (ITMO University) ported for portfolio.

Contains:
- `minesweeper_engine.py` — game engine (Cell, board generation, reveal logic)
- `solver.py` — deterministic + probabilistic solvers (CSP, backtracking, union-find)
- `play_minesweeper.py` — simple CLI for playing
- `test_solver.py` / `test_minesweeper.py` — test harness and unit tests

Quick start (Windows PowerShell):

```
python -m venv .venv
```

```
.\.venv\Scripts\Activate.ps1
```

```
pip install -r requirements.txt
```

Play (interactive):
```
python play_minesweeper.py
```

Test:
```
pytest test_minesweeper.py
```

Test solvers:
```
python test_solver.py
```
You can change game's settings in `test_solver.py`, if you need.
