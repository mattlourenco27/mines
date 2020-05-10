# Created on 19 Apr 2020
# Created by: Matthew Lourenco
# This file defines class and methods used to control the mines GUI

import pygame
import tile
import game
import solver


class Gui:
    CANVAS_SIZE = 900
    COMMANDS_BAR_SIZE = 200
    PADDING = 10

    # colours
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    LIGHT_GRAY = (240, 240, 240)
    MID_LIGHT_GRAY = (220, 220, 220)
    MID_GRAY = (190, 190, 190)
    GRAY_BLUE = (216, 227, 232)
    NAVY_BLUE = (21, 118, 171)

    # characters for minefield
    BLANK = ' ' # '\u25A1'
    COVERED = '\u25A8'
    FLAG = '\u2690'
    UNKNOWN = '?'
    MINE = '\u2737'

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

        colour = Gui.NAVY_BLUE

        # Draw the row dividers
        channel_width: float = Gui.CANVAS_SIZE / self.size
        line_width: int = 1
        for row_divider in range(0, self.size + 1):
            pygame.draw.line(self.screen, colour,
                             (Gui.PADDING, Gui.PADDING + int(row_divider * channel_width)),
                             (Gui.PADDING + Gui.CANVAS_SIZE, Gui.PADDING + int(row_divider * channel_width)),
                             line_width)

        # Draw the column dividers
        for col_divider in range(0, self.size + 1):
            pygame.draw.line(self.screen, colour,
                             (Gui.PADDING + int(col_divider * channel_width), Gui.PADDING),
                             (Gui.PADDING + int(col_divider * channel_width), Gui.PADDING + Gui.CANVAS_SIZE),
                             line_width)

    # draw the minefield that the game is played on
    def _draw_minefield(self, mouse_pos):
        channel_width = Gui.CANVAS_SIZE / self.size
        text = pygame.font.Font("assets/fonts/FreeSerif.ttf", int(channel_width))

        mouse_x = int((mouse_pos[0] - Gui.PADDING) / channel_width)
        mouse_y = int((mouse_pos[1] - Gui.PADDING) / channel_width)

        for x in range(self.size):
            for y in range(self.size):
                # get the state of the tile and determine the character to print
                tile_state = self.game.get_tile_state(x, y)
                if tile_state is tile.State.covered:
                    character = Gui.COVERED
                elif tile_state is tile.State.visible:
                    character = self.game.get_tile_value(x, y)
                elif tile_state is tile.State.flag:
                    character = Gui.FLAG
                elif tile_state is tile.State.unknown:
                    character = Gui.UNKNOWN

                if x == mouse_x and y == mouse_y:
                    colour = Gui.MID_GRAY
                else:
                    colour = Gui.BLACK

                text_surface = text.render(character, True, colour)
                text_rect = text_surface.get_rect()
                text_rect.center = (Gui.PADDING + int((x + 0.5) * channel_width),
                                    Gui.PADDING + int((y + 0.5) * channel_width))
                self.screen.blit(text_surface, text_rect)

    # draw the command bar with buttons to click
    def _draw_command_bar(self, mouse_pos):
        x_off = Gui.CANVAS_SIZE + 2 * Gui.PADDING  # X offset to the command bar
        y_off = Gui.PADDING # Y offset to the command bar

        # Set up text
        text = pygame.font.Font(None, 28)

        # Solve board button
        rect = pygame.Rect(x_off + 25, y_off + 25, 150, 50)
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, Gui.MID_LIGHT_GRAY, rect)
        else:
            pygame.draw.rect(self.screen, Gui.WHITE, rect)
        pygame.draw.rect(self.screen, Gui.BLACK, rect, 5)
        text_surface = text.render("Auto-Solve", True, Gui.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.center = rect.center
        self.screen.blit(text_surface, text_rect)

        # Step-solve button
        rect = rect.move(0, 75)

    # draws the mines game and the command bar
    def _draw_screen(self, mouse_pos):
        self.screen.fill(Gui.LIGHT_GRAY)

        self._draw_base_canvas()
        self._draw_minefield(mouse_pos)
        self._draw_command_bar(mouse_pos)
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

            mouse_pos = pygame.mouse.get_pos()
            self._draw_screen(mouse_pos)
            self.clock.tick(60)
