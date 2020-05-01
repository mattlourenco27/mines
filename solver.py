# Created on 19 Apr 2020
# Created by: Matthew Lourenco
# This file solves the mines game using logic and probability when given a game object

import collections
from copy import deepcopy
import game
import tile


class GameObjectError(game.Error):
    """Exception raised when the object passed is not the same as the one used to initialize the solver

        Attributes:
            - message
        """

    def __init__(self, message):
        self.message = message


class _AwareTile(tile.Tile):
    def __init__(self, x: int, y: int, size: int):
        super().__init__()

        # stores the number of flags that surround the tile
        self.flags: int = 0

        # stores the adjacent tile coordinates
        self.adjacent: [(int, int)] = []

        # stores the adjacent covered tiles
        self.covered: [(int, int)] = []

        # true if this tile has been visited in a scan. volatile
        self.visited = False

        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if 0 <= i < size and 0 <= j < size and not (i == x and j == y):
                    self.adjacent.append((i, j))
                    self.covered.append((i, j))

    def is_satisfied(self):
        return len(self.covered) == 0 and self.state is tile.State.visible


class _Block:
    # counter that ensures that block ids are never the same
    num_ids = 0

    def __init__(self, mines: int, tiles: [(int, int)] = []):
        # maximum number of mines in this block of tiles
        self.max_mines = mines

        # minimum number of mines in this block of tiles
        self.min_mines = mines

        # list of tile positions
        self.tiles = tiles

        # id of this instance of a block
        self.id = _Block.num_ids

        _Block.num_ids += 1


def _consistent_game_check(func):
    def function_wrapper(self, g: game.Game, *args, **kwargs):
        if id(g) != self._gameID:
            raise GameObjectError("The entered game object is not the same as the original")

        return func(self, g, *args, **kwargs)

    return function_wrapper


# given the number of true items in a list and the length of the list,
# this function generates every possible arrangement of true and false items
def _permute(items: int, length: int) -> [[bool]]:
    # template for possible solutions
    solutions = collections.deque([[]])
    for _ in range(length):
        solutions[0].append(False)

    num_templates: int = 1

    # add a new true element once in each loop
    for next_true_element in range(items):
        # generate more template solutions with one more true element
        for solution in range(num_templates):
            temp = solutions.popleft()

            # find the last true element in this temp list
            final_true: int = -1
            for i in range(length - 1, -1, -1): # scan the list in reverse
                if temp[i]:
                    final_true = i
                    break

            for position in range(final_true + 1, length):
                temp[position] = True
                solutions.append(deepcopy(temp))
                temp[position] = False

        # update the number of templates to iterate over next loop
        num_templates = len(solutions)

    return solutions


class Solver:
    def __init__(self, g: game.Game):
        # begin the game if it was not already begun
        g.begin()

        # identifier to check if the same game object is used
        self._gameID = id(g)

        # grid to store known tile values
        self._grid: [[_AwareTile]] = []

        # list of tiles that were visited and need to be returned to normal
        self._visited_tiles: [(int, int)] = []

        # size of the board
        self._size = g.get_size()

        for x in range(self._size):
            self._grid.append([])
            for y in range(self._size):
                self._grid[x].append(_AwareTile(x, y, self._size))

        # initialize grid tile parameters
        self._update_grid(g)

    # update the local state of the tile at the specified position
    @_consistent_game_check
    def _update_tile(self, g: game.Game, x: int, y: int):
        if g.get_tile_state(x, y) is tile.State.covered:
            self._grid[x][y].state = tile.State.covered
        elif g.get_tile_state(x, y) is tile.State.flag:
            self._grid[x][y].state = tile.State.flag

            # remove this tile from adjacent covered lists
            for element in self._grid[x][y].adjacent:
                i, j = element

                try:
                    self._grid[i][j].covered.remove((x, y))
                except ValueError:
                    pass
        elif g.get_tile_state(x, y) is tile.State.visible:
            self._grid[x][y].state = tile.State.visible
            self._grid[x][y].set_value(g.get_tile_value(x, y))

            self._grid[x][y].flags = 0
            # remove this tile from adjacent covered lists
            for element in self._grid[x][y].adjacent:
                i, j = element

                if self._grid[i][j].state is tile.State.flag:
                    self._grid[x][y].flags += 1

                try:
                    self._grid[i][j].covered.remove((x, y))
                except ValueError:
                    pass
        elif g.get_tile_state(x, y) is tile.State.unknown:
            g.right_mouse_button(x, y)
            self._grid[x][y].state = tile.State.covered

    # update all of the local tiles
    @_consistent_game_check
    def _update_grid(self, g: game.Game):
        for x in range(self._size):
            for y in range(self._size):
                self._update_tile(g, x, y)

    # do a single logical placement of a flag or uncovering a valid covered tile
    # the search starts from the hint starting position
    # returns true if it was successful
    @_consistent_game_check
    def _do_logic_placement(self, g: game.Game, hint: (int, int)) -> bool:

        self._reset_visited()
        wavefront = collections.deque([hint])

        while len(wavefront) > 0:
            x, y = wavefront.popleft()

            if self._grid[x][y].state is tile.State.visible and not self._grid[x][y].is_satisfied():

                # scan the surrounding tiles
                flags = 0

                for element in self._grid[x][y].adjacent:
                    i, j = element
                    if self._grid[i][j].state is tile.State.flag:
                        flags += 1

                # first check if there are enough flags to satisfy the tile value
                if flags == self._grid[x][y].get_value() and len(self._grid[x][y].covered) > 0:
                    i, j = self._grid[x][y].covered[0]
                    g.left_mouse_button(i, j)
                    self._update_tile(g, i, j)

                    # if a blank was hit update the whole board
                    if self._grid[i][j].is_blank():
                        self._update_grid(g)

                    return True

                # next check if the number of covered spaces + number of flags is equal to the tile value
                elif flags + len(self._grid[x][y].covered) == self._grid[x][y].get_value():
                    i, j = self._grid[x][y].covered[0]
                    g.right_mouse_button(i, j)
                    self._update_tile(g, i, j)

                    return True

            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if 0 <= i < self._size and 0 <= j < self._size:
                        if not self._grid[i][j].visited:
                            wavefront.append((i, j))
                            self._visited_tiles.append((i, j))
                            self._grid[i][j].visited = True

        return False

    # reset the visited tiles list
    def _reset_visited(self):
        for element in self._visited_tiles:
            x, y = element
            self._grid[x][y].visited = False

        self._visited_tiles.clear()

    # do a logical scan of all the tiles on the local grid with a hint starting position
    # updates the local board first if update is true. flags or reveals valid tiles
    # returns true if it made a change to the grid tiles
    @_consistent_game_check
    def _do_logic_wave(self, g: game.Game, update: bool, hint: (int, int)) -> bool:
        if update:
            self._update_grid(g)

        self._reset_visited()
        wavefront = collections.deque([hint])
        self._grid[hint[0]][hint[1]].visited = True

        did_action = False

        while len(wavefront) > 0:
            x, y = wavefront.popleft()

            if self._grid[x][y].state is tile.State.visible and not self._grid[x][y].is_satisfied():

                # scan the surrounding tiles
                flags = 0

                for element in self._grid[x][y].adjacent:
                    i, j = element
                    if self._grid[i][j].state is tile.State.flag:
                        flags += 1

                # first check if there are enough flags to satisfy the tile value
                if flags == self._grid[x][y].get_value() and len(self._grid[x][y].covered) > 0:
                    did_action = True
                    for element in self._grid[x][y].covered:
                        i, j = element
                        g.left_mouse_button(i, j)

                    for element in self._grid[x][y].adjacent:
                        i, j = element
                        self._update_tile(g, i, j)

                        # if a blank was hit update the whole board
                        if self._grid[i][j].is_blank():
                            self._update_grid(g)
                            break

                    #self.print()

                # next check if the number of covered spaces + number of flags is equal to the tile value
                elif flags + len(self._grid[x][y].covered) == self._grid[x][y].get_value():
                    did_action = True
                    for element in self._grid[x][y].covered:
                        i, j = element
                        g.right_mouse_button(i, j)

                    for element in self._grid[x][y].adjacent:
                        i, j = element
                        self._update_tile(g, i, j)

                    #self.print()

            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if 0 <= i < self._size and 0 <= j < self._size:
                        if not self._grid[i][j].visited:
                            wavefront.append((i, j))
                            self._visited_tiles.append((i, j))
                            self._grid[i][j].visited = True

        return did_action

    # do a logical scan of all the tiles on the local grid
    # updates the local board first if update is true. flags or reveals valid tiles
    # returns true if it made a change to the grid tiles
    @_consistent_game_check
    def _do_logic_scan(self, g: game.Game, update: bool) -> bool:
        if update:
            self._update_grid(g)

        did_action = False

        for x in range(self._size):
            for y in range(self._size):
                if self._grid[x][y].state is tile.State.visible and not self._grid[x][y].is_satisfied():

                    # scan the surrounding tiles
                    flags = 0

                    for element in self._grid[x][y].adjacent:
                        i, j = element
                        if self._grid[i][j].state is tile.State.flag:
                            flags += 1

                    # first check if there are enough flags to satisfy the tile value
                    if flags == self._grid[x][y].get_value() and len(self._grid[x][y].covered) > 0:
                        did_action = True
                        for element in self._grid[x][y].covered:
                            i, j = element
                            g.left_mouse_button(i, j)
                            self._update_tile(g, i, j)

                            # if a blank was hit update the whole board
                            if self._grid[i][j].is_blank():
                                self._update_grid(g)

                    # next check if the number of covered spaces + number of flags is equal to the tile value
                    elif flags + len(self._grid[x][y].covered) == self._grid[x][y].get_value():
                        did_action = True
                        for element in self._grid[x][y].covered:
                            i, j = element
                            g.right_mouse_button(i, j)
                            self._update_tile(g, i, j)

        return did_action

    # do a single placement of a flag or reveal of a covered tile using probability
    # takes a hint of where to start the search
    # returns true if it was able to make a change to the board
    @_consistent_game_check
    def _do_prob_placement(self, g: game.Game, hint: (int, int)) -> bool:
        self._reset_visited()
        wavefront = collections.deque([hint])

        while len(wavefront) > 0:
            x, y = wavefront.popleft()

            if self._grid[x][y].state is tile.State.visible and not self._grid[x][y].is_satisfied():
                pass

            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if 0 <= i < self._size and 0 <= j < self._size:
                        if not self._grid[i][j].visited:
                            wavefront.append((i, j))
                            self._visited_tiles.append((i, j))
                            self._grid[i][j].visited = True

        return False

    # returns true if the tile has a valid number of flags around it
    def _valid_tile(self, x: int, y: int) -> bool:
        value = self._grid[x][y].get_value()

        for item in self._grid[x][y].adjacent:
            i, j = item
            if self._grid[i][j].state is tile.State.flag:
                value -= 1

        return value == 0

    # returns true if all visible tiles are valid and all flags are placed
    @_consistent_game_check
    def _valid_grid(self, g: game.Game) -> bool:
        flags: int = 0

        for x in range(self._size):
            for y in range(self._size):
                if self._grid[x][y].state is tile.State.flag:
                    flags += 1
                elif self._grid[x][y].state is tile.State.visible and not self._valid_tile(x, y):
                    return False

        return flags == g.get_mines()

    def print(self):
        print('  ', end='')
        for i in range(self._size):
            print(str(i) + ' ', end='')
        print()

        count = 0
        for y in range(len(self._grid[0])):
            print(str(count) + ' ', end='')
            count += 1
            for x in range(len(self._grid)):
                print(str(self._grid[x][y]) + ' ', end='')
            print()
        print()


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

    # true if the last move was made by a user
    last_move_user = False

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
                    solver._do_logic_wave(g, last_move_user, (int(size / 2), int(size / 2)))
                    last_move_user = False
                    break

                if values[0].upper() != 'L' and values[0].upper() != 'R':
                    print("Please enter L or R for 'left' or 'right' click")
                    continue

                left = values[0].upper() == 'L'
                x = int(values[1])
                y = int(values[2])

                last_move_user = True

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
