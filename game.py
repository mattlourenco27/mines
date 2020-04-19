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


class SizeError(Error):
    """Exception raised when the size of the board is invalid

    Attributes:
        - message
    """

    def __init__(self, message):
        self.message = message


class MineError(Error):
    """Exception raised when number of mines is invalid

    Attributes:
        - message
        - size - the size of the grid
        - mines - the number of mines
    """

    def __init__(self, message, size, mines):
        self.message = message
        self.size = size
        self.mines = mines

    def __str__(self):
        return self.message + ". The grid has " + str(self.size * self.size) + " tiles and " + str(
            self.mines) + " mines"


class TilePositionError(Error):
    """Exception raised when an attempt is made to access a tile that is out of bounds

    Attributes:
        - message
        - size - the size of the grid
        - position - pair that holds coordinates to the attempted access
    """

    def __init__(self, message, size, position):
        self.message = message
        self.size = size
        self.position = position

    def __str__(self):
        return self.message + ". Attempted access at " + str(self.position) + ", width of grid is " + str(self.size)


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
        self._size = 10
        self._mines = 10

        # integer keeping track of the number of flags that were placed
        self._flags = 0

        # true if board has been clicked once
        self._first_click = False

        # grid that will be used to store the game board
        self._grid: [[tile.Tile]] = []
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
        self._flags = 0

    # returns true if the game is done
    def game_done(self) -> bool:
        return self._state is State.victory or self._state is State.loss

    # reveals the mines when the game is lost
    def reveal_mines(self):
        if self._state is State.loss:
            for col in self._grid:
                for element in col:
                    element.state = tile.State.visible

    # sets the number of mines in the game if it is a valid game state
    def set_mines(self, m: int):
        if self._state is not State.ongoing:
            self._mines = m

    # sets the size of the board if it is a valid game state
    # updates the size of self._grid and calls self.reset()
    def set_size(self, s: int):
        if self._state is not State.ongoing:
            if s < 10:
                raise SizeError("Invalid board size. size is less than 10")
            if s > 100:
                raise SizeError("Invalid board size. size is greater than 100")

            self._size = s

            self._grid.clear()
            for i in range(self._size):
                self._grid.append([])
                for j in range(self._size):
                    self._grid[i].append(tile.Tile())

            self.reset()

    # returns the tile value at a given position if it is visible
    def get_tile_value(self, x: int, y: int) -> int:
        if x < 0 or y < 0 or x >= self._size or y >= self._size:
            raise TilePositionError("Access to Tile out of range", self._size, (x, y))

        if self._grid[x][y].state is tile.State.visible:
            return self._grid[x][y].get_value()
        else:
            return 0

    # returns the tile state at a given position
    def get_tile_state(self, x: int, y: int) -> tile.State:
        if x < 0 or y < 0 or x >= self._size or y >= self._size:
            raise TilePositionError("Access to Tile out of range", self._size, (x, y))

        return self._grid[x][y].state

    # reveals the tile at the specified x, y coordinate
    def left_mouse_button(self, x: int, y: int):
        if x < 0 or y < 0 or x >= self._size or y >= self._size:
            raise TilePositionError("Access to Tile out of range", self._size, (x, y))

        if self._state != State.ongoing:
            return

        # do nothing if the tile is not a covered tile
        if self._grid[x][y].state is not tile.State.covered:
            return

        if not self._first_click:
            self._populate(x, y)
            self._update_all_tiles()
            self._first_click = True

            if self._grid[x][y].is_blank():
                self._reveal_adjacent_blanks(x, y)
            else:
                self._grid[x][y].state = tile.State.visible

            if self._check_win():
                self._state = State.victory

        else:
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

    # cycles the state of a covered tile
    def right_mouse_button(self, x: int, y: int):
        if x < 0 or y < 0 or x >= self._size or y >= self._size:
            raise TilePositionError("Access to Tile out of range", self._size, (x, y))

        if self._state != State.ongoing:
            return

        # do nothing to visible tiles
        if self._grid[x][y].state is tile.State.visible:
            return

        if self._grid[x][y].state is tile.State.covered:
            self._grid[x][y].state = tile.State.flag
            self._flags += 1
        elif self._grid[x][y].state is tile.State.flag:
            self._grid[x][y].state = tile.State.unknown
            self._flags -= 1
        elif self._grid[x][y].state is tile.State.unknown:
            self._grid[x][y].state = tile.State.covered

    # clear the grid
    def _clear(self):
        for col in self._grid:
            for element in col:
                element.set_value(tile.BLANK)
                element.state = tile.State.covered

    # populates the grid with mines
    # Does not generate mines on the init x and y tile or immediately beside it
    def _populate(self, init_x: int, init_y: int):
        mines = self._mines

        if mines > self._size * self._size - 9:
            raise MineError("Too many mines for this size of board", self._size, self._mines)

        random.seed()

        while mines > 0:
            x: int = random.randint(0, self._size - 1)
            y: int = random.randint(0, self._size - 1)

            # if this is an existing mine tile do not count down mine count
            if self._grid[x][y].is_mine():
                continue

            # if this tile is the initial position do not place a mine
            if init_x - 1 <= x <= init_x + 1 and init_y - 1 <= y <= init_y + 1:
                continue

            self._grid[x][y].set_value(tile.MINE)
            mines -= 1

    # update what number a given tile should display
    def _update_tile_value(self, x: int, y: int):
        if x < 0 or y < 0 or x >= self._size or y >= self._size:
            raise TilePositionError("Access to Tile out of range", self._size, (x, y))

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

    # reveals all blanks starting from this tile
    # also reveals tiles surrounding blanks
    def _reveal_adjacent_blanks(self, x: int, y: int):
        blanks: [(int, int)] = []
        if self._grid[x][y].is_blank():
            blanks.append((x, y))

        while len(blanks) > 0:
            x_pos: int
            y_pos: int
            x_pos, y_pos = blanks.pop()

            # if this was a flag reduce the flag count
            if self._grid[x_pos][y_pos].state is tile.State.flag:
                self._flags -= 1

            # set this blank to visible
            self._grid[x_pos][y_pos].state = tile.State.visible

            for i in range(x_pos - 1, x_pos + 2):
                for j in range(y_pos - 1, y_pos + 2):
                    if 0 <= i < self._size and 0 <= j < self._size:
                        if self._grid[i][j].is_blank() and self._grid[i][j].state is not tile.State.visible:
                            # add all non-visible blanks to the list
                            blanks.append((i, j))
                        else:
                            # if this was a flag reduce the flag count
                            if self._grid[i][j].state is tile.State.flag:
                                self._flags -= 1

                            # make all non-blank adjacent tiles visible
                            self._grid[i][j].state = tile.State.visible

    # checks if the game was won
    def _check_win(self) -> bool:
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
        for y in range(len(self._grid[0])):
            for x in range(len(self._grid)):
                print(str(self._grid[x][y]) + ' ', end='')
            print()


if __name__ == "__main__":
    g = Game()

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
        except SizeError:
            print("Please enter a grid between 10 and 100 tiles wide")

    mines: int
    while True:
        try:
            mines = int(input("Enter the number of mines on the grid: "))
            break
        except ValueError:
            print("Please enter an integer")

    g.set_mines(mines)

    print("Please use 'L' or 'R' for left or right click followed by coordinates to interact\nEx: L 0 0")
    g.begin()

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

                if values[0].capitalize() != 'L' and values[0].capitalize() != 'R':
                    print("Please enter L or R for 'left' or 'right' click")
                    print(values[0].capitalize() + '|')
                    continue

                left = values[0].capitalize() == 'L'
                x = int(values[1])
                y = int(values[2])

                if left:
                    g.left_mouse_button(x, y)
                else:
                    g.right_mouse_button(x, y)

                break
            except ValueError:
                print("Please enter valid integers in your expression")
            except TilePositionError as err:
                print(err)
                print("Please enter a valid expression")

    # final print of the grid
    g.reveal_mines()
    g.print()
