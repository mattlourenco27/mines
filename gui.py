# Created on 19 Apr 2020
# Created by: Matthew Lourenco
# This file defines class and methods used to control the mines GUI

import pygame
import game
import solver

class Gui:
    CANVAS_SIZE = 800
    COMMANDS_BAR_SIZE = 100

    # colours
    GRAY_BLUE = (186, 216, 219)

    def __init__(self):
        # game clock
        self.clock: pygame.time.Clock

        # screen
        self.screen: pygame.display.Surface

        # Initialize the game
        pygame.init()

        pygame.display.set_caption("'Mines' made by mattlourenco27 on Github")
        # Icon made by Creaticca Creative Agency from www.flaticon.com
        icon = pygame.image.load("./assets/sprites/icon.png")
        pygame.display.set_icon(icon)

    # Start the gui
    def start(self):
        # Create the game clock
        self.clock = pygame.time.Clock()

        # Create the screen
        self.screen = pygame.display.set_mode((Gui.CANVAS_SIZE, Gui.CANVAS_SIZE + Gui.COMMANDS_BAR_SIZE))

        # start the game loop
        self._game_loop()

    def _draw_base_canvas(self):
        self.screen.fill(Gui.GRAY_BLUE)

    def _draw_screen(self):
        self._draw_base_canvas()
        pygame.display.update()

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