# enemy.py
import pygame

class SkeletonEnemy(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.source_frame_width = 64
        self.source_frame_height = 96
        self.scale = 1.5
        self.canvas_width = int(self.source_frame_width * self.scale)
        self.canvas_height = int(self.source_frame_height * self.scale)
        self.frames = self.import_frames("../graphics/skeleton/Skeleton_01_Yellow_Idle.png")
        self.frame_index = 0
        self.animation_speed = 0.06
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect(midbottom=pos)

    def import_frames(self, path):
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        frame_count = sheet.get_width() // self.source_frame_width

        for col in range(frame_count):
            x = col * self.source_frame_width
            source_frame = pygame.Surface((self.source_frame_width, self.source_frame_height), pygame.SRCALPHA)
            source_frame.blit(sheet, (0, 0), pygame.Rect(x, 0, self.source_frame_width, self.source_frame_height))
            crop_rect = source_frame.get_bounding_rect()

            if crop_rect.width > 0 and crop_rect.height > 0:
                cropped = pygame.Surface((crop_rect.width, crop_rect.height), pygame.SRCALPHA)
                cropped.blit(source_frame, (0, 0), crop_rect)
                scaled_width = int(crop_rect.width * self.scale)
                scaled_height = int(crop_rect.height * self.scale)
                scaled = pygame.transform.scale(cropped, (scaled_width, scaled_height))
                final_frame = pygame.Surface((self.canvas_width, self.canvas_height), pygame.SRCALPHA)
                paste_x = self.canvas_width // 2 - scaled_width // 2
                paste_y = self.canvas_height - scaled_height
                final_frame.blit(scaled, (paste_x, paste_y))
                frames.append(final_frame)

        return frames

    def animate(self):
        old_midbottom = self.rect.midbottom
        self.frame_index += self.animation_speed

        if self.frame_index >= len(self.frames):
            self.frame_index = 0

        self.image = self.frames[int(self.frame_index)]
        self.rect = self.image.get_rect(midbottom=old_midbottom)

    def update(self):
        self.animate()