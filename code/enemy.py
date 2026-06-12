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

        # Collision boxes
        self.hurtbox = pygame.Rect(0, 0, 38, 78)
        self.body_rect = pygame.Rect(0, 0, 42, 78)
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.attack_active = False
        self.update_collision_boxes()

        # Movement and detection
        self.speed = 2
        self.facing_right = True
        self.detection_range = 350

        # range
        self.attack_range = 50
        self.same_platform_range = 35

        # Combat
        self.attacking = False
        self.dying = False
        self.attack_has_hit_player = False
        self.attack_cooldown = 900
        self.last_attack_time = 0
        self.health = 100

    def update_collision_boxes(self):
        self.hurtbox.midbottom = (
            self.rect.centerx,
            self.rect.bottom
        )
        self.body_rect.midbottom = (
            self.rect.centerx,
            self.rect.bottom
        )

    def import_frames(self, path):
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        frame_count = sheet.get_width() // self.source_frame_width

        for col in range(frame_count):
            x = col * self.source_frame_width
            frame = pygame.Surface(
                (self.source_frame_width, self.source_frame_height),
                pygame.SRCALPHA
            )
            frame.blit(
                sheet,
                (0, 0),
                pygame.Rect(
                    x,
                    0,
                    self.source_frame_width,
                    self.source_frame_height
                )
            )
            scaled_frame = pygame.transform.scale(
                frame,
                (self.frame_width, self.frame_height)
            )
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
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.attack_active = False


    def can_see_player(self, player):
        distance_x = abs(
            player.hitbox.centerx - self.body_rect.centerx
        )
        distance_y = abs(
            player.hitbox.bottom - self.body_rect.bottom
        )

        return (
            distance_x <= self.detection_range
            and distance_y <= self.same_platform_range
        )

    def close_to_player(self, player):
        distance_x = abs(
            player.hitbox.centerx - self.body_rect.centerx
        )
        distance_y = abs(
            player.hitbox.bottom - self.body_rect.bottom
        )

        return (
            distance_x <= self.attack_range
            and distance_y <= self.same_platform_range
        )

    def face_player(self, player):
        self.facing_right = (
            player.hitbox.centerx > self.body_rect.centerx
        )

    def stop_at_collision_marker(self, move_direction):
        for sprite in self.collision_sprites:
            if self.body_rect.colliderect(sprite.rect):
                if move_direction > 0:
                    self.rect.right -= (
                        self.body_rect.right - sprite.rect.left
                    )
                elif move_direction < 0:
                    self.rect.left += (
                        sprite.rect.right - self.body_rect.left
                    )

                self.update_collision_boxes()
                return True

        return False

    def chase_player(self, player):
        move_speed = abs(self.speed)

        if player.hitbox.centerx > self.body_rect.centerx:
            self.rect.x += move_speed
            self.facing_right = True
            self.update_collision_boxes()
            self.stop_at_collision_marker(1)

        elif player.hitbox.centerx < self.body_rect.centerx:
            self.rect.x -= move_speed
            self.facing_right = False
            self.update_collision_boxes()
            self.stop_at_collision_marker(-1)

        self.update_collision_boxes()

    def patrol(self):
        self.rect.x += self.speed
        self.facing_right = self.speed > 0
        self.update_collision_boxes()

        for sprite in self.collision_sprites:
            if self.body_rect.colliderect(sprite.rect):
                if self.speed > 0:
                    overlap = self.body_rect.right - sprite.rect.left
                    self.rect.x -= overlap
                elif self.speed < 0:
                    overlap = sprite.rect.right - self.body_rect.left
                    self.rect.x += overlap

                self.speed *= -1
                self.update_collision_boxes()
                break

    def start_attack(self):
        current_time = pygame.time.get_ticks()

        if current_time - self.last_attack_time >= self.attack_cooldown:
            self.status = "attack"
            self.attacking = True
            self.attack_active = False
            self.attack_has_hit_player = False
            self.frame_index = 0
            self.last_attack_time = current_time

    def update_attack_rect(self):
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.attack_active = False

        if self.status != "attack" or self.dying:
            return

        current_frame = int(self.frame_index)

        # Only these frames can hurt Eira
        active_attack_frames = 5 <= current_frame <= 6

        if not active_attack_frames:
            return

        self.attack_active = True

        attack_width = 36
        attack_height = 44
        attack_y = self.body_rect.centery - attack_height // 2

        if self.facing_right:
            self.attack_rect = pygame.Rect(
                self.body_rect.right - 4,
                attack_y,
                attack_width,
                attack_height
            )
        else:
            self.attack_rect = pygame.Rect(
                self.body_rect.left - attack_width + 4,
                attack_y,
                attack_width,
                attack_height
            )

    def can_damage_player(self, player):
        if self.dying:
            return False

        if self.attack_has_hit_player:
            return False

        if not self.attack_active:
            return False

        return self.attack_rect.colliderect(player.hitbox)

    def animate(self):
        old_midbottom = self.rect.midbottom
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed

        if self.frame_index >= len(animation):
            if self.status == "death":
                self.kill()
                return

            if self.status == "attack":
                self.status = "walk"
                self.attacking = False
                self.attack_active = False
                self.attack_rect = pygame.Rect(0, 0, 0, 0)
                self.frame_index = 0
                animation = self.animations[self.status]
            else:
                self.frame_index = 0

        self.image = animation[int(self.frame_index)]

        if not self.facing_right:
            self.image = pygame.transform.flip(
                self.image,
                True,
                False
            )

        self.rect = self.image.get_rect(
            midbottom=old_midbottom
        )

        self.update_collision_boxes()
        self.update_attack_rect()

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