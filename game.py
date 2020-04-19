# Created on 10 Mar 2020
# Created by: Matthew Lourenco
# This file plays the mines game

import random
import tile
from enum import Enum, auto


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


class TilePositionError(Error):
    """Exception raised when an attempt is made to access a tile that is out of bounds

    Attributes:
        - message
    """

    def __init__(self, message):
        self.message = message


# this enum describes the state of the game
class State(Enum):
    beforeStart = auto()
    ongoing = auto()
    loss = auto()
    victory = auto()


# This class controls the mines game
class Game:
    def __init__(self):
        # state variable that keeps track of the game
        self._state = State.beforeStart

        # integers describing the size and format of the game
        self._size = 20
        self._mines = 40

        # true if board has been clicked once
        self._first_click = False

        # grid that will be used to store the game board
        self._grid = []
        for i in range(self._size):
            self._grid.append([])
            for j in range(self._size):
                self._grid[i].append(tile.Tile())

    # begin the game
    def begin(self):
        if self._state is State.beforeStart:
            self._state = State.ongoing
            self._first_click = False

    # resets the game
    def reset(self):
        self._clear()
        self._state = State.beforeStart

    # sets the number of mines in the game if it is a valid game state
    def set_mines(self, m):
        if self._state is not State.ongoing:
            self._mines = m

    # sets the size of the board if it is a valid game state
    # updates the size of self._grid and calls self.reset()
    def set_size(self, s):
        if self._state is not State.ongoing:
            self._size = s

            self._grid = []
            for i in range(self._size):
                self._grid.append([])
                for j in range(self._size):
                    self._grid[i].append(tile.Tile())

            self.reset()

    # Reveals the tile at the specified x, y coordinate
    def left_mouse_button(self, x, y):
        if x < 0 or y < 0 or x >= self._size or y >= self._size:
            raise TilePositionError("Access to Tile out of range [" + str(x) + "][" + str(y) + "]")

        if self._state != State.ongoing:
            return

        if not self._first_click:
            self._populate(x, y)
            self._update_all_tiles()
            self._first_click = True

            self._reveal_adjacent_blanks(x, y)

            if self._check_win():
                self._state = State.victory
        elif self._grid[x][y].state != tile.State.visible:
            if self._grid[x][y].is_blank():
                self._reveal_adjacent_blanks(x, y)

                if self._check_win():
                    self._state = State.victory
            else:
                self._grid[x][y].state = tile.State.visible

                if self._grid[x][y].is_mine():
                    self._state = State.loss
                elif self._check_win():
                    self._state = State.victory

    # clear the grid
    def _clear(self):
        for col in self._grid:
            for element in col:
                element.set_value(tile.BLANK)
                element.state = tile.State.covered

    # Clear the grid and populate it with mines
    # Does not generate mines in a 1 tile radius of init x and y
    def _populate(self, init_x, init_y):
        self._clear()

        mines = self._mines

        if mines > self._size * self._size - 9:
            raise MineError("Too many mines for this size of board")

        random.seed()

        while mines > 0:
            x = random.randint(0, self._size - 1)
            y = random.randint(0, self._size - 1)

            # if this is an existing mine tile do not count down mine count
            if self._grid[x][y].is_mine():
                continue

            # if this tile is within 1 tile radius of the initial position do not place a mine
            if init_x - 1 <= x <= init_x + 1 or init_y - 1 <= y <= init_y + 1:
                continue

            self._grid[x][y].set_value(tile.MINE)
            mines -= 1

    # update what number a given tile should display
    def _update_tile_value(self, x, y):
        if x < 0 or y < 0 or x >= self._size or y >= self._size:
            raise TilePositionError("Access to Tile out of range [" + str(x) + "][" + str(y) + "]")

        if self._grid[x][y].is_mine():
            return

        count = 0

        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if 0 <= i < self._size and 0 <= j < self._size and self._grid[i][j].is_mine():
                    count += 1

        self._grid[x][y].set_value(count)

    # updates all tiles
    def _update_all_tiles(self):
        for x in range(self._size):
            for y in range(self._size):
                self._update_tile_value(x, y)

    # reveals all blanks that are connected to this tile including itself
    # also reveals surrounding tiles
    def _reveal_adjacent_blanks(self, x, y):
        blanks = []
        if self._grid[x][y].is_blank():
            blanks.append((x, y))

        while (len(blanks) > 0):
            x_pos, y_pos = blanks.pop()

            # set this blank to visible
            self._grid[x_pos][y_pos].state = tile.State.visible

            for i in range(x_pos - 1, x_pos + 2):
                for j in range(y_pos - 1, y_pos + 2):
                    if 0 <= i < self._size and 0 <= j < self._size:
                        if self._grid[i][j].is_blank() and self._grid[i][j].state != tile.State.visible:
                            # add all non-visible blanks to the list
                            blanks.append((i, j))
                        else:
                            # make all non-blank adjacent tiles visible
                            self._grid[i][j].state = tile.State.visible

    # checks if the game was won
    def _check_win(self):
        all_visible = True
        all_mines = True

        for col in self._grid:
            for element in col:
                if element.is_mine() and element.state != tile.State.flag:
                    all_mines = False
                elif not element.is_mine() and element.state != tile.State.visible:
                    all_visible = False

        return all_visible or all_mines

    def print(self):
        for col in self._grid:
            for element in col:
                print(str(element) + ' ', end='')
            print()


if __name__ == "__main__":
    g = Game()
    g.begin()
    g.left_mouse_button(10, 10)
    g.print()
