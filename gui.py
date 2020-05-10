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
    RED = (194, 59, 56)
    GREEN = (60, 199, 85)

    # characters for minefield
    BLANK = ' ' # '\u25A1'
    COVERED = '\u25A8'
    FLAG = '\u2690'
    UNKNOWN = '?'
    MINE = '\u2737'

    def __init__(self):
        # size of the grid
        self.size = 16

        # number of mines on the grid
        self.mines = 40

        # game clock
        self.clock = pygame.time.Clock()

        # screen
        self.screen = pygame.display.set_mode((Gui.CANVAS_SIZE + Gui.COMMANDS_BAR_SIZE + 2 * Gui.PADDING,
                                               Gui.CANVAS_SIZE + 2 * Gui.PADDING))

        # Initialize the mines game
        self.game = game.Game()
        self.game.set_size(self.size)
        self.game.set_mines(self.mines)

        # the last mine tile where the left mouse was down
        self.last_left_down = (-1, -1)

        # the last mine tile where the right mouse was down
        self.last_right_down = (-1, -1)

        # tile that was pressed when the game was lost
        self.failed_tile = (-1, -1)

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

    # restart the game and change the size and mines
    def restart(self, size, mines):
        self.game.reset()
        self.game.set_size(size)
        self.size = size
        self.game.set_mines(mines)
        self.mines = mines
        self.failed_tile = (-1, -1)
        self.game.begin()

    # draw the canvas where the game of mines will show
    def _draw_base_canvas(self):
        background = pygame.Rect(Gui.PADDING, Gui.PADDING, Gui.CANVAS_SIZE, Gui.CANVAS_SIZE)
        pygame.draw.rect(self.screen, Gui.WHITE, background)

        colour = Gui.BLACK

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
        text = pygame.font.Font("assets/fonts/FreeSerif.ttf", int(channel_width * 0.6))

        mouse_x = (mouse_pos[0] - Gui.PADDING)
        mouse_y = (mouse_pos[1] - Gui.PADDING)

        if mouse_x < 0:
            mouse_x = -1
        else:
            mouse_x = int(mouse_x / channel_width)

        if mouse_y < 0:
            mouse_y = -1
        else:
            mouse_y = int(mouse_y / channel_width)

        for x in range(self.size):
            for y in range(self.size):
                tile_state = self.game.get_tile_state(x, y)

                # determine the colour fo the tile
                if x == mouse_x and y == mouse_y and tile_state is not tile.State.visible and not self.game.game_done():
                    colour = Gui.MID_GRAY
                elif (x, y) == self.failed_tile:
                    colour = Gui.RED
                else:
                    colour = Gui.BLACK

                # determine the character to print based on the tile state and value
                if tile_state is tile.State.covered:
                    character = Gui.COVERED
                elif tile_state is tile.State.visible:
                    value = self.game.get_tile_value(x, y)

                    if value == 0:
                        character = Gui.BLANK
                    elif value == -1:
                        character = Gui.MINE
                    else:
                        character = str(value)

                        # change colour based on the value
                        colour = pygame.Color(0, 0, 0)
                        colour.hsla = (((value - 1) * 200) % 360, 70, 40, 100)
                elif tile_state is tile.State.flag:
                    character = Gui.FLAG
                elif tile_state is tile.State.unknown:
                    character = Gui.UNKNOWN

                text_surface = text.render(character, True, colour)
                text_rect = text_surface.get_rect()
                text_rect.center = (Gui.PADDING + int((x + 0.5) * channel_width),
                                    Gui.PADDING + int((y + 0.5) * channel_width))
                self.screen.blit(text_surface, text_rect)

    # draw the command bar with buttons to click
    def _draw_command_bar(self, mouse_pos):
        x_off = Gui.CANVAS_SIZE + 2 * Gui.PADDING  # X offset to the command bar
        y_off = Gui.PADDING # Y offset to the command bar

        # indicate the number of flags placed
        text = pygame.font.Font("assets/fonts/FreeSerif.ttf", 40)
        message = str(self.game.get_flags()) + " / " + str(self.mines) + " " + Gui.FLAG
        rect = pygame.Rect(x_off + 15, y_off + 10, 170, 50)
        text_surface = text.render(message, True, Gui.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.center = rect.center
        self.screen.blit(text_surface, text_rect)

        # Set up text for buttons
        text = pygame.font.Font("assets/fonts/FreeSans.ttf", 20)

        # Reset button
        rect = rect.move(0, 75)
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, Gui.MID_LIGHT_GRAY, rect)
        else:
            pygame.draw.rect(self.screen, Gui.WHITE, rect)
        pygame.draw.rect(self.screen, Gui.BLACK, rect, 5)
        text_surface = text.render("Reset", True, Gui.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.center = rect.center
        self.screen.blit(text_surface, text_rect)

        # 8x8 10 mines button
        rect = rect.move(0, 75)
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, Gui.MID_LIGHT_GRAY, rect)
        else:
            pygame.draw.rect(self.screen, Gui.WHITE, rect)
        pygame.draw.rect(self.screen, Gui.BLACK, rect, 5)
        text_surface = text.render("8x8 10 mines", True, Gui.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.center = rect.center
        self.screen.blit(text_surface, text_rect)

        # 16x16 40 mines button
        rect = rect.move(0, 75)
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, Gui.MID_LIGHT_GRAY, rect)
        else:
            pygame.draw.rect(self.screen, Gui.WHITE, rect)
        pygame.draw.rect(self.screen, Gui.BLACK, rect, 5)
        text_surface = text.render("16x16 40 mines", True, Gui.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.center = rect.center
        self.screen.blit(text_surface, text_rect)

        # 25x25 99 mines button
        rect = rect.move(0, 75)
        if rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, Gui.MID_LIGHT_GRAY, rect)
        else:
            pygame.draw.rect(self.screen, Gui.WHITE, rect)
        pygame.draw.rect(self.screen, Gui.BLACK, rect, 5)
        text_surface = text.render("25x25 99 mines", True, Gui.BLACK)
        text_rect = text_surface.get_rect()
        text_rect.center = rect.center
        self.screen.blit(text_surface, text_rect)

    # draws victory text
    def _draw_win(self):
        message = "Victory"
        colour = Gui.GREEN

        text = pygame.font.Font("assets/fonts/FreeSerifBoldItalic.ttf", 127)
        text_surface = text.render(message, True, colour)
        text_rect = text_surface.get_rect()
        text_rect.center = (int((Gui.PADDING + Gui.CANVAS_SIZE) * 0.5), int((Gui.PADDING + Gui.CANVAS_SIZE) * 0.5))
        self.screen.blit(text_surface, text_rect)

    # draws the mines game and the command bar
    def _draw_screen(self, mouse_pos):
        self.screen.fill(Gui.LIGHT_GRAY)

        self._draw_base_canvas()
        self._draw_minefield(mouse_pos)
        self._draw_command_bar(mouse_pos)

        if self.game.victory():
            self._draw_win()

        pygame.display.update()

    # handles the pygame events 60 times per second
    def _event_handler(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # mouse position at the current event
            mouse_pos = pygame.mouse.get_pos()

            # check if mouse intersects the minefield
            rect = pygame.Rect(Gui.PADDING, Gui.PADDING, Gui.CANVAS_SIZE, Gui.CANVAS_SIZE)

            if rect.collidepoint(mouse_pos):
                channel_width = Gui.CANVAS_SIZE / self.size
                mouse_x = int((mouse_pos[0] - Gui.PADDING) / channel_width)
                mouse_y = int((mouse_pos[1] - Gui.PADDING) / channel_width)

                if pygame.mouse.get_pressed()[0]:
                    self.last_left_down = (mouse_x, mouse_y)
                elif pygame.mouse.get_pressed()[2]:
                    self.last_right_down = (mouse_x, mouse_y)

            # check if the mouse is over the command bar
            rect = pygame.Rect(Gui.PADDING + Gui.CANVAS_SIZE, Gui.PADDING, Gui.COMMANDS_BAR_SIZE, Gui.CANVAS_SIZE)

            if rect.collidepoint(mouse_pos):
                self._mouse_command_handler(mouse_pos, mouse_down=True)

        elif event.type == pygame.MOUSEBUTTONUP:
            # mouse position at the current event
            mouse_pos = pygame.mouse.get_pos()

            # check if mouse intersects the minefield
            rect = pygame.Rect(Gui.PADDING, Gui.PADDING, Gui.CANVAS_SIZE, Gui.CANVAS_SIZE)

            if rect.collidepoint(mouse_pos):
                channel_width = Gui.CANVAS_SIZE / self.size
                mouse_x = int((mouse_pos[0] - Gui.PADDING) / channel_width)
                mouse_y = int((mouse_pos[1] - Gui.PADDING) / channel_width)

                if not pygame.mouse.get_pressed()[0] and self.last_left_down != (-1, -1):
                    if (mouse_x, mouse_y) == self.last_left_down:
                        self.game.left_mouse_button(mouse_x, mouse_y)

                    self.last_left_down = (-1, -1)

                    if self.game.game_done() and not self.game.victory() and self.failed_tile == (-1, -1):
                        self.failed_tile = (mouse_x, mouse_y)
                elif not pygame.mouse.get_pressed()[2] and self.last_right_down != (-1, -1):
                    if (mouse_x, mouse_y) == self.last_right_down:
                        self.game.right_mouse_button(mouse_x, mouse_y)

                    self.last_right_down = (-1, -1)

            # check if the mouse is over the command bar
            rect = pygame.Rect(Gui.PADDING + Gui.CANVAS_SIZE, Gui.PADDING, Gui.COMMANDS_BAR_SIZE, Gui.CANVAS_SIZE)

            if rect.collidepoint(mouse_pos):
                self._mouse_command_handler(mouse_pos, mouse_down=False)

    def _mouse_command_handler(self, mouse_pos, mouse_down=True):
        x_off = Gui.CANVAS_SIZE + 2 * Gui.PADDING  # X offset to the command bar
        y_off = Gui.PADDING  # Y offset to the command bar

        reset_rect = pygame.Rect(x_off + 15, y_off + 85, 170, 50)
        _8x8_rect = reset_rect.move(0, 75)
        _16x16_rect = _8x8_rect.move(0, 75)
        _25x25_rect = _16x16_rect.move(0, 75)

        if reset_rect.collidepoint(mouse_pos):
            self.restart(self.size, self.mines)
        elif _8x8_rect.collidepoint(mouse_pos):
            self.restart(8, 10)
        elif _16x16_rect.collidepoint(mouse_pos):
            self.restart(16, 40)
        elif _25x25_rect.collidepoint(mouse_pos):
            self.restart(25, 99)

    # game loop that controls the buttons, game, and solver as well as drawing the screen
    def _game_loop(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    # Exit the game
                    pygame.quit()
                    quit()
                else:
                    self._event_handler(event)

            mouse_pos = (10000, 10000)
            if pygame.mouse.get_focused():
                mouse_pos = pygame.mouse.get_pos()
            self._draw_screen(mouse_pos)
            self.clock.tick(60)
