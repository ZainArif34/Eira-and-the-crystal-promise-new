import pygame
from support import import_csv_layout, import_cut_graphics
from settings import tile_size
from NPCS import NPC

class Town:

    def __init__(self, surface, camera_group):

        self.display_surface = surface
        self.camera_group = camera_group

        self.nodes = pygame.sprite.Group()

        # Collision objects
        self.obstacles = pygame.sprite.Group()

        # NPC group
        self.npcs = pygame.sprite.Group()

        self.graphics = import_cut_graphics(
            '../graphics/terrainTown/Frostpoint Tiles.png'
        )

        # Map layers
        self.create_layer('../mapData/Town/Floor_Floor.csv')
        self.create_layer('../mapData/Town/Floor_Fences.csv')
        self.create_layer('../mapData/Town/Floor_Houses.csv')

        # Collision layer
        self.create_collision_layer(
            '../mapData/Town/collisions_Collisions.csv'
        )

        # NPC layer
        self.create_npc_layer(
            '../mapData/Town/NPCS_NPCS.csv'
        )

    def create_npc_layer(self, path):

        layout = import_csv_layout(path)

        for row_index, row in enumerate(layout):

            for col_index, val in enumerate(row):

                if val != '-1':
                    print("NPC VALUE:", val)

                    x = col_index * tile_size
                    y = row_index * tile_size

                    # DEFAULT
                    dialogue = [
                        "Hello traveler."
                    ]

                    level_to_load = None

                    if val == "5":

                        dialogue = [
                            "Welcome to Frostpoint.",
                            "The winter has lasted years.",
                            "People fear the crystal...",
                            "Would you like to enter the test level?"
                        ]

                        level_to_load = "test"

                    elif val == "6":

                        dialogue = [
                            "The crystal chose Eira...",
                            "At least that's what they say.",
                            "I hope they're right."
                        ]

                        level_to_load = None

                    elif val == '7':

                        dialogue = [
                            "I heard the crystal is in the mountains.",
                            "But no one has been there in ages.",
                            "It's too dangerous."
                        ]

                    npc = NPC(
                        (x, y),
                        [self.camera_group, self.npcs],
                        "Villager",
                        dialogue,
                        level_to_load
                    )

                    # NPC collision
                    self.obstacles.add(npc)

    def create_layer(self, path):

        layout = import_csv_layout(path)

        for row_index, row in enumerate(layout):

            for col_index, val in enumerate(row):

                if val != '-1':

                    x = col_index * tile_size
                    y = row_index * tile_size

                    tile_surf = self.graphics[int(val)]

                    sprite = pygame.sprite.Sprite()

                    sprite.image = tile_surf

                    sprite.rect = sprite.image.get_rect(
                        topleft=(x, y)
                    )

                    self.nodes.add(sprite)
                    self.camera_group.add(sprite)

    def create_collision_layer(self, path):

        layout = import_csv_layout(path)

        for row_index, row in enumerate(layout):

            for col_index, val in enumerate(row):

                if val != '-1':

                    x = col_index * tile_size
                    y = row_index * tile_size

                    sprite = pygame.sprite.Sprite()

                    sprite.image = pygame.Surface(
                        (tile_size, tile_size)
                    )

                    sprite.image.fill('red')
                    sprite.image.set_alpha(100)

                    full_rect = pygame.Rect(
                        x,
                        y,
                        tile_size,
                        tile_size
                    )

                    sprite.rect = full_rect.inflate(0, -10)

                    self.obstacles.add(sprite)

                    # Uncomment to show collisions
                    # self.camera_group.add(sprite)