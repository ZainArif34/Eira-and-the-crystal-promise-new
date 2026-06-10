import pygame
from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer
from settings import tile_size

class Town:
    def __init__(self, surface, camera_group):
        self.display_surface = surface
        self.camera_group = camera_group
        self.nodes = pygame.sprite.Group()

        # Collision objects
        self.obstacles = pygame.sprite.Group()

        # NPC group
        self.npcs = pygame.sprite.Group()

        # Door group
        self.doors = pygame.sprite.Group()

        # Default player start if no PlayerStart tile is found
        self.player_start = (640, 360)

        self.tmx_path = "../mapData/Town/town.tmx"
        self.tmx_data = load_pygame(self.tmx_path)

        self.load_tmx_map()

    def scale_surface(self, surface):
        if surface.get_width() == tile_size and surface.get_height() == tile_size:
            return surface

        return pygame.transform.scale(surface, (tile_size, tile_size))

    def load_tmx_map(self):
        for layer in self.tmx_data.layers:
            if isinstance(layer, TiledTileLayer):
                layer_name = layer.name.strip()

                if layer_name == "Collisions":
                    self.create_collision_layer(layer)
                elif layer_name == "PlayerStart":
                    self.create_player_start_layer(layer)
                elif layer_name.startswith("Door"):
                    self.create_door_layer(layer)
                elif layer_name == "NPCS":
                    pass
                else:
                    self.create_visual_layer(layer)

    def create_visual_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    tile_surf = self.tmx_data.get_tile_image_by_gid(gid)

                    if tile_surf is not None:
                        tile_surf = self.scale_surface(tile_surf)
                        x = col_index * tile_size
                        y = row_index * tile_size
                        sprite = pygame.sprite.Sprite()
                        sprite.image = tile_surf
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))

                        if layer.name.strip() == "Nature":
                            sprite.draw_above_player = True
                        else:
                            sprite.draw_above_player = False

                        self.nodes.add(sprite)
                        self.camera_group.add(sprite)

    def create_collision_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * tile_size
                    y = row_index * tile_size
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                    sprite.rect = pygame.Rect(x, y, tile_size, tile_size)
                    self.obstacles.add(sprite)

    def create_player_start_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * tile_size + tile_size // 2
                    y = row_index * tile_size + tile_size
                    self.player_start = (x, y)
                    return

    def create_door_layer(self, layer):
        layer_name = layer.name.strip()
        door_number = layer_name.replace("Door", "")
        house_name = "house" + door_number

        for row_index, row in enumerate(layer.data): 
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * tile_size
                    y = row_index * tile_size
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface((tile_size, tile_size), pygame.SRCALPHA)
                    sprite.rect = pygame.Rect(x, y, tile_size, tile_size)
                    sprite.house_name = house_name
                    self.doors.add(sprite)