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


class BlockGenerationError(game.Error):
    """Exception raised when a given tile does not meet the requirements to generate a block

        Attributes:
            - message
            - tile position
        """

    def __init__(self, message, tile_position: (int, int)):
        self.message = message
        self.tile_position = tile_position

    def __str__(self):
        return self.message + ". Tile: " + str(self.tile_position)


class _AwareTile(tile.Tile):
    def __init__(self, x: int, y: int, size: int):
        super().__init__()

        # stores the number of flags that surround the tile
        self.flags: int = 0

        # stores the adjacent tile coordinates
        self.adjacent: [(int, int)] = []

        # stores the adjacent covered tiles
        self.covered: [(int, int)] = []

        # ids of all parent blocks
        self.parent_ids: [int] = []

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
    num_ids: int = 0

    def __init__(self, mines: int, tiles: [(int, int)] = []):
        # the exact number of mines in this block of tiles
        self.mines: int = mines

        # list of tile positions
        self.tiles: [(int, int)] = tiles

        # id of this instance of a block
        self.id: int = _Block.num_ids

        _Block.num_ids += 1


# wrapper that raises an exception if the game used in the solver is inconsistent
def _consistent_game_check(func):
    def function_wrapper(self, g: game.Game, *args, **kwargs):
        if id(g) != self._gameID:
            raise GameObjectError("The entered game object is not the same as the original")

        return func(self, g, *args, **kwargs)

    return function_wrapper


# given the number of true items in a list and the length of the list,
# this function generates every possible arrangement of true and false items
def _permute(items: int, length: int):
    # template for possible solutions
    solutions = collections.deque([[]])
    for _ in range(length):
        solutions[0].append(False)

    num_templates: int = 1

    # return full list of True
    if items >= length:
        for i in range(length):
            solutions[0][i] = True

        return solutions

    # add a new true element once in each loop
    for next_true_element in range(items):
        # generate more template solutions with one more true element
        for solution in range(num_templates):
            temp = solutions.popleft()

            # find the last true element in this temp list
            final_true: int = -1
            for i in range(length - 1, -1, -1):  # scan the list in reverse
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

                    # self.print()

                # next check if the number of covered spaces + number of flags is equal to the tile value
                elif flags + len(self._grid[x][y].covered) == self._grid[x][y].get_value():
                    did_action = True
                    for element in self._grid[x][y].covered:
                        i, j = element
                        g.right_mouse_button(i, j)

                    for element in self._grid[x][y].adjacent:
                        i, j = element
                        self._update_tile(g, i, j)

                    # self.print()

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
        self._update_grid(g)
        self._reset_visited()
        wavefront = collections.deque([hint])

        while len(wavefront) > 0:
            x, y = wavefront.popleft()

            if self._grid[x][y].state is tile.State.visible and not self._grid[x][y].is_satisfied():
                return self._prob_placement_helper(g, x, y)

            for i in range(x - 1, x + 2):
                for j in range(y - 1, y + 2):
                    if 0 <= i < self._size and 0 <= j < self._size:
                        if not self._grid[i][j].visited:
                            wavefront.append((i, j))
                            self._visited_tiles.append((i, j))
                            self._grid[i][j].visited = True

        return False

    # helper functions for the _do_prob_placement function
    # returns true upon success of placing a flag or uncovering a tile
    def _prob_placement_helper(self, g: game.Game, x: int, y: int) -> bool:
        # generate the main block of this analysis
        main_block: _Block = self._gen_block_at_tile((x, y))

        # find all adjacent non_satisfied, visible tiles
        adjacent_tiles: [(int, int)] = []
        for covered_tile in main_block.tiles:
            i, j = covered_tile
            for tile_element in self._grid[i][j].adjacent:
                m, n = tile_element

                if (m, n) != (x, y) and self._grid[m][n].state is tile.State.visible and not self._grid[m][
                    n].is_satisfied() and tile_element not in adjacent_tiles:
                    adjacent_tiles.append(tile_element)

        # generate a block for each of these tiles
        all_blocks: [_Block] = [main_block]
        max_mines: int = main_block.mines  # the maximum number of mines in these blocks
        for working_tile in adjacent_tiles:
            new_block: _Block = self._gen_block_at_tile(working_tile)
            all_blocks.append(new_block)
            max_mines += new_block.mines

        # count the number of tiles that are in blocks
        all_tiles: [(int, int)] = []
        for block in all_blocks:
            for _tile in block.tiles:
                if _tile not in all_tiles:
                    all_tiles.append(_tile)

        # the number of mines cannot be greater than the number of tiles in blocks
        max_mines = min(len(all_tiles), max_mines)

        # iterate to generate every possible placement of mines
        solutions = collections.deque([])

        while max_mines > 0:
            # start with max_mines and generate possible solutions, decreasing max_mines until it hits zero

            possibilities = collections.deque(_permute(max_mines, len(all_tiles)))

            # check every possibility
            for arrangement in possibilities:

                # place flags at true markers
                for item in range(len(arrangement)):
                    if arrangement[item]:
                        i, j = all_tiles[item]
                        self._grid[i][j].state = tile.State.flag

                # check for validity of adjacent tiles
                all_valid = True
                for item in range(len(adjacent_tiles)):
                    i, j = adjacent_tiles[item]
                    if not self._valid_tile(i, j):
                        all_valid = False
                        break

                if all_valid:
                    solutions.append(arrangement)

                # reset placed flags
                for item in range(len(arrangement)):
                    if arrangement[item]:
                        i, j = all_tiles[item]
                        self._grid[i][j].state = tile.State.covered

            max_mines -= 1

        # check solutions against the entire grid, saving the data from the valid ones
        data: [float] = []
        num_valid_soln: int = 0
        for _ in range(len(all_tiles)):
            # initialization of data list
            data.append(0)
        for arrangement in solutions:

            # place flags at true markers
            for item in range(len(arrangement)):
                if arrangement[item]:
                    i, j = all_tiles[item]
                    self._grid[i][j].state = tile.State.flag

            # check for validity of entire board
            valid = self._valid_grid(g)

            if valid:
                num_valid_soln += 1
                for item in range(len(all_tiles)):
                    if arrangement[item]:
                        data[item] += 1

            # reset placed flags
            for item in range(len(arrangement)):
                if arrangement[item]:
                    i, j = all_tiles[item]
                    self._grid[i][j].state = tile.State.covered

        if num_valid_soln == 0:
            self._clean_blocks(all_blocks)
            return False

        did_action: bool = False
        for item in range(len(data)):
            if data[item] == num_valid_soln:
                # flag tiles that are always mines
                did_action = True
                i, j = all_tiles[item]
                g.right_mouse_button(i, j)
            elif data[item] == 0:
                # click tiles that are never mines
                did_action = True
                i, j = all_tiles[item]
                g.left_mouse_button(i, j)

        self._clean_blocks(all_blocks)
        return did_action

    # generates a block at a given visible, non-satisfied tile
    def _gen_block_at_tile(self, tile_position: (int, int)) -> _Block:
        x, y = tile_position
        if self._grid[x][y].state is not tile.State.visible or self._grid[x][y].is_satisfied():
            raise BlockGenerationError("Given tile is not a valid candidate to generate a block", tile_position)

        # number of mines in this block
        mines: int = self._grid[x][y].get_value() - self._grid[x][y].flags

        new_block: _Block = _Block(mines, deepcopy(self._grid[x][y].covered))

        # update the child tiles
        for element in self._grid[x][y].covered:
            i, j = element
            self._grid[i][j].parent_ids.append(new_block.id)

        return new_block

    # cleans up all if the given blocks before deleting them
    def _clean_blocks(self, blocks: [_Block]):
        _Block.num_ids = 0

        for block in blocks:
            for item in block.tiles:
                x, y = item
                self._grid[x][y].parent_ids.clear()

    # returns true if the tile has a valid number of flags around it
    def _valid_tile(self, x: int, y: int) -> bool:
        value = self._grid[x][y].get_value()

        for item in self._grid[x][y].adjacent:
            i, j = item
            if self._grid[i][j].state is tile.State.flag:
                value -= 1

        return value == 0

    # returns true if all visible tiles are valid and less than the max flags are placed
    @_consistent_game_check
    def _valid_grid(self, g: game.Game) -> bool:
        flags: int = 0

        for x in range(self._size):
            for y in range(self._size):
                if self._grid[x][y].state is tile.State.flag:
                    flags += 1
                elif self._grid[x][y].state is tile.State.visible and not self._valid_tile(x, y):
                    return False

        return flags <= g.get_mines()

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
    g = game.Game(testing=True)

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

                if values[0].upper() == 'P' and values[1].upper() == 'R' and values[2].upper() == 'O':
                    solver._do_prob_placement(g, (2, 1))
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
