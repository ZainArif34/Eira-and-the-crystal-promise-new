#Yelixa Tan
#2026-04-20
#camera.py
#camera file for project, will draw everything relative to the player's position

import pygame
from settings import screen_width, screen_height, map_width, map_height

class CameraGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.display_surface = pygame.display.get_surface()
        self.offset = pygame.math.Vector2()
        self.half_w = self.display_surface.get_width() // 2
        self.half_h = self.display_surface.get_height() // 2

    def center_on(self, target_rect):
            self.offset.x = round(target_rect.centerx - self.half_w)
            self.offset.y = round(target_rect.centery - self.half_h)

            # Stop the camera from showing anything outside the map
            if self.offset.x < 0: 
                self.offset.x = 0
            if self.offset.y < 0: 
                self.offset.y = 0
                
            if self.offset.x > map_width - screen_width:
                self.offset.x = map_width - screen_width
            if self.offset.y > map_height - screen_height:
                self.offset.y = map_height - screen_height

    def draw(self, target):
        self.center_on(target.rect)

        #draws the tiles first 
        for sprite in self.sprites():
            if sprite != target:
                offset_pos = sprite.rect.topleft - self.offset
                self.display_surface.blit(sprite.image, offset_pos)

        #draws everything else: fixes the issue with the blinking
        offset_pos = target.rect.topleft - self.offset
        self.display_surface.blit(target.image, offset_pos)