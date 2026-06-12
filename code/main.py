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
from platformer_level import PlatformerLevel
from house import House
from boss_chamber import BossChamber


class Game:
    def __init__(self):
        #pygame initialization
        pygame.init()
        pygame.joystick.init()
        pygame.mixer.init()

        # Volume setup
        self.master_volume = 1.0
        self.menu_volume = 0.7
        self.town_volume = 0.4
        self.house_volume = 0.4
        self.level_volume = 0.45
        self.boss_volume = 0.45

        # Menu music
        self.menu_music = pygame.mixer.Sound("../audio/menu/3-13 The Isle of Songs.mp3")

        # Town music
        self.town_music = pygame.mixer.Sound("../audio/town/3-17. Snowbelle City.mp3")

        # House music
        self.house_music = pygame.mixer.Sound("../audio/town/1-05. Littleroot Town.mp3")

        # Backup level music
        self.level_one_music = pygame.mixer.Sound("../audio/levels/level 1/2-17. tartarus_0d06.mp3")

        # no level/boss song is active yet
        self.current_level_music = None

        self.apply_music_volumes()
        self.menu_music.play(loops=-1)

        #Screen setup
        self.screen = pygame.display.set_mode(
            (screen_width, screen_height),
            pygame.SCALED | pygame.DOUBLEBUF,
            vsync=1
        )
        pygame.display.set_caption("Eira and The Crystal Promise")
        self.clock = pygame.time.Clock()

        #Controller setup
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]
        for joystick in self.joysticks:
            joystick.init()

        self.A_BUTTON = 0
        self.B_BUTTON = 1
        self.MINUS_BUTTON = 6
        self.PLUS_BUTTON = 7
        self.DPAD_UP_BUTTON = 11
        self.DPAD_DOWN_BUTTON = 12
        self.DPAD_LEFT_BUTTON = 13
        self.DPAD_RIGHT_BUTTON = 14

        self.pause_active = False
        self.pause_choice_index = 0
        self.pause_last_move_time = 0
        self.pause_move_delay = 180

        # Create camera group first
        self.camera_group = CameraGroup()

        # Create the town and player
        self.town = Town(self.screen, self.camera_group)
        self.player = Player(self.town.player_start, self.town.obstacles)
        self.camera_group.add(self.player)

        # Dialogue system
        self.dialogue_active = False
        self.current_dialogue = []
        self.dialogue_index = 0
        self.dialogue_text = ""

        # Game state
        self.status = "intro"
        self.platformer_level = None
        self.boss_chamber = None
        self.current_level_name = None
        self.current_level_music = None
        self.house = None
        self.house_paths = {
            "house1": "../mapData/Interiors/House1/House1.tmx",
            "house2": "../mapData/Interiors/House2/House2.tmx",
            "house3": "../mapData/Interiors/House3/House3.tmx",
            "house4": "../mapData/Interiors/House4/House4.tmx"
        }

        # Platformer level paths
        self.level_data = {
            "level1": {
                "tmx": "../mapData/levels/level1.tmx",
                "music": "../audio/levels/level 1/2-23. When Mother Was There.mp3",
                "weather": "cave_drips"
            },
            "level2": {
                "tmx": "../mapData/levels/level2.tmx",
                "music": "../audio/levels/level 2/5-05. So Happy World.mp3",
                "weather": "heavy_snow"
            },
            "level3": {
                "tmx": "../mapData/levels/level3.tmx",
                "music": "../audio/levels/level 3/2-08. A Woman.mp3",
                "weather": "light_rain"
            },
            "level4": {
                "tmx": "../mapData/levels/level4.tmx",
                "music": "../audio/levels/level 4/1-48. Living With Determination -Iwatodai Dorm Arrange-.mp3",
                "weather": "cave_drips"
            }
        }
        # Yes / No choice
        self.choice_active = False
        self.choice_index = 0
        self.choice_level = None
        self.choice_question = "Yes or No?"

        # Crystal shard progress
        self.completed_shard_levels = set()
        self.shards_collected = 0
        self.required_shards = 3

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

        # Intro cutscene stuff
        self.intro_step = 0
        self.intro_timer = 0
    # updates all the music volumes from the music menu values
    def apply_music_volumes(self):
        # updates all the music volumes from the music menu values
        self.menu_music.set_volume(self.menu_volume * self.master_volume)
        self.town_music.set_volume(self.town_volume * self.master_volume)
        self.house_music.set_volume(self.house_volume * self.master_volume)
        self.level_one_music.set_volume(self.level_volume * self.master_volume)

        if self.current_level_music is not None:
            if self.status == "boss_chamber":
                self.current_level_music.set_volume(
                    self.boss_volume * self.master_volume
                )
            else:
                self.current_level_music.set_volume(
                    self.level_volume * self.master_volume
                )

    def start_boss_chamber(self):
        # starts the boss fight and its music
        self.status = "boss_chamber"
        self.platformer_level = None
        self.boss_chamber = None
        self.house = None
        self.pause_active = False
        self.choice_active = False
        self.dialogue_active = False
        self.choice_level = None

        self.town_music.stop()
        self.house_music.stop()

        if self.current_level_music is not None:
            self.current_level_music.stop()
            self.current_level_music = None

        self.current_level_music = pygame.mixer.Sound(
            "../audio/levels/boss/12. Heartful Cry.mp3"
        )
        self.current_level_music.set_volume(self.boss_volume * self.master_volume)
        self.current_level_music.play(loops=-1)

        self.boss_chamber = BossChamber(
            self.screen,
            self.return_to_town,
            "../mapData/levels/bossChamber.tmx",
            self.start_boss_chamber
        )
    def draw_snow(self):
        # draws the snow particles so the town feels alive
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

    # draws the phone/map warning during the opening cutscene
    def draw_phone_ui(self):
        # draws the phone/map warning during the opening cutscene
        phone_rect = pygame.Rect(340, 150, 600, 350)
        screen_rect = pygame.Rect(360, 180, 560, 300)

        pygame.draw.rect(
            self.screen,
            (30, 30, 30),
            phone_rect,
            border_radius=25
        )
        pygame.draw.rect(
            self.screen,
            (220, 220, 220),
            screen_rect,
            border_radius=20
        )

        status_rect = pygame.Rect(360, 180, 560, 40)
        pygame.draw.rect(
            self.screen,
            (240, 240, 240),
            status_rect,
            border_radius=20
        )

        font = pygame.font.Font("EagleLake-Regular.ttf", 24)
        time_text = font.render("9:32", True, (40, 40, 40))
        self.screen.blit(time_text, (380, 180))

        battery_outline = pygame.Rect(860, 188, 50, 20)
        pygame.draw.rect(
            self.screen,
            (40, 40, 40),
            battery_outline,
            2,
            border_radius=4
        )
        pygame.draw.rect(self.screen, (40, 40, 40), (910, 193, 6, 10))

        low_battery = pygame.Rect(864, 192, 12, 12)
        pygame.draw.rect(
            self.screen,
            (200, 40, 40),
            low_battery,
            border_radius=3
        )

        warning_font = pygame.font.Font("EagleLake-Regular.ttf", 26)
        warning_text = warning_font.render(
            "Unable to load map",
            True,
            (180, 40, 40)
        )
        self.screen.blit(warning_text, (380, 225))

        for x in range(370, 900, 40):
            pygame.draw.line(
                self.screen,
                (200, 200, 200),
                (x, 230),
                (x, 460)
            )

        for y in range(230, 460, 40):
            pygame.draw.line(
                self.screen,
                (200, 200, 200),
                (370, y),
                (900, y)
            )

        pygame.draw.circle(self.screen, (255, 60, 60), (650, 350), 10)

        label = font.render(
            "Last Known Location: Frostpoint",
            True,
            (40, 40, 40)
        )
        self.screen.blit(label, (380, 430))

    # runs the opening cutscene before the main menu shows up
    def run_intro(self):
        # runs the opening cutscene before the main menu shows up
        dt = self.clock.get_time()
        self.intro_timer += dt

        if self.intro_step == 0:
            if self.intro_timer > 2000:
                self.intro_step = 1
                self.intro_timer = 0

            fade = max(0, 255 - int(self.intro_timer / 2000 * 255))
            overlay = pygame.Surface((screen_width, screen_height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(fade)
            self.screen.blit(overlay, (0, 0))

        elif self.intro_step == 1:
            font = pygame.font.Font("EagleLake-Regular.ttf", 40)
            text = font.render(
                "I lost him in the storm...",
                True,
                (255, 255, 255)
            )
            text_rect = text.get_rect(
                center=(screen_width // 2, screen_height // 2)
            )
            self.screen.blit(text, text_rect)

            if self.intro_timer > 3000:
                self.intro_step = 2
                self.intro_timer = 0

        elif self.intro_step == 2:
            self.draw_phone_ui()

            font = pygame.font.Font("EagleLake-Regular.ttf", 32)
            msg = font.render(
                "I have to go find him...",
                True,
                (255, 255, 255)
            )
            msg_rect = msg.get_rect(center=(screen_width // 2, 520))
            self.screen.blit(msg, msg_rect)

            if self.intro_timer > 5000:
                self.intro_step = 3
                self.intro_timer = 0

        elif self.intro_step == 3:
            fade = min(255, int(self.intro_timer / 2000 * 255))
            overlay = pygame.Surface((screen_width, screen_height))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(fade)
            self.screen.blit(overlay, (0, 0))

            if self.intro_timer > 2000:
                self.status = "menu"

    def draw_shard_progress(self):
        # shows how many crystal shards the player has
        title_font = pygame.font.Font("EagleLake-Regular.ttf", 22)
        progress_font = pygame.font.Font("EagleLake-Regular.ttf", 17)

        title_font.set_bold(True)
        progress_font.set_bold(True)

        title_text = title_font.render(
            "FIND ALL CRYSTAL SHARDS",
            True,
            (255, 230, 80)
        )

        progress_text = progress_font.render(
            "HINT: check houses   Shards: "
            + str(self.shards_collected)
            + "/"
            + str(self.required_shards),
            True,
            (220, 60, 60)
        )

        self.screen.blit(title_text, (30, 28))
        self.screen.blit(progress_text, (30, 58))

    def show_locked_boss_door_message(self):
        # shows the message when the boss door is still locked
        shards_remaining = self.required_shards - self.shards_collected
        self.current_dialogue = [
            "The door is sealed by a powerful force.",
            "You must recover all three crystal shards first.",
            "Shards collected: " + str(self.shards_collected) + "/" + str(self.required_shards)
        ]
        self.dialogue_index = 0
        self.dialogue_text = self.current_dialogue[0]
        self.dialogue_active = True
        self.choice_active = False
        self.choice_level = None

    def check_door_interaction(self):
        # checks if Eira is trying to enter a house
        interact_rect = self.player.hitbox.inflate(40, 40)

        for door in self.town.doors:
            if interact_rect.colliderect(door.rect):
                if door.house_name == "house2":
                    if self.shards_collected < self.required_shards:
                        self.show_locked_boss_door_message()
                        return True

                self.start_house(door.house_name)
                return True

        return False

    def award_shard(self, level_id):
        # gives a shard when a shard level is completed
        shard_levels = {"level1", "level3", "level4"}

        if level_id in shard_levels:
            self.completed_shard_levels.add(level_id)
            self.shards_collected = len(self.completed_shard_levels)

    def start_house(self, house_name):
        # loads the house interior and switches music
        if house_name not in self.house_paths:
            print("House path not found:", house_name)
            return

        self.house = House(
            self.screen,
            self.house_paths[house_name]
        )
        self.status = "house"
        self.town_music.stop()
        self.house_music.play(loops=-1)

    def return_to_town_from_house(self):
        # sends Eira back to town after leaving a house
        self.status = "town"
        self.house = None
        self.house_music.stop()
        self.town_music.play(loops=-1)

    def check_npc_interaction(self):
        # checks if Eira is talking to a town NPC
        interact_rect = self.player.hitbox.inflate(40, 40)

        for npc in self.town.npcs:
            if interact_rect.colliderect(npc.rect):
                self.current_dialogue = npc.interact()
                self.choice_level = getattr(npc, "level_to_load", None)
                self.dialogue_index = 0
                self.dialogue_text = self.current_dialogue[0]
                self.dialogue_active = True
                break

    def check_house_npc_interaction(self):
        # checks if Eira is talking to a house NPC
        if self.house is None:
            return False

        interact_rect = self.house.player.hitbox.inflate(40, 40)

        for npc in self.house.npcs:
            if interact_rect.colliderect(npc.rect):
                self.current_dialogue = npc.interact()
                self.choice_level = getattr(npc, "level_to_load", None)
                self.choice_question = getattr(
                    npc,
                    "choice_question",
                    "Will you accept?"
                )
                self.dialogue_index = 0
                self.dialogue_text = self.current_dialogue[0]
                self.dialogue_active = True
                return True

        return False

    def next_dialogue(self):
        # moves to the next dialogue line or opens a choice
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
        # draws the dialogue box at the bottom of the screen
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
        # draws the yes/no choice box
        box_rect = pygame.Rect(340, 245, 600, 225)
        pygame.draw.rect(self.screen, (20, 20, 30), box_rect)
        pygame.draw.rect(self.screen, (200, 200, 220), box_rect, 4)

        question_font = pygame.font.Font("EagleLake-Regular.ttf", 25)
        option_font = pygame.font.Font("EagleLake-Regular.ttf", 30)

        title = question_font.render(
            self.choice_question,
            True,
            (255, 255, 255)
        )
        title_rect = title.get_rect(center=(box_rect.centerx, box_rect.y + 55))
        self.screen.blit(title, title_rect)

        yes_color = (255, 230, 120) if self.choice_index == 0 else (255, 255, 255)
        no_color = (255, 230, 120) if self.choice_index == 1 else (255, 255, 255)

        yes_text = option_font.render(
            "> Yes" if self.choice_index == 0 else "  Yes",
            True,
            yes_color
        )
        no_text = option_font.render(
            "> No" if self.choice_index == 1 else "  No",
            True,
            no_color
        )

        self.screen.blit(yes_text, (box_rect.centerx - 75, box_rect.y + 115))
        self.screen.blit(no_text, (box_rect.centerx - 75, box_rect.y + 165))

    def start_platformer_level(self, level_id):
        # loads one of the platformer levels
        if level_id not in self.level_data:
            print("Missing level data for:", level_id)
            return

        level_info = self.level_data[level_id]
        self.current_level_name = level_id

        self.town_music.stop()
        self.house_music.stop()

        if self.current_level_music is not None:
            self.current_level_music.stop()

        self.current_level_music = pygame.mixer.Sound(
            level_info["music"]
        )
        self.current_level_music.set_volume(self.level_volume * self.master_volume)
        self.current_level_music.play(loops=-1)

        self.platformer_level = PlatformerLevel(
            self.screen,
            self.return_to_town,
            level_info["tmx"],
            level_info["weather"],
            self.complete_platformer_level
        )

        self.status = "platformer"
        self.pause_active = False
        self.choice_active = False
        self.choice_level = None

    def block_spell_button_after_pause(self):
        # stops B from instantly casting magic after closing pause
        if self.platformer_level is not None:
            if hasattr(self.platformer_level, "spell_button_held"):
                self.platformer_level.spell_button_held = True

        if self.boss_chamber is not None:
            if hasattr(self.boss_chamber, "spell_button_held"):
                self.boss_chamber.spell_button_held = True

    def open_pause_menu(self):
        # opens the pause menu during levels or the boss
        if self.status not in ["platformer", "boss_chamber"]:
            return

        self.pause_active = True
        self.pause_choice_index = 0
        self.pause_last_move_time = pygame.time.get_ticks()

    def close_pause_menu(self):
        # closes pause and blocks accidental spell casting
        self.pause_active = False
        self.block_spell_button_after_pause()

    def toggle_pause_menu(self):
        # opens or closes the pause menu
        if self.status not in ["platformer", "boss_chamber"]:
            return

        if self.pause_active:
            self.close_pause_menu()
        else:
            self.open_pause_menu()

    def pause_menu_move(self, direction):
        # moves the pause menu selection
        current_time = pygame.time.get_ticks()

        if current_time - self.pause_last_move_time < self.pause_move_delay:
            return

        self.pause_choice_index += direction

        if self.pause_choice_index < 0:
            self.pause_choice_index = 1

        if self.pause_choice_index > 1:
            self.pause_choice_index = 0

        self.pause_last_move_time = current_time

    def confirm_pause_menu(self):
        # chooses the selected pause menu option
        if self.pause_choice_index == 0:
            self.return_to_menu()
        elif self.pause_choice_index == 1:
            self.return_to_town()

    def return_to_menu(self):
        # sends the player back to the main menu
        self.pause_active = False
        self.choice_active = False
        self.dialogue_active = False
        self.choice_level = None

        self.platformer_level = None
        self.boss_chamber = None
        self.house = None
        self.current_level_name = None
        self.status = "town"

        self.town_music.stop()
        self.house_music.stop()

        if self.current_level_music is not None:
            self.current_level_music.stop()
            self.current_level_music = None

        self.menu_music.play(loops=-1)
        result = main_menu(self.screen)

        if result == "play":
            self.menu_music.stop()
            self.town_music.play(loops=-1)
            self.status = "town"

    def handle_pause_event(self, event):
        # handles ESC and controller pause input
        if self.status not in ["platformer", "boss_chamber"]:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.toggle_pause_menu()
                return True

            if self.pause_active:
                if event.key in [pygame.K_UP, pygame.K_w, pygame.K_LEFT, pygame.K_a]:
                    self.pause_menu_move(-1)
                    return True
                elif event.key in [pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d]:
                    self.pause_menu_move(1)
                    return True
                elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    self.confirm_pause_menu()
                    return True

        if event.type == pygame.JOYBUTTONDOWN:
            if event.button in [self.PLUS_BUTTON, self.MINUS_BUTTON, 8, 9]:
                self.toggle_pause_menu()
                return True

            if self.pause_active:
                if event.button in [self.DPAD_UP_BUTTON, self.DPAD_LEFT_BUTTON]:
                    self.pause_menu_move(-1)
                    return True
                elif event.button in [self.DPAD_DOWN_BUTTON, self.DPAD_RIGHT_BUTTON]:
                    self.pause_menu_move(1)
                    return True
                elif event.button == self.A_BUTTON:
                    self.confirm_pause_menu()
                    return True
                elif event.button == self.B_BUTTON:
                    self.close_pause_menu()
                    return True

        if event.type == pygame.JOYHATMOTION:
            if self.pause_active:
                hat_x, hat_y = event.value

                if hat_y == 1 or hat_x == -1:
                    self.pause_menu_move(-1)
                    return True
                elif hat_y == -1 or hat_x == 1:
                    self.pause_menu_move(1)
                    return True

        if event.type == pygame.JOYAXISMOTION:
            if self.pause_active:
                if event.axis == 1:
                    if event.value < -0.55:
                        self.pause_menu_move(-1)
                        return True
                    elif event.value > 0.55:
                        self.pause_menu_move(1)
                        return True

        return self.pause_active

    def draw_pause_menu(self):
        # draws the pause menu overlay
        if not self.pause_active:
            return

        overlay = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        box_rect = pygame.Rect(
            screen_width // 2 - 290,
            210,
            580,
            270
        )

        pygame.draw.rect(self.screen, (20, 20, 30), box_rect)
        pygame.draw.rect(self.screen, (220, 220, 230), box_rect, 4)

        title_font = pygame.font.Font("EagleLake-Regular.ttf", 42)
        option_font = pygame.font.Font("EagleLake-Regular.ttf", 30)
        hint_font = pygame.font.Font("EagleLake-Regular.ttf", 17)

        title = title_font.render(
            "Pause",
            True,
            (255, 255, 255)
        )
        title_rect = title.get_rect(
            center=(box_rect.centerx, box_rect.y + 55)
        )
        self.screen.blit(title, title_rect)

        options = [
            "Return to Menu",
            "Return to Town"
        ]

        for index, option in enumerate(options):
            y = box_rect.y + 125 + index * 55

            if index == self.pause_choice_index:
                color = (255, 230, 120)
                label = "> " + option
            else:
                color = (230, 230, 230)
                label = "  " + option

            text = option_font.render(label, True, color)
            self.screen.blit(text, (box_rect.x + 115, y))

        hint = hint_font.render(
            "ESC / +/- to close    SPACE / A to select    B to go back",
            True,
            (170, 170, 180)
        )
        hint_rect = hint.get_rect(
            center=(box_rect.centerx, box_rect.bottom - 32)
        )
        self.screen.blit(hint, hint_rect)

    def return_to_town(self):
        # sends the player back to town and stops level music
        self.status = "town"
        self.pause_active = False
        self.platformer_level = None
        self.boss_chamber = None
        self.current_level_name = None
        self.house_music.stop()

        if self.current_level_music is not None:
            self.current_level_music.stop()
            self.current_level_music = None

        self.town_music.play(loops=-1)

    def complete_platformer_level(self):
        # decides what happens after a level is completed
        completed_level = self.current_level_name

        if completed_level == "level2":
            self.start_boss_chamber()
            return

        self.award_shard(completed_level)
        self.return_to_town()

    def confirm_choice(self):
        # confirms a yes/no choice
        if self.choice_index == 0:
            if self.choice_level is not None:
                self.start_platformer_level(self.choice_level)
        else:
            self.cancel_choice()

    def cancel_choice(self):
        # cancels a yes/no choice
        self.choice_active = False
        self.choice_level = None
        self.choice_question = "Yes or No?"
        self.choice_index = 0

    def press_confirm(self):
        # handles A/confirm depending on the current state
        if self.choice_active:
            self.confirm_choice()
        elif self.dialogue_active:
            self.next_dialogue()
        else:
            if self.status == "house":
                if self.house is not None:
                    if self.house.check_exit_interaction():
                        self.return_to_town_from_house()
                    else:
                        self.check_house_npc_interaction()
            else:
                if not self.check_door_interaction():
                    self.check_npc_interaction()

    def press_cancel(self):
        # handles B/cancel depending on the current state
        if self.choice_active:
            self.cancel_choice()
        elif self.dialogue_active:
            self.next_dialogue()

    def run(self):
        # main game loop that updates and draws everything
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

                if self.handle_pause_event(event):
                    continue

                if event.type == pygame.KEYDOWN:
                    if self.status == "house":
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
                                if self.house is not None:
                                    if self.house.check_exit_interaction():
                                        self.return_to_town_from_house()
                                    else:
                                        self.check_house_npc_interaction()

                    elif self.status == "platformer":
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
                                if not self.check_door_interaction():
                                    self.check_npc_interaction()

                if event.type == pygame.JOYBUTTONDOWN:
                    if self.status == "house":
                        if event.button == self.A_BUTTON:
                            self.press_confirm()
                        elif event.button == self.B_BUTTON:
                            self.press_cancel()

                    elif self.status == "town":
                        if event.button == self.A_BUTTON:
                            self.press_confirm()
                        elif event.button == self.B_BUTTON:
                            self.press_cancel()

                if event.type == pygame.JOYHATMOTION:
                    if self.choice_active:
                        hat_x, hat_y = event.value
                        if hat_x != 0 or hat_y != 0:
                            self.choice_index = 1 - self.choice_index

            self.screen.fill("black")

            if self.status == "intro":
                self.run_intro()

            elif self.status == "menu":
                result = main_menu(self.screen)

                if result == "play":
                    self.status = "town"
                    self.menu_music.stop()
                    self.town_music.play(loops=-1)

            elif self.status == "town":
                if not self.dialogue_active and not self.choice_active:
                    self.player.update()

                self.camera_group.update()
                self.camera_group.draw(self.player)
                self.draw_snow()
                self.draw_shard_progress()

                if self.dialogue_active:
                    self.draw_dialogue()

                if self.choice_active:
                    self.draw_choice()

            elif self.status == "platformer":
                if self.platformer_level is not None:
                    if self.pause_active:
                        if hasattr(self.platformer_level, "draw_level"):
                            self.platformer_level.draw_level()
                    else:
                        self.platformer_level.run()

            elif self.status == "boss_chamber":
                if self.boss_chamber is not None:
                    if self.pause_active:
                        if hasattr(self.boss_chamber, "draw_chamber"):
                            self.boss_chamber.draw_chamber()
                    else:
                        self.boss_chamber.run()

            elif self.status == "house":
                if self.house is not None:
                    if self.dialogue_active or self.choice_active:
                        if hasattr(self.house, "draw"):
                            self.house.draw()
                        else:
                            self.house.run()
                    else:
                        self.house.run()

                if self.dialogue_active:
                    self.draw_dialogue()

                if self.choice_active:
                    self.draw_choice()

            self.draw_pause_menu()
            pygame.display.flip()
            self.clock.tick(60)


def draw_keycap(surface, rect, text, font, bg_color, text_color, radius=12):
    # draws one keyboard key on the controls screen
    pygame.draw.rect(surface, bg_color, rect, border_radius=radius)

    key_text = font.render(text, True, text_color)
    key_rect = key_text.get_rect(center=rect.center)
    surface.blit(key_text, key_rect)


def how_to_play_menu(screen):
    # shows the controls image and keeps only the back button on top
    how_img = pygame.image.load("how_to_play.png").convert_alpha()
    how_img = pygame.transform.scale(how_img, (screen_width, screen_height))

    button_font = pygame.font.Font("EagleLake-Regular.ttf", 40)
    back_button = pygame.Rect(40, 620, 200, 60)

    while True:
        mouse = pygame.mouse.get_pos()
        screen.blit(how_img, (0, 0))

        back_color = (
            (172, 179, 193)
            if back_button.collidepoint(mouse)
            else (156, 172, 198)
        )
        pygame.draw.rect(screen, back_color, back_button, border_radius=12)

        back_text = button_font.render("Back", True, (21, 30, 42))
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


# gets whichever volume value the music menu is looking at
def get_volume(option):
    # returns the volume value for the selected slider
    if option == 0:
        return game.master_volume
    elif option == 1:
        return game.menu_volume
    elif option == 2:
        return game.town_volume
    elif option == 3:
        return game.house_volume
    elif option == 4:
        return game.level_volume
    elif option == 5:
        return game.boss_volume

    return 0


# changes the selected volume and reapplies it to the music
def adjust_volume(option, amount):
    # changes a volume slider and applies it right away
    if option == 0:
        game.master_volume = max(0, min(1, game.master_volume + amount))
    elif option == 1:
        game.menu_volume = max(0, min(1, game.menu_volume + amount))
    elif option == 2:
        game.town_volume = max(0, min(1, game.town_volume + amount))
    elif option == 3:
        game.house_volume = max(0, min(1, game.house_volume + amount))
    elif option == 4:
        game.level_volume = max(0, min(1, game.level_volume + amount))
    elif option == 5:
        game.boss_volume = max(0, min(1, game.boss_volume + amount))

    game.apply_music_volumes()


# opens the music settings screen and lets keyboard/controller adjust volumes
def settings_menu(screen):
    # this is the music settings menu with sliders and controller support
    font = pygame.font.Font("EagleLake-Regular.ttf", 45)
    small_font = pygame.font.Font("EagleLake-Regular.ttf", 28)
    hint_font = pygame.font.Font("EagleLake-Regular.ttf", 18)

    options = [
        "Master Volume",
        "Menu Music",
        "Town Music",
        "House Music",
        "Level Music",
        "Boss Music",
        "Back"
    ]

    index = 0
    last_move_time = 0
    move_delay = 180

    def move_selection(direction):
        # moves through the settings options without flying past them
        nonlocal index, last_move_time

        current_time = pygame.time.get_ticks()

        if current_time - last_move_time < move_delay:
            return

        index += direction

        if index < 0:
            index = len(options) - 1

        if index >= len(options):
            index = 0

        last_move_time = current_time

    def adjust_selected(amount):
        # changes the chosen slider if it is not the back option
        if index < 6:
            adjust_volume(index, amount)

    while True:
        screen.fill((21, 30, 42))
        mouse = pygame.mouse.get_pos()

        title = font.render("Music Settings", True, (163, 189, 223))
        title_rect = title.get_rect(center=(screen_width // 2, 100))
        screen.blit(title, title_rect)

        for option_index, label_text in enumerate(options):
            color = (
                (255, 230, 120)
                if option_index == index
                else (220, 220, 230)
            )

            label = small_font.render(label_text, True, color)
            label_x = screen_width // 2 - 390
            label_y = 195 + option_index * 62
            screen.blit(label, (label_x, label_y))

            if option_index < 6:
                slider_x = screen_width // 2 - 80
                slider_y = 205 + option_index * 62
                slider_width = 330
                slider_height = 20

                pygame.draw.rect(
                    screen,
                    (80, 80, 100),
                    (slider_x, slider_y, slider_width, slider_height)
                )
                pygame.draw.rect(
                    screen,
                    (200, 200, 240),
                    (
                        slider_x,
                        slider_y,
                        int(slider_width * get_volume(option_index)),
                        slider_height
                    )
                )

                percent = str(int(get_volume(option_index) * 100)) + "%"
                percent_text = hint_font.render(
                    percent,
                    True,
                    (220, 220, 230)
                )
                screen.blit(
                    percent_text,
                    (slider_x + slider_width + 25, slider_y - 3)
                )

                left_arrow = pygame.Rect(
                    slider_x - 45,
                    slider_y - 10,
                    30,
                    40
                )
                right_arrow = pygame.Rect(
                    slider_x + slider_width + 12,
                    slider_y - 10,
                    30,
                    40
                )

                pygame.draw.polygon(
                    screen,
                    (220, 220, 230),
                    [
                        (left_arrow.right, left_arrow.top),
                        (left_arrow.left, left_arrow.centery),
                        (left_arrow.right, left_arrow.bottom)
                    ]
                )
                pygame.draw.polygon(
                    screen,
                    (220, 220, 230),
                    [
                        (right_arrow.left, right_arrow.top),
                        (right_arrow.right, right_arrow.centery),
                        (right_arrow.left, right_arrow.bottom)
                    ]
                )

                if option_index == index:
                    pygame.draw.rect(
                        screen,
                        (255, 230, 120),
                        (
                            slider_x - 6,
                            slider_y - 6,
                            slider_width + 12,
                            slider_height + 12
                        ),
                        2
                    )

        hint = hint_font.render(
            "UP/DOWN choose   LEFT/RIGHT adjust   A/ENTER select   B/ESC back",
            True,
            (170, 170, 180)
        )
        hint_rect = hint.get_rect(center=(screen_width // 2, 650))
        screen.blit(hint, hint_rect)

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)

            if joystick.get_numaxes() >= 2:
                stick_y = joystick.get_axis(1)
                stick_x = joystick.get_axis(0)

                if stick_y < -0.55:
                    move_selection(-1)
                elif stick_y > 0.55:
                    move_selection(1)

                current_time = pygame.time.get_ticks()

                if current_time - last_move_time >= move_delay:
                    if stick_x < -0.55:
                        adjust_selected(-0.05)
                        last_move_time = current_time
                    elif stick_x > 0.55:
                        adjust_selected(0.05)
                        last_move_time = current_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEMOTION:
                for option_index in range(len(options)):
                    option_rect = pygame.Rect(
                        screen_width // 2 - 410,
                        185 + option_index * 62,
                        780,
                        52
                    )

                    if option_rect.collidepoint(mouse):
                        index = option_index

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()

                for option_index in range(6):
                    slider_x = screen_width // 2 - 80
                    slider_y = 205 + option_index * 62
                    left_arrow = pygame.Rect(
                        slider_x - 45,
                        slider_y - 10,
                        30,
                        40
                    )
                    right_arrow = pygame.Rect(
                        slider_x + 342,
                        slider_y - 10,
                        30,
                        40
                    )
                    slider_rect = pygame.Rect(
                        slider_x,
                        slider_y - 8,
                        330,
                        36
                    )

                    if left_arrow.collidepoint(mx, my):
                        adjust_volume(option_index, -0.05)

                    if right_arrow.collidepoint(mx, my):
                        adjust_volume(option_index, 0.05)

                    if slider_rect.collidepoint(mx, my):
                        new_volume = (mx - slider_x) / 330
                        current_volume = get_volume(option_index)
                        adjust_volume(option_index, new_volume - current_volume)

                back_rect = pygame.Rect(
                    screen_width // 2 - 410,
                    185 + 6 * 62,
                    780,
                    52
                )

                if back_rect.collidepoint(mx, my):
                    return

            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_b]:
                    return
                elif event.key in [pygame.K_UP, pygame.K_w]:
                    move_selection(-1)
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    move_selection(1)
                elif event.key in [pygame.K_LEFT, pygame.K_a]:
                    adjust_selected(-0.05)
                elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                    adjust_selected(0.05)
                elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    if index == len(options) - 1:
                        return

            if event.type == pygame.JOYHATMOTION:
                hat_x, hat_y = event.value

                if hat_y == 1:
                    move_selection(-1)
                elif hat_y == -1:
                    move_selection(1)

                if hat_x == -1:
                    adjust_selected(-0.05)
                elif hat_x == 1:
                    adjust_selected(0.05)

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:
                    if index == len(options) - 1:
                        return
                elif event.button == 1:
                    return
                elif event.button == 11:
                    move_selection(-1)
                elif event.button == 12:
                    move_selection(1)
                elif event.button == 13:
                    adjust_selected(-0.05)
                elif event.button == 14:
                    adjust_selected(0.05)

        pygame.display.update()


def draw_text_with_outline(surface, text, font, text_color, outline_color, center_pos, thickness=3):
    # draws title text with an outline so it pops
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
    # this is the main menu, just handles play/settings/quit
    background = pygame.image.load("Background 4.png").convert()
    background = pygame.transform.scale(background, (screen_width, screen_height))

    title_font_small = pygame.font.Font("EagleLake-Regular.ttf", 45)
    title_font_big = pygame.font.Font("EagleLake-Regular.ttf", 75)
    font = pygame.font.Font("EagleLake-Regular.ttf", 35)

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
    button_texts = ["Play", "Controls", "Music Settings", "Quit"]
    selected_index = 0
    last_stick_move = 0
    stick_delay = 180

    def move_selection(direction):
        # moves the menu cursor up or down
        nonlocal selected_index

        selected_index += direction

        if selected_index < 0:
            selected_index = len(buttons) - 1

        if selected_index >= len(buttons):
            selected_index = 0

    def select_option(index):
        # runs whichever menu option is selected
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
            color = (
                (117, 143, 178)
                if index == selected_index
                else (163, 189, 223)
            )
            pygame.draw.rect(screen, color, button)

            text_surface = font.render(
                button_texts[index],
                True,
                (21, 30, 42)
            )
            text_rect = text_surface.get_rect(center=button.center)
            screen.blit(text_surface, text_rect)

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
                            return "play"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    move_selection(-1)
                elif event.key == pygame.K_DOWN:
                    move_selection(1)
                elif event.key == pygame.K_RETURN:
                    result = select_option(selected_index)

                    if result == "play":
                        return "play"
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
                        return "play"

                elif event.button == DPAD_UP:
                    move_selection(-1)
                elif event.button == DPAD_DOWN:
                    move_selection(1)

        pygame.display.update()


game = Game()
game.run()
