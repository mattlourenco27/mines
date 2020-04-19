# Created on 10 Mar 2020
# Created by: Matthew Lourenco
# This file is a class for a tile in the mines game

from enum import Enum

BLANK = '\u25A1'
COVERED = '\u25A8'
FLAG = '\u2690'
UNKNOWN = '?'
MINE = '*'

class State(Enum):
    covered = 0
    flag = 1
    unknown = 2
    visible = 3


class Tile:

    def __init__(self):
        self.value = 0
        self.state = State.covered
        self.is_mine = False

    def __str__(self):
        if self.state == State.covered:
            return COVERED
        elif self.state == State.visible:
            if self.is_mine:
                return MINE
            if self.value == 0:
                return BLANK
            if self.value < 9 and self.value > 0:
                return str(self.value)
            else:
                raise Exception("Tile value is not valid")
        elif self.state == State.flag:
            return FLAG
        elif self.state == State.unknown:
            return UNKNOWN
