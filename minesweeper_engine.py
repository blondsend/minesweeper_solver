from dataclasses import dataclass
import random
from collections import deque 


DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]  # For count adjacent mines and cascade open


@dataclass
class Cell:
    is_mine: bool = False
    is_revealed: bool = False
    is_flagged: bool = False
    adjacent_mines: int = 0


def generate_board(rows: int, cols: int, num_mines: int, first_click_coords: tuple[int, int]) -> list[list[Cell]]:
    """Generate board with mines

    Args:
        rows (int): Number of rows
        cols (int): Number of columns
        num_mines (int): Number of mines
        first_click_coords (tuple[int, int]): Coords of first click

    Returns:
        list[list[Cell]]: Board
    """

    board = [[Cell() for _ in range(cols)] for _ in range(rows)]
    all_positions = [(r, c) for r in range(rows) for c in range(cols)]
    
    first_row, first_col = first_click_coords
    all_positions.remove((first_row, first_col))

    max_mines = len(all_positions)
    actual_mines = min(num_mines, max_mines)

    mine_positions = random.sample(all_positions, actual_mines)
    for row, col in mine_positions:
        board[row][col].is_mine = True

    _calculate_adjacent_mines(board, rows, cols)  # For optimization

    return board


def _calculate_adjacent_mines(board: list[list[Cell]], rows: int, cols: int) -> None:
    """Calculate adjacent mines

    Args:
        board (list[list[Cell]]): Board with mines
        rows (int): Number of rows
        cols (int): Number of columns
    """

    for row in range(rows):
        for col in range(cols):
            if not board[row][col].is_mine:
                mine_count = 0
                for d_row, d_col in DIRECTIONS:
                    n_row, n_col = row + d_row, col + d_col
                    if 0 <= n_row < rows and 0 <= n_col < cols and board[n_row][n_col].is_mine:
                        mine_count += 1
                board[row][col].adjacent_mines = mine_count
    

def reveal_cell(board: list[list[Cell]], row: int, col: int) -> bool:
    """Reveal cell

    Args:
        board (list[list[Cell]]): Board with mines
        row (int): Number of rows
        col (int): Number of columns

    Returns:
        bool: True, if game continues, else False (player lost)
    """

    rows = len(board)
    cols = len(board[0] if rows > 0 else 0)

    if not(0 <= row < rows and 0 <= col < cols):
        return True

    cell = board[row][col]

    if cell.is_revealed or cell.is_flagged:
        return True
    
    cell.is_revealed = True

    if cell.is_mine:
        return False
    
    if cell.adjacent_mines == 0:
        _cascade_reveal(board, row, col, rows, cols)

    return True

def _cascade_reveal(board: list[list[Cell]], start_row: int, start_col: int, rows: int, cols: int) -> None:
    """Cascade reveal with BFS

    Args:
        board (list[list[Cell]]): Board with mines
        start_row (int): Start row
        start_col (int): Start col
        rows (int): Number of rows
        cols (int): Number of cols
    """

    queue = deque([(start_row, start_col)])
    visited = {(start_row, start_col)}

    while queue:
        row, col = queue.popleft()

        for d_row, d_col in DIRECTIONS:
            n_row, n_col = row + d_row, col + d_col

            if not (0 <= n_row < rows and 0 <= n_col < cols) or (n_row, n_col) in visited:
                continue

            visited.add((n_row, n_col))
            cell = board[n_row][n_col]

            if cell.is_mine or cell.is_flagged:
                continue

            cell.is_revealed = True

            if cell.adjacent_mines == 0:
                queue.append((n_row, n_col))


def toggle_flag(board: list[list[Cell]], row: int, col: int) -> bool:
    """Toggle flag

    Args:
        board (list[list[Cell]]): Board with mines
        row (int): Number of rows
        col (int): Number of columns

    Returns:
        bool: True if everything is successful 
    """

    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0
    
    if not (0 <= row < rows and 0 <= col < cols):
        return False
    
    cell = board[row][col]
    
    if cell.is_revealed:
        return False
    
    cell.is_flagged = not cell.is_flagged

    return True

def check_win(board: list[list[Cell]]) -> bool:
    """Check if player win or not

    Args:
        board (list[list[Cell]]): Board with mines

    Returns:
        bool: True if player win, else False
    """

    for row in board:
        for cell in row:
            if not cell.is_mine and not cell.is_revealed:
                return False
    return True

def reveal_all_mines(board: list[list[Cell]]) -> None:
    """Reveal all mines if player lost

    Args:
        board (list[list[Cell]]): Board with mines
    """

    for row in board:
        for cell in row:
            if cell.is_mine:
                cell.is_revealed = True