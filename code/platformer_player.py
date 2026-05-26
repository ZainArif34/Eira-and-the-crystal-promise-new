# platformer_player.py
import pygame
import os

class PlatformerPlayer(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.import_assets()
        self.frame_index = 0
        self.animation_speed = 0.15
        self.status = "idle"
        self.facing_right = True
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(midbottom=pos)

        # rect is for drawing, hitbox is for collision
        self.hitbox = pygame.Rect(0, 0, 26, self.rect.height - 6)
        self.hitbox.midbottom = self.rect.midbottom

        self.direction = pygame.math.Vector2(0, 0)
        self.normal_speed = 8
        #self.sprint_speed = 8
        self.speed = self.normal_speed
        self.gravity = 0.8
        self.jump_speed = -20
        self.on_ground = False
        self.on_ceiling = False
        self.on_left = False
        self.on_right = False
        self.A_BUTTON = 0
        self.B_BUTTON = 1

    def import_folder(self, path):
        frames = []

        for file_name in sorted(os.listdir(path)):
            full_path = os.path.join(path, file_name)

            if file_name.endswith(".png"):
                image = pygame.image.load(full_path).convert_alpha()
                frames.append(image)

        return frames

    def import_assets(self):
        path = "../graphics/playerLevel/"
        self.animations = {
            "idle": self.import_folder(path + "idle"),
            "run": self.import_folder(path + "run"),
            "jump": self.import_folder(path + "jump"),
            "fall": self.import_folder(path + "fall")
        }

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = 0
        self.speed = self.normal_speed

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.direction.x = -1
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.direction.x = 1
            self.facing_right = True

        if keys[pygame.K_SPACE] and self.on_ground:
            self.jump()

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)

            # Left stick movement
            if joystick.get_numaxes() > 0:
                left_stick_x = joystick.get_axis(0)
                deadzone = 0.25

                if abs(left_stick_x) > deadzone:
                    self.direction.x = left_stick_x

                    if left_stick_x < 0:
                        self.facing_right = False
                    elif left_stick_x > 0:
                        self.facing_right = True

            # B button cheat jump, unchanged
            if joystick.get_numbuttons() > self.B_BUTTON:
                if joystick.get_button(self.B_BUTTON):
                    self.jump()

            # D-pad movement
            if joystick.get_numhats() > 0:
                hat_x, hat_y = joystick.get_hat(0)

                if hat_x < 0:
                    self.direction.x = -1
                    self.facing_right = False
                elif hat_x > 0:
                    self.direction.x = 1
                    self.facing_right = True

            if joystick.get_numbuttons() > self.A_BUTTON:
                if joystick.get_button(self.A_BUTTON) and self.on_ground:
                    self.jump()

            if joystick.get_numbuttons() >= 16:
                if joystick.get_button(13):
                    self.direction.x = -1
                    self.facing_right = False
                elif joystick.get_button(14):
                    self.direction.x = 1
                    self.facing_right = True

    def get_status(self):
        if self.direction.y < 0:
            self.status = "jump"
        elif self.direction.y > 1:
            self.status = "fall"
        else:
            if self.direction.x != 0:
                self.status = "run"
            else:
                self.status = "idle"

    def animate(self):
        animation = self.animations[self.status]
        old_midbottom = self.hitbox.midbottom
        self.frame_index += self.animation_speed

        if self.frame_index >= len(animation):
            self.frame_index = 0

        image = animation[int(self.frame_index)]

        if self.facing_right:
            self.image = image
        else:
            self.image = pygame.transform.flip(image, True, False)

        self.rect = self.image.get_rect(midbottom=old_midbottom)

    def apply_gravity(self):
        self.direction.y += self.gravity
        self.hitbox.y += self.direction.y

    def jump(self):
        self.direction.y = self.jump_speed

    def sync_rect_to_hitbox(self):
        self.rect.midbottom = self.hitbox.midbottom

    def update(self):
        self.get_input()
        self.get_status()
        self.animate()