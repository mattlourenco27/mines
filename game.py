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


class TilePositionError(Error):
    """Exception raised when an attempt is made to access a tile that is out of bounds

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
        # true if board has been clicked once
        self._first_click = False

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
                element.set_value(tile.BLANK)
                element.state = tile.State.covered

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
        if x < 0 or y < 0 or x >= Game.SIZE or y >= Game.SIZE:
            raise TilePositionError("Access to Tile out of range [" + str(x) + "][" + str(y) + "]")

        if self._grid[x][y].is_mine():
            return

        count = 0

        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if 0 <= i < Game.SIZE and 0 <= j < Game.SIZE and self._grid[i][j].is_mine():
                    count += 1

        self._grid[x][y].set_value(count)

    # updates all tiles
    def _update_all_tiles(self):
        for x in range(Game.SIZE):
            for y in range(Game.SIZE):
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
                    if 0 <= i < Game.SIZE and 0 <= j < Game.SIZE:
                        if self._grid[i][j].is_blank() and self._grid[i][j].state != tile.State.visible:
                            # add all non-visible blanks to the list
                            blanks.append((i, j))
                        else:
                            # make all non-blank adjacent tiles visible
                            self._grid[i][j].state = tile.State.visible

    # Reveals the tile at the specified x, y coordinate
    def left_mouse_button(self, x, y):
        if x < 0 or y < 0 or x >= Game.SIZE or y >= Game.SIZE:
            raise TilePositionError("Access to Tile out of range [" + str(x) + "][" + str(y) + "]")

        if not self._first_click:
            self._populate(x, y)
            self._update_all_tiles()
            self._first_click = True

            self._reveal_adjacent_blanks(x, y)
        elif self._grid[x][y].state != tile.State.visible:
            if self._grid[x][y].is_blank():
                self._reveal_adjacent_blanks(x, y)
            else:
                self._grid[x][y].state = tile.State.visible

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

    # resets the game
    def reset(self):
        self._clear()
        self._first_click = False

    def print(self):
        for col in self._grid:
            for element in col:
                print(str(element) + ' ', end='')
            print()


if __name__ == "__main__":
    g = Game()
    g.left_mouse_button(10, 10)
    g.print()
