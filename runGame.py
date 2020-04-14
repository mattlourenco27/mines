# Created on 10 Mar 2020
# Created by: Matthew Lourenco
# This file plays the mines game

import random
import tile

SIZE = 20
MINES = 40


# This class controls the mines game
class Game:
    def __init__(self):
        # grid that will be used to store the game board
        self._grid = []
        for i in range(SIZE):
            self._grid.append([])
            for j in range(SIZE):
                self._grid[i].append(tile.Tile())

    # clear the grid
    def _clear(self):
        for col in self._grid:
            for element in col:
                element.character = '_'
                element.state = tile.State.covered
                element.is_mine = False

    # Clear the grid and populate it with mines
    def _populate(self):
        self._clear()

        mines = MINES

        random.seed()

        while mines > 0:
            x = random.randint(0, SIZE - 1)
            y = random.randint(0, SIZE - 1)

            if self._grid[x][y].is_mine:
                continue

            self._grid[x][y].is_mine = True
            self._grid[x][y].character = '*'
            mines -= 1

    # update what number a given tile should display
    def _update_tile_value(self, x, y):
        if x < 0 or y < 0 or x >= SIZE or y >= SIZE:
            print("Access to grid out of range [" + str(x) + "][" + str(y) + "]")

        if self._grid[x][y].is_mine:
            return

        count = 0

        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                if (i >= 0 and i < SIZE and j >= 0 and j < SIZE and self._grid[i][j].is_mine):
                    count += 1

        if count == 0:
            self._grid[x][y].character = ' '
        elif count == 1:
            self._grid[x][y].character = '1'
        elif count == 2:
            self._grid[x][y].character = '2'
        elif count == 3:
            self._grid[x][y].character = '3'
        elif count == 4:
            self._grid[x][y].character = '4'
        elif count == 5:
            self._grid[x][y].character = '5'
        elif count == 6:
            self._grid[x][y].character = '6'
        elif count == 7:
            self._grid[x][y].character = '7'
        elif count == 8:
            self._grid[x][y].character = '8'

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
        self._populate()

        for x in range(SIZE):
            for y in range(SIZE):
                self._update_tile_value(x, y)

    def print(self):
        for col in self._grid:
            for element in col:
                char = 'A'

                if element.state == tile.State.covered:
                    char = '-'
                elif element.state == tile.State.visible:
                    char = element.character
                elif element.state == tile.State.flag:
                    char = 'F'
                elif element.state == tile.State.unknown:
                    char = '?'

                print(char, end='')
            print()


if __name__ == "__main__":
    g = Game()
    g.run()
    g.print()
