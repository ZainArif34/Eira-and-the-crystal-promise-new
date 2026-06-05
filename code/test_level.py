# test_level.py
import pygame
import random

from support import import_csv_layout
from settings import screen_width, screen_height
from platformer_player import PlatformerPlayer
from enemy import SkeletonEnemy

class TestLevel:
    def __init__(self, surface, return_to_town):
        self.display_surface = surface
        self.return_to_town = return_to_town
        self.source_tile_size = 32
        self.draw_tile_size = 64
        self.floor_csv_path = "../mapData/levels/test/test_floor.csv"
        self.player_csv_path = "../mapData/levels/test/test_player.csv"
        self.goal_csv_path = "../mapData/levels/test/test_goal.csv"
        self.collectable_csv_path = "../mapData/levels/test/test_collectable.csv"
        self.checkpoint_csv_path = "../mapData/levels/test/test_checkpoint.csv"
        self.enemy_csv_path = "../mapData/levels/test/test_enemies.csv"
        self.enemy_collision_csv_path = "../mapData/levels/test/test_collisions.csv"
        self.health_csv_path = "../mapData/levels/test/test_health.csv"
        self.magic_csv_path = "../mapData/levels/test/test_magic.csv"
        self.tileset_path = "../graphics/terrainlevel/Terrain (32x32).png"
        self.decorations_tileset_path = "../graphics/terrainlevel/Decorations (32x32).png"
        self.tiles = self.import_tileset(self.tileset_path)
        self.decoration_tiles = self.import_tileset(self.decorations_tileset_path)
        self.terrain_sprites = pygame.sprite.Group()
        self.goal_sprites = pygame.sprite.Group()
        self.collectable_sprites = pygame.sprite.Group()
        self.health_potion_sprites = pygame.sprite.Group()
        self.magic_potion_sprites = pygame.sprite.Group()
        self.health_potion_image = pygame.image.load("../graphics/terrainLevel/potion_A_red_full.png").convert_alpha()
        self.magic_potion_image = pygame.image.load("../graphics/terrainLevel/potion_A_green_full.png").convert_alpha()
        self.health_potion_image = pygame.transform.scale(self.health_potion_image, (42, 42))
        self.magic_potion_image = pygame.transform.scale(self.magic_potion_image, (42, 42))
        self.checkpoint_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.enemy_collision_sprites = pygame.sprite.Group()
        self.camera_offset = pygame.math.Vector2(0, 0)
        self.collectables_collected = 0
        self.total_collectables = 0
        self.collectable_image = pygame.image.load("../graphics/terrainLevel/key_A_gold.png").convert_alpha()
        self.collectable_image = pygame.transform.scale(self.collectable_image, (42, 42))
        self.goal_locked_timer = 0
        self.checkpoints_activated = 0
        self.total_checkpoints = 0

        # Player stats
        self.max_health = 100
        self.health = 100
        self.max_magic = 100
        self.magic = 50

        # Enemy damage
        self.enemy_damage = self.max_health / 8
        self.enemy_damage_cooldown = 800
        self.last_enemy_damage_time = 0

        # Checkpoint sound effect
        self.checkpoint_sound = pygame.mixer.Sound("../audio/sfx/checkpoint/01. 1up.mp3")
        self.checkpoint_sound.set_volume(0.5)

        self.create_level(self.floor_csv_path)
        self.create_goal_layer(self.goal_csv_path)
        self.create_collectable_layer(self.collectable_csv_path)
        self.create_checkpoint_layer(self.checkpoint_csv_path)
        self.create_enemy_collision_layer(self.enemy_collision_csv_path)
        self.create_enemy_layer(self.enemy_csv_path)
        self.create_health_potion_layer(self.health_csv_path)
        self.create_magic_potion_layer(self.magic_csv_path)
              

        spawn_pos = self.get_player_spawn(self.player_csv_path)
        self.current_checkpoint = spawn_pos
        self.player = PlatformerPlayer(spawn_pos)

        # Wind effect
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

    def check_enemy_damage(self):
        for enemy in self.enemy_sprites:
            if getattr(enemy, "dying", False):
                continue

            if enemy.can_damage_player(self.player):
                self.health -= self.enemy_damage
                enemy.attack_has_hit_player = True
                if self.health < 0:
                    self.health = 0

    def enemy_body_collision(self):
        player = self.player
        for enemy in self.enemy_sprites:
            if getattr(enemy, "dying", False):
                continue

            enemy_body = enemy.body_rect if hasattr(enemy, "body_rect") else enemy.rect.inflate(-90, -20)
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

                enemy_hurtbox = (
                    enemy.hurtbox
                    if hasattr(enemy, "hurtbox")
                    else enemy.rect
                )

                if self.player.attack_rect.colliderect(enemy_hurtbox):
                    if enemy not in self.player.enemies_hit_this_attack:
                        enemy.take_damage(self.player.attack_damage)
                        self.player.enemies_hit_this_attack.append(enemy)

    def create_enemy_collision_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface((self.draw_tile_size, self.draw_tile_size), pygame.SRCALPHA)
                    sprite.rect = sprite.image.get_rect(topleft=(x, y))
                    self.enemy_collision_sprites.add(sprite)

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

    def import_tileset(self, path):
        tileset_surface = pygame.image.load(path).convert_alpha()
        tiles = []
        columns = tileset_surface.get_width() // self.source_tile_size
        rows = tileset_surface.get_height() // self.source_tile_size
        for row in range(rows):
            for col in range(columns):
                x = col * self.source_tile_size
                y = row * self.source_tile_size
                tile_surface = pygame.Surface((self.source_tile_size, self.source_tile_size), pygame.SRCALPHA)
                tile_surface.blit(
                    tileset_surface,
                    (0, 0),
                    pygame.Rect(x, y, self.source_tile_size, self.source_tile_size)
                )
                scaled_tile = pygame.transform.scale(tile_surface, (self.draw_tile_size, self.draw_tile_size))
                tiles.append(scaled_tile)

        return tiles

    def create_health_potion_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = self.health_potion_image
                    sprite.rect = sprite.image.get_rect(center=(x + self.draw_tile_size // 2, y + self.draw_tile_size // 2))
                    self.health_potion_sprites.add(sprite)

    def create_magic_potion_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = self.magic_potion_image
                    sprite.rect = sprite.image.get_rect(center=(x + self.draw_tile_size // 2, y + self.draw_tile_size // 2))
                    self.magic_potion_sprites.add(sprite)

    def create_level(self, path):
        layout = import_csv_layout(path)
        self.level_width = len(layout[0]) * self.draw_tile_size
        self.level_height = len(layout) * self.draw_tile_size
        self.y_offset = screen_height - self.level_height
        if self.y_offset < 0:
            self.y_offset = 0

        self.world_height = max(screen_height, self.y_offset + self.level_height)
        self.spawn_y = self.y_offset + self.level_height - self.draw_tile_size * 2
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    tile_index = int(val)
                    if 0 <= tile_index < len(self.tiles):
                        x = col_index * self.draw_tile_size
                        y = row_index * self.draw_tile_size + self.y_offset
                        sprite = pygame.sprite.Sprite()
                        sprite.image = self.tiles[tile_index]
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))
                        solid_rect = sprite.image.get_bounding_rect()
                        sprite.collision_rect = solid_rect.move(sprite.rect.topleft)
                        self.terrain_sprites.add(sprite)

    def create_enemy_collision_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface((self.draw_tile_size, self.draw_tile_size), pygame.SRCALPHA)
                    sprite.rect = sprite.image.get_rect(topleft=(x, y))
                    self.enemy_collision_sprites.add(sprite)

    def get_player_spawn(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset + self.draw_tile_size
                    return (x, y)

        return (150, self.spawn_y)

    def create_goal_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    tile_index = int(val)
                    if 0 <= tile_index < len(self.decoration_tiles):
                        x = col_index * self.draw_tile_size
                        y = row_index * self.draw_tile_size + self.y_offset
                        sprite = pygame.sprite.Sprite()
                        sprite.image = self.decoration_tiles[tile_index]
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))
                        self.goal_sprites.add(sprite)

    def create_collectable_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = self.collectable_image
                    sprite.rect = sprite.image.get_rect(
                        center=(
                            x + self.draw_tile_size // 2,
                            y + self.draw_tile_size // 2
                        )
                    )
                    self.collectable_sprites.add(sprite)
                    self.total_collectables += 1

    def create_checkpoint_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    tile_index = int(val)
                    if 0 <= tile_index < len(self.decoration_tiles):
                        x = col_index * self.draw_tile_size
                        y = row_index * self.draw_tile_size + self.y_offset
                        sprite = pygame.sprite.Sprite()
                        sprite.image = self.decoration_tiles[tile_index]
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))
                        sprite.activated = False
                        self.checkpoint_sprites.add(sprite)
                        self.total_checkpoints += 1

    def create_enemy_layer(self, path):
        layout = import_csv_layout(path)
        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()
                if val != "-1" and val != "":
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset + self.draw_tile_size + 3
                    enemy = SkeletonEnemy((x, y), self.enemy_collision_sprites)
                    self.enemy_sprites.add(enemy)

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

    def check_goal(self):
        for goal in self.goal_sprites:
            if goal.rect.colliderect(self.player.hitbox):
                if self.collectables_collected >= self.total_collectables:
                    self.return_to_town()
                else:
                    self.goal_locked_timer = 120

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

    def update_camera(self):
        target_x = self.player.hitbox.centerx - screen_width // 2
        target_y = self.player.hitbox.centery - screen_height // 2
        max_x = max(0, self.level_width - screen_width)
        max_y = max(0, self.world_height - screen_height)
        self.camera_offset.x = max(0, min(target_x, max_x))
        self.camera_offset.y = max(0, min(target_y, max_y))

    def draw_sprite_group(self, group):
        for sprite in group:
            offset_pos = sprite.rect.topleft - self.camera_offset
            self.display_surface.blit(sprite.image, offset_pos)

    def draw_level(self):
        self.display_surface.fill((25, 25, 35))
        self.draw_sprite_group(self.terrain_sprites)
        self.draw_sprite_group(self.goal_sprites)
        self.draw_sprite_group(self.collectable_sprites)
        self.draw_sprite_group(self.health_potion_sprites)
        self.draw_sprite_group(self.magic_potion_sprites)
        self.draw_sprite_group(self.checkpoint_sprites)
        self.draw_sprite_group(self.enemy_sprites)

        player_offset_pos = self.player.rect.topleft - self.camera_offset
        self.display_surface.blit(self.player.image, player_offset_pos)

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

    def reset_player_if_fallen(self):
        if self.player.hitbox.top > self.world_height + 300:
            self.player.hitbox.midbottom = self.current_checkpoint
            self.player.direction.y = 0
            self.player.sync_rect_to_hitbox()

    def run(self):
        self.player.update()
        self.enemy_sprites.update(self.player)
        self.check_player_attack_enemy()
        self.horizontal_movement_collision()
        self.vertical_movement_collision()
        self.enemy_body_collision()
        self.check_potions()
        self.check_collectables()
        self.check_enemy_damage()
        self.check_checkpoints()
        self.check_goal()
        self.reset_player_if_fallen()
        self.update_camera()
        self.draw_level()