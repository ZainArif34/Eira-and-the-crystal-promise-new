# spell.py
import pygame

class MagicLaser(pygame.sprite.Sprite):
    def __init__(self, pos, direction):
        super().__init__()
        self.direction = direction
        self.speed = 24
        self.spawn_time = pygame.time.get_ticks()
        self.lifetime = 450
        self.image = pygame.Surface((220, 20), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (180, 220, 255, 120), (0, 2, 220, 16), border_radius=8)
        pygame.draw.rect(self.image, (255, 255, 255, 230), (0, 7, 220, 6), border_radius=3)
        pygame.draw.circle(self.image, (255, 255, 255, 240), (205, 10), 10)

        if self.direction < 0:
            self.image = pygame.transform.flip(self.image, True, False)
            self.rect = self.image.get_rect(midright=pos)
        else:
            self.rect = self.image.get_rect(midleft=pos)

    def update(self):
        self.rect.x += self.speed * self.direction
        current_time = pygame.time.get_ticks()
        if current_time - self.spawn_time >= self.lifetime:
            self.kill()