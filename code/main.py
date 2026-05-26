#Zain Arif
#2026-04-12
#main.py
#main file for the project, will be checking game state and running all functions on the screen

import os

import pygame
import sys
import random

#makes sure teh directrory alwaays works no matter where the file is run from
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)

from settings import *
from town import Town
from player import Player
from camera import CameraGroup
from test_level import TestLevel


class Game:
    def __init__(self):
        #pygame initialization
        pygame.init()
        pygame.joystick.init()
        pygame.mixer.init()

        #Menu music
        self.menu_music = pygame.mixer.Sound("../audio/menu/3-13 The Isle of Songs.mp3")
        self.menu_music.set_volume(0.7)
        self.menu_music.play(loops=-1)

        #Town music
        self.town_music = pygame.mixer.Sound("../audio/town/3-17. Snowbelle City.mp3")
        self.town_music.set_volume(0.4)
     
        #Level 1 music
        self.level_one_music = pygame.mixer.Sound("../audio/levels/level 1/2-17. tartarus_0d06.mp3")
        self.level_one_music.set_volume(0.45)

        #Screen setup
        self.screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Eira and The Crystal Promise")
        self.clock = pygame.time.Clock()

        #Controller setup
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joystick in self.joysticks:
            joystick.init()

        self.A_BUTTON = 0
        self.B_BUTTON = 1

        # Create camera group first
        self.camera_group = CameraGroup()

        # Create the town and player
        self.town = Town(self.screen, self.camera_group)
        self.player = Player((640, 360), self.town.obstacles)
        self.camera_group.add(self.player)

        # Dialogue system
        self.dialogue_active = False
        self.current_dialogue = []
        self.dialogue_index = 0
        self.dialogue_text = ""

        # Game state
        self.status = "town"
        self.test_level = None

        # Yes / No choice
        self.choice_active = False
        self.choice_index = 0
        self.choice_level = None

        # Snow effect
        self.snow_particles = []
        for i in range(350):
            particle = {
                "x": random.randint(0, map_width),
                "y": random.randint(0, map_height),
                "speed": random.uniform(0.7, 1.8),
                "size": random.randint(2, 4),
                "drift": random.uniform(-0.4, 0.4)
            }
            self.snow_particles.append(particle)

    def draw_snow(self):
        for particle in self.snow_particles:
            particle["y"] += particle["speed"]
            particle["x"] += particle["drift"]

            if particle["y"] > map_height:
                particle["y"] = random.randint(-20, -5)
                particle["x"] = random.randint(0, map_width)

            if particle["x"] < 0:
                particle["x"] = map_width

            if particle["x"] > map_width:
                particle["x"] = 0

            screen_x = particle["x"] - self.camera_group.offset.x
            screen_y = particle["y"] - self.camera_group.offset.y

            if -10 < screen_x < screen_width + 10 and -10 < screen_y < screen_height + 10:
                pygame.draw.circle(
                    self.screen,
                    (210, 210, 210),
                    (int(screen_x), int(screen_y)),
                    particle["size"]
                )

    def check_npc_interaction(self):
        interact_rect = self.player.hitbox.inflate(40, 40)

        for npc in self.town.npcs:
            if interact_rect.colliderect(npc.rect):
                self.current_dialogue = npc.interact()
                self.choice_level = getattr(npc, "level_to_load", None)
                self.dialogue_index = 0
                self.dialogue_text = self.current_dialogue[0]
                self.dialogue_active = True
                break

    def next_dialogue(self):
        self.dialogue_index += 1

        if self.dialogue_index < len(self.current_dialogue):
            self.dialogue_text = self.current_dialogue[self.dialogue_index]
        else:
            self.dialogue_active = False
            self.current_dialogue = []
            self.dialogue_index = 0
            self.dialogue_text = ""

            if self.choice_level is not None:
                self.choice_active = True
                self.choice_index = 0
            else:
                self.choice_active = False
                self.choice_level = None

    def draw_dialogue(self):
        box_rect = pygame.Rect(60, 500, 1160, 160)
        pygame.draw.rect(self.screen, (20, 20, 30), box_rect)
        pygame.draw.rect(self.screen, (200, 200, 220), box_rect, 4)

        font = pygame.font.Font("EagleLake-Regular.ttf", 32)
        text = font.render(self.dialogue_text, True, (255, 255, 255))
        self.screen.blit(text, (90, 550))

        hint_font = pygame.font.Font("EagleLake-Regular.ttf", 18)
        hint = hint_font.render("SPACE / ENTER / A / B", True, (180, 180, 180))
        self.screen.blit(hint, (900, 620))

    def draw_choice(self):
        box_rect = pygame.Rect(390, 260, 500, 200)
        pygame.draw.rect(self.screen, (20, 20, 30), box_rect)
        pygame.draw.rect(self.screen, (200, 200, 220), box_rect, 4)

        font = pygame.font.Font("EagleLake-Regular.ttf", 30)
        title = font.render("Enter the test level?", True, (255, 255, 255))
        self.screen.blit(title, (430, 290))

        yes_color = (255, 230, 120) if self.choice_index == 0 else (255, 255, 255)
        no_color = (255, 230, 120) if self.choice_index == 1 else (255, 255, 255)

        yes_text = font.render("> Yes" if self.choice_index == 0 else "  Yes", True, yes_color)
        no_text = font.render("> No" if self.choice_index == 1 else "  No", True, no_color)

        self.screen.blit(yes_text, (530, 350))
        self.screen.blit(no_text, (530, 395))

    def start_test_level(self):
        self.test_level = TestLevel(self.screen, self.return_to_town)
        self.status = "test"
        self.choice_active = False
        self.choice_level = None
        self.town_music.stop()
        self.level_one_music.play(loops=-1)

    def return_to_town(self):
        self.status = "town"
        self.test_level = None
        self.level_one_music.stop()
        self.town_music.play(loops=-1)

    def confirm_choice(self):
        if self.choice_index == 0:
            if self.choice_level == "test":
                self.start_test_level()
        else:
            self.choice_active = False
            self.choice_level = None

    def cancel_choice(self):
        self.choice_active = False
        self.choice_level = None
        self.choice_index = 0

    def press_confirm(self):
        if self.choice_active:
            self.confirm_choice()
        elif self.dialogue_active:
            self.next_dialogue()
        else:
            self.check_npc_interaction()

    def press_cancel(self):
        if self.choice_active:
            self.cancel_choice()
        elif self.dialogue_active:
            self.next_dialogue()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if self.status == "test":
                        pass

                    elif self.status == "town":
                        if self.choice_active:
                            if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                                self.choice_index = 1 - self.choice_index
                            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                                self.confirm_choice()
                            elif event.key == pygame.K_ESCAPE:
                                self.cancel_choice()

                        elif self.dialogue_active:
                            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                                self.next_dialogue()

                        else:
                            if event.key == pygame.K_e:
                                self.check_npc_interaction()

                if event.type == pygame.JOYBUTTONDOWN:
                    if self.status == "town":
                        if event.button == self.A_BUTTON:
                            self.press_confirm()
                        elif event.button == self.B_BUTTON:
                            self.press_cancel()

                if event.type == pygame.JOYHATMOTION:
                    if self.status == "town" and self.choice_active:
                        hat_x, hat_y = event.value
                        if hat_x != 0 or hat_y != 0:
                            self.choice_index = 1 - self.choice_index

            self.screen.fill("black")

            if self.status == "town":
                if not self.dialogue_active and not self.choice_active:
                    self.player.update()

                self.camera_group.update()
                self.camera_group.draw(self.player)
                self.draw_snow()

                if self.dialogue_active:
                    self.draw_dialogue()

                if self.choice_active:
                    self.draw_choice()

            elif self.status == "test":
                if self.test_level is not None:
                    self.test_level.run()

            pygame.display.update()
            self.clock.tick(60)


def draw_keycap(surface, rect, text, font, bg_color, text_color, radius=12):
    pygame.draw.rect(surface, bg_color, rect, border_radius=radius)

    key_text = font.render(text, True, text_color)
    key_rect = key_text.get_rect(center=rect.center)
    surface.blit(key_text, key_rect)


def how_to_play_menu(screen):
    how_img = pygame.image.load("how_to_play.png").convert_alpha()
    how_img = pygame.transform.scale(how_img, (screen_width, screen_height))

    title_font = pygame.font.Font("EagleLake-Regular.ttf", 60)
    key_font = pygame.font.Font("EagleLake-Regular.ttf", 40)
    button_font = pygame.font.Font("EagleLake-Regular.ttf", 40)

    key_bg = (109, 117, 141)
    key_text_color = (21, 30, 42)
    back_button = pygame.Rect(40, 620, 200, 60)

    while True:
        screen.fill((0, 0, 0))
        mouse = pygame.mouse.get_pos()
        screen.blit(how_img, (0, 0))

        title_text = title_font.render("How to Play", True, (109, 117, 141))
        title_rect = title_text.get_rect(center=(1280 // 2, 70))
        screen.blit(title_text, title_rect)

        up_rect = pygame.Rect(180, 250, 70, 70)
        left_rect = pygame.Rect(100, 330, 70, 70)
        down_rect = pygame.Rect(180, 330, 70, 70)
        right_rect = pygame.Rect(260, 330, 70, 70)

        draw_keycap(screen, up_rect, "↑", key_font, key_bg, key_text_color)
        draw_keycap(screen, left_rect, "←", key_font, key_bg, key_text_color)
        draw_keycap(screen, down_rect, "↓", key_font, key_bg, key_text_color)
        draw_keycap(screen, right_rect, "→", key_font, key_bg, key_text_color)

        back_color = (172, 179, 193) if back_button.collidepoint(mouse) else (156, 172, 198)
        pygame.draw.rect(screen, back_color, back_button, border_radius=12)

        back_text = button_font.render("Back", True, (109, 117, 141))
        back_rect = back_text.get_rect(center=back_button.center)
        screen.blit(back_text, back_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse = pygame.mouse.get_pos()
                if back_button.collidepoint(mouse):
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    return

            if event.type == pygame.JOYBUTTONDOWN:
                return

        pygame.display.update()


def settings_menu(screen):
    font = pygame.font.Font("EagleLake-Regular.ttf", 45)
    small_font = pygame.font.Font("EagleLake-Regular.ttf", 28)
    back_button = pygame.Rect(40, 620, 200, 60)

    while True:
        screen.fill((21, 30, 42))
        mouse = pygame.mouse.get_pos()

        title = font.render("Settings", True, (163, 189, 223))
        title_rect = title.get_rect(center=(screen_width // 2, 120))
        screen.blit(title, title_rect)

        message = small_font.render("Settings will be added later.", True, (220, 220, 230))
        message_rect = message.get_rect(center=(screen_width // 2, 260))
        screen.blit(message, message_rect)

        back_color = (172, 179, 193) if back_button.collidepoint(mouse) else (156, 172, 198)
        pygame.draw.rect(screen, back_color, back_button, border_radius=12)

        back_text = small_font.render("Back", True, (21, 30, 42))
        back_rect = back_text.get_rect(center=back_button.center)
        screen.blit(back_text, back_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if back_button.collidepoint(mouse):
                    return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_RETURN:
                    return

            if event.type == pygame.JOYBUTTONDOWN:
                return

        pygame.display.update()


def draw_text_with_outline(surface, text, font, text_color, outline_color, center_pos, thickness=3):
    main = font.render(text, True, text_color)
    outline = font.render(text, True, outline_color)
    x, y = center_pos
    offsets = []

    for ox in range(-thickness, thickness + 1):
        for oy in range(-thickness, thickness + 1):
            if ox != 0 or oy != 0:
                offsets.append((ox, oy))

    for ox, oy in offsets:
        surface.blit(outline, outline.get_rect(center=(x + ox, y + oy)))

    surface.blit(main, main.get_rect(center=center_pos))


def main_menu(screen):
    background = pygame.image.load("Background 4.png").convert()
    background = pygame.transform.scale(background, (screen_width, screen_height))

    title_font_small = pygame.font.Font("EagleLake-Regular.ttf", 45)
    title_font_big = pygame.font.Font("EagleLake-Regular.ttf", 75)
    font = pygame.font.Font("EagleLake-Regular.ttf", 40)

    A_BUTTON = 0
    DPAD_UP = 11
    DPAD_DOWN = 12

    button_width = 300
    button_height = 80

    play_button = pygame.Rect(1280 // 2 - button_width // 2, 250, button_width, button_height)
    how_button = pygame.Rect(1280 // 2 - button_width // 2, 350, button_width, button_height)
    settings_button = pygame.Rect(1280 // 2 - button_width // 2, 450, button_width, button_height)
    quit_button = pygame.Rect(1280 // 2 - button_width // 2, 550, button_width, button_height)

    buttons = [play_button, how_button, settings_button, quit_button]
    button_texts = ["Play", "How to Play", "Settings", "Quit"]
    selected_index = 0
    last_stick_move = 0
    stick_delay = 180

    def move_selection(direction):
        nonlocal selected_index
        selected_index += direction

        if selected_index < 0:
            selected_index = len(buttons) - 1

        if selected_index >= len(buttons):
            selected_index = 0

    def select_option(index):
        if index == 0:
            return "play"
        elif index == 1:
            how_to_play_menu(screen)
        elif index == 2:
            settings_menu(screen)
        elif index == 3:
            pygame.quit()
            sys.exit()

        return None

    while True:
        screen.blit(background, (0, 0))
        mouse = pygame.mouse.get_pos()

        for index, button in enumerate(buttons):
            if button.collidepoint(mouse):
                selected_index = index

        draw_text_with_outline(
            screen,
            "Eira and The",
            title_font_small,
            (163, 189, 223),
            (21, 30, 42),
            (1280 // 2, 90),
            thickness=3
        )

        draw_text_with_outline(
            screen,
            "Crystal Promise",
            title_font_big,
            (163, 189, 223),
            (21, 30, 42),
            (1280 // 2, 160),
            thickness=5
        )

        for index, button in enumerate(buttons):
            color = (117, 143, 178) if index == selected_index else (163, 189, 223)
            pygame.draw.rect(screen, color, button)

            text_surface = font.render(button_texts[index], True, (21, 30, 42))
            text_rect = text_surface.get_rect(center=button.center)
            screen.blit(text_surface, text_rect)

        # Left stick menu movement
        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            current_time = pygame.time.get_ticks()

            if joystick.get_numaxes() >= 2:
                stick_y = joystick.get_axis(1)

                if current_time - last_stick_move > stick_delay:
                    if stick_y < -0.55:
                        move_selection(-1)
                        last_stick_move = current_time
                    elif stick_y > 0.55:
                        move_selection(1)
                        last_stick_move = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                for index, button in enumerate(buttons):
                    if button.collidepoint(mouse):
                        result = select_option(index)
                        if result == "play":
                            return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    move_selection(-1)
                elif event.key == pygame.K_DOWN:
                    move_selection(1)
                elif event.key == pygame.K_RETURN:
                    result = select_option(selected_index)
                    if result == "play":
                        return
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value

                if hat_y == 1:
                    move_selection(-1)
                elif hat_y == -1:
                    move_selection(1)

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == A_BUTTON:
                    result = select_option(selected_index)
                    if result == "play":
                        return
                elif event.button == DPAD_UP:
                    move_selection(-1)
                elif event.button == DPAD_DOWN:
                    move_selection(1)

        pygame.display.update()

game = Game()
main_menu(game.screen)
game.menu_music.stop()
game.town_music.play(loops=-1)
game.run()