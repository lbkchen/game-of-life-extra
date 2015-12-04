"""CONWAY'S GAME OF LIFE, EXTENDED"""

##################
# TYPES OF CELLS #
##################

"""
1. Inactive cell - the default state of a cell, has not been touched by other cells
2. Live cell - a live member of the game
3. Fire cell - a cell that extinguishes life
4. Water cell - a cell that extinguishes fire, but may cause drowning
5. Virus cell - a cell that moves on its own, spreads, and slowly causes life to perish
6. Diseased cell - a live cell that has been infected, and will infect other cells
7. Hospital cell - a cell that cures and eliminates Viruses and the Diseased
8. Technology cell - a cell that creates money
9. Money cell - a cell that attracts live cells
"""
#########
# RULES #
#########

# Standard
"""
1. SOLITUDE: Any live cell with fewer than two live neighbours dies, as if caused by under-population.
2. STASIS: Any live cell with two or three live neighbours lives on to the next generation.
3. OVERPOPULATION: Any live cell with more than three live neighbours dies
4. REPRODUCTION: Any dead cell with exactly three live neighbours becomes a live cell
"""

# Extra
"""
- BURNOUT: Fire that is not directly adjacent to other fire cells will extinguish the next tick
- SPREADING FIRE: Active/inactive cells neighboring 4 or more fire cells will become a fire cell
- SCORCH: Any live cell directly adjacent (no corners) to fire will die the next tick
- FIREFIGHTER: Any fire cell neighboring two or more live cells but not directly
    adjacent will turn into a water cell
- ABLAZE: Hospital cells neighboring 4 or more fire cells will be burnt down (-> active)
- EXTINGUISH: Fire cells neighboring water cells will be extinguished (-> active)
- DROWNING: Live cells neighboring 6 or more water cells will drown
- EVAPORATION: Water that is not directly adjacent to other water cells will evaporate the next tick
"""
# import pygame

class Cell(object):
    """A cell in the game."""
    def __init__(self, world, row, col, identity="inactive"):
        """Initializes a cell in a certain world object at position (row, col)."""
        self.world = world
        self.row = row
        self.col = col
        self.identity = identity
        self.ticks = 0
        # self.top_border = (row == 0)
        # self.bottom_border = (row == world.rows - 1)
        # self.left_border = (col == 0)
        # self.right_border = (col == world.cols - 1)

    def __repr__(self):
        return "Cell(%s, %s, %s, '%s')" %(repr(self.world), self.row, self.col, self.identity)

    def __str__(self):
        return self.identity

    @property
    def updated(self):
        """Returns whether the cell is updated with the current world"""
        return self.ticks == self.world.ticks

    #####################
    # UTILITY FUNCTIONS #
    #####################
    def get_adjacent(self):
        """Returns a dictionary of the types of cells adjacent around self
        and their corresponding frequencies.""" #FIXME inefficient checking
        adjacent = {}
        list_adjacent = [
            self.world.get_cell((self.row - 1) % self.world.rows, self.col).identity, # top
            self.world.get_cell((self.row + 1) % self.world.rows, self.col).identity, # bottom
            self.world.get_cell(self.row, (self.col - 1) % self.world.cols).identity, # left
            self.world.get_cell(self.row, (self.col + 1) % self.world.cols).identity] # right

        for identity in list_adjacent:
            if identity in adjacent:
                adjacent[identity] += 1
            else:
                adjacent.update({identity:1})

    def get_diagonals(self):
        """Returns a dictionary of the types of cells diagonal around self
        and their corresponding frequencies."""
        diagonals = {}
        list_diagonals = []
        for x in [-1, 1]:
            for y in [-1, 1]:
                list_diagonals.append(
                self.world.get_cell((self.row + x) % self.world.rows,
                                    (self.col + y) % self.world.cols).identity)

        for identity in list_diagonals:
            if identity in diagonals:
                diagonals[identity] += 1
            else:
                diagonals.update({identity:1})

    def get_neighbors(self):
        neighbors, more = self.get_adjacent(), self.get_diagonals()
        for identity in more:
            if identity in neighbors:
                neighbors[identity] += more[identity]
            else:
                neighbors.update({identity : more[identity]})

    def revive(self):
        """Turns a cell's identity to live in the cell's world."""
        assert self.identity == "inactive" or self.identity == "diseased", "Cannot apply revive to %s cell" %self.identity
        self.identity = "live"

    def remove(self):
        """Turns the cell's identity to inactive in the cell's world.""" #FIXME can probably just do self.identity = inactive
        self.world.remove_cell(self.row, self.col)

    ########################
    # RULE IMPLEMENTATIONS #
    ########################

    def apply_solitude(self, neighbors):
        """Applies the solitude rule: removes a live cell if it has fewer than
        2 live cell neighbors."""
        assert self.identity == "live", "Solitude can only be applied to live cells."
        if "live" not in neighbors:
            self.remove()
        elif neighbors["live"] < 2:
            self.remove()

    def apply_overpopulation(self, neighbors):
        """Applies the overpopulation rule: removes a live cell with more than
        3 live neighbors."""
        assert self.identity == "live", "Overpopulation can only be applied to live cells."
        if "live" in neighbors and neighbors["live"] > 3:
            self.remove()

    def apply_reproduction(self, neighbors):
        """Applies the reproduction rule: an inactive cell becomes live if it has
        exactly 3 live neighbors."""
        assert self.identity == "inactive", "Reproduction can only be applied to inactive cells."
        if "live" in neighbors and neighbors["live"] == 3:
            self.revive()

class World(object):
    """The board that represents the game world."""
    def __init__(self, name, rows, cols):
        self.name = name
        self.rows = rows
        self.cols = cols
        self.cells = [[Cell(self, i, j) for j in range(cols)] for i in range(rows)]
        self.ticks = 0

    def __repr__(self):
        return "World('%s', %s, %s)" %(self.name, self.rows, self.cols)

    def __str__(self):
        rows = [" ".join(list(map(lambda cell: str(CELLS_INDEX[cell.identity]), row))) for row in self.cells]
        return "\n".join(rows)

    def get_cell(self, row, col):
        """Returns the cell at position (row, col)."""
        return self.cells[row][col]

    def change_cell_identity(self, new, row, col):
        """Changes the cell identity at position (row, col) with the new one."""
        self.cells[row][col].identity = new

    def replace_cell(self, new, row, col):
        """Replaces the cell at position (row, col) with the new cell."""
        self.cells[row][col] = new

    def remove_cell(self, row, col):
        """Changes the identity of cell at position (row, col) to inactive."""
        this_cell = self.get_cell(row, col)
        this_cell.identity = "inactive"

    def initialize(self, initial):
        """Initializes the world with a given initial configuration."""
        assert len(initial) == self.rows and len(initial[0]) == self.cols, "Bad dimensions"
        for i in range(self.rows):
            for j in range(self.cols):
                initial_cell_type = CELLS[initial[i][j]]
                self.change_cell_identity(initial_cell_type, i, j)

    #######################
    # GAME LOOP FUNCTIONS #
    #######################

    def tick(self):
        """Updates the world board after one tick has passed."""
        pass

CELLS = {
    0: "inactive",
    1: "live",
    2: "fire",
    3: "water"
}

CELLS_INDEX = {
    "inactive": 0,
    "live":     1,
    "fire":     2,
    "water":    3
}

# Comment rules to deactivate them for the game
RULES = {
    "solitude": Cell.apply_solitude,
    "overpopulation": Cell.apply_overpopulation,
    "reproduction": Cell.apply_reproduction
}

sample_initial = [
[1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0],
[0, 0, 0, 1, 0, 1, 0, 1, 1, 0, 0, 0, 0, 0],
[0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
[0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0],
[0 for i in range(14)],
[0 for i in range(14)],
[0 for i in range(14)],
[0 for i in range(14)],
[0 for i in range(14)]
]

def play(rows, cols, initial):
    """Simulates the game of life."""
    world = World("Life", rows, cols)
    world.initialize(initial)
