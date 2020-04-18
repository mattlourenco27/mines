# Created on 10 Mar 2020
# Created by: Matthew Lourenco
# This file is a class for a tile in the mines game

from enum import Enum

BLANK = '\u25A1'
COVERED = '\u25A8'
FLAG = '\u2690'
UNKNOWN = '?'

class State(Enum):
    covered = 0
    flag = 1
    unknown = 2
    visible = 3


class Tile:

    def __init__(self):
        self.character = '_'
        self.state = State.covered
        self.is_mine = False
