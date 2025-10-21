import sys
from typing import Optional
from minesweeper_engine import (
    Cell, generate_board, reveal_cell, toggle_flag, 
    check_win, reveal_all_mines
)


def display_board(board: list[list[Cell]], game_over: bool = False) -> None:
    """Display board

    Args:
        board (list[list[Cell]]): Board with mines
        game_over (bool, optional): Game end flag (Defaults to False)
    """

    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0
    
    print("\n   ", end="")
    for col in range(cols):
        print(f"{col:2}", end=" ")
    print()
    
    print("  +" + "---" * cols + "+")
    
    for row in range(rows):
        print(f"{row:2}|", end="")
        for col in range(cols):
            cell = board[row][col]
            
            if cell.is_flagged and not game_over:
                print(" F ", end="")
            elif cell.is_revealed:
                if cell.is_mine:
                    print(" * ", end="")
                elif cell.adjacent_mines == 0:
                    print("   ", end="")
                else:
                    print(f" {cell.adjacent_mines} ", end="")
            else:
                if game_over and cell.is_mine:
                    print(" * ", end="")
                else:
                    print(" # ", end="")
        print("|")
    
    print("  +" + "---" * cols + "+")


def parse_command(command: str) -> Optional[tuple[str, int, int]]:
    """Parse players command

    Args:
        command (str): Players command

    Returns:
        tuple[str, int, int]: Action or None (if not correct)
    """

    parts = command.strip().lower().split()
    
    if len(parts) != 3:
        return None
    
    action, row_str, col_str = parts
    
    if action not in ['open', 'o', 'flag', 'f']:
        return None
    
    if action == 'o':
        action = 'open'
    elif action == 'f':
        action = 'flag'
    
    try:
        row = int(row_str)
        col = int(col_str)
        return (action, row, col)
    except ValueError:
        return None

def get_game_parameters() -> tuple[int, int, int]:
    """Get Game Parameters from player

    Returns:
        tuple[int, int, int]: (rows, cols, num_mines)
    """

    print("======== Minesweeper ========\n")
    
    while True:
        try:
            rows = int(input("Enter number of rows: "))
            cols = int(input("Enter number of columns: "))
            num_mines = int(input("Enter number of mines: "))
            
            if rows <= 0 or cols <= 0:
                print("Field dimensions must be positive numbers\n")
                continue
            
            if num_mines < 0:
                print("The number of mines cannot be negative\n")
                continue
            
            if num_mines >= rows * cols:
                print(f"Too many mines. Maximum: {rows * cols - 1}\n")
                continue
            
            return rows, cols, num_mines
        
        except ValueError:
            print("Enter correct numbers\n")

def main() -> None:
    """Main game loop"""
    
    rows, cols, num_mines = get_game_parameters()
    
    board: Optional[list[list[Cell]]] = None
    first_move = True
    game_over = False
    
    print("\n======== Game starts! ========")
    print("\nCommands:")
    print("  open <row> <col>  or  o <row> <col>  - open cell")
    print("  flag <row> <col>  or  f <row> <col>  - put/remove flag")
    print()
    
    while True:
        if board is not None:
            display_board(board, game_over)
        else:
            print("Make the first move (it's always safe)\n")
        
        if game_over:
            break
        
        command = input("\nEnter the command: ").strip()
        parsed = parse_command(command)
        if parsed is None:
            print("Invalid command")
            continue
        action, row, col = parsed
        
        if not (0 <= row < rows and 0 <= col < cols):
            print(f"Coordinates out of bounds. Use row: 0-{rows-1}, col: 0-{cols-1}")
            continue
        
        if first_move:
            if action == 'flag':
                print("The first move should be an opening of a cell")
                continue
            
            board = generate_board(rows, cols, num_mines, (row, col))
            first_move = False
        
        if action == 'open':
            if board[row][col].is_flagged:
                print("Uncheck the flag first")
                continue
            
            safe = reveal_cell(board, row, col)
            
            if not safe:
                print("\n======== GAME OVER ========")
                print("\nYou stepped on a mine!")
                reveal_all_mines(board)
                display_board(board, game_over=True)
                game_over = True
                sys.exit(0)

            elif check_win(board):
                print("======== YOU WON ========")
                display_board(board)
                game_over = True
                sys.exit(0)
        
        elif action == 'flag':
            success = toggle_flag(board, row, col)
            if not success:
                print("You can't place a flag on an open cell")
    


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nThe game is interrupted")
        sys.exit(0)