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
        self.speed = self.normal_speed
        self.gravity = 0.8
        self.jump_speed = -20
        self.super_jump_speed = -28
        self.on_ground = False
        self.on_ceiling = False
        self.on_left = False
        self.on_right = False

        # Controller buttons
        self.A_BUTTON = 0
        self.B_BUTTON = 1
        self.X_BUTTON = 2
        self.Y_BUTTON = 3
        self.LB_BUTTON = 4

        # Left trigger axis
        self.LT_AXIS = 4
        self.LT_DEADZONE = 0.5

        # Shield
        self.shielding = False
        self.shield_raised = False
        self.shield_enabled = True

        # Attack
        self.can_attack = True
        self.attacking = False
        self.attack_damage = 25
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.attack_immunity = False
        self.enemies_hit_this_attack = []

        # Spell
        self.spell_casting = False

        # Death
        self.dead = False
        self.death_done = False

    def import_folder(self, path):
        frames = []

        for file_name in sorted(os.listdir(path)):
            full_path = os.path.join(path, file_name)

            if file_name.endswith(".png"):
                image = pygame.image.load(full_path).convert_alpha()
                frames.append(image)

        return frames

    def import_strip(self, path, frame_width=100, frame_height=64):
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        frame_count = sheet.get_width() // frame_width

        for col in range(frame_count):
            x = col * frame_width
            frame = pygame.Surface(
                (frame_width, frame_height),
                pygame.SRCALPHA
            )
            frame.blit(
                sheet,
                (0, 0),
                pygame.Rect(x, 0, frame_width, frame_height)
            )

            if frame.get_bounding_rect().width > 0:
                frames.append(frame)

        return frames

    def import_assets(self):
        path = "../graphics/playerLevel/"

        self.animations = {
            "idle": self.import_folder(path + "idle"),
            "run": self.import_folder(path + "run"),
            "jump": self.import_folder(path + "jump"),
            "fall": self.import_folder(path + "fall"),
            "attack": self.import_strip(
                path + "attack/Attack_KG_1.png",
                100,
                64
            ),
            "spell": self.import_strip(
                path + "spell/Attack_KG_2.png",
                100,
                64
            ),
            "death": self.import_strip(
                path + "death/Dying_KG_2.png",
                100,
                64
            ),
            "shield_up": self.import_strip(
                path + "shield/Shield_Up_KG_1.png",
                100,
                64
            ),
            "shield_idle": self.import_strip(
                path + "shield/Shield_idle_KG.png",
                100,
                64
            )
        }

    def start_shield(self):
        if not self.shield_enabled:
            return

        if self.dead or self.attacking or self.spell_casting:
            return

        if not self.shielding:
            self.shielding = True
            self.shield_raised = False
            self.status = "shield_up"
            self.frame_index = 0

        self.direction.x = 0

    def update_stamina(self):
        current_time = pygame.time.get_ticks()
        delta_time = (
            current_time - self.last_stamina_update
        ) / 1000.0
        self.last_stamina_update = current_time

        if self.player.shielding:
            self.stamina -= (
                self.stamina_drain_rate * delta_time
            )

            if self.stamina <= 0:
                self.stamina = 0
                self.stamina_exhausted = True
                self.player.shield_enabled = False
                self.player.stop_shield()
        else:
            self.stamina += (
                self.stamina_regen_rate * delta_time
            )

            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

        if (
            self.stamina_exhausted
            and self.stamina >= self.stamina_reactivate_amount
        ):
            self.stamina_exhausted = False
            self.player.shield_enabled = True

        if not self.stamina_exhausted:
            self.player.shield_enabled = self.stamina > 0

    def stop_shield(self):
        if self.shielding:
            self.shielding = False
            self.shield_raised = False
            self.status = "idle"
            self.frame_index = 0

    def is_shield_active(self):
        return self.shielding and not self.dead

    def start_attack(self):
        if not self.can_attack:
            return

        if (
            not self.attacking
            and not self.spell_casting
            and not self.shielding
            and not self.dead
        ):
            self.attacking = True
            self.attack_immunity = True
            self.enemies_hit_this_attack = []
            self.status = "attack"
            self.frame_index = 0
            self.direction.x = 0

    def start_spell(self):
        if (
            not self.spell_casting
            and not self.attacking
            and not self.shielding
            and not self.dead
        ):
            self.spell_casting = True
            self.status = "spell"
            self.frame_index = 0
            self.direction.x = 0

    def start_death(self):
        if not self.dead:
            self.dead = True
            self.death_done = False
            self.attacking = False
            self.spell_casting = False
            self.shielding = False
            self.shield_raised = False
            self.attack_immunity = False
            self.attack_rect = pygame.Rect(0, 0, 0, 0)
            self.direction.x = 0
            self.direction.y = 0
            self.status = "death"
            self.frame_index = 0

    def revive(self):
        self.dead = False
        self.death_done = False
        self.attacking = False
        self.spell_casting = False
        self.shielding = False
        self.shield_raised = False
        self.attack_immunity = False
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.status = "idle"
        self.frame_index = 0
        self.direction.x = 0
        self.direction.y = 0
        self.animate()

    def get_input(self):
        if self.dead:
            return

        keys = pygame.key.get_pressed()
        self.direction.x = 0
        self.speed = self.normal_speed

        # Keyboard shield
        shield_pressed = (
            keys[pygame.K_LSHIFT]
            or keys[pygame.K_RSHIFT]
        )

        joystick = None

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)

            # LB shield
            if joystick.get_numbuttons() > self.LB_BUTTON:
                if joystick.get_button(self.LB_BUTTON):
                    shield_pressed = True

            # Left Trigger shield
            if joystick.get_numaxes() > self.LT_AXIS:
                left_trigger = joystick.get_axis(self.LT_AXIS)

                if left_trigger > self.LT_DEADZONE:
                    shield_pressed = True

        if shield_pressed:
            self.start_shield()
        else:
            self.stop_shield()

        # Shield prevents movement, jumping, attacking and spell casting
        if self.shielding:
            self.direction.x = 0
            return

        if self.spell_casting:
            return

        # Keyboard attack
        if keys[pygame.K_x]:
            self.start_attack()

        if not self.attacking:
            # Keyboard movement
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.direction.x = -1
                self.facing_right = False
            elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.direction.x = 1
                self.facing_right = True

            # Keyboard normal jump
            if keys[pygame.K_SPACE] and self.on_ground:
                self.jump()

        if joystick is not None:
            # Y attack
            if joystick.get_numbuttons() > self.Y_BUTTON:
                if joystick.get_button(self.Y_BUTTON):
                    self.start_attack()

            if not self.attacking:
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

                # D-pad movement
                if joystick.get_numhats() > 0:
                    hat_x, hat_y = joystick.get_hat(0)

                    if hat_x < 0:
                        self.direction.x = -1
                        self.facing_right = False
                    elif hat_x > 0:
                        self.direction.x = 1
                        self.facing_right = True

                # A normal jump
                if joystick.get_numbuttons() > self.A_BUTTON:
                    if (
                        joystick.get_button(self.A_BUTTON)
                        and self.on_ground
                    ):
                        self.jump()

                # X super jump
                if joystick.get_numbuttons() > self.X_BUTTON:
                    if (
                        joystick.get_button(self.X_BUTTON)
                        and self.on_ground
                    ):
                        self.super_jump()

                # Controllers that report D-pad as buttons
                if joystick.get_numbuttons() >= 16:
                    if joystick.get_button(13):
                        self.direction.x = -1
                        self.facing_right = False
                    elif joystick.get_button(14):
                        self.direction.x = 1
                        self.facing_right = True

    def get_status(self):
        if self.dead:
            self.status = "death"
            return

        if self.shielding:
            return

        if self.spell_casting:
            self.status = "spell"
            return

        if self.attacking:
            self.status = "attack"
            return

        if self.direction.y < 0:
            self.status = "jump"
        elif self.direction.y > 1:
            self.status = "fall"
        elif self.direction.x != 0:
            self.status = "run"
        else:
            self.status = "idle"

    def update_attack_rect(self):
        if self.attacking:
            attack_width = 45
            attack_height = self.hitbox.height + 10
            attack_y = self.hitbox.top - 5

            if self.facing_right:
                self.attack_rect = pygame.Rect(
                    self.hitbox.right,
                    attack_y,
                    attack_width,
                    attack_height
                )
            else:
                self.attack_rect = pygame.Rect(
                    self.hitbox.left - attack_width,
                    attack_y,
                    attack_width,
                    attack_height
                )
        else:
            self.attack_rect = pygame.Rect(0, 0, 0, 0)

    def has_attack_immunity(self):
        return self.attack_immunity

    def animate(self):
        animation = self.animations[self.status]
        old_midbottom = self.hitbox.midbottom

        if self.status == "death":
            speed = 0.16
        elif self.status == "attack":
            speed = 0.22
        elif self.status == "spell":
            speed = 0.2
        elif self.status == "shield_up":
            speed = 0.18
        elif self.status == "shield_idle":
            speed = 0.1
        else:
            speed = self.animation_speed

        self.frame_index += speed

        if self.frame_index >= len(animation):
            if self.status == "death":
                self.frame_index = len(animation) - 1
                self.death_done = True
            elif self.status == "attack":
                self.frame_index = 0
                self.attacking = False
                self.attack_immunity = False
                self.status = "idle"
                animation = self.animations[self.status]
            elif self.status == "spell":
                self.frame_index = 0
                self.spell_casting = False
                self.status = "idle"
                animation = self.animations[self.status]
            elif self.status == "shield_up":
                self.frame_index = 0
                self.shield_raised = True
                self.status = "shield_idle"
                animation = self.animations[self.status]
            elif self.status == "shield_idle":
                self.frame_index = 0
            else:
                self.frame_index = 0

        image = animation[int(self.frame_index)]

        if self.facing_right:
            self.image = image
        else:
            self.image = pygame.transform.flip(
                image,
                True,
                False
            )

        self.rect = self.image.get_rect(midbottom=old_midbottom)

    def apply_gravity(self):
        if not self.dead:
            self.direction.y += self.gravity
            self.hitbox.y += self.direction.y

    def jump(self):
        if not self.dead:
            self.direction.y = self.jump_speed

    def super_jump(self):
        if not self.dead:
            self.direction.y = self.super_jump_speed

    def sync_rect_to_hitbox(self):
        self.rect.midbottom = self.hitbox.midbottom

    def update_death(self):
        self.status = "death"
        self.animate()
        self.sync_rect_to_hitbox()

    def update(self):
        self.get_input()
        self.get_status()
        self.animate()
        self.update_attack_rect()