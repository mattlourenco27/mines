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

        # number of mines on the board
        self._mines = g.get_mines()

        # size of the board
        self._size = g.get_size()

        for x in range(self._size):
            self._grid.append([])
            for y in range(self._size):
                self._grid[x].append(_AwareTile(x, y, self._size))

        # initialize grid tile parameters
        self._update_grid(g)

    # solves one step of the the board
    # can place multiple flags or reveal multiple tiles in one call if they are obvious
    # will only edit tiles in a way that is guaranteed to be safe
    # returns true if it changed any of the grid tiles
    @_consistent_game_check
    def solve_next_step(self, g: game.Game):
        self._update_grid(g)

        logic_success: bool = self._do_logic_wave(g, False, (int(self._size * 0.5), int(self._size * 0.5)))
        prob_success: bool

        if not logic_success:
            prob_success = self._do_prob_wave(g)
        else:
            return True

        return prob_success

    # will use probability to make the best guess of where to click next
    # returns true if it was able to make a guess
    @_consistent_game_check
    def guess(self, g: game.Game) -> bool:
        data = self._do_prob_wave(g, return_data=True)

        if len(data[0]) == 0:
            # there is no data to work with
            return False

        # find the most likely to be a mine or the most likely to be safe and click it

        max_prob: float = 0 # %
        max_index: int = -1
        max_is_safe: bool = True
        for i in len(data[1]):
            if data[1][i] > max_prob:
                max_prob = data[1][i]
                max_index = i
                max_is_safe = False
            elif 100 - data[1][i] > max_prob:
                max_prob = 100 - data[1][i]
                max_index = i
                max_is_safe = True

        x, y = data[0][max_index]

        if max_is_safe:
            g.left_mouse_button(x, y)
        else:
            g.right_mouse_button(x, y)

        return True


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
    @_consistent_game_check
    def _prob_placement_helper(self, g: game.Game, x_root: int, y_root: int) -> bool:
        # generate the main block of this analysis
        main_block: _Block = self._gen_block_at_tile((x_root, y_root))

        # find all non_satisfied, visible tiles that interact with this block. these will the roots for blocks
        all_blocks: [_Block] = [main_block]
        for covered_tile in main_block.tiles:
            x, y = covered_tile
            for adjacent_tile in self._grid[x][y].adjacent:
                i, j = adjacent_tile

                if self._grid[i][j].state is tile.State.visible and not self._grid[i][j].is_satisfied():
                    all_blocks.append(self._gen_block_at_tile(adjacent_tile))

        # list of all tiles in these blocks
        # this list should not be modified after initialization
        all_tiles: [(int, int)] = []
        for block in all_blocks:
            for working_tile in block.tiles:
                if working_tile not in all_tiles:
                    all_tiles.append(working_tile)

        # iterate to generate every possible placement of mines
        solutions = collections.deque([])

        # define recursive function that permutes every combination of mines in the blocks
        def permute_blocks(index: int):
            nonlocal self
            nonlocal all_blocks
            nonlocal all_tiles
            nonlocal solutions

            current: _Block = all_blocks[index]

            # return if this block cannot be satisfied
            if current.mines < 0:
                return
            if current.mines > len(current.tiles):
                return

            possibilities = collections.deque(_permute(current.mines, len(current.tiles)))

            for arrangement in possibilities:
                # set flags
                for i in range(len(current.tiles)):
                    if arrangement[i]:
                        x, y = current.tiles[i]
                        self._grid[x][y].state = tile.State.flag

                # update blocks
                for i in range(len(current.tiles)):
                    x, y = current.tiles[i]
                    if arrangement[i]:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].mines -= 1
                                all_blocks[block_id].tiles.remove(current.tiles[i])
                    else:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].tiles.remove(current.tiles[i])

                # permute the next block if there is a next block
                if index < len(all_blocks) - 1:
                    permute_blocks(index + 1)
                else:
                    # scan all tiles and generate a solution
                    solution: bool = []
                    for item in all_tiles:
                        x, y = item
                        if self._grid[x][y].state is tile.State.flag:
                            solution.append(True)
                        else:
                            solution.append(False)
                    solutions.append(solution)

                # reset changed blocks
                for i in range(len(current.tiles)):
                    x, y = current.tiles[i]
                    if arrangement[i]:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].mines += 1
                                all_blocks[block_id].tiles.append(current.tiles[i])
                    else:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].tiles.append(current.tiles[i])

                # remove placed flags
                for i in range(len(current.tiles)):
                    if arrangement[i]:
                        x, y = current.tiles[i]
                        self._grid[x][y].state = tile.State.covered

        permute_blocks(0)

        # check solutions against the entire grid, saving the data from the valid ones
        # the data vector stores the number of solutions in which any given tile is a mine
        data: [int] = []
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

            # check that no tiles on the grid are over-burdened with flags
            valid = self._lt_valid_grid(g)

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

        # parse data to see which tiles are always mines or always safe
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
        if did_action:
            self._update_grid(g)
        return did_action

    # do a probability evaluation of all of the tiles on the grid to see which are guarenteed to be mines or safe
    # returns true if it made a change to the grid tiles
    # if return_data=True the function will instead return the data it generated
    @_consistent_game_check
    def _do_prob_wave(self, g: game.Game, return_data=False):
        # find all non_satisfied, visible tiles. these will the roots for blocks
        all_blocks: [_Block] = []

        # list of all tiles in these blocks
        # this list should not be modified after initialization
        all_tiles: [(int, int)] = []

        for x in range(self._size):
            for y in range(self._size):
                if self._grid[x][y].state is tile.State.visible and not self._grid[x][y].is_satisfied():
                    all_blocks.append(self._gen_block_at_tile((x, y)))
                elif self._grid[x][y].state is tile.State.covered:
                    # add this covered tile to all_tiles if there are viable tiles beside it
                    for adjacent_tile in self._grid[x][y].adjacent:
                        i, j = adjacent_tile
                        if self._grid[i][j].state is tile.State.visible and not self._grid[i][j].is_satisfied():
                            all_tiles.append((x, y))
                            break

        # return if there are no blocks that can be generated
        if len(all_blocks) == 0:
            if return_data:
                return [[], []]
            return False

        # total flags on the grid during permutation
        total_flags: int = g.get_flags()

        # iterate to generate every possible placement of mines
        solutions = collections.deque([])

        # define recursive function that permutes every combination of mines in the blocks
        def permute_blocks(index: int):
            nonlocal self
            nonlocal all_blocks
            nonlocal all_tiles
            nonlocal total_flags
            nonlocal solutions

            current: _Block = all_blocks[index]

            # return if this block cannot be satisfied
            if current.mines < 0:
                return
            if current.mines > len(current.tiles):
                return

            possibilities = collections.deque(_permute(current.mines, len(current.tiles)))

            for arrangement in possibilities:
                # set flags
                for i in range(len(current.tiles)):
                    if arrangement[i]:
                        x, y = current.tiles[i]
                        self._grid[x][y].state = tile.State.flag
                        total_flags += 1

                # update blocks
                for i in range(len(current.tiles)):
                    x, y = current.tiles[i]
                    if arrangement[i]:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].mines -= 1
                                all_blocks[block_id].tiles.remove(current.tiles[i])
                    else:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].tiles.remove(current.tiles[i])

                # permute the next block if there is a next block and there are enough flags left
                if index < len(all_blocks) - 1 and total_flags <= self._mines:
                    permute_blocks(index + 1)
                elif total_flags <= self._mines:
                    # scan all tiles and generate a solution
                    solution: bool = []
                    for item in all_tiles:
                        x, y = item
                        if self._grid[x][y].state is tile.State.flag:
                            solution.append(True)
                        else:
                            solution.append(False)
                    solutions.append(solution)

                # reset changed blocks
                for i in range(len(current.tiles)):
                    x, y = current.tiles[i]
                    if arrangement[i]:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].mines += 1
                                all_blocks[block_id].tiles.append(current.tiles[i])
                    else:
                        for block_id in self._grid[x][y].parent_ids:
                            if block_id != current.id:
                                all_blocks[block_id].tiles.append(current.tiles[i])

                # remove placed flags
                for i in range(len(current.tiles)):
                    if arrangement[i]:
                        x, y = current.tiles[i]
                        self._grid[x][y].state = tile.State.covered
                        total_flags -= 1

        permute_blocks(0)

        # done with blocks
        self._clean_blocks(all_blocks)

        num_valid_soln: int = len(solutions)
        if num_valid_soln == 0:
            return False

        # the data vector stores the number of solutions in which any given tile is a mine
        data: [int] = []
        for _ in range(len(all_tiles)):
            # initialization of data list
            data.append(0)

        for arrangement in solutions:
            for item in range(len(all_tiles)):
                if arrangement[item]:
                    data[item] += 1

        if return_data:
            # convert data to percent probability
            result_data = [all_tiles]
            percentages: [float] = []
            for item in range(len(data)):
                percentages.append(data[item] / num_valid_soln * 100)

            result_data.append(percentages)
            return result_data

        # parse data to see which tiles are always mines or always safe
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

        if did_action:
            self._update_grid(g)
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

    # returns true if all visible tiles are valid and the max flags are placed exactly
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

    # returns true if no tiles are invalid
    def _lt_valid_grid(self, g: game.Game) -> bool:
        flags: int = 0

        for x in range(self._size):
            for y in range(self._size):
                if self._grid[x][y].state is tile.State.flag:
                    flags += 1
                elif self._grid[x][y].state is tile.State.visible:
                    value = self._grid[x][y].get_value()

                    for item in self._grid[x][y].adjacent:
                        i, j = item
                        if self._grid[i][j].state is tile.State.flag:
                            value -= 1

                    if value < 0:
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
    print("Type 'solve one step' to have the solver analyze the board and place what it can")

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
                    success = solver.solve_next_step(g)
                    if not success:
                        print("Unsuccessful")
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
