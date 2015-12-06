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
- SPREADING FIRE: Inactive cells neighboring 4 or more fire cells will become a fire cell
- SCORCH: Any live cell directly adjacent (no corners) to fire will die the next tick
- FIREFIGHTER: Any fire cell neighboring two or more live cells but not directly
    adjacent will turn into a water cell
- ABLAZE: Hospital cells neighboring 4 or more fire cells will be burnt down (-> inactive)
- EXTINGUISH: Fire cells neighboring water cells will be extinguished (-> inactive)
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
GRAY = (225, 225, 225)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (245, 50, 95)
BLUE = (50, 150, 250)
YELLOW = (245, 215, 50)
DARK_YELLOW = (255, 200, 15)

BACKGROUND_COLOR = WHITE
GRID_COLOR = GRAY

MAX_SCREEN_WIDTH = 1400
MAX_SCREEN_HEIGHT = 800
GRID_SPACING = 2

FRAMERATE = 5


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

        # cached later by World.setup_cells
        self.static = None
        self.neighbors = {}

    def __repr__(self):
        return "Cell(%s, %s, %s, '%s')" %(repr(self.world), self.row, self.col, self.identity)

    def __str__(self):
        return self.identity

    @property
    def updated(self):
        """Returns whether the cell is updated with the current world"""
        return self.ticks == self.world.ticks

    def is_static(self):
        """MUST CALL cache_neighbors BEFORE! Returns whether the cell should be static,
        based on its neighbors. (Itself and neighbors are all inactive cells)"""
        return self.identity == "inactive" and "inactive" in self.neighbors and len(self.neighbors) == 1

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

    def set_neighbors(self):
        """Sets instance attribute neighbors/adjacent/diagonals to the result of
        calling the respective functions."""
        neighbors, more = self.get_adjacent(), self.get_diagonals()
        self.adjacent, self.diagonals = neighbors, more
        for identity in more:
            if identity in neighbors:
                neighbors[identity] += more[identity]
            else:
                neighbors.update({identity : more[identity]})

        self.neighbors = neighbors

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

    # only returns the identity of the resulting cell
    # neighbors/adjaent/diagonals of cells must be cached beforehand
    def apply_solitude(self):
        """Applies the solitude rule: removes a live cell if it has fewer than
        2 live cell self.neighbors."""
        assert self.identity == "live", "Solitude can only be applied to live cells."
        if "live" not in self.neighbors:
            return "inactive"
        elif self.neighbors["live"] < 2:
            return "inactive"
        else:
            return "live"

    def apply_overpopulation(self):
        """Applies the overpopulation rule: removes a live cell with more than
        3 live self.neighbors."""
        assert self.identity == "live", "Overpopulation can only be applied to live cells."
        if "live" in self.neighbors and self.neighbors["live"] > 3:
            return "inactive"
        else:
            return "live"

    def apply_reproduction(self):
        """Applies the reproduction rule: an inactive cell becomes live if it has
        exactly 3 live self.neighbors."""
        assert self.identity == "inactive", "Reproduction can only be applied to inactive cells."
        if "live" in self.neighbors and self.neighbors["live"] == 3:
            return "live"
        else:
            return "inactive"

    def apply_burnout(self):
        """Applies the burnout rule: fire that is not directly adjacent to other
        fire cells will extinguish the next tick."""
        assert self.identity == "fire", "Burnout can only be applied to fire cells."
        if "fire" not in self.adjacent:
            return "inactive"
        else:
            return "fire"

    def apply_spreading_fire(self):
        """Applies the spreading fire rule: inactive cells neighboring 4 or more
        fire cells will become a fire cell."""
        assert self.identity == "inactive", "Spreading fire can only be applied to inactive cells."
        if "fire" in self.neighbors and self.neighbors["fire"] >= 4:
            return "fire"
        else:
            return "inactive"

    def apply_scorch(self):
        """Applies the scorch rule: any live cell directly adjacent (no corners)
        to fire will die the next tick."""
        assert self.identity == "live", "Spreading fire can only be applied to live cells."
        if "fire" in self.adjacent:
            return "inactive"
        else:
            return "live"

    def apply_firefighter(self):
        """Applies the firefighter rule: any fire cell neighboring two or more
        live cells but not directly adjacent will turn into a water cell."""
        assert self.identity == "fire", "Firefighter can only be applied to fire cells."
        if "live" in self.diagonals and self.diagonals["live"] >= 2:
            return "water"
        else:
            return "fire"

    def apply_extinguish(self):
        """Applies the extinguish rule: fire cells neighboring water cells will
        be extinguished (-> inactive)."""
        assert self.identity == "fire", "Extinguish can only be applied to fire cells."
        if "water" in self.neighbors:
            return "inactive"
        else:
            return "fire"

    def apply_drowning(self):
        """Applies the drowning rule: live cells neighboring 6 or more water
        cells will drown."""
        assert self.identity == "live", "Drowning can only be applied to live cells."
        if "water" in self.neighbors and self.neighbors["water"] >= 6:
            return "inactive"
        else:
            return "live"

    def apply_evaporation(self):
        """Applies the evaporation rule: water that is not directly adjacent to
        other water cells will evaporate the next tick."""
        assert self.identity == "water", "Evaporation can only be applied to water cells."
        if "water" not in self.adjacent:
            return "inactive"
        else:
            return "water"

# class InactiveCell(Cell):
#     color = WHITE
#     def __init__(self, world, row, col):
#         Cell.__init__(self, world, row, col, identity="inactive")


class World(object):
    """The board that represents the game world."""
    def __init__(self, name, rows, cols):
        self.name = name
        self.rows = rows
        self.cols = cols
        self.cells = [[Cell(self, i, j) for j in range(cols)] for i in range(rows)]
        self.ticks = 0

        self.setup_cells()

    def __repr__(self):
        return "World('%s', %s, %s)" %(self.name, self.rows, self.cols)

    # def __str__(self):
    #     "Print version"
    #     rows = [" ".join(list(map(lambda cell: str(CELLS_INDEX[cell.identity]), row))) for row in self.cells]
    #     return "\n".join(rows)

    def __str__(self):
        "The list version"
        return str([list(map(lambda cell: CELLS_INDEX[cell.identity], row)) for row in self.cells])

    def get_cell(self, row, col):
        """Returns the cell at position (row, col)."""
        return self.cells[row][col]

    def change_cell_identity(self, new, row, col):
        """Changes the cell identity at position (row, col) with the new one."""
        self.cells[row][col].identity = new

    def change_this_cell_identity(self, new, cell):
        """Changes the cell identity of an existing cell."""
        assert cell.world == self, "The cell does not exist in this world."
        self.change_cell_identity(new, cell.row, cell.col)

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

    def cache_neighbors(self):
        """Sets the instance variables neighbors/adjacent/diagonals of the
        World's Cells."""
        for row in self.cells:
            for cell in row:
                cell.set_neighbors()

    def cache_static(self):
        """Caches information about whether each cell should be updated (apply
        rules and blit)."""
        for row in self.cells:
            for cell in row:
                cell.static = cell.is_static()

    def setup_cells(self):
        """Caches the neighbors of cells and determines which ones are static."""
        self.cache_neighbors()
        self.cache_static()

    #######################
    # GAME LOOP FUNCTIONS #
    #######################

    def tick(self):
        """Updates the world board after one tick has passed."""
        self.setup_cells()

        updated = []
        for i in range(self.rows):
            this_row = []
            for j in range(self.cols):
                this_cell = self.get_cell(i, j)
                result_identity = this_cell.identity
                if not this_cell.static: # not only inactive cells surrounding
                    for rule in RULES[this_cell.identity]:
                        result_identity = rule(this_cell)
                        if result_identity != this_cell.identity: # breaks on first identity change
                            break
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
        self.dirty_rects = [pygame.Rect(0, 0, self.screen_size[0], self.screen_size[1])]

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

    def get_cell_rect(self, cell):
        """Gets the rect of a cell."""
        x_coor = cell.col * (self.cell_size + GRID_SPACING) + GRID_SPACING
        y_coor = cell.row * (self.cell_size + GRID_SPACING) + GRID_SPACING
        return pygame.Rect(x_coor, y_coor, self.cell_size, self.cell_size)

    def draw_cell(self, cell):
        """Blits a cell to the screen."""
        color = COLORS[cell.identity]

        cell_surface = pygame.Surface((self.cell_size, self.cell_size)).convert()
        cell_surface.fill(color)
        cell_rect = self.get_cell_rect(cell)
        self.dirty_rects.append(cell_rect)

        self.screen.blit(cell_surface, cell_rect)

    def draw_initial(self):
        """Blits the initial world to the screen."""
        for row in self.world.cells:
            for cell in row:
                self.draw_cell(cell)
        self.clock.tick(FRAMERATE)
        pygame.display.update()

    def draw_world(self):
        """Blits the world to the screen."""
        for row in self.world.cells:
            for cell in row:
                if not cell.static:
                    self.draw_cell(cell)

    def refresh(self):
        """Updates the screen without ticking the world."""
        self.draw_initial()

    def update(self):
        """Ticks the world and updates the screen."""
        self.dirty_rects, old = [], self.dirty_rects
        self.world.tick()
        self.draw_world()

        self.clock.tick(FRAMERATE)
        pygame.display.update(self.dirty_rects + old)
        # print(self.world)
        print(self.world.ticks)


class Drawing(pygame.sprite.Sprite):
    """An object that represents the game board in the drawing stage."""
    def __init__(self, display):
        self.display = display
        self.current = "live" # represents live cell
        self.mutable = self.get_mutable_cells()
        self.hitboxes = self.get_hitboxes()
        self.final_board()

    def get_mutable_cells(self):
        """Returns a list of all mutable (paintable) cells on the sceen."""
        mutable = []
        for row in self.display.world.cells:
            for cell in row:
                if cell.identity == "inactive":
                    mutable.append(cell)
        return mutable

    def get_hitboxes(self):
        """Returns a list of the hitboxes of all inactive cells on the sceen."""
        return [self.display.get_cell_rect(cell) for cell in self.mutable]

    def check_mouseover(self):
        """Called when mouse button is pressed. Returns the cell that the mouse
        is currently hovering over, or None."""
        pos = pygame.mouse.get_pos()
        for cell in self.mutable:
            if self.display.get_cell_rect(cell).collidepoint(pos):
                return cell

    def paint_cell(self):
        """Paints the cell that the mouse is currently over, or does nothing if
        the operation can't be done."""
        possible_cell = self.check_mouseover()
        if possible_cell:
            self.display.world.change_this_cell_identity(self.current, possible_cell)
            self.display.refresh()
        print(self.display.world)
        print("\n\n")

    def final_board(self):
        """Returns a list of lists that represents the final board to start the
        current game with."""
        drawing = True
        while drawing:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    drawing = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_0:
                    self.current = "inactive"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_1:
                    self.current = "live"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_2:
                    self.current = "fire"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_3:
                    self.current = "water"
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.paint_cell()

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
    Cell.apply_reproduction,
    Cell.apply_spreading_fire
]

LIVE_RULES = [
    Cell.apply_solitude,
    Cell.apply_overpopulation,
    Cell.apply_scorch,
    Cell.apply_drowning
]

FIRE_RULES = [
    Cell.apply_burnout,
    Cell.apply_firefighter,
    Cell.apply_extinguish
]

WATER_RULES = [
    Cell.apply_evaporation
]

RULES = {
    "inactive": INACTIVE_RULES,
    "live": LIVE_RULES,
    "fire": FIRE_RULES,
    "water": WATER_RULES
}

sample_initial = [[0 for i in range(30)] for j in range(20)]
sample_initial = [[0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1], [1, 0, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 1, 1], [0, 2, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 2, 2, 2, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 2, 1], [0, 2, 0, 2, 2, 0, 1, 1, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 0, 1, 0, 0, 2, 2, 0, 2, 0], [0, 2, 0, 2, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 2, 0, 2, 0], [0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 2, 0, 0, 1, 0, 0, 2, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0], [0, 0, 1, 1, 0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0], [0, 0, 0, 0, 1, 0, 0, 0, 0, 2, 0, 0, 0, 2, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], [0, 0, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 2, 0, 2, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 1, 1, 1, 0, 0], [0, 1, 0, 1, 0, 1, 0, 2, 2, 2, 2, 2, 0, 2, 0, 2, 0, 2, 2, 2, 2, 2, 0, 0, 0, 1, 1, 0, 1, 0], [0, 1, 1, 1, 1, 0, 0, 0, 2, 0, 0, 0, 2, 0, 2, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 1, 1, 1, 0, 0], [0, 0, 1, 0, 0, 0, 1, 0, 0, 2, 0, 0, 0, 2, 0, 2, 0, 0, 0, 2, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0], [0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0], [0, 2, 0, 2, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 2, 0], [0, 2, 0, 2, 2, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 0, 2, 2, 0, 2, 0], [1, 2, 0, 0, 0, 0, 0, 0, 3, 3, 0, 0, 0, 2, 2, 2, 0, 0, 0, 3, 3, 0, 0, 0, 0, 0, 0, 0, 2, 1], [1, 1, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 0, 1], [1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]]
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
    display.draw_initial()

    # Drawing loop
    drawing_board = Drawing(display)

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

# play(9, 14, sample_initial)
play(20, 30, sample_initial)
