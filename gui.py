# Created on 19 Apr 2020
# Created by: Matthew Lourenco
# This file defines class and methods used to control the mines GUI

import pygame
import game
import solver


class Gui:
    CANVAS_SIZE = 900
    COMMANDS_BAR_SIZE = 200
    PADDING = 10

    # colours
    BLACK = (0, 0, 0)
    LIGHT_GRAY = (230, 230, 230)
    GRAY_BLUE = (186, 216, 219)

    def __init__(self):
        # size of the grid
        self.size = 15

        # number of mines on the grid
        self.mines = 35

        # game clock
        self.clock = pygame.time.Clock()

        # screen
        self.screen = pygame.display.set_mode((Gui.CANVAS_SIZE + Gui.COMMANDS_BAR_SIZE + 2 * Gui.PADDING,
                                               Gui.CANVAS_SIZE + 2 * Gui.PADDING))

        # Initialize the mines game
        self.game = game.Game()
        self.game.set_size(self.size)
        self.game.set_mines(self.mines)

        # Initialize pygame
        pygame.init()

        pygame.display.set_caption("'Mines' made by mattlourenco27 on Github")
        # Icon made by Creaticca Creative Agency from www.flaticon.com
        icon = pygame.image.load("./assets/sprites/icon.png")
        pygame.display.set_icon(icon)

    # Start the gui
    def start(self):
        # start the game
        self.game.begin()

        # start the game loop
        self._game_loop()

    # draw the canvas where the game of mines will show
    def _draw_base_canvas(self):
        background = pygame.Rect(Gui.PADDING, Gui.PADDING, Gui.CANVAS_SIZE, Gui.CANVAS_SIZE)
        pygame.draw.rect(self.screen, Gui.GRAY_BLUE, background)

        # Draw the row dividers
        channel_width: float = Gui.CANVAS_SIZE / self.size
        line_width: int = 3
        for row_divider in range(0, self.size + 1):
            pygame.draw.line(self.screen, Gui.BLACK,
                             (Gui.PADDING, Gui.PADDING + int(row_divider * channel_width)),
                             (Gui.PADDING + Gui.CANVAS_SIZE, Gui.PADDING + int(row_divider * channel_width)),
                             line_width)

        # Draw the column dividers
        for col_divider in range(0, self.size + 1):
            pygame.draw.line(self.screen, Gui.BLACK,
                             (Gui.PADDING + int(col_divider * channel_width), Gui.PADDING),
                             (Gui.PADDING + int(col_divider * channel_width), Gui.PADDING + Gui.CANVAS_SIZE),
                             line_width)

    # draw the minefield that the game is played on
    def _draw_minefield(self):
        pass

    # draw the command bar with buttons to click
    def _draw_command_bar(self):
        pass

    # draws the mines game and the command bar
    def _draw_screen(self):
        self.screen.fill(Gui.LIGHT_GRAY)

        self._draw_base_canvas()
        self._draw_minefield()
        self._draw_command_bar()
        pygame.display.update()

    # game loop that controls the buttons, game, and solver as well as drawing the screen
    def _game_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Exit the game
                    pygame.quit()
                    quit()

            self._draw_screen()
            self.clock.tick(60)
