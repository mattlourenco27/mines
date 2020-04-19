# Created on 10 Mar 2020
# Created by: Matthew Lourenco
# This file plays the mines game

import random
import tile


class Error(Exception):
    """
    Base class for exceptions in this game
    """
    pass


class MineError(Error):
    """Exception raised when number of mines is invalid

    Attributes:
        - message
    """

    def __init__(self, message):
        self.message = message


# This class controls the mines game
class Game:
    SIZE = 20
    MINES = 40

    def __init__(self):
        # grid that will be used to store the game board
        self._grid = []
        for i in range(Game.SIZE):
            self._grid.append([])
            for j in range(Game.SIZE):
                self._grid[i].append(tile.Tile())

    # clear the grid
    def _clear(self):
        for col in self._grid:
            for element in col:
                element.value = 0
                element.state = tile.State.covered
                element.is_mine = False

    # Clear the grid and populate it with mines
    # Does not generate mines in a 1 tile radius of init x and y
    def _populate(self, init_x, init_y):
        self._clear()

        mines = Game.MINES

        if mines > Game.SIZE * Game.SIZE - 9:
            raise MineError("Too many mines for this size of board")

        random.seed()

        while mines > 0:
            x = random.randint(0, Game.SIZE - 1)
            y = random.randint(0, Game.SIZE - 1)

            if self._grid[x][y].is_mine:
                continue

            self._grid[x][y].is_mine = True
            mines -= 1

    # update what number a given tile should display
    def _update_tile_value(self, x, y):
        if x < 0 or y < 0 or x >= Game.SIZE or y >= Game.SIZE:
            print("Access to grid out of range [" + str(x) + "][" + str(y) + "]")

        if self._grid[x][y].is_mine:
            return

        count = 0

        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if i >= 0 and i < Game.SIZE and j >= 0 and j < Game.SIZE and self._grid[i][j].is_mine:
                    count += 1

    # checks if the game was won
    def _check_win(self):
        all_visible = True
        all_mines = True

        for col in self._grid:
            for element in col:
                if element.is_mine and element.state != tile.State.flag:
                    all_mines = False
                elif not element.is_mine and element.state != tile.State.visible:
                    all_visible = False

        return all_visible or all_mines

    # runs the game
    def run(self):
        self._populate(0, 0)

        for x in range(Game.SIZE):
            for y in range(Game.SIZE):
                self._update_tile_value(x, y)

    def print(self):
        for col in self._grid:
            for element in col:
                print(str(element) + ' ', end='')
            print()


if __name__ == "__main__":
    g = Game()
    g.run()
    g.print()
