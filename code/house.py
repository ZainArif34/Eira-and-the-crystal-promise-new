# house.py
import pygame
from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer, TiledObjectGroup
from pathlib import Path

from settings import tile_size, screen_width, screen_height
from player import Player
from NPCS import NPC

HOUSE_NPC_DATA = {
    "house1": {
        "name": "Frostpoint Elder",
        "dialogue": [
            "I hear you are looking for someone, Eira.",
            "people usually only go missing in this town,",
            "in the outskirts of the Frostpoint mountains",
            "But..",
            "That part of the city has been cursed,",
            "the only way to break the curse is to reunite the shards",
            "One of the shards is hidden in an abandoned mine in the mountains,",
            "but be careful,",
            "its a long dangerous hike",
            "I can help you get there,",
            "but you won't be able to get back here until you find the shard."
        ],
        "question": "Will you travel to the cave mine?",
        "level": "level1"
    },
    "house2": {
        "name": "Village Scholar",
        "dialogue": [
            "Dear child, you have freed me at last,",
            "You have my greatest thanks child",
            "So you want to find your fiance...",
            "He's most likely trapped in the mountain side",
            "I can help you get there, yet I can't help you survive",
            "you've already shown to be quite the survivalist though,",
            "so I have faith in you",
            "That mountain, however will be the hardest trial you've faced.",
            "At the end expect the last shard that will free your fiance",
            "it won't be easy though as the crystal is guarded by an ancient warrior,",
            "who's sworn to protect the shard",
            "He's been guarding it for centuries, so he's quite powerful,",
            "but I know you can do it!",
            "He may be dangerous, but he's not evil, so please take pity.",
            "Your journey is coming to an end, I can tell.",
            "Good luck Eira!"
        ],
        "question": "Will you take on the final challenge?",
        "level": "level2"
    },
    "house3": {
        "name": "Mountain Guardian",
        "dialogue": [
            "You desire a shard don't you?",
            "Everyone does, yet none have been able to get one and survive!",
            "I can tell you where a shard lies,",
            "but don't blame me if you find yourself dead.",
            "Before you go,",
            "You must've seen that the central dojo has been locked",
            "It's cursed now, all shards must be brought to it",
            "If you dare find the shards you better fix the dojo.",
            "Our elder is trapped",
            "so to the quiet woods we go!",
            "There you will find a shard...",
            "if you survive",
            "HAHAHAHAHAHA"
        ],
        "question": "Will you venture into the woods?",
        "level": "level3"
    },
    "house4": {
        "name": "Crystal Keeper",
        "dialogue": [
            "Our poor elder, oh how I weep for him.",
            "I know your kind, child.",
            "You want a shard don't you?",
            "sniffle",
            "I can lead you to the shard in the abandoned dungeon.",
            "but you won't like what you find there.",
            "please stay safe,",
            "I can not let another child perish in that place.",
            "But promise me, if you get the shard please help our elder."
        ],
        "question": "Will you help me free him?",
        "level": "level4"
    }
}

class House:
    def __init__(self, surface, tmx_path):
        self.display_surface = surface
        self.tmx_path = tmx_path
        self.house_id = Path(self.tmx_path).stem.lower()
        self.tmx_data = load_pygame(self.tmx_path)
        self.scale_factor = tile_size / self.tmx_data.tilewidth

        self.sprites = pygame.sprite.Group()
        self.obstacles = pygame.sprite.Group()
        self.exits = pygame.sprite.Group()
        self.npcs = pygame.sprite.Group()

        self.map_width = self.tmx_data.width * tile_size
        self.map_height = self.tmx_data.height * tile_size

        # Centre small houses, but start large houses at world position 0
        self.offset_x = max(0, (screen_width - self.map_width) // 2)
        self.offset_y = max(0, (screen_height - self.map_height) // 2)

        self.left_limit = self.offset_x
        self.right_limit = self.offset_x + self.map_width
        self.top_limit = self.offset_y
        self.bottom_limit = self.offset_y + self.map_height

        # House-specific camera
        self.camera_offset = pygame.math.Vector2(0, 0)

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
        npc_data = HOUSE_NPC_DATA.get(
            self.house_id,
            {
                "name": "Villager",
                "dialogue": [
                    "Hello, Eira.",
                    "There is nothing more I can tell you."
                ],
                "question": "Will you continue?",
                "level": None
            }
        )

        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    marker_x = col_index * tile_size + self.offset_x
                    marker_y = row_index * tile_size + self.offset_y
                    npc_x = marker_x - tile_size
                    npc_y = marker_y - tile_size * 2

                    npc = NPC(
                        (npc_x, npc_y),
                        [self.npcs],
                        npc_data["name"],
                        npc_data["dialogue"],
                        npc_data["level"]
                    )

                    npc.choice_question = npc_data["question"]
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

    def update_camera(self):
        if self.map_width > screen_width:
            target_x = self.player.hitbox.centerx - screen_width // 2
            max_camera_x = self.map_width - screen_width
            self.camera_offset.x = round(max(0, min(target_x, max_camera_x)))
        else:
            self.camera_offset.x = 0

        if self.map_height > screen_height:
            target_y = self.player.hitbox.centery - screen_height // 2
            max_camera_y = self.map_height - screen_height
            self.camera_offset.y = round(max(0, min(target_y, max_camera_y)))
        else:
            self.camera_offset.y = 0

    def update(self):
        self.player.update_with_limits(
            self.left_limit,
            self.right_limit,
            self.top_limit,
            self.bottom_limit
        )
        self.npcs.update()
        self.update_camera()

    def draw(self):
        self.display_surface.fill((15, 15, 25))
        camera_x = round(self.camera_offset.x)
        camera_y = round(self.camera_offset.y)

        for sprite in self.sprites:
            screen_x = sprite.rect.x - camera_x
            screen_y = sprite.rect.y - camera_y
            self.display_surface.blit(sprite.image, (screen_x, screen_y))

        player_x = self.player.rect.x - camera_x
        player_y = self.player.rect.y - camera_y
        self.display_surface.blit(self.player.image, (player_x, player_y))

        for npc in self.npcs:
            flipped_npc_image = pygame.transform.flip(npc.image, True, False)
            npc_x = npc.rect.x - camera_x
            npc_y = npc.rect.y - camera_y
            self.display_surface.blit(flipped_npc_image, (npc_x, npc_y))

    def run(self):
        self.update()
        self.draw()