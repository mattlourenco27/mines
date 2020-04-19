# Created on 10 Mar 2020
# Created by: Matthew Lourenco
# This file is a class for a tile in the mines game

"""
Defines Tile class and constants that are used to simulate a tile in a mines game

Constants:
    * tile.BLANK = 0
    * tile.MINE = -1

Public objects:
    * Enum tile.State
    * Class tile.Tile
"""

from enum import Enum, auto

BLANK = 0
_BLANK_CHAR = '\u25A1'
_COVERED = '\u25A8'
_FLAG = '\u2690'
_UNKNOWN = '?'
_MINE_CHAR = '\u2737'
MINE = -1


class State(Enum):
    """
This enum describes the state of the tile

Constants:
 * covered
 * flag
 * unknown
 * visible
    """
    covered = auto()
    flag = auto()
    unknown = auto()
    visible = auto()


class Tile:
    """
defines a Tile in a game of mines

self.is_blank(self) -> bool:     returns true if this tile has no number or mine
self.is_mine(self) -> bool:      returns true if this tile is a mine
self.get_value(self) -> int:     returns the value of the tile (1-8), (-1 for mine), (0 for blank)
self.set_value(self, v: int):    sets the value of the tile. Raises Exception if the tile value is not valid
    """

    def __init__(self):
        self._value = BLANK
        self.state = State.covered

    def is_blank(self) -> bool:
        return self._value == BLANK

    def is_mine(self) -> bool:
        return self._value == MINE

    def get_value(self) -> int:
        return self._value

    def set_value(self, v: int):
        if -1 <= v <= 8:
            self._value = v
        else:
            raise Exception("Value is not valid: v = " + str(v))

    def __str__(self):
        if self.state == State.covered:
            return _COVERED
        elif self.state == State.visible:
            if self.is_mine():
                return _MINE_CHAR
            if self._value == 0:
                return _BLANK_CHAR
            if 0 < self._value < 9:
                return str(self._value)
            else:
                raise Exception("Tile value is not valid")
        elif self.state == State.flag:
            return _FLAG
        elif self.state == State.unknown:
            return _UNKNOWN
