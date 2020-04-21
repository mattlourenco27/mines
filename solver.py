# Created on 19 Apr 2020
# Created by: Matthew Lourenco
# This file solves the mines game using logic and probability when given a game object

import game
import tile

_COVERED = -1
_FLAG = -2


class Solver:
    def __init__(self, g: game.Game):
        # begin the game if it was not already begun
        g.begin()

        # grid to store known tile values
        self._grid: [[int]] = []

        # size of the board
        self._size = g.get_size()

        for x in range(self._size):
            self._grid.append([])
            for y in range(self._size):
                self._grid[x].append(_COVERED)

        self._update_grid(g)

    # update the local state of the tile at the specified position
    def _update_tile(self, g: game.Game, x: int, y: int):
        if g.get_tile_state(x, y) is tile.State.covered:
            self._grid[x][y] = _COVERED
        elif g.get_tile_state(x, y) is tile.State.flag:
            self._grid[x][y] = _FLAG
        elif g.get_tile_state(x, y) is tile.State.visible:
            self._grid[x][y] = g.get_tile_value(x, y)
        elif g.get_tile_state(x, y) is tile.State.unknown:
            raise Exception("Unknown tile encountered at (" + str(x) + ", " + str(y) + ")")

    # update all of the local tiles
    def _update_grid(self, g: game.Game):
        for x in range(self._size):
            for y in range(self._size):
                self._update_tile(g, x, y)

    # do a logical scan of all the tiles on the local grid
    # flag or reveal valid tiles
    def _do_logic_scan(self, g: game.Game):
        self._update_grid(g)

        for x in range(self._size):
            for y in range(self._size):
                if self._grid[x][y] > 0:

                    # scan the surrounding tiles
                    flags = 0
                    covered: [(int, int)] = []

                    for i in range(x - 1, x + 2):
                        for j in range(y - 1, y + 2):
                            if 0 <= i < self._size and 0 <= j < self._size and self._grid[i][j] == _FLAG:
                                flags += 1
                            if 0 <= i < self._size and 0 <= j < self._size and self._grid[i][j] == _COVERED:
                                covered.append((i, j))

                    # first check if there are enough flags to satisfy the tile value
                    if flags == self._grid[x][y] and len(covered) > 0:
                        for element in covered:
                            i, j = element
                            g.left_mouse_button(i, j)
                            self._update_tile(g, i, j)

                            # if a blank was hit update the whole board
                            if self._grid[i][j] == 0:
                                self._update_grid(g)

                    # next check if the number of covered spaces + number of flags is equal to the tile value
                    elif flags + len(covered) == self._grid[x][y]:
                        for element in covered:
                            i, j = element
                            g.right_mouse_button(i, j)
                            self._update_tile(g, i, j)


if __name__ == "__main__":
    g = game.Game()

    print("Welcome to mines! Created by mattlourenco27 on github")

    # get size and number of mines
    size: int
    while True:
        try:
            size = int(input("Enter the size of the grid: "))
            g.set_size(size)
            g.print()
            break
        except ValueError:
            print("Please enter an integer")
        except game.SizeError:
            print("Please enter a grid between 10 and 100 tiles wide")

    mines: int
    while True:
        try:
            mines = int(input("Enter the number of mines on the grid: "))
            g.set_mines(mines)
            g.begin()
            break
        except ValueError:
            print("Please enter an integer")
        except game.MineError as err:
            print(err)
            print("Please enter a valid number of mines")

    print("Please use 'L' or 'R' for left or right click followed by coordinates to interact\nEx: L 0 0")
    print("Type 'solve one step' to do one logical step over the board")

    solver = Solver(g)

    while not g.game_done():
        # print the grid
        g.print()

        # get the next move
        left: bool = True
        x: int
        y: int
        while True:
            try:
                user_in = input("Enter your next move: ")
                values = user_in.split(' ')

                if values[0].capitalize() == 'Q':
                    print("Exiting...")
                    quit()

                if values[0].upper() == 'SOLVE' and values[1].upper() == 'ONE' and values[2].upper() == 'STEP':
                    solver._do_logic_scan(g)
                    break

                if values[0].upper() != 'L' and values[0].upper() != 'R':
                    print("Please enter L or R for 'left' or 'right' click")
                    continue

                left = values[0].upper() == 'L'
                x = int(values[1])
                y = int(values[2])

                if left:
                    g.left_mouse_button(x, y)
                else:
                    g.right_mouse_button(x, y)

                break
            except IndexError:
                print("Please enter three values separated by spaces")
            except ValueError:
                print("Please enter valid integers in your expression")
            except game.TilePositionError as err:
                print(err)
                print("Please enter a valid expression")

    # final print of the grid
    g.print()
