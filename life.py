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
import pygame
import math

################
# PYGAME SETUP #
################

# Define some colors
BLACK = (0, 0, 0)
GRAY = (40, 40, 40)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (245, 50, 95)
BLUE = (50, 150, 250)
YELLOW = (245, 215, 50)
DARK_YELLOW = (255, 200, 15)

BACKGROUND_COLOR = WHITE
GRID_COLOR = GRAY

MAX_SCREEN_WIDTH = 1200
MAX_SCREEN_HEIGHT = 600
GRID_SPACING = 1

FRAMERATE = 100


class Cell(pygame.sprite.Sprite):
    """A cell in the game."""
    def __init__(self, world, row, col, identity="inactive"):
        """Initializes a cell in a certain world object at position (row, col)."""
        pygame.sprite.Sprite.__init__(self)
        self.world = world
        self.row = row
        self.col = col
        self.identity = identity
        self.ticks = 0

        self.static = True #FIXME could be buggy
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

    def is_static(self, neighbors):
        """Returns whether the cell should be static, based on its neighbors.
        (Itself and neighbors are all inactive cells)"""
        return self.identity == "inactive" and "inactive" in neighbors and len(neighbors) == 1

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

        return adjacent

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

        return diagonals

    def get_neighbors(self):
        neighbors, more = self.get_adjacent(), self.get_diagonals()
        for identity in more:
            if identity in neighbors:
                neighbors[identity] += more[identity]
            else:
                neighbors.update({identity : more[identity]})

        return neighbors

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

    # def apply_solitude(self, neighbors):
    #     """Applies the solitude rule: removes a live cell if it has fewer than
    #     2 live cell neighbors."""
    #     assert self.identity == "live", "Solitude can only be applied to live cells."
    #     if "live" not in neighbors:
    #         self.remove()
    #     elif neighbors["live"] < 2:
    #         self.remove()
    #
    # def apply_overpopulation(self, neighbors):
    #     """Applies the overpopulation rule: removes a live cell with more than
    #     3 live neighbors."""
    #     assert self.identity == "live", "Overpopulation can only be applied to live cells."
    #     if "live" in neighbors and neighbors["live"] > 3:
    #         self.remove()
    #
    # def apply_reproduction(self, neighbors):
    #     """Applies the reproduction rule: an inactive cell becomes live if it has
    #     exactly 3 live neighbors."""
    #     assert self.identity == "inactive", "Reproduction can only be applied to inactive cells."
    #     if "live" in neighbors and neighbors["live"] == 3:
    #         self.revive()

    # only returns the identity of the resulting cell
    def apply_solitude(self, neighbors):
        """Applies the solitude rule: removes a live cell if it has fewer than
        2 live cell neighbors."""
        assert self.identity == "live", "Solitude can only be applied to live cells."
        if "live" not in neighbors:
            return "inactive"
        elif neighbors["live"] < 2:
            return "inactive"
        else:
            return "live"

    def apply_overpopulation(self, neighbors):
        """Applies the overpopulation rule: removes a live cell with more than
        3 live neighbors."""
        assert self.identity == "live", "Overpopulation can only be applied to live cells."
        if "live" in neighbors and neighbors["live"] > 3:
            return "inactive"
        else:
            return "live"

    def apply_reproduction(self, neighbors):
        """Applies the reproduction rule: an inactive cell becomes live if it has
        exactly 3 live neighbors."""
        assert self.identity == "inactive", "Reproduction can only be applied to inactive cells."
        if "live" in neighbors and neighbors["live"] == 3:
            return "live"
        else:
            return "inactive"

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
        """Initializes or overwrites the world with a given configuration."""
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
        updated = []
        for i in range(self.rows):
            this_row = []
            for j in range(self.cols):
                this_cell = self.get_cell(i, j)
                result_identity = this_cell.identity
                neighbors = this_cell.get_neighbors()
                if not this_cell.is_static(neighbors): # not only inactive cells surrounding
                    this_cell.static = False
                    for rule in RULES[this_cell.identity]:
                        result_identity = rule(this_cell, neighbors)
                this_cell.ticks += 1
                this_row.append(CELLS_INDEX[result_identity])
            updated.append(this_row)

        self.initialize(updated)
        self.ticks += 1

class Display(pygame.sprite.Sprite):
    """A Display object that renders a world. There can only be one Display instance."""

    def __init__(self, world):
        pygame.sprite.Sprite.__init__(self)
        self.world = world

        self.cell_size = self.get_cell_size()
        self.screen_size = self.get_screen_size()

        self.screen = pygame.display.set_mode(self.screen_size)
        self.screen.fill(GRID_COLOR)
        pygame.display.set_caption("The Game of Life")

        # Used to manage how fast the screen updates
        self.clock = pygame.time.Clock()

        # Used to update position of cells
        self.dirty_rects = []

    def get_cell_size(self):
        """Returns the side length (pixels) of each cell based on screen/grid bounds."""
        x_width = (MAX_SCREEN_WIDTH - GRID_SPACING)/self.world.cols - GRID_SPACING
        y_width = (MAX_SCREEN_HEIGHT - GRID_SPACING)/self.world.rows - GRID_SPACING
        return int(math.floor(min(x_width, y_width)))

    def get_screen_size(self):
        """Returns the screen width, height in pixels."""
        return [int(coor) for coor in
            [self.world.cols * (self.cell_size + GRID_SPACING) + GRID_SPACING,
            self.world.rows * (self.cell_size + GRID_SPACING) + GRID_SPACING]]

    def draw_cell(self, cell):
        """Blits a cell to the screen."""
        color = COLORS[cell.identity]
        x_coor = cell.col * (self.cell_size + GRID_SPACING) + GRID_SPACING
        y_coor = cell.row * (self.cell_size + GRID_SPACING) + GRID_SPACING

        cell_surface = pygame.Surface((self.cell_size, self.cell_size)).convert()
        cell_surface.fill(color)
        cell_rect = cell_surface.get_rect()
        self.dirty_rects.append(cell_rect)

        self.screen.blit(cell_surface, (x_coor, y_coor))

    def draw_initial(self):
        """Blits the initial world to the screen."""
        for row in self.world.cells:
            for cell in row:
                self.draw_cell(cell)

    def draw_world(self):
        """Blits the world to the screen."""
        for row in self.world.cells:
            for cell in row:
                if not cell.static:
                    self.draw_cell(cell)

    def update(self):
        """Ticks the world and updates the screen."""
        self.dirty_rects = []
        self.world.tick()
        self.draw_world()
        self.clock.tick(FRAMERATE)
        pygame.display.update(self.dirty_rects)

#################
# CELLS & RULES #
#################

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

COLORS = {
    "inactive": WHITE,
    "live": BLACK,
    "fire": RED,
    "water": BLUE
}

# Comment rules to deactivate them for the game
INACTIVE_RULES = [
    Cell.apply_reproduction
]

LIVE_RULES = [
    Cell.apply_solitude,
    Cell.apply_overpopulation
]

RULES = {
    "inactive": INACTIVE_RULES,
    "live": LIVE_RULES
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

#############
# GAME LOOP #
#############

def play(rows, cols, initial):
    """Simulates the game of life."""
    pygame.init()
    done = False

    # Set up World and Display
    world = World("Life", rows, cols)
    world.initialize(initial)

    display = Display(world)
    world.tick()
    display.draw_initial()

    # Main game loop
    while not done:
        """
        PYGAME EVENT LOOP
         - for button presses, mouse clicks, quitting, etc.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True

        # Main update loop
        display.update()
    pygame.quit()

play(9, 14, sample_initial)
