"""CONWAY'S GAME OF LIFE, EXTENDED"""

##################
# TYPES OF CELLS #
##################

"""
1. Live cell - a live member of the game
2. Active cell - a cell that was once a live cell or another type of cell but has died/vanished
3. Inactive cell - the default state of a cell, has not been touched by other cells
4. Fire cell - a cell that extinguishes life
5. Water cell - a cell that extinguishes fire, but may cause drowning
6. Virus cell - a cell that moves on its own, spreads, and slowly causes life to perish
7. Diseased cell - a live cell that has been infected, and will infect other cells
8. Hospital cell - a cell that cures and eliminates Viruses and the Diseased
9. Technology cell - a cell that creates money
10. Money cell - a cell that attracts live cells
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
- FIREFIGHTER: Any fire cell neighboring two or more live cells but not directly adjacent will turn into a water cell
- ABLAZE: Hospital cells neighboring 4 or more fire cells will be burnt down (-> active)
- EXTINGUISH: Fire cells neighboring water cells will be extinguished (-> active)
- DROWNING: Live cells neighboring 6 or more water cells will drown
- EVAPORATION: Water that is not directly adjacent to other water cells will evaporate the next tick
"""
