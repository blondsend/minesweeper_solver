import random

from minesweeper_engine import (
    Cell,
    generate_board,
    reveal_cell,
    toggle_flag,
    check_win,
)
from solver import Solver


ROWS, COLS, MINES = 8, 8, 8


def get_random_first_click() -> tuple[int, int]:
    return (random.randint(0, ROWS - 1), random.randint(0, COLS - 1))


def count_open_and_flags(board: list[list[Cell]]) -> tuple[int, int]:
    opened = sum(1 for row in board for c in row if c.is_revealed)
    flags = sum(1 for row in board for c in row if c.is_flagged)
    return opened, flags


def run_deterministic_until_stuck(board: list[list[Cell]], solver: Solver) -> tuple[int, int, int, bool]:
    iters = 0
    total_safes = 0
    total_mines = 0
    while True:
        safe_cells, mine_cells = solver.solve_step(board)
        if not safe_cells and not mine_cells:
            break
        for r, c in safe_cells:
            reveal_cell(board, r, c)
        for r, c in mine_cells:
            toggle_flag(board, r, c)
        total_safes += len(safe_cells)
        total_mines += len(mine_cells)
        iters += 1
        if check_win(board):
            return iters, total_safes, total_mines, True
    return iters, total_safes, total_mines, check_win(board)


def new_board_with_seed(seed: int) -> tuple[list[list[Cell]], tuple[int, int]]:
    random.seed(seed)
    first_click = get_random_first_click()
    b = generate_board(ROWS, COLS, MINES, first_click)
    reveal_cell(b, *first_click)
    return b, first_click


def log_first_click(board: list[list[Cell]], step: int) -> int:
    opened, flags = count_open_and_flags(board)
    print(f"Step {step}: first click, opened={opened}, flags={flags}")
    return step + 1


def display_final_board(board: list[list[Cell]]) -> None:
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0
    
    print("\nFinal board:")
    print("   ", end="")
    for c in range(cols):
        print(f"{c:2}", end=" ")
    print()
    
    for r in range(rows):
        print(f"{r:2}|", end="")
        for c in range(cols):
            cell = board[r][c]
            if cell.is_flagged:
                print(" F ", end="")
            elif cell.is_revealed:
                if cell.is_mine:
                    print(" * ", end="")
                elif cell.adjacent_mines == 0:
                    print("   ", end="")
                else:
                    print(f" {cell.adjacent_mines} ", end="")
            else:
                print(" # ", end="")
        print("|")
    print()


def test_deterministic_solver():
    print("\n=== Deterministic solver 8x8, 8 mines ===")
    solver = Solver(total_mines=MINES)
    board, first_click = new_board_with_seed(12345)
    print(f"First click: {first_click}")

    step = 1
    step = log_first_click(board, step)
    while True:
        safe_cells, mine_cells = solver.solve_step(board)

        if safe_cells or mine_cells:
            for r, c in safe_cells:
                reveal_cell(board, r, c)
            for r, c in mine_cells:
                toggle_flag(board, r, c)

            opened, flags = count_open_and_flags(board)
            safe_list = sorted(list(safe_cells))
            mine_list = sorted(list(mine_cells))
            print(f"\nStep {step} (deterministic):")
            if safe_list:
                print(f"  Opened safe: {safe_list}")
            if mine_list:
                print(f"  Flagged mines: {mine_list}")
            print(f"  Total: opened={opened}, flags={flags}")
            step += 1

            if check_win(board):
                print("Result: win (deterministic solver)")
                display_final_board(board)
                break
            continue

        guess = None
        for r in range(ROWS):
            for c in range(COLS):
                cell = board[r][c]
                if not cell.is_revealed and not cell.is_flagged:
                    guess = (r, c)
                    break
            if guess is not None:
                break

        if guess is None:
            opened, flags = count_open_and_flags(board)
            print(f"Step {step}: nothing to open, total opened={opened}, flags={flags}")
            print("Result: win")
            display_final_board(board)
            break

        r, c = guess
        safe = reveal_cell(board, r, c)
        opened, flags = count_open_and_flags(board)
        print(f"Step {step} (guess): {guess},  {'safe' if safe else 'MINE!'}; total opened={opened}, flags={flags}")
        step += 1

        if not safe:
            print("Result: lose (guess)")
            display_final_board(board)
            break

        if check_win(board):
            print("Result: win (guess)")
            display_final_board(board)
            break


def test_probabilistic_solver_only():
    print("\n=== Probabilistic solver: 8x8, 8 mines ===")
    solver = Solver(total_mines=MINES)
    board, first_click = new_board_with_seed(54321)
    print(f"First click: {first_click}")

    step = 1
    step = log_first_click(board, step)
    while True:
        move = solver.make_probabilistic_move(board)
        r, c = move
        safe = reveal_cell(board, r, c)

        opened, flags = count_open_and_flags(board)
        print(f"Step {step} (probabilistic): move {move},  {'safe' if safe else 'MINE!'}; total opened={opened}, flags={flags}")
        step += 1

        if not safe:
            print("Result: lose (probabilistic solver)")
            display_final_board(board)
            break

        if check_win(board):
            print("Result: win (probabilistic solver)")
            display_final_board(board)
            break


def main():
    test_deterministic_solver()
    test_probabilistic_solver_only()


if __name__ == "__main__":
    main()
