# enemy.py
import pygame

class SkeletonEnemy(pygame.sprite.Sprite):
    def __init__(self, pos, collision_sprites):
        super().__init__()
        self.collision_sprites = collision_sprites
        self.source_frame_width = 96
        self.source_frame_height = 64
        self.scale = 1.5
        self.frame_width = int(self.source_frame_width * self.scale)
        self.frame_height = int(self.source_frame_height * self.scale)
        self.animations = {
            "walk": self.import_frames("../graphics/skeleton/Skeleton_01_Yellow_Walk.png"),
            "attack": self.import_frames("../graphics/skeleton/Skeleton_01_Yellow_Attack2.png"),
            "death": self.import_frames("../graphics/skeleton/Skeleton_01_Yellow_Die.png")
        }
        self.status = "walk"
        self.frame_index = 0
        self.animation_speed = 0.08
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(midbottom=pos)
        self.hurtbox = pygame.Rect(0, 0, 38, 78)
        self.update_hurtbox()
        self.speed = 2
        self.facing_right = True
        self.detection_range = 350
        self.attack_range = 85
        self.same_platform_range = 35
        self.attacking = False
        self.dying = False
        self.attack_cooldown = 900
        self.last_attack_time = 0
        self.health = 50

    def update_hurtbox(self):
        self.hurtbox.midbottom = (
            self.rect.centerx,
            self.rect.bottom
        )

    def import_frames(self, path):
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        frame_count = sheet.get_width() // self.source_frame_width

        for col in range(frame_count):
            x = col * self.source_frame_width
            frame = pygame.Surface((self.source_frame_width, self.source_frame_height), pygame.SRCALPHA)
            frame.blit(sheet, (0, 0), pygame.Rect(x, 0, self.source_frame_width, self.source_frame_height))
            scaled_frame = pygame.transform.scale(frame, (self.frame_width, self.frame_height))
            frames.append(scaled_frame)

        return frames

    def take_damage(self, amount):
        if self.dying:
            return

        self.health -= amount
        if self.health <= 0:
            self.start_death()

    def start_death(self):
        self.status = "death"
        self.frame_index = 0
        self.attacking = False
        self.dying = True

    def can_see_player(self, player):
        distance_x = abs(player.hitbox.centerx - self.rect.centerx)
        distance_y = abs(player.hitbox.bottom - self.rect.bottom)
        return distance_x <= self.detection_range and distance_y <= self.same_platform_range

    def close_to_player(self, player):
        distance_x = abs(player.hitbox.centerx - self.rect.centerx)
        distance_y = abs(player.hitbox.bottom - self.rect.bottom)
        return distance_x <= self.attack_range and distance_y <= self.same_platform_range

    def face_player(self, player):
        self.facing_right = player.hitbox.centerx > self.rect.centerx

    def stop_at_collision_marker(self, move_direction):
        for sprite in self.collision_sprites:
            if self.rect.colliderect(sprite.rect):
                if move_direction > 0:
                    self.rect.right = sprite.rect.left
                elif move_direction < 0:
                    self.rect.left = sprite.rect.right

                return True

        return False

    def chase_player(self, player):
        move_speed = abs(self.speed)

        if player.hitbox.centerx > self.rect.centerx:
            self.rect.x += move_speed
            self.facing_right = True
            self.stop_at_collision_marker(1)
        elif player.hitbox.centerx < self.rect.centerx:
            self.rect.x -= move_speed
            self.facing_right = False
            self.stop_at_collision_marker(-1)

    def patrol(self):
        self.rect.x += self.speed
        self.facing_right = self.speed > 0

        for sprite in self.collision_sprites:
            if self.rect.colliderect(sprite.rect):
                if self.speed > 0:
                    self.rect.right = sprite.rect.left
                elif self.speed < 0:
                    self.rect.left = sprite.rect.right

                self.speed *= -1

    def start_attack(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_attack_time >= self.attack_cooldown:
            self.status = "attack"
            self.attacking = True
            self.frame_index = 0
            self.last_attack_time = current_time

    def animate(self):
        old_midbottom = self.rect.midbottom
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed

        if self.frame_index >= len(animation):
            if self.status == "death":
                self.kill()
                return

            self.frame_index = 0
            if self.status == "attack":
                self.status = "walk"
                self.attacking = False
                animation = self.animations[self.status]

        self.image = animation[int(self.frame_index)]
        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

        self.rect = self.image.get_rect(midbottom=old_midbottom)
        self.update_hurtbox()

    def update(self, player):
        if self.dying:
            self.animate()
            return

        if self.attacking:
            self.animate()
            return

        if self.close_to_player(player):
            self.face_player(player)
            self.start_attack()
        elif self.can_see_player(player):
            self.status = "walk"
            self.chase_player(player)
        else:
            self.status = "walk"
            self.patrol()

        self.animate()