# test_level.py
import pygame
from support import import_csv_layout
from settings import screen_width, screen_height


class TestLevel:
    def __init__(self, surface, return_to_town):
        self.display_surface = surface
        self.return_to_town = return_to_town

        # Original tileset tiles are 32x32
        self.source_tile_size = 32

        # Draw tiles as 64x64 in-game
        self.draw_tile_size = 64

        # File paths
        self.csv_path = "../mapData/levels/test/test.csv"
        self.tileset_path = "../graphics/terrainlevel/Terrain (32x32).png"

        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.camera_speed = 8

        # Load tiles and level
        self.tiles = self.import_tileset(self.tileset_path)
        self.level_sprites = pygame.sprite.Group()
        self.level_width = 0
        self.level_height = 0
        self.create_level(self.csv_path)

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

    def create_level(self, path):
        layout = import_csv_layout(path)
        self.level_width = len(layout[0]) * self.draw_tile_size
        self.level_height = len(layout) * self.draw_tile_size

        for row_index, row in enumerate(layout):
            for col_index, val in enumerate(row):
                val = val.strip()

                if val != "-1" and val != "":
                    tile_index = int(val)

                    if 0 <= tile_index < len(self.tiles):
                        x = col_index * self.draw_tile_size
                        y = row_index * self.draw_tile_size

                        sprite = pygame.sprite.Sprite()
                        sprite.image = self.tiles[tile_index]
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))
                        self.level_sprites.add(sprite)

    def update_camera(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.camera_x -= self.camera_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.camera_x += self.camera_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.camera_y -= self.camera_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.camera_y += self.camera_speed

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)

            if joystick.get_numhats() > 0:
                hat_x, hat_y = joystick.get_hat(0)
                self.camera_x += hat_x * self.camera_speed
                self.camera_y -= hat_y * self.camera_speed

        max_camera_x = max(0, self.level_width - screen_width)
        max_camera_y = max(0, self.level_height - screen_height)

        if self.camera_x < 0:
            self.camera_x = 0
        if self.camera_y < 0:
            self.camera_y = 0
        if self.camera_x > max_camera_x:
            self.camera_x = max_camera_x
        if self.camera_y > max_camera_y:
            self.camera_y = max_camera_y

    def draw_level(self):
        for sprite in self.level_sprites:
            screen_rect = sprite.rect.move(-self.camera_x, -self.camera_y)

            if screen_rect.colliderect(pygame.Rect(0, 0, screen_width, screen_height)):
                self.display_surface.blit(sprite.image, screen_rect)

    def run(self):
        self.update_camera()
        self.display_surface.fill((25, 25, 35))
        self.draw_level()

        font = pygame.font.Font(None, 36)
        text = font.render("TEST LEVEL - Arrow keys / D-pad to move camera - ESC to return", True, (255, 255, 255))
        self.display_surface.blit(text, (30, 30))