from minesweeper_engine import Cell, DIRECTIONS
import random

class UnionFind:
    """A disjoint set system for finding independent regions"""
    
    def __init__(self):
        self.parent: dict[tuple[int, int], tuple[int, int]] = {}
        self.rank: dict[tuple[int, int], int] = {}
    
    def __add__(self, item: tuple[int, int]) -> None:
        """Adds element to the structure

        Args:
            item (tuple[int, int]): Element
        """

        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0

    # Public alias used by solver code
    def add(self, item: tuple[int, int]) -> None:
        """Public method to add an element (alias for __add__)."""
        self.__add__(item)
    
    def find(self, item: tuple[int, int]) -> tuple[int, int]:
        """Finds the root of set with path compression

        Args:
            item (tuple[int, int]): Element

        Returns:
            tuple[int, int]: Root
        """

        if item not in self.parent:
            self.add(item)
        
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]
    
    def union(self, item1: tuple[int, int], item2: tuple[int, int]) -> None:
        """Combines two sets

        Args:
            item1 (tuple[int, int]): 1 set
            item2 (tuple[int, int]): 2 set
        """

        root1 = self.find(item1)
        root2 = self.find(item2)
        
        if root1 == root2:
            return  # Already in one set
        
        if self.rank[root1] < self.rank[root2]:
            self.parent[root1] = root2
        elif self.rank[root1] > self.rank[root2]:
            self.parent[root2] = root1
        else:
            self.parent[root2] = root1
            self.rank[root1] += 1
    
    def get_groups(self) -> dict[tuple[int, int], set[tuple[int, int]]]:
        """Returns a dictionary of groups (root -> set of elements)

        Returns:
            dict[tuple[int, int], set[tuple[int, int]]]: Dictionary of groups
        """

        groups: dict[tuple[int, int], set[tuple[int, int]]] = {}
        for item in self.parent:
            root = self.find(item)
            if root not in groups:
                groups[root] = set()
            groups[root].add(item)
        return groups


class Solver:
    """Class for automatic minesweeper solving"""
    
    def __init__(self, total_mines: int = 0):
        """Initialize solver with knowledge of total mine count
        
        Args:
            total_mines (int): Total number of mines on the board
        """
        self.total_mines = total_mines
    
    def solve_step(self, board: list[list[Cell]]) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        """Performs one solution step by finding safe cells and mines

        Args:
            board (list[list[Cell]]): Board with mines

        Returns:
            tuple[set[tuple[int, int]], set[tuple[int, int]]]: Set (row, col) that are guaranteed to be safe to open + Set that are guaranteed to contain mines (for planting flags)
        """

        rows = len(board)
        cols = len(board[0]) if rows > 0 else 0
        
        safe_cells: set[tuple[int, int]] = set()
        mine_cells: set[tuple[int, int]] = set()
        
        flag = True  # Do it while can find new moves
        while flag:
            flag = False
            new_safe, new_mines = self._apply_basic_rules(board, rows, cols, safe_cells, mine_cells)
            
            if new_safe or new_mines:
                safe_cells.update(new_safe)
                mine_cells.update(new_mines)
                flag = True
        
        csp_safe, csp_mines = self._apply_csp_solver(board, rows, cols, safe_cells, mine_cells)
        safe_cells.update(csp_safe)
        mine_cells.update(csp_mines)
        
        return safe_cells, mine_cells
    
    def _apply_basic_rules(self, 
        board: list[list[Cell]], 
        rows: int, 
        cols: int,
        known_safe: set[tuple[int, int]],
        known_mines: set[tuple[int, int]]
    ) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        """Applies the basic solution rules

        Args:
            board (list[list[Cell]]): Board with mines
            rows (int): Number of rows
            cols (int): Number of columns
            known_safe (set[tuple[int, int]]): Known safe cells
            known_mines (set[tuple[int, int]]): Known mines

        Returns:
            tuple[set[tuple[int, int]], set[tuple[int, int]]]: New safe cells and new mines
        """

        safe_cells: set[tuple[int, int]] = set()
        mine_cells: set[tuple[int, int]] = set()
        
        for row in range(rows):
            for col in range(cols):
                cell = board[row][col]
                
                if not cell.is_revealed or cell.is_mine:
                    continue
                
                unrevealed_n_cells: list[tuple[int, int]] = []
                flagged_cell_count = 0
                
                for d_row, d_col in DIRECTIONS:
                    n_row, n_col = row + d_row, col + d_col
                    if 0 <= n_row < rows and 0 <= n_col < cols:
                        n_cell = board[n_row][n_col]
                        
                        if not n_cell.is_revealed:
                            if n_cell.is_flagged or (n_row, n_col) in known_mines:
                                flagged_cell_count += 1
                            elif (n_row, n_col) not in known_safe and (n_row, n_col) not in known_mines:
                                unrevealed_n_cells.append((n_row, n_col))
                
                # Rule 1: All mines if number of mines == number of known mines + number of unknown neighbor cells
                if unrevealed_n_cells and cell.adjacent_mines == flagged_cell_count + len(unrevealed_n_cells):
                    for coordinates in unrevealed_n_cells:
                        if coordinates not in known_mines:
                            mine_cells.add(coordinates)
                
                # Rule 2: All safe if number of mines == number of known mines
                elif unrevealed_n_cells and cell.adjacent_mines == flagged_cell_count:
                    for coordinates in unrevealed_n_cells:
                        if coordinates not in known_safe:
                            safe_cells.add(coordinates)
        
        return safe_cells, mine_cells
    
    def _apply_csp_solver(
        self,
        board: list[list[Cell]],
        rows: int,
        cols: int,
        known_safe: set[tuple[int, int]],
        known_mines: set[tuple[int, int]]
    ) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
        """Uses an advanced CSP solver based on the subset rule

        Args:
            board (list[list[Cell]]): Board with mines
            rows (int): Number of rows
            cols (int): Number of columns
            known_safe (set[tuple[int, int]]): Known safe cells
            known_mines (set[tuple[int, int]]): Known mines

        Returns:
            tuple[set[tuple[int, int]], set[tuple[int, int]]]: New safe cells and new mines
        """

        safe_cells: set[tuple[int, int]] = set()
        mine_cells: set[tuple[int, int]] = set()
        
        constraints = self._generate_constraints(board, rows, cols, known_safe, known_mines)
        
        if not constraints:
            return safe_cells, mine_cells
        
        flag = True
        while flag:
            flag = False
            new_constraints = []
            processed = set()
            
            for i, (limits1, count1) in enumerate(constraints):
                if i in processed:
                    continue
                
                added = False
                for j, (limits2, count2) in enumerate(constraints):
                    if i == j or j in processed:
                        continue
                    
                    if limits1.issubset(limits2) and limits1 != limits2:
                        new_limits = limits2 - limits1
                        new_count = count2 - count1
                        
                        # Boundary cases
                        if new_count == 0:
                            safe_cells.update(new_limits)
                            flag = True
                        elif new_count == len(new_limits):
                            mine_cells.update(new_limits)
                            flag = True
                        elif new_limits:
                            new_constraints.append((new_limits, new_count))
                            added = True
                        
                        processed.add(j)
                    
                    # Opposite 
                    elif limits2.issubset(limits1) and limits1 != limits2:
                        new_limits = limits1 - limits2
                        new_count = count1 - count2
                        
                        # Boundary cases
                        if new_count == 0:
                            safe_cells.update(new_limits)
                            flag = True
                        elif new_count == len(new_limits):
                            mine_cells.update(new_limits)
                            flag = True
                        elif new_limits:
                            new_constraints.append((new_limits, new_count))
                            added = True
                        
                        processed.add(j)
                
                if not added and i not in processed:

                    # Boundary cases
                    if count1 == 0:
                        safe_cells.update(limits1)
                        flag = True
                    elif count1 == len(limits1):
                        mine_cells.update(limits1)
                        flag = True
                    else:
                        new_constraints.append((limits1, count1))
            
            constraints = new_constraints
            
            # If find new cells
            if flag and (safe_cells or mine_cells):
                constraints = self._generate_constraints(
                    board, rows, cols, 
                    known_safe | safe_cells,  # Union
                    known_mines | mine_cells  # Union
                )
        
        return safe_cells, mine_cells
    
    def _generate_constraints(
        self,
        board: list[list[Cell]],
        rows: int,
        cols: int,
        known_safe: set[tuple[int, int]],
        known_mines: set[tuple[int, int]]
    ) -> list[tuple[frozenset[tuple[int, int]], int]]:
        """Generates CSP constraints from the current board state

        Args:
            board (list[list[Cell]]): Board with mines
            rows (int): Number of rows
            cols (int): Number of columns
            known_safe (set[tuple[int, int]]): Known safe cells
            known_mines (set[tuple[int, int]]): Known mines

        Returns:
            list[tuple[frozenset[tuple[int, int]], int]]: List of constraints
        """

        constraints: list[tuple[frozenset[tuple[int, int]], int]] = []
        
        for row in range(rows):
            for col in range(cols):
                cell = board[row][col]
                
                if not cell.is_revealed or cell.is_mine or cell.adjacent_mines == 0:
                    continue
                
                unknown_neighbors: set[tuple[int, int]] = set()
                known_mine_count = 0
                
                for d_row, d_col in DIRECTIONS:
                    n_row, n_col = row + d_row, col + d_col
                    if 0 <= n_row < rows and 0 <= n_col < cols:
                        n_cell = board[n_row][n_col]
                        
                        if (n_row, n_col) in known_mines or n_cell.is_flagged:
                            known_mine_count += 1
                        elif not n_cell.is_revealed and (n_row, n_col) not in known_safe:
                            unknown_neighbors.add((n_row, n_col))
                
                if unknown_neighbors:
                    remaining_mines = cell.adjacent_mines - known_mine_count
                    constraints.append((frozenset(unknown_neighbors), remaining_mines))
        
        return constraints
    
    def make_probabilistic_move(self, board: list[list[Cell]]) -> tuple[int, int]:
        """Makes a probabilistic move, calculating the exact probabilities for each cell

        Args:
            board (list[list[Cell]]): Board with mines

        Returns:
            tuple[int, int]: Coordinates for the next move
        """

        rows = len(board)
        cols = len(board[0]) if rows > 0 else 0
        
        unrevealed_cells = set()
        for row in range(rows):
            for col in range(cols):
                cell = board[row][col]
                if not cell.is_revealed and not cell.is_flagged:
                    unrevealed_cells.add((row, col))
        
        if not unrevealed_cells:
            return (0, 0)  # Default (random)
        
        constraints = self._generate_constraints(board, rows, cols, set(), set())
        
        if not constraints:
            return random.choice(list(unrevealed_cells))
        
        # Border cells
        border_cells = set()
        for limits_set, _ in constraints:
            border_cells.update(limits_set)
        
        # Interior cells
        interior_cells = unrevealed_cells - border_cells
        
        independent_regions = self._find_independent_regions(constraints)
        
        cell_probabilities: dict[tuple[int, int], float] = {}
        
        for region_constraints in independent_regions:
            region_cells = set()
            for limits_set, _ in region_constraints:
                region_cells.update(limits_set)
            
            if not region_cells:
                continue
            
            probabilities = self._calculate_probabilities(region_constraints, region_cells)
            cell_probabilities.update(probabilities)
        
        if interior_cells:
            flagged_mines = 0
            for row in range(rows):
                for col in range(cols):
                    if board[row][col].is_flagged:
                        flagged_mines += 1
            
            border_mine_count = sum(cell_probabilities.get(cell, 0.5) for cell in border_cells)
            
            remaining_mines = self.total_mines - flagged_mines - border_mine_count
            
            interior_probability = max(0.0, remaining_mines / len(interior_cells)) if interior_cells else 1.0
            
            for cell in interior_cells:
                cell_probabilities[cell] = interior_probability
        
        # Select the cell with the minimum probability
        if cell_probabilities:
            return min(cell_probabilities.keys(), key=lambda c: cell_probabilities[c])
        
        return random.choice(list(unrevealed_cells))
    
    def _find_independent_regions(
        self, 
        constraints: list[tuple[frozenset[tuple[int, int]], int]]
    ) -> list[list[tuple[frozenset[tuple[int, int]], int]]]:
        """Finds independent constraint regions using Union-Find

        Args:
            constraints (list[tuple[frozenset[tuple[int, int]], int]]): List of constraints

        Returns:
            list[list[tuple[frozenset[tuple[int, int]], int]]]: List of groups of independent constraints
        """
        if not constraints:
            return []
        
        uf = UnionFind()
        
        constraint_to_cells: dict[int, frozenset[tuple[int, int]]] = {}
        for i, (cells, _) in enumerate(constraints):
            constraint_to_cells[i] = cells
            for cell in cells:
                uf.add(cell)
        
        for i, cells in constraint_to_cells.items():
            cells_list = list(cells)
            for j in range(len(cells_list) - 1):
                uf.union(cells_list[j], cells_list[j + 1])
        
        groups = uf.get_groups()
        region_to_constraints: dict[tuple[int, int], list[tuple[frozenset[tuple[int, int]], int]]] = {}
        
        for i, (cells, count) in enumerate(constraints):
            representative = uf.find(next(iter(cells)))
            if representative not in region_to_constraints:
                region_to_constraints[representative] = []
            region_to_constraints[representative].append((cells, count))
        
        return list(region_to_constraints.values())
    
    def _calculate_probabilities(
        self,
        constraints: list[tuple[frozenset[tuple[int, int]], int]],
        cells: set[tuple[int, int]]
    ) -> dict[tuple[int, int], float]:
        """Calculates probabilities for cells using backtracking

        Args:
            constraints (list[tuple[frozenset[tuple[int, int]], int]]): List of constraints for the region
            cells (set[tuple[int, int]]): Set of cells in the region

        Returns:
            dict[tuple[int, int], float]: Dictionary {cell: probability of being a mine}
        """
        
        cells_list = sorted(list(cells))
        n = len(cells_list)
        
        if n == 0:
            return {}
        
        mine_counts: dict[tuple[int, int], int] = {cell: 0 for cell in cells}
        total_solutions = 0
        
        # Backtracking
        def backtrack(index: int, assignment: list[int]) -> None:
            nonlocal total_solutions
            
            if index == n:  # Went through everything
                if self._check_constraints(assignment, cells_list, constraints):
                    total_solutions += 1
                    for i, cell in enumerate(cells_list):
                        if assignment[i] == 1:
                            mine_counts[cell] += 1
                return
            
            for value in [0, 1]:
                assignment.append(value)
                
                # Early check
                if self._is_promising(assignment, cells_list, constraints):
                    backtrack(index + 1, assignment)
                
                assignment.pop()
        
        backtrack(0, [])
        
        if total_solutions == 0:  # 50/50
            return {cell: 0.5 for cell in cells}
        
        probabilities = {cell: mine_counts[cell] / total_solutions for cell in cells}
        
        return probabilities
    
    def _check_constraints(
        self,
        assignment: list[int],
        cells_list: list[tuple[int, int]],
        constraints: list[tuple[frozenset[tuple[int, int]], int]]
    ) -> bool:
        """Checks whether the assignment satisfies all constraints

        Args:
            assignment (list[int]): List of values ​​(0 or 1) for each cell
            cells_list (list[tuple[int, int]]): List of cells
            constraints (list[tuple[frozenset[tuple[int, int]], int]]): List of constraints

        Returns:
            bool: True if all constraints are met, else False
        """

        cell_to_value = {cells_list[i]: assignment[i] for i in range(len(assignment))}
        
        for constraint_cells, required_mines in constraints:
            mine_sum = sum(cell_to_value.get(cell, 0) for cell in constraint_cells)
            if mine_sum != required_mines:
                return False
        
        return True
    
    def _is_promising(
        self,
        partial_assignment: list[int],
        cells_list: list[tuple[int, int]],
        constraints: list[tuple[frozenset[tuple[int, int]], int]]
    ) -> bool:
        """Checks whether a partial assignment can lead to a valid solution

        Args:
            partial_assignment (list[int]): Partial list of values
            cells_list (list[tuple[int, int]]): List of cells
            constraints (list[tuple[frozenset[tuple[int, int]], int]]): List of constraints

        Returns:
            bool: True if there is a chance of finding a valid solution, else False
        """

        cell_to_value = {cells_list[i]: partial_assignment[i] 
                        for i in range(len(partial_assignment))}
        
        for constraint_cells, required_mines in constraints:
            assigned_count = 0
            mine_count = 0
            unassigned_count = 0
            
            for cell in constraint_cells:
                if cell in cell_to_value:
                    assigned_count += 1
                    if cell_to_value[cell] == 1:
                        mine_count += 1
                else:
                    unassigned_count += 1
            
            if mine_count > required_mines:
                return False
            
            if mine_count + unassigned_count < required_mines:
                return False
        
        return True  # There is a chance!