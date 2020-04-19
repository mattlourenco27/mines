# Created on 10 Mar 2020
# Created by: Matthew Lourenco
# This file is a class for a tile in the mines game

from enum import Enum

BLANK = 0
_BLANK_CHAR = '\u25A1'
_COVERED = '\u25A8'
_FLAG = '\u2690'
_UNKNOWN = '?'
_MINE_CHAR = '*'
MINE = -1


class State(Enum):
    covered = 0
    flag = 1
    unknown = 2
    visible = 3


class Tile:

    def __init__(self):
        self._value = BLANK
        self.state = State.covered

    def is_blank(self):
        return self._value == BLANK

    def is_mine(self):
        return self._value == MINE

    def set_value(self, v):
        self._value = v

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
