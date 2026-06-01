# house.py
import pygame
from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer, TiledObjectGroup
from settings import tile_size, screen_width, screen_height
from player import Player
from NPCS import NPC

class House:
    def __init__(self, surface, tmx_path):
        self.display_surface = surface
        self.tmx_path = tmx_path
        self.tmx_data = load_pygame(self.tmx_path)
        self.scale_factor = tile_size / self.tmx_data.tilewidth
        self.sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.exits = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()
        self.map_width = self.tmx_data.width * tile_size
        self.map_height = self.tmx_data.height * tile_size
        self.offset_x = (screen_width - self.map_width) // 2
        self.offset_y = (screen_height - self.map_height) // 2
        self.left_limit = self.offset_x
        self.right_limit = self.offset_x + self.map_width
        self.top_limit = self.offset_y
        self.bottom_limit = self.offset_y + self.map_height
        self.player_start = (
            self.offset_x + tile_size,
            self.offset_y + self.map_height - tile_size
        )
        self.load_house()
        self.player = Player(self.player_start, self.obstacles)

    def clean_name(self, name):
        return name.strip().lower().replace(" ", "")

    def scale_surface(self, surface):
        if surface.get_width() == tile_size and surface.get_height() == tile_size:
            return surface
        return pygame.transform.scale(surface, (tile_size, tile_size))

    def load_house(self):
        for layer in self.tmx_data.layers:
            layer_name = self.clean_name(layer.name)

            if isinstance(layer, TiledTileLayer):
                if layer_name in ["collisions", "collision"]:
                    self.create_collision_tile_layer(layer)
                elif layer_name in ["playerstart", "player"]:
                    self.create_player_start_tile_layer(layer)
                elif layer_name in ["exit", "exits"]:
                    self.create_exit_tile_layer(layer)
                elif layer_name in ["npcs", "npc"]:
                    self.create_npc_tile_layer(layer)
                else:
                    self.create_visual_layer(layer)

            elif isinstance(layer, TiledObjectGroup):
                if layer_name in ["collisions", "collision"]:
                    self.create_collision_object_layer(layer)
                elif layer_name in ["playerstart", "player"]:
                    self.create_player_start_object_layer(layer)
                elif layer_name in ["exit", "exits"]:
                    self.create_exit_object_layer(layer)

    def create_visual_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    tile_surf = self.tmx_data.get_tile_image_by_gid(gid)

                    if tile_surf is not None:
                        tile_surf = self.scale_surface(tile_surf)
                        x = col_index * tile_size + self.offset_x
                        y = row_index * tile_size + self.offset_y
                        sprite = pygame.sprite.Sprite()
                        sprite.image = tile_surf
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))
                        self.sprites.add(sprite)

    def create_collision_tile_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * tile_size + self.offset_x
                    y = row_index * tile_size + self.offset_y
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                    sprite.rect = pygame.Rect(x, y, tile_size, tile_size)
                    self.obstacles.add(sprite)

    def create_exit_tile_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * tile_size + self.offset_x
                    y = row_index * tile_size + self.offset_y
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                    sprite.rect = pygame.Rect(x, y, tile_size, tile_size)
                    self.exits.add(sprite)

    def create_player_start_tile_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * tile_size + tile_size // 2 + self.offset_x
                    y = row_index * tile_size + tile_size + self.offset_y
                    self.player_start = (x, y)
                    return

    def create_npc_tile_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    marker_x = col_index * tile_size + self.offset_x
                    marker_y = row_index * tile_size + self.offset_y

                    npc_x = marker_x - tile_size
                    npc_y = marker_y - tile_size * 2

                    dialogue = [
                        "Welcome to Frostpoint.",
                        "The winter has lasted years.",
                        "People fear the crystal...",
                        "Would you like to enter the test level?"
                    ]

                    npc = NPC(
                        (npc_x, npc_y),
                        [self.npcs],
                        "Villager",
                        dialogue,
                        "test"
                    )

                    self.obstacles.add(npc)

    def create_collision_object_layer(self, layer):
        for obj in layer:
            rect = pygame.Rect(
                int(obj.x * self.scale_factor) + self.offset_x,
                int(obj.y * self.scale_factor) + self.offset_y,
                int(obj.width * self.scale_factor),
                int(obj.height * self.scale_factor)
            )
            sprite = pygame.sprite.Sprite()
            sprite.image = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            sprite.rect = rect
            self.obstacles.add(sprite)

    def create_exit_object_layer(self, layer):
        for obj in layer:
            rect = pygame.Rect(
                int(obj.x * self.scale_factor) + self.offset_x,
                int(obj.y * self.scale_factor) + self.offset_y,
                int(obj.width * self.scale_factor),
                int(obj.height * self.scale_factor)
            )
            sprite = pygame.sprite.Sprite()
            sprite.image = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            sprite.rect = rect
            self.exits.add(sprite)

    def create_player_start_object_layer(self, layer):
        for obj in layer:
            x = int(obj.x * self.scale_factor) + self.offset_x
            y = int(obj.y * self.scale_factor) + self.offset_y
            self.player_start = (x, y)
            return

    def check_exit_interaction(self):
        interact_rect = self.player.hitbox.inflate(40, 40)

        for exit_sprite in self.exits:
            if interact_rect.colliderect(exit_sprite.rect):
                return True

        return False

    def update(self):
        self.player.update_with_limits(
            self.left_limit,
            self.right_limit,
            self.top_limit,
            self.bottom_limit
        )
        self.npcs.update()

    def draw(self):
        self.display_surface.fill((15, 15, 25))

        for sprite in self.sprites:
            self.display_surface.blit(sprite.image, sprite.rect)

        self.display_surface.blit(self.player.image, self.player.rect)

        for npc in self.npcs:
            flipped_npc_image = pygame.transform.flip(npc.image, True, False)
            self.display_surface.blit(flipped_npc_image, npc.rect)

        #font = pygame.font.Font(None, 36)
        #text = font.render("Press E / A near the exit", True, (255, 255, 255))
        #self.display_surface.blit(text, (30, 30))

    def run(self):
        self.update()
        self.draw()