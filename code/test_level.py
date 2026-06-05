# test_level.py
import pygame
import random

from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer
from settings import screen_width, screen_height
from platformer_player import PlatformerPlayer
from enemy import SkeletonEnemy
from spell import MagicLaser

class TestLevel:
    def __init__(self, surface, return_to_town):
        self.display_surface = surface
        self.return_to_town = return_to_town
        self.tmx_path = "../mapData/levels/test.tmx"
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

        self.max_health = 100
        self.health = 100
        self.max_magic = 100
        self.magic = 50
        self.enemy_damage = self.max_health / 8

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

        self.load_tmx_level()
        self.current_checkpoint = self.player_start
        self.player = PlatformerPlayer(self.player_start)

        self.wind_particles = []
        for i in range(90):
            particle = {
                "x": random.randint(-100, screen_width + 200),
                "y": random.randint(0, screen_height),
                "speed": random.uniform(2.0, 3.8),
                "length": random.randint(35, 80),
                "alpha": random.randint(55, 95),
                "drift": random.uniform(-0.12, 0.12)
            }
            self.wind_particles.append(particle)

        for i in range(180):
            particle = {
                "x": random.randint(0, self.level_width),
                "y": random.randint(0, self.world_height),
                "speed": random.uniform(2.0, 3.8),
                "length": random.randint(35, 80),
                "alpha": random.randint(45, 85),
                "drift": random.uniform(-0.12, 0.12)
            }
            self.wind_particles.append(particle)

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
        self.__init__(self.display_surface, self.return_to_town)

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
                    self.create_visual_tile_layer(layer, self.goal_sprites, False)
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
                    enemy.take_damage(999)
                    laser.kill()
                    break

    def draw_wind(self):
        wind_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        for particle in self.wind_particles:
            particle["x"] += particle["speed"]
            particle["y"] += particle["drift"]

            if particle["x"] > self.level_width + particle["length"]:
                particle["x"] = random.randint(-250, -50)
                particle["y"] = random.randint(0, self.world_height)
                particle["speed"] = random.uniform(2.0, 3.8)
                particle["length"] = random.randint(35, 80)
                particle["alpha"] = random.randint(45, 90)

            if particle["y"] < 0:
                particle["y"] = self.world_height

            if particle["y"] > self.world_height:
                particle["y"] = 0

            screen_x = particle["x"] - self.camera_offset.x
            screen_y = particle["y"] - self.camera_offset.y

            if -100 < screen_x < screen_width + 100 and -30 < screen_y < screen_height + 30:
                x = int(screen_x)
                y = int(screen_y)
                length = particle["length"]
                alpha = particle["alpha"]
                for i in range(3):
                    offset_y = random.randint(-2, 2)
                    offset_x = random.randint(-3, 3)
                    start_pos = (x + offset_x, y + offset_y)
                    end_pos = (x + int(length * random.uniform(0.45, 0.75)), y + offset_y - random.randint(1, 3))
                    pygame.draw.line(wind_surface, (230, 230, 230, alpha // 3), start_pos, end_pos, 1)

        self.display_surface.blit(wind_surface, (0, 0))

    def draw_player_bars(self):
        bar_x = 30
        bar_y = 25
        bar_width = 220
        bar_height = 18
        gap = 8
        health_ratio = self.health / self.max_health
        magic_ratio = self.magic / self.max_magic

        health_back = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        health_fill = pygame.Rect(bar_x, bar_y, int(bar_width * health_ratio), bar_height)
        magic_back = pygame.Rect(bar_x, bar_y + bar_height + gap, bar_width, bar_height)
        magic_fill = pygame.Rect(bar_x, bar_y + bar_height + gap, int(bar_width * magic_ratio), bar_height)

        pygame.draw.rect(self.display_surface, (35, 35, 45), health_back)
        pygame.draw.rect(self.display_surface, (180, 40, 40), health_fill)
        pygame.draw.rect(self.display_surface, (230, 230, 230), health_back, 3)
        pygame.draw.rect(self.display_surface, (35, 35, 45), magic_back)
        pygame.draw.rect(self.display_surface, (60, 180, 80), magic_fill)
        pygame.draw.rect(self.display_surface, (230, 230, 230), magic_back, 3)

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
                        enemy.take_damage(self.player.attack_damage)
                        self.player.enemies_hit_this_attack.append(enemy)

    def check_enemy_damage(self):
        if hasattr(self, "revive_immunity"):
            if self.revive_immunity:
                return

        for enemy in self.enemy_sprites:
            if getattr(enemy, "dying", False):
                continue

            if hasattr(enemy, "can_damage_player"):
                if enemy.can_damage_player(self.player):
                    self.health -= self.enemy_damage
                    enemy.attack_has_hit_player = True
                    if self.health < 0:
                        self.health = 0

    def check_potions(self):
        for potion in self.health_potion_sprites:
            if potion.rect.colliderect(self.player.hitbox):
                potion.kill()
                self.health += 25
                if self.health > self.max_health:
                    self.health = self.max_health

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

    def check_checkpoints(self):
        for checkpoint in self.checkpoint_sprites:
            if checkpoint.rect.colliderect(self.player.hitbox):
                self.current_checkpoint = checkpoint.rect.midbottom
                if not checkpoint.activated:
                    checkpoint.activated = True
                    self.checkpoints_activated += 1
                    self.checkpoint_sound.play()

    def check_goal(self):
        for goal in self.goal_sprites:
            if goal.rect.colliderect(self.player.hitbox):
                if self.collectables_collected >= self.total_collectables:
                    self.return_to_town()
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
        self.display_surface.fill((25, 25, 35))
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

        self.draw_wind()
        self.draw_player_bars()

        font = pygame.font.Font(None, 36)
        text = font.render("Keys: " + str(self.collectables_collected) + "/" + str(self.total_collectables), True, (255, 255, 255))
        self.display_surface.blit(text, (30, 85))

        checkpoint_text = font.render(
            "Checkpoints: " + str(self.checkpoints_activated) + "/" + str(self.total_checkpoints),
            True,
            (255, 255, 255)
        )
        self.display_surface.blit(checkpoint_text, (30, 125))

        if self.goal_locked_timer > 0:
            locked_text = font.render("You need all 10 keys first!", True, (255, 230, 120))
            self.display_surface.blit(locked_text, (30, 165))
            self.goal_locked_timer -= 1

    def run(self):
        if self.death_active:
            self.player.update_death()
            self.update_camera()
            self.draw_level()
            self.draw_death_screen()
            self.handle_death_menu_input()
            return

        self.update_revive_immunity()
        self.handle_spell_input()
        self.player.update()
        self.horizontal_movement_collision()
        self.vertical_movement_collision()

        if hasattr(self, "enemy_body_collision"):
            self.enemy_body_collision()

        self.enemy_sprites.update(self.player)
        self.spell_sprites.update()
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