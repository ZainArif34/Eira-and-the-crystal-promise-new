# npc.py
import pygame
from settings import *
from support import import_npc_sprites

class NPC(pygame.sprite.Sprite):

    def __init__(self, pos, groups, name, dialogue, level_to_load=None):
        super().__init__(groups)

        self.import_assets()

        self.frame_index = 0
        self.animation_speed = 0.1

        self.image = self.animations['idle'][self.frame_index]
        self.rect = self.image.get_rect(topleft=pos)

        # Small collision box at feet
        self.hitbox = pygame.Rect(0, 0, 80, 35)
        self.name = name
        self.dialogue = dialogue
        self.level_to_load = level_to_load

    def import_assets(self):

        self.animations = {
            'idle': import_npc_sprites('../graphics/NPCs/IDLE.png')
        }

    def animate(self):

        self.frame_index += self.animation_speed

        if self.frame_index >= len(self.animations['idle']):
            self.frame_index = 0

        self.image = self.animations['idle'][int(self.frame_index)]

    def interact(self):

        # Return ALL dialogue pages
        return self.dialogue

    def update(self):

        self.animate()

        # Keep hitbox aligned with feet
        self.hitbox.midbottom = (
            self.rect.centerx,
            self.rect.bottom - 55
        )