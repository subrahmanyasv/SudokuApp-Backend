import random
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from src.Config.settings import get_settings
from src.API.Controllers.game_controller import add_games_to_db_util, get_games_count_util

# --- Core Backtracking Algorithm ---
def _fill_grid(grid: List[List[int]]) -> bool:
    """
    Recursively fills a 9x9 Sudoku grid using a backtracking algorithm.
    This function modifies the grid in place.
    """
    find = _find_empty_cell(grid)
    if not find:
        return True
    else:
        row, col = find

    numbers = list(range(1, 10))
    random.shuffle(numbers)

    for num in numbers:
        if _is_valid_placement(grid, row, col, num):
            grid[row][col] = num

            if _fill_grid(grid):
                return True

            grid[row][col] = 0
    return False

def _find_empty_cell(grid: List[List[int]]) -> Optional[Tuple[int, int]]:
    """Finds the next empty cell (represented by 0) in the grid."""
    for r in range(9):
        for c in range(9):
            if grid[r][c] == 0:
                return (r, c)
    return None

def _is_valid_placement(grid: List[List[int]], row: int, col: int, num: int) -> bool:
    """Checks if placing a number in a cell is valid according to Sudoku rules."""
    if num in grid[row]:
        return False

    
    if num in [grid[i][col] for i in range(9)]:
        return False

    box_start_row, box_start_col = 3 * (row // 3), 3 * (col // 3)
    for r in range(box_start_row, box_start_row + 3):
        for c in range(box_start_col, box_start_col + 3):
            if grid[r][c] == num:
                return False

    return True


# --- Puzzle Creation ---
def _poke_holes(grid: List[List[int]], holes: int) -> List[List[int]]:
    """
    Removes a given number of cells from a solved Sudoku grid to create a puzzle.
    """
    puzzle_grid = [row[:] for row in grid] 
    
    cells = set(range(81)) 
    
    for _ in range(holes):
        if not cells:
            break 
        
        cell_index = random.choice(list(cells))
        row, col = cell_index // 9, cell_index % 9
        
        puzzle_grid[row][col] = 0
        cells.remove(cell_index)
        
    return puzzle_grid


# --- Main Public Function ---
def generate_games(difficulty: str) -> List[Dict[str, str]]:
    """
    Generates a specified number of Sudoku puzzles for a given difficulty.

    Args:
        difficulty (str): The difficulty level ('easy', 'medium', or 'hard').

    Returns:
        A list of dictionaries, where each dictionary contains:
        - 'board_string': The puzzle with blank cells (as '0').
        - 'solution_string': The fully solved puzzle.
    """
    settings = get_settings()
    num_to_generate = settings.PUZZLES_TO_GENERATE_PER_JOB
    blanks_map = {
        "easy": settings.EASY_BLANKS,
        "medium": settings.MEDIUM_BLANKS,
        "hard": settings.HARD_BLANKS,
    }
    
    if difficulty not in blanks_map:
        raise ValueError("Invalid difficulty level provided.")
        
    blanks_to_create = blanks_map[difficulty]
    generated_puzzles = []
    
    print(f"Starting job to generate {num_to_generate} puzzles of '{difficulty}' difficulty...")

    for i in range(num_to_generate):
        grid = [[0 for _ in range(9)] for _ in range(9)]
        _fill_grid(grid)
        solution_string = "".join([str(num) for row in grid for num in row])
        puzzle_grid = _poke_holes(grid, blanks_to_create)
        board_string = "".join([str(num) for row in puzzle_grid for num in row])
        
        generated_puzzles.append({
            "board_string": board_string,
            "solution_string": solution_string,
        })
        print(f"  ...Generated puzzle {i + 1}/{num_to_generate}")

    print("Puzzle generation job complete.")
    return generated_puzzles



def generate_initial_games(db: Session):
    count = get_games_count_util(db)
    if count == 0:
        puzzles = generate_games('easy')
        add_games_to_db_util(db,puzzles, "easy")

        puzzles = generate_games('medium')
        add_games_to_db_util(db, puzzles , "medium")

        puzzles = generate_games('hard')
        add_games_to_db_util(db, puzzles, "hard")

        print("Games generated and added to DB")
    else:
        print("Games already exist in DB")

