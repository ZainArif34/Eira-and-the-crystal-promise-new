# player.py
import pygame
from support import import_sprite_list
from settings import *

class Player(pygame.sprite.Sprite):

    def __init__(self, pos, obstacles):
        super().__init__()

        self.import_assets()

        self.status = 'down_idle'
        self.frame_index = 0
        self.animation_speed = 0.05

        self.obstacle_sprites = obstacles

        self.image = self.animations[self.status][self.frame_index]

        self.rect = self.image.get_rect(midbottom=pos)

        # Physical collision box
        self.hitbox = self.rect.inflate(-25, -50)

        self.direction = pygame.math.Vector2(0, 0)

        self.normal_speed = 3
        self.sprint_speed = 5
        self.speed = self.normal_speed

    
        # A = 0, B = 1
        self.B_BUTTON = 1

    def import_assets(self):

        path = '../graphics/player/'

        # WALK
        walk_up = import_sprite_list(path + 'walk/walk_Up.png')
        walk_down = import_sprite_list(path + 'walk/walk_Down.png')
        walk_right_down = import_sprite_list(
            path + 'walk/walk_Right_Down.png'
        )

        # IDLE
        idle_up = import_sprite_list(path + 'idle/Idle_Up.png')
        idle_down = import_sprite_list(path + 'idle/Idle_Down.png')
        idle_right_down = import_sprite_list(
            path + 'idle/Idle_Right_Down.png'
        )

        self.animations = {

            # VERTICAL
            'up': walk_up,
            'down': walk_down,

            'up_idle': idle_up,
            'down_idle': idle_down,

            # DOWN DIAGONALS
            'right_down': walk_right_down,

            'left_down': [
                pygame.transform.flip(f, True, False)
                for f in walk_right_down
            ],

            'right_down_idle': idle_right_down,

            'left_down_idle': [
                pygame.transform.flip(f, True, False)
                for f in idle_right_down
            ],

            # UP DIAGONALS
            'right_up': [
                pygame.transform.flip(f, False, False)
                for f in walk_right_down
            ],

            'left_up': [
                pygame.transform.flip(f, True, False)
                for f in walk_right_down
            ],

            'right_up_idle': [
                pygame.transform.flip(f, False, False)
                for f in idle_right_down
            ],

            'left_up_idle': [
                pygame.transform.flip(f, True, False)
                for f in idle_right_down
            ]
        }

    def get_input(self):

        keys = pygame.key.get_pressed()

        self.direction.x = 0
        self.direction.y = 0

        # Start at normal speed every frame
        self.speed = self.normal_speed

        # Keyboard vertical
        if keys[pygame.K_UP]:
            self.direction.y = -1

        elif keys[pygame.K_DOWN]:
            self.direction.y = 1

        # Keyboard horizontal
        if keys[pygame.K_LEFT]:
            self.direction.x = -1

        elif keys[pygame.K_RIGHT]:
            self.direction.x = 1

        # Controller input
        if pygame.joystick.get_count() > 0:

            joystick = pygame.joystick.Joystick(0)

            # B button sprint
            if joystick.get_numbuttons() > self.B_BUTTON:
                if joystick.get_button(self.B_BUTTON):
                    self.speed = self.sprint_speed

            # D-pad movement using HAT
            if joystick.get_numhats() > 0:

                hat_x, hat_y = joystick.get_hat(0)

                if hat_x != 0:
                    self.direction.x = hat_x

                if hat_y != 0:
                    self.direction.y = -hat_y

            # Some controllers use buttons for D-pad
            if joystick.get_numbuttons() >= 16:

                if joystick.get_button(11):  # D-pad up
                    self.direction.y = -1

                elif joystick.get_button(12):  # D-pad down
                    self.direction.y = 1

                if joystick.get_button(13):  # D-pad left
                    self.direction.x = -1

                elif joystick.get_button(14):  # D-pad right
                    self.direction.x = 1

        # Prevent diagonal speed boost
        if self.direction.magnitude() > 0:
            self.direction = self.direction.normalize()
    def get_status(self):

        old_status = self.status

        # Moving up
        if self.direction.y < 0:

            if self.direction.x < 0:
                self.status = 'left_up'

            elif self.direction.x > 0:
                self.status = 'right_up'

            else:
                self.status = 'up'

        # Moving down
        elif self.direction.y > 0:

            if self.direction.x < 0:
                self.status = 'left_down'

            elif self.direction.x > 0:
                self.status = 'right_down'

            else:
                self.status = 'down'

        # Sideways only
        elif self.direction.x < 0:
            self.status = 'left_down'

        elif self.direction.x > 0:
            self.status = 'right_down'

        # Idle
        if self.direction.magnitude() == 0:

            if '_idle' not in self.status:
                self.status += '_idle'

        # Reset animation on state change
        if old_status != self.status:
            self.frame_index = 0

    def animate(self):

        animation = self.animations[self.status]

        # Slower idle animation
        speed = 0.05 if '_idle' in self.status else 0.15

        self.frame_index += speed

        if self.frame_index >= len(animation):
            self.frame_index = 0

        self.image = animation[int(self.frame_index)]

        # Align sprite with hitbox
        self.rect.center = self.hitbox.center

    def collide(self, direction):

        if direction == 'horizontal':

            for sprite in self.obstacle_sprites:

                collision_rect = (
                    sprite.hitbox
                    if hasattr(sprite, 'hitbox')
                    else sprite.rect
                )

                if collision_rect.colliderect(self.hitbox):

                    if self.direction.x > 0:
                        self.hitbox.right = collision_rect.left

                    if self.direction.x < 0:
                        self.hitbox.left = collision_rect.right

        if direction == 'vertical':

            for sprite in self.obstacle_sprites:

                collision_rect = (
                    sprite.hitbox
                    if hasattr(sprite, 'hitbox')
                    else sprite.rect
                )

                if collision_rect.colliderect(self.hitbox):

                    if self.direction.y > 0:
                        self.hitbox.bottom = collision_rect.top

                    if self.direction.y < 0:
                        self.hitbox.top = collision_rect.bottom

    def update(self):

        self.get_input()

        self.get_status()

        self.animate()

        # Horizontal movement
        self.hitbox.x += round(self.direction.x * self.speed)

        self.collide('horizontal')

        # Map limits
        if self.hitbox.left < 0:
            self.hitbox.left = 0

        if self.hitbox.right > map_width:
            self.hitbox.right = map_width

        # Vertical movement
        self.hitbox.y += round(self.direction.y * self.speed)

        self.collide('vertical')

        # Map limits
        if self.hitbox.top < 0:
            self.hitbox.top = 0

        if self.hitbox.bottom > map_height:
            self.hitbox.bottom = map_height

        # Keep sprite synced to hitbox
        self.rect.center = self.hitbox.center