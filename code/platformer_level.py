# test_level.py
import pygame
import random

from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer
from settings import screen_width, screen_height
from platformer_player import PlatformerPlayer
from enemy import SkeletonEnemy
from spell import MagicLaser

class AnimatedGoalShard(pygame.sprite.Sprite):
    def __init__(self, pos, frames):
        super().__init__()
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 0.12
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(center=pos)

    def update(self):
        self.frame_index += self.animation_speed

        if self.frame_index >= len(self.frames):
            self.frame_index = 0

        old_center = self.rect.center
        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(center=old_center)

class PlatformerLevel:
    def __init__(self, surface, return_to_town, tmx_path, weather_type="wind", complete_level=None):
        self.display_surface = surface
        self.return_to_town = return_to_town
        self.complete_level = complete_level
        self.tmx_path = tmx_path
        self.weather_type = weather_type

        self.parallax_layers = []
        self.create_parallax_background()
        self.background_tint = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA
        )

        self.background_tint.fill((10, 20, 45, 65))

        self.tmx_data = load_pygame(self.tmx_path)
        self.source_tile_size = self.tmx_data.tilewidth
        self.draw_tile_size = 64
        self.level_width = self.tmx_data.width * self.draw_tile_size
        self.level_height = self.tmx_data.height * self.draw_tile_size
        self.y_offset = screen_height - self.level_height

        if self.y_offset < 0:
            self.y_offset = 0

        self.world_height = max(screen_height, self.y_offset + self.level_height)
        self.spawn_y = self.y_offset + self.level_height - self.draw_tile_size * 2
        self.player_start = (150, self.spawn_y)

        self.background_sprites = pygame.sprite.Group()
        self.terrain_sprites = pygame.sprite.Group()
        self.decoration_sprites = pygame.sprite.Group()
        self.goal_sprites = pygame.sprite.Group()
        self.collectable_sprites = pygame.sprite.Group()
        self.health_potion_sprites = pygame.sprite.Group()
        self.magic_potion_sprites = pygame.sprite.Group()
        self.checkpoint_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.enemy_collision_sprites = pygame.sprite.Group()
        self.spell_sprites = pygame.sprite.Group()
        self.camera_offset = pygame.math.Vector2(0, 0)

        self.collectables_collected = 0
        self.total_collectables = 0
        self.goal_locked_timer = 0
        self.checkpoints_activated = 0
        self.total_checkpoints = 0
        self.score = 0
        self.score_goal = 10000
        self.points_per_enemy = 1000
        self.keys_required = 10

        self.max_health = 100
        self.health = 100
        self.max_magic = 100
        self.magic = 50
        self.enemy_damage = self.max_health / 8

        # Stamina
        self.max_stamina = 100
        self.stamina = 100
        self.stamina_drain_rate = 10
        self.stamina_regen_rate = 5
        self.stamina_kill_reward = 20
        self.stamina_reactivate_amount = 20
        self.stamina_exhausted = False
        self.last_stamina_update = pygame.time.get_ticks()

        # Spell
        self.spell_cost = self.max_magic / 4
        self.spell_button_held = False
        self.B_BUTTON = 1

        # Death menu
        self.death_active = False
        self.death_choice_index = 0
        self.death_confirm_held = False
        self.death_last_move_time = 0
        self.death_move_delay = 180

        # Level completion screen
        self.level_complete = False
        self.level_complete_start = 0
        self.level_complete_duration = 2500

        # Revive immunity
        self.revive_immunity = False
        self.revive_immunity_start = 0
        self.revive_immunity_duration = 5000

        self.collectable_image = pygame.image.load("../graphics/terrainLevel/key_A_gold.png").convert_alpha()
        self.collectable_image = pygame.transform.scale(self.collectable_image, (42, 42))
        self.health_potion_image = pygame.image.load("../graphics/terrainLevel/potion_A_red_full.png").convert_alpha()
        self.magic_potion_image = pygame.image.load("../graphics/terrainLevel/potion_A_green_full.png").convert_alpha()
        self.health_potion_image = pygame.transform.scale(self.health_potion_image, (42, 42))
        self.magic_potion_image = pygame.transform.scale(self.magic_potion_image, (42, 42))

        self.checkpoint_sound = pygame.mixer.Sound("../audio/sfx/checkpoint/01. 1up.mp3")
        self.checkpoint_sound.set_volume(0.5)

        self.attack_sound = pygame.mixer.Sound("../audio/sfx/player/attack.mp3")
        self.hurt_sound = pygame.mixer.Sound("../audio/sfx/player/hurt.mp3")
        self.item_sound = pygame.mixer.Sound("../audio/sfx/player/item.mp3")
        self.shield_sound = pygame.mixer.Sound("../audio/sfx/player/shield.mp3")

        self.attack_sound.set_volume(0.50)
        self.hurt_sound.set_volume(0.50)
        self.item_sound.set_volume(0.35)
        self.shield_sound.set_volume(0.50)

        self.goal_frames = self.load_goal_animation()
        self.load_tmx_level()
        self.current_checkpoint = self.player_start
        self.player = PlatformerPlayer(self.player_start)

        self.weather_particles = []
        self.create_weather_particles()

    def load_goal_animation(self):
        sheet = pygame.image.load(
            "../graphics/terrainLevel/spr_coin_azu.png"
        ).convert_alpha()

        frames = []
        frame_width = 16
        frame_height = 16
        frame_count = sheet.get_width() // frame_width

        for frame_index in range(frame_count):
            frame = pygame.Surface(
                (frame_width, frame_height),
                pygame.SRCALPHA
            )

            frame.blit(
                sheet,
                (0, 0),
                pygame.Rect(
                    frame_index * frame_width,
                    0,
                    frame_width,
                    frame_height
                )
            )

            frame = pygame.transform.scale(
                frame,
                (46, 46)
            )

            frames.append(frame)

        return frames

    def check_attack_sound(self, was_attacking):
        if self.player.attacking and not was_attacking:
            self.attack_sound.play()

    def load_parallax_layer(self, path, speed):
        try:
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.scale(
                image,
                (screen_width, screen_height)
            )

            self.parallax_layers.append({
                "image": image,
                "speed": speed
            })

        except:
            print("Could not load parallax layer:", path)

    def create_parallax_background(self):
        self.parallax_layers = []

        if "level1" in self.tmx_path.lower():
            folder = "../graphics/backgrounds/level 1/"
            self.load_parallax_layer(folder + "background1.png", 0.00)
            self.load_parallax_layer(folder + "background2.png", 0.05)
            self.load_parallax_layer(folder + "background3.png", 0.12)
            self.load_parallax_layer(folder + "background4b.png", 0.20)


        elif "level2" in self.tmx_path.lower(): 
            folder = "../graphics/backgrounds/level 2/"

            self.load_parallax_layer(folder + "sky_lightened.png", 0.00)
            self.load_parallax_layer(folder + "clouds_bg.png", 0.05)
            self.load_parallax_layer(folder + "glacial_mountains_lightened.png", 0.12)
            self.load_parallax_layer(folder + "glacial_mountains.png", 0.20)
            self.load_parallax_layer(folder + "clouds_mg_3.png", 0.30)
            self.load_parallax_layer(folder + "clouds_mg_2.png", 0.42)
            self.load_parallax_layer(folder + "clouds_mg_1_lightened.png", 0.55)
            self.load_parallax_layer(folder + "clouds_mg_1.png", 0.70)
            self.load_parallax_layer(folder + "cloud_lonely.png", 0.90)

        elif "level3" in self.tmx_path.lower():
            folder = "../graphics/backgrounds/level 3/"
            self.load_parallax_layer(folder + "background_layer_1.png", 0.00)
            self.load_parallax_layer(folder + "background_layer_2.png", 0.05)
            self.load_parallax_layer(folder + "background_layer_3.png", 0.12)

        elif "level4" in self.tmx_path.lower():
            folder = "../graphics/backgrounds/level 4/"
            self.load_parallax_layer(folder + "7.png", 0.00)
            self.load_parallax_layer(folder + "6.png", 0.05)
            self.load_parallax_layer(folder + "5.png", 0.12)
            self.load_parallax_layer(folder + "4.png", 0.20)
            self.load_parallax_layer(folder + "3.png", 0.30)
            self.load_parallax_layer(folder + "2.png", 0.42)
            self.load_parallax_layer(folder + "1.png", 0.55)
        else:
            return


    def draw_parallax_background(self):
        if len(self.parallax_layers) == 0:
            self.display_surface.fill("black")
            return

        for layer in self.parallax_layers:
            image = layer["image"]
            speed = layer["speed"]

            x_offset = -self.camera_offset.x * speed
            x_offset = x_offset % screen_width

            self.display_surface.blit(
                image,
                (x_offset - screen_width, 0)
            )

            self.display_surface.blit(
                image,
                (x_offset, 0)
            )

            self.display_surface.blit(
                image,
                (x_offset + screen_width, 0)
            )

        self.display_surface.blit(
            image,
            (x_offset + screen_width, 0)
        )

        self.display_surface.blit(self.background_tint, (0, 0))

    def start_level_complete(self):
        if self.level_complete:
            return

        self.level_complete = True
        self.level_complete_start = pygame.time.get_ticks()
        self.player.direction.x = 0
        self.player.direction.y = 0
        self.player.attacking = False

        if hasattr(self.player, "spell_casting"):
            self.player.spell_casting = False

        self.player.status = "idle"
        self.player.frame_index = 0

    def draw_level_complete_screen(self):
        self.display_surface.fill((0, 0, 0))

        title_font = pygame.font.Font("EagleLake-Regular.ttf", 58)
        small_font = pygame.font.Font("EagleLake-Regular.ttf", 24)

        title = title_font.render(
            "Level Completed",
            True,
            (255, 255, 255)
        )
        title_rect = title.get_rect(
            center=(screen_width // 2, 180)
        )
        self.display_surface.blit(title, title_rect)

        if "level2" in self.tmx_path.lower():
            subtitle_message = "An enemy appeared!"
        else:
            subtitle_message = "Returning to Frostpoint..."

        subtitle = small_font.render(
            subtitle_message,
            True,
            (175, 175, 185)
        )
        subtitle_rect = subtitle.get_rect(
            center=(screen_width // 2, 245)
        )
        self.display_surface.blit(subtitle, subtitle_rect)

        idle_animation = self.player.animations["idle"]
        animation_time = pygame.time.get_ticks() // 160
        frame_index = animation_time % len(idle_animation)
        player_image = idle_animation[frame_index]

        if not self.player.facing_right:
            player_image = pygame.transform.flip(
                player_image,
                True,
                False
            )

        player_rect = player_image.get_rect(
            midbottom=(
                screen_width // 2,
                screen_height // 2 + 190
            )
        )

        shadow_rect = pygame.Rect(
            0,
            0,
            player_rect.width - 10,
            14
        )
        shadow_rect.center = (
            player_rect.centerx,
            player_rect.bottom - 3
        )

        shadow_surface = pygame.Surface(
            shadow_rect.size,
            pygame.SRCALPHA
        )
        pygame.draw.ellipse(
            shadow_surface,
            (255, 255, 255, 35),
            shadow_surface.get_rect()
        )

        self.display_surface.blit(
            shadow_surface,
            shadow_rect
        )
        self.display_surface.blit(
            player_image,
            player_rect
        )

    def update_level_complete(self):
        elapsed_time = (
            pygame.time.get_ticks()
            - self.level_complete_start
        )

        if elapsed_time >= self.level_complete_duration:
            if self.complete_level is not None:
                self.complete_level()
            else:
                self.return_to_town()

    def damage_enemy(self, enemy, amount):
        was_alive = (
            enemy.health > 0
            and not getattr(enemy, "dying", False)
        )

        enemy.take_damage(amount)

        if was_alive and enemy.health <= 0:
            if not getattr(enemy, "points_awarded", False):
                self.score += self.points_per_enemy
                enemy.points_awarded = True

                self.stamina += self.stamina_kill_reward

                if self.stamina > self.max_stamina:
                    self.stamina = self.max_stamina

    def start_death_sequence(self):
        if not self.death_active:
            self.health = 0
            self.death_active = True
            self.death_choice_index = 0 if self.magic >= self.max_magic else 1
            self.player.start_death()

    def check_player_death(self):
        if self.health <= 0:
            self.start_death_sequence()

    def revive_player(self):
        self.health = self.max_health
        self.magic = 0
        self.death_active = False
        self.revive_immunity = True
        self.revive_immunity_start = pygame.time.get_ticks()
        self.player.revive()

    def restart_level(self):
        current_tmx_path = self.tmx_path
        current_weather_type = self.weather_type
        current_complete_level = self.complete_level

        self.__init__(
            self.display_surface,
            self.return_to_town,
            current_tmx_path,
            current_weather_type,
            current_complete_level
        )

    def death_menu_move(self, direction):
        self.death_choice_index += direction
        if self.death_choice_index < 0:
            self.death_choice_index = 2

        if self.death_choice_index > 2:
            self.death_choice_index = 0

    def confirm_death_choice(self):
        if self.death_choice_index == 0:
            if self.magic >= self.max_magic:
                self.revive_player()
        elif self.death_choice_index == 1:
            self.restart_level()
        elif self.death_choice_index == 2:
            self.return_to_town()

    def handle_death_menu_input(self):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        move_direction = 0
        confirm_pressed = keys[pygame.K_SPACE] or keys[pygame.K_RETURN]

        if current_time - self.death_last_move_time >= self.death_move_delay:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                move_direction = -1
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                move_direction = 1

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            if current_time - self.death_last_move_time >= self.death_move_delay:
                if joystick.get_numhats() > 0:
                    hat_x, hat_y = joystick.get_hat(0)
                    if hat_y > 0:
                        move_direction = -1
                    elif hat_y < 0:
                        move_direction = 1

                if joystick.get_numaxes() > 1:
                    stick_y = joystick.get_axis(1)
                    if stick_y < -0.5:
                        move_direction = -1
                    elif stick_y > 0.5:
                        move_direction = 1

            if joystick.get_numbuttons() > 0:
                if joystick.get_button(0):
                    confirm_pressed = True

        if move_direction != 0:
            self.death_menu_move(move_direction)
            self.death_last_move_time = current_time

        if confirm_pressed and not self.death_confirm_held:
            self.confirm_death_choice()

        self.death_confirm_held = confirm_pressed


    def draw_death_screen(self):
        screen_copy = self.display_surface.copy()
        small_width = max(1, screen_width // 8)
        small_height = max(1, screen_height // 8)
        small_surface = pygame.transform.smoothscale(screen_copy, (small_width, small_height))
        blur_surface = pygame.transform.smoothscale(small_surface, (screen_width, screen_height))
        self.display_surface.blit(blur_surface, (0, 0))

        overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.display_surface.blit(overlay, (0, 0))

        player_offset_pos = self.player.rect.topleft - self.camera_offset
        self.display_surface.blit(self.player.image, player_offset_pos)

        box_rect = pygame.Rect(screen_width // 2 - 260, 190, 520, 300)
        pygame.draw.rect(self.display_surface, (20, 20, 30), box_rect)
        pygame.draw.rect(self.display_surface, (220, 220, 230), box_rect, 4)

        title_font = pygame.font.Font(None, 56)
        option_font = pygame.font.Font(None, 38)
        hint_font = pygame.font.Font(None, 28)
        title = title_font.render("Eira has fallen", True, (255, 255, 255))
        title_rect = title.get_rect(center=(box_rect.centerx, box_rect.y + 55))
        self.display_surface.blit(title, title_rect)

        options = [
            "Revive - Full magic required",
            "Restart level",
            "Return to town"
        ]

        for index, option in enumerate(options):
            y = box_rect.y + 120 + index * 50
            if index == 0 and self.magic < self.max_magic:
                color = (100, 100, 100)
            elif index == self.death_choice_index:
                color = (255, 230, 120)
            else:
                color = (230, 230, 230)

            label = "> " + option if index == self.death_choice_index else "  " + option
            text = option_font.render(label, True, color)
            self.display_surface.blit(text, (box_rect.x + 55, y))

        if self.magic < self.max_magic:
            magic_text = hint_font.render("Magic not full: revive unavailable", True, (150, 150, 150))
        else:
            magic_text = hint_font.render("Revive uses all magic and gives 5 seconds immunity", True, (180, 255, 180))

        self.display_surface.blit(magic_text, (box_rect.x + 55, box_rect.y + 265))

    def update_revive_immunity(self):
        if self.revive_immunity:
            current_time = pygame.time.get_ticks()
            if current_time - self.revive_immunity_start >= self.revive_immunity_duration:
                self.revive_immunity = False

    def update_stamina(self):
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_stamina_update) / 1000.0
        self.last_stamina_update = current_time

        if self.player.shielding:
            self.stamina -= self.stamina_drain_rate * delta_time

            if self.stamina <= 0:
                self.stamina = 0
                self.stamina_exhausted = True
                self.player.shield_enabled = False
                self.player.stop_shield()
        else:
            self.stamina += self.stamina_regen_rate * delta_time

            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

        if self.stamina_exhausted:
            if self.stamina >= self.stamina_reactivate_amount:
                self.stamina_exhausted = False
                self.player.shield_enabled = True
        else:
            self.player.shield_enabled = self.stamina > 0

    def clean_name(self, name):
        return name.strip().lower().replace(" ", "").replace("_", "")

    def scale_surface(self, surface):
        return pygame.transform.scale(surface, (self.draw_tile_size, self.draw_tile_size))

    def load_tmx_level(self):
        for layer in self.tmx_data.layers:
            if isinstance(layer, TiledTileLayer):
                layer_name = self.clean_name(layer.name)

                if layer_name in ["background", "bg"]:
                    self.create_visual_tile_layer(layer, self.background_sprites, False)
                elif layer_name in ["floor", "terrain"]:
                    self.create_visual_tile_layer(layer, self.terrain_sprites, True)
                elif layer_name in ["decor", "decoration", "decorations"]:
                    self.create_visual_tile_layer(layer, self.decoration_sprites, False)
                elif layer_name == "goal":
                    self.create_goal_layer(layer)
                elif layer_name in ["player", "playerstart"]:
                    self.create_player_layer(layer)
                elif layer_name in ["collectable", "collectables", "keys"]:
                    self.create_image_marker_layer(layer, self.collectable_image, self.collectable_sprites, "collectable")
                elif layer_name in ["checkpoint", "checkpoints"]:
                    self.create_checkpoint_layer(layer)
                elif layer_name in ["collision", "collisions", "enemycollision", "enemycollisions", "enemywalls"]:
                    self.create_enemy_collision_layer(layer)
                elif layer_name in ["enemy", "enemies"]:
                    self.create_enemy_layer(layer)
                elif layer_name in ["health", "healthpotion", "healthpotions"]:
                    self.create_image_marker_layer(layer, self.health_potion_image, self.health_potion_sprites, "health")
                elif layer_name in ["magic", "magicpotion", "magicpotions"]:
                    self.create_image_marker_layer(layer, self.magic_potion_image, self.magic_potion_sprites, "magic")

    def create_visual_tile_layer(self, layer, group, solid=False):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    tile_surface = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile_surface is not None:
                        x = col_index * self.draw_tile_size
                        y = row_index * self.draw_tile_size + self.y_offset
                        sprite = pygame.sprite.Sprite()
                        sprite.image = self.scale_surface(tile_surface)
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))

                        if solid:
                            solid_rect = sprite.image.get_bounding_rect()
                            sprite.collision_rect = solid_rect.move(sprite.rect.topleft)

                        group.add(sprite)

    def create_player_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset + self.draw_tile_size
                    self.player_start = (x, y)
                    return

    def create_goal_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset + self.draw_tile_size // 2

                    goal = AnimatedGoalShard(
                        (x, y),
                        self.goal_frames
                    )

                    self.goal_sprites.add(goal)

    def create_image_marker_layer(self, layer, image, group, marker_type):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = image
                    sprite.rect = sprite.image.get_rect(center=(x + self.draw_tile_size // 2, y + self.draw_tile_size // 2))
                    group.add(sprite)

                    if marker_type == "collectable":
                        self.total_collectables += 1

    def create_checkpoint_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    tile_surface = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile_surface is not None:
                        x = col_index * self.draw_tile_size
                        y = row_index * self.draw_tile_size + self.y_offset
                        sprite = pygame.sprite.Sprite()
                        sprite.image = self.scale_surface(tile_surface)
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))
                        sprite.activated = False
                        self.checkpoint_sprites.add(sprite)
                        self.total_checkpoints += 1

    def create_enemy_collision_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface((self.draw_tile_size, self.draw_tile_size), pygame.SRCALPHA)
                    sprite.rect = sprite.image.get_rect(topleft=(x, y))
                    self.enemy_collision_sprites.add(sprite)

    def create_enemy_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset + self.draw_tile_size + 3
                    enemy = SkeletonEnemy((x, y), self.enemy_collision_sprites)
                    self.enemy_sprites.add(enemy)

    def handle_spell_input(self):
        keys = pygame.key.get_pressed()
        spell_pressed = keys[pygame.K_c]

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)
            if joystick.get_numbuttons() > self.B_BUTTON:
                if joystick.get_button(self.B_BUTTON):
                    spell_pressed = True

        if spell_pressed and not self.spell_button_held:
            self.cast_spell()

        self.spell_button_held = spell_pressed

    def cast_spell(self):
        if self.magic < self.spell_cost:
            return

        if self.player.attacking or self.player.spell_casting or getattr(self.player, "dead", False):
            return

        self.magic -= self.spell_cost
        self.player.start_spell()

        if self.player.facing_right:
            start_pos = (self.player.hitbox.right + 5, self.player.hitbox.centery)
            direction = 1
        else:
            start_pos = (self.player.hitbox.left - 5, self.player.hitbox.centery)
            direction = -1

        laser = MagicLaser(start_pos, direction)
        self.spell_sprites.add(laser)

    def check_spell_enemy_collision(self):
        for laser in self.spell_sprites:
            for enemy in self.enemy_sprites:
                if getattr(enemy, "dying", False):
                    continue

                enemy_hurtbox = enemy.hurtbox if hasattr(enemy, "hurtbox") else enemy.rect
                if laser.rect.colliderect(enemy_hurtbox):
                    self.damage_enemy(enemy, 999)
                    laser.kill()
                    break

    def create_weather_particles(self):
        self.weather_particles = []

        if self.weather_type == "heavy_snow":
            particle_count = 350

            for i in range(particle_count):
                particle = {
                    "x": random.randint(0, self.level_width),
                    "y": random.randint(0, self.world_height),
                    "speed": random.uniform(2.0, 4.5),
                    "drift": random.uniform(-0.8, 0.8),
                    "size": random.randint(2, 5),
                    "alpha": random.randint(120, 210)
                }
                self.weather_particles.append(particle)

        elif self.weather_type == "light_snow":
            particle_count = 160

            for i in range(particle_count):
                particle = {
                    "x": random.randint(0, self.level_width),
                    "y": random.randint(0, self.world_height),
                    "speed": random.uniform(0.8, 1.8),
                    "drift": random.uniform(-0.35, 0.35),
                    "size": random.randint(1, 3),
                    "alpha": random.randint(80, 150)
                }
                self.weather_particles.append(particle)

        elif self.weather_type == "light_rain":
            particle_count = 220

            for i in range(particle_count):
                particle = {
                    "x": random.randint(0, self.level_width),
                    "y": random.randint(0, self.world_height),
                    "speed": random.uniform(7.0, 11.0),
                    "drift": random.uniform(-1.8, -0.6),
                    "length": random.randint(10, 18),
                    "alpha": random.randint(70, 130)
                }
                self.weather_particles.append(particle)

        elif self.weather_type == "cave_drips":
            particle_count = 90

            for i in range(particle_count):
                particle = {
                    "x": random.randint(0, self.level_width),
                    "y": random.randint(-self.world_height, self.world_height),
                    "speed": random.uniform(3.0, 7.0),
                    "drift": random.uniform(-0.15, 0.15),
                    "length": random.randint(4, 9),
                    "alpha": random.randint(90, 170),
                    "size": random.randint(1, 2)
                }
                self.weather_particles.append(particle)

    def draw_weather(self):
        if self.weather_type == "none":
            return

        weather_surface = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA
        )

        for particle in self.weather_particles:
            particle["x"] += particle["drift"]
            particle["y"] += particle["speed"]

            if particle["y"] > self.world_height:
                particle["y"] = random.randint(-120, -10)
                particle["x"] = random.randint(0, self.level_width)

            if particle["x"] < 0:
                particle["x"] = self.level_width

            if particle["x"] > self.level_width:
                particle["x"] = 0

            screen_x = particle["x"] - self.camera_offset.x
            screen_y = particle["y"] - self.camera_offset.y

            if -100 < screen_x < screen_width + 100 and -100 < screen_y < screen_height + 100:
                if self.weather_type == "light_rain":
                    pygame.draw.line(
                        weather_surface,
                        (150, 175, 205, particle["alpha"]),
                        (int(screen_x), int(screen_y)),
                        (
                            int(screen_x - 3),
                            int(screen_y + particle["length"])
                        ),
                        1
                    )

                elif self.weather_type == "cave_drips":
                    pygame.draw.line(
                        weather_surface,
                        (120, 155, 190, particle["alpha"]),
                        (int(screen_x), int(screen_y)),
                        (
                            int(screen_x),
                            int(screen_y + particle["length"])
                        ),
                        1
                    )

                    pygame.draw.circle(
                        weather_surface,
                        (150, 185, 220, particle["alpha"]),
                        (
                            int(screen_x),
                            int(screen_y + particle["length"])
                        ),
                        particle["size"]
                    )

                else:
                    pygame.draw.circle(
                        weather_surface,
                        (235, 235, 240, particle["alpha"]),
                        (int(screen_x), int(screen_y)),
                        particle["size"]
                    )

        self.display_surface.blit(weather_surface, (0, 0))

    def draw_player_bars(self):
        bar_x = 30
        bar_y = 25
        bar_width = 220
        bar_height = 18
        gap = 8

        health_ratio = self.health / self.max_health
        magic_ratio = self.magic / self.max_magic
        stamina_ratio = self.stamina / self.max_stamina

        health_back = pygame.Rect(
            bar_x,
            bar_y,
            bar_width,
            bar_height
        )
        health_fill = pygame.Rect(
            bar_x,
            bar_y,
            int(bar_width * health_ratio),
            bar_height
        )

        magic_y = bar_y + bar_height + gap
        magic_back = pygame.Rect(
            bar_x,
            magic_y,
            bar_width,
            bar_height
        )
        magic_fill = pygame.Rect(
            bar_x,
            magic_y,
            int(bar_width * magic_ratio),
            bar_height
        )

        stamina_y = magic_y + bar_height + gap
        stamina_back = pygame.Rect(
            bar_x,
            stamina_y,
            bar_width,
            bar_height
        )
        stamina_fill = pygame.Rect(
            bar_x,
            stamina_y,
            int(bar_width * stamina_ratio),
            bar_height
        )

        pygame.draw.rect(
            self.display_surface,
            (35, 35, 45),
            health_back
        )
        pygame.draw.rect(
            self.display_surface,
            (180, 40, 40),
            health_fill
        )
        pygame.draw.rect(
            self.display_surface,
            (230, 230, 230),
            health_back,
            3
        )

        pygame.draw.rect(
            self.display_surface,
            (35, 35, 45),
            magic_back
        )
        pygame.draw.rect(
            self.display_surface,
            (60, 180, 80),
            magic_fill
        )
        pygame.draw.rect(
            self.display_surface,
            (230, 230, 230),
            magic_back,
            3
        )

        pygame.draw.rect(
            self.display_surface,
            (35, 35, 45),
            stamina_back
        )
        pygame.draw.rect(
            self.display_surface,
            (210, 170, 60),
            stamina_fill
        )
        pygame.draw.rect(
            self.display_surface,
            (230, 230, 230),
            stamina_back,
            3
        )

    def horizontal_movement_collision(self):
        player = self.player
        player.hitbox.x += player.direction.x * player.speed

        for sprite in self.terrain_sprites:
            if sprite.collision_rect.colliderect(player.hitbox):
                if player.direction.x < 0:
                    player.hitbox.left = sprite.collision_rect.right
                elif player.direction.x > 0:
                    player.hitbox.right = sprite.collision_rect.left

        player.sync_rect_to_hitbox()

    def vertical_movement_collision(self):
        player = self.player
        player.on_ground = False
        player.on_ceiling = False
        player.apply_gravity()

        for sprite in self.terrain_sprites:
            if sprite.collision_rect.colliderect(player.hitbox):
                if player.direction.y > 0:
                    player.hitbox.bottom = sprite.collision_rect.top
                    player.direction.y = 0
                    player.on_ground = True
                elif player.direction.y < 0:
                    player.hitbox.top = sprite.collision_rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True

        player.sync_rect_to_hitbox()

    def enemy_body_collision(self):
        player = self.player
        for enemy in self.enemy_sprites:
            if getattr(enemy, "dying", False):
                continue

            if hasattr(enemy, "body_rect"):
                enemy_body = enemy.body_rect
            elif hasattr(enemy, "hurtbox"):
                enemy_body = enemy.hurtbox
            else:
                enemy_body = enemy.rect.inflate(-90, -20)

            if enemy_body.colliderect(player.hitbox):
                overlap_left = player.hitbox.right - enemy_body.left
                overlap_right = enemy_body.right - player.hitbox.left
                overlap_top = player.hitbox.bottom - enemy_body.top
                overlap_bottom = enemy_body.bottom - player.hitbox.top
                min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)

                if min_overlap == overlap_left:
                    player.hitbox.right = enemy_body.left
                elif min_overlap == overlap_right:
                    player.hitbox.left = enemy_body.right
                elif min_overlap == overlap_top:
                    player.hitbox.bottom = enemy_body.top
                    player.direction.y = 0
                    player.on_ground = True
                elif min_overlap == overlap_bottom:
                    player.hitbox.top = enemy_body.bottom
                    player.direction.y = 0

        player.sync_rect_to_hitbox()

    def check_player_attack_enemy(self):
        if self.player.attacking:
            for enemy in self.enemy_sprites:
                if getattr(enemy, "dying", False):
                    continue

                enemy_hurtbox = enemy.hurtbox if hasattr(enemy, "hurtbox") else enemy.rect
                if self.player.attack_rect.colliderect(enemy_hurtbox):
                    if enemy not in self.player.enemies_hit_this_attack:
                        self.damage_enemy(enemy, self.player.attack_damage)
                        self.player.enemies_hit_this_attack.append(enemy)

    def check_enemy_damage(self):
        if self.revive_immunity:
            return

        for enemy in self.enemy_sprites:
            if getattr(enemy, "dying", False):
                continue

            if not hasattr(enemy, "can_damage_player"):
                continue

            if enemy.can_damage_player(self.player):
                # Consume this enemy swing either way
                enemy.attack_has_hit_player = True

                # Shield blocks all damage
                if getattr(self.player, "shielding", False):
                    self.shield_sound.play()
                    continue

                self.hurt_sound.play()
                self.health -= self.enemy_damage

                if self.health < 0:
                    self.health = 0

    def check_potions(self):
        for potion in self.health_potion_sprites:
            if potion.rect.colliderect(self.player.hitbox):
                potion.kill()
                self.item_sound.play()
                self.health += 25

                if self.health > self.max_health:
                    self.health = self.max_health

        for potion in self.magic_potion_sprites:
            if potion.rect.colliderect(self.player.hitbox):
                potion.kill()
                self.item_sound.play()
                self.magic += 25

                if self.magic > self.max_magic:
                    self.magic = self.max_magic

        for potion in self.magic_potion_sprites:
            if potion.rect.colliderect(self.player.hitbox):
                potion.kill()
                self.magic += 25
                if self.magic > self.max_magic:
                    self.magic = self.max_magic

    def check_collectables(self):
        for collectable in self.collectable_sprites:
            if collectable.rect.colliderect(self.player.hitbox):
                collectable.kill()
                self.collectables_collected += 1
                self.item_sound.play()

    def check_checkpoints(self):
        for checkpoint in self.checkpoint_sprites:
            if checkpoint.rect.colliderect(self.player.hitbox):
                self.current_checkpoint = checkpoint.rect.midbottom
                if not checkpoint.activated:
                    checkpoint.activated = True
                    self.checkpoints_activated += 1
                    self.checkpoint_sound.play()

    def check_goal(self):
        has_enough_keys = (
            self.collectables_collected
            >= self.keys_required
        )
        has_enough_points = (
            self.score
            >= self.score_goal
        )

        for goal in self.goal_sprites:
            if goal.rect.colliderect(self.player.hitbox):
                if has_enough_keys or has_enough_points:
                    self.start_level_complete()
                else:
                    self.goal_locked_timer = 120

    def reset_player_if_fallen(self):
        if self.player.hitbox.top > self.world_height + 300:
            self.player.hitbox.midbottom = self.current_checkpoint
            self.player.direction.y = 0
            self.player.sync_rect_to_hitbox()

    def update_camera(self):
        target_x = self.player.hitbox.centerx - screen_width // 2
        target_y = self.player.hitbox.centery - screen_height // 2
        max_x = max(0, self.level_width - screen_width)
        max_y = max(0, self.world_height - screen_height)
        self.camera_offset.x = max(0, min(target_x, max_x))
        self.camera_offset.y = max(0, min(target_y, max_y))

    def draw_sprite_group(self, group):
        for sprite in group:
            offset_x = sprite.rect.x - self.camera_offset.x
            offset_y = sprite.rect.y - self.camera_offset.y
            self.display_surface.blit(sprite.image, (offset_x, offset_y))

    def draw_level(self):
        self.draw_parallax_background()
        self.draw_sprite_group(self.background_sprites)
        self.draw_sprite_group(self.terrain_sprites)
        self.draw_sprite_group(self.decoration_sprites)
        self.draw_sprite_group(self.goal_sprites)
        self.draw_sprite_group(self.collectable_sprites)
        self.draw_sprite_group(self.health_potion_sprites)
        self.draw_sprite_group(self.magic_potion_sprites)
        self.draw_sprite_group(self.checkpoint_sprites)
        self.draw_sprite_group(self.enemy_sprites)
        self.draw_sprite_group(self.spell_sprites)

        player_offset_x = self.player.rect.x - self.camera_offset.x
        player_offset_y = self.player.rect.y - self.camera_offset.y
        self.display_surface.blit(self.player.image, (player_offset_x, player_offset_y))

        self.draw_weather()
        self.draw_player_bars()

        font = pygame.font.Font(None, 36)

        score_text = font.render(
            "Points: " + str(self.score) + "/" + str(self.score_goal),
            True,
            (255, 255, 255)
        )
        self.display_surface.blit(score_text, (30, 115))

        key_text = font.render(
            "Keys: " + str(self.collectables_collected) + "/" + str(self.keys_required),
            True,
            (255, 255, 255)
        )
        self.display_surface.blit(key_text, (30, 155))

        checkpoint_text = font.render(
            "Checkpoints: " + str(self.checkpoints_activated) + "/" + str(self.total_checkpoints),
            True,
            (255, 255, 255)
        )
        self.display_surface.blit(checkpoint_text, (30, 195))

        if self.goal_locked_timer > 0:
            locked_text = font.render(
                "You need 10 keys or 10,000 points!",
                True,
                (255, 230, 120)
            )
            self.display_surface.blit(locked_text, (30, 235))
            self.goal_locked_timer -= 1

    def run(self):
        if self.death_active:
            self.player.update_death()
            self.update_camera()
            self.draw_level()
            self.draw_death_screen()
            self.handle_death_menu_input()
            return
        if self.level_complete:
            self.draw_level_complete_screen()
            self.update_level_complete()
            return

        self.update_revive_immunity()
        self.handle_spell_input()

        was_attacking = self.player.attacking
        self.player.update()
        self.check_attack_sound(was_attacking)

        self.update_stamina()

        self.horizontal_movement_collision()
        self.vertical_movement_collision()
        self.enemy_sprites.update(self.player)
        self.enemy_body_collision()
        
        self.spell_sprites.update()
        self.goal_sprites.update()
        self.check_spell_enemy_collision()
        self.check_player_attack_enemy()
        self.check_potions()
        self.check_collectables()
        self.check_enemy_damage()
        self.check_player_death()
        self.check_checkpoints()
        self.check_goal()
        self.reset_player_if_fallen()
        self.update_camera()
        self.draw_level()