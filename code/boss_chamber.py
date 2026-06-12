# boss_chamber.py
import pygame
import random

from pytmx.util_pygame import load_pygame
from pytmx import TiledTileLayer
from settings import screen_width, screen_height
from platformer_player import PlatformerPlayer
from spell import MagicLaser


class RespawningPotion(pygame.sprite.Sprite):
    def __init__(self, pos, image, potion_type, respawn_delay):
        super().__init__()
        self.base_image = image
        self.image = self.base_image
        self.rect = self.image.get_rect(center=pos)
        self.potion_type = potion_type
        self.active = True
        self.last_collected_time = 0
        self.respawn_delay = respawn_delay

    def collect(self):
        self.active = False
        self.last_collected_time = pygame.time.get_ticks()

    def update(self):
        if not self.active:
            current_time = pygame.time.get_ticks()

            if current_time - self.last_collected_time >= self.respawn_delay:
                self.active = True


class NinjaBoss(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.scale_factor = 2.5
        self.frame_size = 200

        self.animations = {
            "idle": self.load_animation("../graphics/boss/Idle.png"),
            "run": self.load_animation("../graphics/boss/Run.png"),
            "jump": self.load_animation("../graphics/boss/Jump.png"),
            "fall": self.load_animation("../graphics/boss/Fall.png"),
            "attack1": self.load_animation("../graphics/boss/Attack1.png"),
            "attack2": self.load_animation("../graphics/boss/Attack2.png"),
            "hurt": self.load_animation("../graphics/boss/Take Hit - white silhouette.png"),
            "death": self.load_animation("../graphics/boss/Death.png")
        }

        self.status = "idle"
        self.frame_index = 0
        self.animation_speed = 0.12
        self.image = self.animations[self.status][self.frame_index]
        self.rect = self.image.get_rect(midbottom=pos)

        self.facing_right = False
        self.direction = pygame.math.Vector2(0, 0)
        self.gravity = 0.8
        self.jump_speed = -25
        self.on_ground = False
        self.jump_cooldown = 900
        self.last_jump_time = 0

        self.walk_speed = 2.4
        self.chase_speed = 4.0
        self.sprint_speed = 5.4
        self.current_speed = self.chase_speed

        self.attack_range = 142
        self.attack_cooldown = 2100
        self.burst_attack_gap = 700
        self.last_attack_time = 0
        self.preferred_distance = 225
        self.close_distance = 85
        self.facing_deadzone = 65

        self.ai_mode = "chase"
        self.ai_mode_start = pygame.time.get_ticks()
        self.ai_mode_duration = random.randint(850, 1600)
        self.orbit_direction = random.choice([-1, 1])
        self.chill_until = 0
        self.next_burst_ready = pygame.time.get_ticks() + 900
        self.burst_attacks_left = 0
        self.random_close_attack_time = 0

        self.max_health = 750
        self.health = self.max_health

        self.attacking = False
        self.attack_active = False
        self.attack_has_hit_player = False
        self.attack_rect = pygame.Rect(0, 0, 0, 0)

        self.dying = False
        self.death_finished = False

        self.update_collision_boxes()
        self.place_hurtbox_midbottom(pos)

    def load_animation(self, path):
        sheet = pygame.image.load(path).convert_alpha()
        frame_count = sheet.get_width() // self.frame_size
        frames = []

        for frame_index in range(frame_count):
            frame = pygame.Surface(
                (self.frame_size, self.frame_size),
                pygame.SRCALPHA
            )

            frame.blit(
                sheet,
                (0, 0),
                pygame.Rect(
                    frame_index * self.frame_size,
                    0,
                    self.frame_size,
                    self.frame_size
                )
            )

            scaled_size = int(self.frame_size * self.scale_factor)
            frame = pygame.transform.scale(
                frame,
                (scaled_size, scaled_size)
            )
            frames.append(frame)

        return frames

    def get_visible_rect(self):
        visible_rect = self.image.get_bounding_rect()
        return visible_rect.move(self.rect.topleft)

    def update_collision_boxes(self):
        visible_rect = self.get_visible_rect()

        hurtbox_width = max(60, visible_rect.width - 115)
        hurtbox_height = max(90, visible_rect.height - 50)

        self.hurtbox = pygame.Rect(
            0,
            0,
            hurtbox_width,
            hurtbox_height
        )
        self.hurtbox.midbottom = visible_rect.midbottom

        body_width = max(30, int(self.hurtbox.width * 0.42))
        body_height = max(65, int(self.hurtbox.height * 0.88))

        self.body_rect = pygame.Rect(
            0,
            0,
            body_width,
            body_height
        )
        self.body_rect.midbottom = self.hurtbox.midbottom

    def place_hurtbox_midbottom(self, pos):
        visible_rect = self.get_visible_rect()

        shift_x = pos[0] - visible_rect.midbottom[0]
        shift_y = pos[1] - visible_rect.midbottom[1]

        self.rect.x += shift_x
        self.rect.y += shift_y

        self.update_collision_boxes()

    def sync_rect_to_visible_feet(self, old_feet):
        self.rect = self.image.get_rect()
        self.update_collision_boxes()

        new_feet = self.get_visible_rect().midbottom
        shift_x = old_feet[0] - new_feet[0]
        shift_y = old_feet[1] - new_feet[1]

        self.rect.x += shift_x
        self.rect.y += shift_y

        self.update_collision_boxes()

    def update_ai_mode(self, current_time):
        if current_time - self.ai_mode_start < self.ai_mode_duration:
            return

        self.ai_mode_start = current_time
        self.ai_mode_duration = random.randint(800, 1700)
        self.ai_mode = random.choice([
            "chase",
            "chase",
            "slow_chase",
            "orbit",
            "orbit",
            "sprint"
        ])

        if random.random() < 0.55:
            self.orbit_direction *= -1

    def start_attack(self, force=False):
        if self.dying or self.attacking or self.status == "hurt":
            return False

        current_time = pygame.time.get_ticks()

        if force:
            if current_time - self.last_attack_time < self.burst_attack_gap:
                return False
        else:
            if current_time - self.last_attack_time < self.attack_cooldown:
                return False

        self.status = random.choice(["attack1", "attack2"])
        self.frame_index = 0
        self.attacking = True
        self.attack_has_hit_player = False
        self.last_attack_time = current_time
        self.direction.x = 0
        self.current_speed = 0
        return True

    def take_damage(self, amount):
        if self.dying:
            return

        self.health -= amount

        if self.health <= 0:
            self.health = 0
            self.start_death()
        else:
            if not self.attacking and self.status not in ["attack1", "attack2"]:
                self.status = "hurt"
                self.frame_index = 0

    def start_death(self):
        self.dying = True
        self.status = "death"
        self.frame_index = 0
        self.attacking = False
        self.attack_active = False
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.direction.x = 0
        self.direction.y = 0

    def update_attack_rect(self):
        self.attack_active = False
        self.attack_rect = pygame.Rect(0, 0, 0, 0)

        if self.status not in ["attack1", "attack2"]:
            return

        current_frame = int(self.frame_index)
        active_attack_frames = 3 <= current_frame <= 5

        if not active_attack_frames:
            return

        self.attack_active = True
        attack_width = 125
        attack_height = 105
        attack_y = self.hurtbox.centery - attack_height // 2

        if self.facing_right:
            attack_x = self.hurtbox.right - 8
        else:
            attack_x = self.hurtbox.left - attack_width + 8

        self.attack_rect = pygame.Rect(
            attack_x,
            attack_y,
            attack_width,
            attack_height
        )

    def can_damage_player(self, player):
        if not self.attack_active:
            return False

        if self.attack_has_hit_player:
            return False

        return self.attack_rect.colliderect(player.hitbox)

    def move_toward_player(self, distance_x, speed):
        self.status = "run"
        self.current_speed = speed

        if distance_x > 0:
            self.direction.x = 1
        else:
            self.direction.x = -1

    def orbit_player(self):
        self.status = "run"
        self.current_speed = self.walk_speed
        self.direction.x = self.orbit_direction

    def choose_action(self, player):
        self.direction.x = 0

        if self.dying or self.status == "hurt" or self.attacking:
            return

        current_time = pygame.time.get_ticks()
        self.update_ai_mode(current_time)

        distance_x = player.hitbox.centerx - self.hurtbox.centerx
        distance_y = player.hitbox.centery - self.hurtbox.centery
        abs_distance_x = abs(distance_x)
        abs_distance_y = abs(distance_y)

        if distance_x > self.facing_deadzone:
            self.facing_right = True
        elif distance_x < -self.facing_deadzone:
            self.facing_right = False

        if (
            distance_y < -65
            and abs_distance_x < 540
            and self.on_ground
            and current_time - self.last_jump_time >= self.jump_cooldown
        ):
            self.direction.y = self.jump_speed
            self.on_ground = False
            self.last_jump_time = current_time

        in_attack_zone = (
            abs_distance_x <= self.attack_range
            and abs_distance_y < 150
        )

        close_enough_for_random = (
            abs_distance_x <= self.attack_range + 30
            and abs_distance_y < 165
        )

        if current_time < self.chill_until:
            if close_enough_for_random and current_time >= self.random_close_attack_time:
                self.random_close_attack_time = current_time + random.randint(700, 1100)

                if random.random() < 0.24:
                    if self.start_attack(force=True):
                        return

            if abs_distance_x > self.preferred_distance + 50:
                self.move_toward_player(distance_x, self.walk_speed)
            else:
                self.orbit_player()

        elif in_attack_zone:
            if self.burst_attacks_left <= 0 and current_time >= self.next_burst_ready:
                self.burst_attacks_left = random.randint(2, 3)

            if self.burst_attacks_left > 0:
                if self.start_attack(force=True):
                    self.burst_attacks_left -= 1

                    if self.burst_attacks_left <= 0:
                        self.chill_until = current_time + random.randint(2200, 3300)
                        self.next_burst_ready = self.chill_until + random.randint(900, 1700)

                    return

            self.orbit_player()

        elif abs_distance_x < self.close_distance:
            self.status = "run"
            self.current_speed = self.walk_speed

            if distance_x > 0:
                self.direction.x = -1
            else:
                self.direction.x = 1

        elif abs_distance_x <= self.preferred_distance:
            if self.ai_mode == "orbit":
                self.orbit_player()
            else:
                self.move_toward_player(distance_x, self.walk_speed)

        elif abs_distance_x <= self.preferred_distance + 180:
            if self.ai_mode == "orbit" and abs_distance_x < self.preferred_distance + 90:
                self.orbit_player()
            elif self.ai_mode == "slow_chase":
                self.move_toward_player(distance_x, self.walk_speed)
            elif self.ai_mode == "sprint":
                self.move_toward_player(distance_x, self.sprint_speed)
            else:
                self.move_toward_player(distance_x, self.chase_speed)

        else:
            self.move_toward_player(distance_x, self.sprint_speed)

        if not self.on_ground:
            if self.direction.y < 0:
                self.status = "jump"
            else:
                self.status = "fall"

    def animate(self):
        old_feet = self.get_visible_rect().midbottom
        animation = self.animations[self.status]
        self.frame_index += self.animation_speed

        if self.frame_index >= len(animation):
            if self.status == "death":
                self.frame_index = len(animation) - 1
                self.death_finished = True
            elif self.status in ["attack1", "attack2"]:
                self.status = "idle"
                self.frame_index = 0
                self.attacking = False
                self.attack_active = False
                self.attack_rect = pygame.Rect(0, 0, 0, 0)
            elif self.status == "hurt":
                self.status = "idle"
                self.frame_index = 0
            else:
                self.frame_index = 0

        animation = self.animations[self.status]
        self.image = animation[int(self.frame_index)]

        if not self.facing_right:
            self.image = pygame.transform.flip(self.image, True, False)

        self.sync_rect_to_visible_feet(old_feet)
        self.update_attack_rect()

    def update(self, player):
        self.choose_action(player)
        self.animate()


class BossChamber:
    def __init__(
        self,
        surface,
        return_to_town,
        tmx_path="../mapData/levels/bossChamber.tmx",
        restart_battle_callback=None
    ):
        self.display_surface = surface
        self.return_to_town = return_to_town
        self.tmx_path = tmx_path
        self.restart_battle_callback = restart_battle_callback

        self.tmx_data = load_pygame(self.tmx_path)
        self.draw_tile_size = 64
        self.level_width = self.tmx_data.width * self.draw_tile_size
        self.level_height = self.tmx_data.height * self.draw_tile_size
        self.y_offset = screen_height - self.level_height

        if self.y_offset < 0:
            self.y_offset = 0

        self.world_height = max(screen_height, self.y_offset + self.level_height)
        self.spawn_y = self.y_offset + self.level_height - self.draw_tile_size * 2
        self.player_start = (150, self.spawn_y)
        self.boss_start = (900, self.spawn_y)

        self.camera_offset = pygame.math.Vector2(0, 0)
        self.background_sprites = pygame.sprite.Group()
        self.terrain_sprites = pygame.sprite.Group()
        self.decoration_sprites = pygame.sprite.Group()
        self.health_potion_sprites = pygame.sprite.Group()
        self.magic_potion_sprites = pygame.sprite.Group()
        self.spell_sprites = pygame.sprite.Group()

        self.collectable_image = pygame.image.load("../graphics/terrainLevel/key_A_gold.png").convert_alpha()
        self.health_potion_image = pygame.image.load("../graphics/terrainLevel/potion_A_red_full.png").convert_alpha()
        self.magic_potion_image = pygame.image.load("../graphics/terrainLevel/potion_A_green_full.png").convert_alpha()
        self.health_potion_image = pygame.transform.scale(self.health_potion_image, (42, 42))
        self.magic_potion_image = pygame.transform.scale(self.magic_potion_image, (42, 42))

        self.max_health = 100
        self.health = 100
        self.max_magic = 100
        self.magic = 100
        self.enemy_damage = self.max_health / 4

        self.boss_hit_chain_start = 0
        self.boss_last_hit_time = 0
        self.boss_hit_chain_gap = 900
        self.boss_stunlock_limit = 5000
        self.boss_counter_cooldown = 6000
        self.last_boss_counter_time = 0

        self.boss_heal_interval = 50000
        self.boss_heal_duration = 7000
        self.boss_heal_percent = 0.35
        self.boss_last_heal_time = pygame.time.get_ticks()
        self.boss_healing = False
        self.boss_heal_start_time = 0
        self.boss_heal_last_update = 0
        self.boss_heal_amount_remaining = 0
        self.boss_heal_rate = 0

        self.max_stamina = 100
        self.stamina = 100
        self.stamina_drain_rate = 10
        self.stamina_regen_rate = 5
        self.stamina_reactivate_amount = 20
        self.attack_stamina_cost = self.max_stamina / 8
        self.stamina_exhausted = False
        self.last_stamina_update = pygame.time.get_ticks()

        self.spell_cost = self.max_magic / 4
        self.spell_damage = 50
        self.spell_button_held = False
        self.B_BUTTON = 1

        self.victory_active = False
        self.victory_start = 0
        self.victory_duration = 3000

        self.death_active = False
        self.death_choice_index = 0
        self.death_confirm_held = False
        self.death_last_move_time = 0
        self.death_move_delay = 180

        # Ending / credits scene
        self.ending_state = "fight"
        self.ending_dialogue = [
            "The guardian falls... and the crystal begins to shine again.",
            "With it, a man emerges from an icy prison, it's your fiance!",
            "I missed you so much.."
        ]
        self.ending_dialogue_index = 0
        self.ending_dialogue_start_time = 0
        self.ending_dialogue_line_duration = 3000

        self.credits_lines = [
            "Eira and The Crystal Promise",
            "",
            "Created By",
            "Zain Arif",
            "Iman Razzaq",
            "Yelixa Tan",
            "",
            "Programming",
            "Zain Arif",
            "Yelixa Tan",
            "",
            "Story",
            "Zain Arif",
            "Yelixa Tan",
            "",
            "Art, Level Design, and Sound Direction",
            "Zain Arif",
            "Yelixa Tan",
            "LuizMelo",
            "Pixel Frog",
            "JumpButton",
            "MonoPixelArt",
            "Cainos",
            "vnitti",
            "David G",
            "Sscary",
            "nyx",
            "brullov",
            "Mattz",
            "",
            "Music",
            "Atlus Sound Team",
            "Pokemon Company",
            "Nintendo"
            "",
            "Thank you for playing",
            "",
            "The End"
        ]
        self.credits_scroll_y = screen_height + 90
        self.credits_scroll_speed = 0.75
        self.credits_finished_time = 0
        self.credits_end_delay = 3000

        self.credits_music_path = "../audio/credits/1-02. Glimpse of a Memory.mp3"
        self.credits_music = None
        self.credits_music_started = False

        self.screen_shake_end = 0
        self.screen_shake_intensity = 0
        self.zero_stamina_input_held = False
        self.stamina_lock_active = False
        self.stamina_lock_end = 0

        self.attack_sound = pygame.mixer.Sound("../audio/sfx/player/attack.mp3")
        self.hurt_sound = pygame.mixer.Sound("../audio/sfx/player/hurt.mp3")
        self.item_sound = pygame.mixer.Sound("../audio/sfx/player/item.mp3")
        self.shield_sound = pygame.mixer.Sound("../audio/sfx/player/shield.mp3")

        self.attack_sound.set_volume(0.45)
        self.hurt_sound.set_volume(0.55)
        self.item_sound.set_volume(0.55)
        self.shield_sound.set_volume(0.55)

        self.parallax_layers = []
        self.background_tint = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA
        )
        self.background_tint.fill((10, 20, 45, 65))
        self.create_parallax_background()

        self.weather_particles = []
        self.create_weather_particles()

        self.load_tmx_level()

        self.player = PlatformerPlayer(self.player_start)
        self.player.can_attack = True
        self.boss = NinjaBoss(self.boss_start)

    def force_boss_counter_attack(self):
        current_time = pygame.time.get_ticks()

        self.last_boss_counter_time = current_time
        self.boss_hit_chain_start = 0
        self.boss_last_hit_time = 0

        if self.player.hitbox.centerx > self.boss.hurtbox.centerx:
            self.boss.facing_right = True
            knockback = 115
        else:
            self.boss.facing_right = False
            knockback = -115

        self.boss.status = "attack2"
        self.boss.frame_index = 0
        self.boss.attacking = True
        self.boss.attack_active = False
        self.boss.attack_has_hit_player = True
        self.boss.direction.x = 0
        self.boss.current_speed = 0

        self.hurt_sound.play()
        self.health -= self.health * 0.5

        if self.health < 1:
            self.health = 1

        self.knock_player_back(knockback, -5)

    def knock_player_back(self, knockback, vertical_push):
        if knockback > 0:
            step = 6
        else:
            step = -6

        distance_left = abs(knockback)

        while distance_left > 0:
            move_amount = min(abs(step), distance_left)

            if step < 0:
                move_amount *= -1

            self.player.hitbox.x += move_amount
            hit_wall = False

            for sprite in self.terrain_sprites:
                if sprite.collision_rect.colliderect(self.player.hitbox):
                    if move_amount > 0:
                        self.player.hitbox.right = sprite.collision_rect.left
                    elif move_amount < 0:
                        self.player.hitbox.left = sprite.collision_rect.right

                    hit_wall = True
                    break

            if hit_wall:
                break

            distance_left -= abs(move_amount)

        self.player.direction.y = vertical_push
        self.player.sync_rect_to_hitbox()

    def clean_name(self, name):
        return name.strip().lower().replace(" ", "").replace("_", "")

    def scale_surface(self, surface):
        return pygame.transform.scale(
            surface,
            (self.draw_tile_size, self.draw_tile_size)
        )

    def load_parallax_layer(self, path, speed):
        try:
            image = pygame.image.load(path).convert_alpha()
            image = pygame.transform.scale(
                image,
                (screen_width, screen_height)
            )

            self.parallax_layers.append({
                "image": image,
                "speed": speed
            })

        except:
            print("Could not load parallax layer:", path)

    def create_parallax_background(self):
        self.parallax_layers = []
        folder = "../graphics/backgrounds/level 2/"

        self.load_parallax_layer(folder + "sky_lightened.png", 0.00)
        self.load_parallax_layer(folder + "clouds_bg.png", 0.05)
        self.load_parallax_layer(folder + "glacial_mountains_lightened.png", 0.12)
        self.load_parallax_layer(folder + "glacial_mountains.png", 0.20)
        self.load_parallax_layer(folder + "clouds_mg_3.png", 0.30)
        self.load_parallax_layer(folder + "clouds_mg_2.png", 0.42)
        self.load_parallax_layer(folder + "clouds_mg_1_lightened.png", 0.55)
        self.load_parallax_layer(folder + "clouds_mg_1.png", 0.70)
        self.load_parallax_layer(folder + "cloud_lonely.png", 0.90)

    def draw_parallax_background(self):
        if len(self.parallax_layers) == 0:
            self.display_surface.fill("black")
            return

        for layer in self.parallax_layers:
            image = layer["image"]
            speed = layer["speed"]

            x_offset = -self.camera_offset.x * speed
            x_offset = x_offset % screen_width

            self.display_surface.blit(
                image,
                (x_offset - screen_width, 0)
            )
            self.display_surface.blit(
                image,
                (x_offset, 0)
            )
            self.display_surface.blit(
                image,
                (x_offset + screen_width, 0)
            )

        self.display_surface.blit(self.background_tint, (0, 0))

    def create_weather_particles(self):
        self.weather_particles = []

        for i in range(280):
            particle = {
                "x": random.randint(0, self.level_width),
                "y": random.randint(0, self.world_height),
                "speed": random.uniform(2.0, 4.5),
                "drift": random.uniform(-0.8, 0.8),
                "size": random.randint(2, 5),
                "alpha": random.randint(100, 190)
            }
            self.weather_particles.append(particle)

    def draw_weather(self):
        weather_surface = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA
        )

        for particle in self.weather_particles:
            particle["x"] += particle["drift"]
            particle["y"] += particle["speed"]

            if particle["y"] > self.world_height:
                particle["y"] = random.randint(-80, -10)
                particle["x"] = random.randint(0, self.level_width)

            if particle["x"] < 0:
                particle["x"] = self.level_width

            if particle["x"] > self.level_width:
                particle["x"] = 0

            screen_x = particle["x"] - self.camera_offset.x
            screen_y = particle["y"] - self.camera_offset.y

            if -100 < screen_x < screen_width + 100 and -100 < screen_y < screen_height + 100:
                pygame.draw.circle(
                    weather_surface,
                    (235, 235, 240, particle["alpha"]),
                    (int(screen_x), int(screen_y)),
                    particle["size"]
                )

        self.display_surface.blit(weather_surface, (0, 0))

    def load_tmx_level(self):
        for layer in self.tmx_data.layers:
            if isinstance(layer, TiledTileLayer):
                layer_name = self.clean_name(layer.name)

                if layer_name in ["background", "bg"]:
                    self.create_visual_tile_layer(layer, self.background_sprites, False)
                elif layer_name in ["floor", "terrain"]:
                    self.create_visual_tile_layer(layer, self.terrain_sprites, True)
                elif layer_name in ["decor", "decoration", "decorations"]:
                    self.create_visual_tile_layer(layer, self.decoration_sprites, False)
                elif layer_name in ["collision", "collisions"]:
                    self.create_collision_layer(layer)
                elif layer_name in ["player", "playerstart"]:
                    self.create_player_layer(layer)
                elif layer_name == "boss":
                    self.create_boss_layer(layer)
                elif layer_name in ["health", "healthpotion", "healthpotions"]:
                    self.create_potion_layer(layer, self.health_potion_image, self.health_potion_sprites, "health")
                elif layer_name in ["magic", "magicpotion", "magicpotions"]:
                    self.create_potion_layer(layer, self.magic_potion_image, self.magic_potion_sprites, "magic")

    def create_visual_tile_layer(self, layer, group, solid=False):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    tile_surface = self.tmx_data.get_tile_image_by_gid(gid)

                    if tile_surface is not None:
                        x = col_index * self.draw_tile_size
                        y = row_index * self.draw_tile_size + self.y_offset
                        sprite = pygame.sprite.Sprite()
                        sprite.image = self.scale_surface(tile_surface)
                        sprite.rect = sprite.image.get_rect(topleft=(x, y))

                        if solid:
                            solid_rect = sprite.image.get_bounding_rect()
                            sprite.collision_rect = solid_rect.move(sprite.rect.topleft)

                        group.add(sprite)

    def create_collision_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size
                    y = row_index * self.draw_tile_size + self.y_offset
                    sprite = pygame.sprite.Sprite()
                    sprite.image = pygame.Surface(
                        (self.draw_tile_size, self.draw_tile_size),
                        pygame.SRCALPHA
                    )
                    sprite.rect = sprite.image.get_rect(topleft=(x, y))
                    sprite.collision_rect = sprite.rect.copy()
                    self.terrain_sprites.add(sprite)

    def create_player_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset + self.draw_tile_size
                    self.player_start = (x, y)
                    return

    def create_boss_layer(self, layer):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset
                    self.boss_start = (x, y)
                    return

    def create_potion_layer(self, layer, image, group, potion_type):
        for row_index, row in enumerate(layer.data):
            for col_index, gid in enumerate(row):
                if gid != 0:
                    x = col_index * self.draw_tile_size + self.draw_tile_size // 2
                    y = row_index * self.draw_tile_size + self.y_offset + self.draw_tile_size // 2

                    if potion_type == "magic":
                        respawn_delay = 45000
                    else:
                        respawn_delay = 30000

                    potion = RespawningPotion(
                        (x, y),
                        image,
                        potion_type,
                        respawn_delay
                    )

                    group.add(potion)

    def handle_spell_input(self):
        keys = pygame.key.get_pressed()
        spell_pressed = keys[pygame.K_c]

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)

            if joystick.get_numbuttons() > self.B_BUTTON:
                if joystick.get_button(self.B_BUTTON):
                    spell_pressed = True

        if spell_pressed and not self.spell_button_held:
            self.cast_spell()

        self.spell_button_held = spell_pressed

    def cast_spell(self):
        if self.magic < self.spell_cost:
            return

        if (
            self.player.attacking
            or self.player.spell_casting
            or self.player.shielding
            or getattr(self.player, "dead", False)
        ):
            return

        self.magic -= self.spell_cost
        self.player.start_spell()

        if self.player.facing_right:
            start_pos = (
                self.player.hitbox.right + 5,
                self.player.hitbox.centery
            )
            direction = 1
        else:
            start_pos = (
                self.player.hitbox.left - 5,
                self.player.hitbox.centery
            )
            direction = -1

        laser = MagicLaser(start_pos, direction)
        self.spell_sprites.add(laser)

    def check_attack_sound(self, was_attacking):
        if self.player.attacking and not was_attacking:
            self.attack_sound.play()

    def start_screen_shake(self, duration=220, intensity=7):
        self.screen_shake_end = pygame.time.get_ticks() + duration
        self.screen_shake_intensity = intensity

    def trigger_stamina_empty_penalty(self):
        current_time = pygame.time.get_ticks()
        self.stamina = 0
        self.stamina_exhausted = True
        self.stamina_lock_active = True
        self.stamina_lock_end = current_time + 1500
        self.player.can_attack = False
        self.player.shield_enabled = False
        self.player.stop_shield()
        self.player.attacking = False
        self.player.spell_casting = False
        self.player.attack_immunity = False
        self.player.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.player.direction.x = 0
        self.start_screen_shake()

    def handle_zero_stamina_feedback(self):
        if self.stamina > 0:
            self.zero_stamina_input_held = False
            return

        keys = pygame.key.get_pressed()
        zero_stamina_pressed = (
            keys[pygame.K_x]
            or keys[pygame.K_LSHIFT]
            or keys[pygame.K_RSHIFT]
        )

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)

            if joystick.get_numbuttons() > self.player.Y_BUTTON:
                if joystick.get_button(self.player.Y_BUTTON):
                    zero_stamina_pressed = True

            if joystick.get_numbuttons() > self.player.LB_BUTTON:
                if joystick.get_button(self.player.LB_BUTTON):
                    zero_stamina_pressed = True

            if joystick.get_numaxes() > self.player.LT_AXIS:
                if joystick.get_axis(self.player.LT_AXIS) > self.player.LT_DEADZONE:
                    zero_stamina_pressed = True

        if zero_stamina_pressed and not self.zero_stamina_input_held:
            self.trigger_stamina_empty_penalty()

        self.zero_stamina_input_held = zero_stamina_pressed

    def apply_stamina_lock(self):
        if not self.stamina_lock_active:
            return

        current_time = pygame.time.get_ticks()

        if current_time >= self.stamina_lock_end:
            self.stamina_lock_active = False
            return

        self.player.direction.x = 0
        self.player.attacking = False
        self.player.spell_casting = False
        self.player.shielding = False
        self.player.shield_raised = False
        self.player.attack_immunity = False
        self.player.attack_rect = pygame.Rect(0, 0, 0, 0)
        self.player.can_attack = False
        self.player.shield_enabled = False

        if self.player.on_ground:
            self.player.status = "idle"

    def update_stamina(self):
        current_time = pygame.time.get_ticks()
        delta_time = (current_time - self.last_stamina_update) / 1000.0
        self.last_stamina_update = current_time

        if self.stamina_lock_active:
            self.stamina = 0
            self.apply_stamina_lock()
            return

        if self.player.shielding:
            self.stamina -= self.stamina_drain_rate * delta_time

            if self.stamina <= 0:
                self.trigger_stamina_empty_penalty()
                return
        else:
            self.stamina += self.stamina_regen_rate * delta_time

            if self.stamina > self.max_stamina:
                self.stamina = self.max_stamina

        if self.stamina_exhausted:
            if self.stamina >= self.stamina_reactivate_amount:
                self.stamina_exhausted = False
                self.player.shield_enabled = True
        else:
            self.player.shield_enabled = self.stamina > 0

        self.player.can_attack = self.stamina >= self.attack_stamina_cost

        if self.stamina < self.attack_stamina_cost and self.player.attacking:
            self.trigger_stamina_empty_penalty()

    def horizontal_movement_collision(self):
        player = self.player
        player.hitbox.x += player.direction.x * player.speed

        for sprite in self.terrain_sprites:
            if sprite.collision_rect.colliderect(player.hitbox):
                if player.direction.x < 0:
                    player.hitbox.left = sprite.collision_rect.right
                elif player.direction.x > 0:
                    player.hitbox.right = sprite.collision_rect.left

        player.sync_rect_to_hitbox()

    def vertical_movement_collision(self):
        player = self.player
        player.on_ground = False
        player.on_ceiling = False
        player.apply_gravity()

        for sprite in self.terrain_sprites:
            if sprite.collision_rect.colliderect(player.hitbox):
                if player.direction.y > 0:
                    player.hitbox.bottom = sprite.collision_rect.top
                    player.direction.y = 0
                    player.on_ground = True
                elif player.direction.y < 0:
                    player.hitbox.top = sprite.collision_rect.bottom
                    player.direction.y = 0
                    player.on_ceiling = True

        player.sync_rect_to_hitbox()

    def boss_horizontal_movement_collision(self):
        if self.boss.death_finished:
            return

        self.boss.rect.x += self.boss.direction.x * self.boss.current_speed
        self.boss.update_collision_boxes()

        for sprite in self.terrain_sprites:
            if sprite.collision_rect.colliderect(self.boss.hurtbox):
                if self.boss.direction.x < 0:
                    shift = sprite.collision_rect.right - self.boss.hurtbox.left
                    self.boss.rect.x += shift
                    self.boss.orbit_direction = 1
                elif self.boss.direction.x > 0:
                    shift = sprite.collision_rect.left - self.boss.hurtbox.right
                    self.boss.rect.x += shift
                    self.boss.orbit_direction = -1

                self.boss.direction.x = 0
                self.boss.update_collision_boxes()

    def boss_vertical_movement_collision(self):
        if self.boss.death_finished:
            return

        self.boss.on_ground = False
        self.boss.direction.y += self.boss.gravity
        self.boss.rect.y += self.boss.direction.y
        self.boss.update_collision_boxes()

        for sprite in self.terrain_sprites:
            if sprite.collision_rect.colliderect(self.boss.hurtbox):
                if self.boss.direction.y > 0:
                    shift = sprite.collision_rect.top - self.boss.hurtbox.bottom
                    self.boss.rect.y += shift
                    self.boss.direction.y = 0
                    self.boss.on_ground = True
                elif self.boss.direction.y < 0:
                    shift = sprite.collision_rect.bottom - self.boss.hurtbox.top
                    self.boss.rect.y += shift
                    self.boss.direction.y = 0

                self.boss.update_collision_boxes()

    def boss_body_collision(self):
        if self.boss.dying:
            return

        if self.boss.attacking or self.player.attacking or self.player.spell_casting:
            return

        if self.boss.body_rect.colliderect(self.player.hitbox):
            overlap_left = self.player.hitbox.right - self.boss.body_rect.left
            overlap_right = self.boss.body_rect.right - self.player.hitbox.left
            smaller_overlap = min(overlap_left, overlap_right)

            if smaller_overlap < 8:
                return

            push_amount = min(6, smaller_overlap)

            if overlap_left < overlap_right:
                self.player.hitbox.x -= push_amount
            else:
                self.player.hitbox.x += push_amount

            for sprite in self.terrain_sprites:
                if sprite.collision_rect.colliderect(self.player.hitbox):
                    if overlap_left < overlap_right:
                        self.player.hitbox.left = sprite.collision_rect.right
                    else:
                        self.player.hitbox.right = sprite.collision_rect.left

            self.player.sync_rect_to_hitbox()

    def check_player_attack_boss(self):
        if self.boss.dying:
            return

        if self.player.attacking and self.stamina < self.attack_stamina_cost:
            self.trigger_stamina_empty_penalty()
            return

        if self.stamina < self.attack_stamina_cost:
            return

        if self.player.attacking:
            if self.player.attack_rect.colliderect(self.boss.hurtbox):
                if self.boss not in self.player.enemies_hit_this_attack:
                    current_time = pygame.time.get_ticks()

                    if current_time - self.boss_last_hit_time > self.boss_hit_chain_gap:
                        self.boss_hit_chain_start = current_time

                    self.boss_last_hit_time = current_time
                    self.cancel_boss_healing_cycle()
                    self.boss.take_damage(25)
                    self.player.enemies_hit_this_attack.append(self.boss)
                    self.stamina -= self.attack_stamina_cost

                    if self.stamina <= 0:
                        self.trigger_stamina_empty_penalty()
                        return

                    if (
                        current_time - self.boss_hit_chain_start >= self.boss_stunlock_limit
                        and current_time - self.last_boss_counter_time >= self.boss_counter_cooldown
                    ):
                        self.force_boss_counter_attack()

    def check_spell_boss_collision(self):
        if self.boss.dying:
            return

        for laser in self.spell_sprites:
            if laser.rect.colliderect(self.boss.hurtbox):
                self.cancel_boss_healing_cycle()
                self.boss.take_damage(self.spell_damage)
                laser.kill()

    def check_boss_damage(self):
        if self.boss.can_damage_player(self.player):
            self.boss.attack_has_hit_player = True

            if getattr(self.player, "shielding", False):
                self.shield_sound.play()
                return

            self.hurt_sound.play()
            self.health -= self.enemy_damage

            if self.health < 0:
                self.health = 0

    def check_potions(self):
        for potion in self.health_potion_sprites:
            if potion.active and potion.rect.colliderect(self.player.hitbox):
                potion.collect()
                self.item_sound.play()
                self.health += 25

                if self.health > self.max_health:
                    self.health = self.max_health

        for potion in self.magic_potion_sprites:
            if potion.active and potion.rect.colliderect(self.player.hitbox):
                potion.collect()
                self.item_sound.play()
                self.magic += 25

                if self.magic > self.max_magic:
                    self.magic = self.max_magic

    def reset_player_if_fallen(self):
        if self.player.hitbox.top > self.world_height + 300:
            self.player.hitbox.midbottom = self.player_start
            self.player.direction.y = 0
            self.player.sync_rect_to_hitbox()
            self.health -= 20

            if self.health < 0:
                self.health = 0

    def start_death_sequence(self):
        if self.death_active:
            return

        self.health = 0
        self.death_active = True
        self.death_choice_index = 0 if self.magic >= self.max_magic else 1
        self.player.start_death()

    def check_player_death(self):
        if self.health <= 0:
            self.start_death_sequence()

    def revive_player(self):
        self.health = self.max_health
        self.magic = 0
        self.stamina = self.max_stamina
        self.death_active = False
        self.player.can_attack = True
        self.player.revive()

    def restart_battle(self):
        if self.restart_battle_callback is not None:
            self.restart_battle_callback()
        else:
            self.__init__(
                self.display_surface,
                self.return_to_town,
                self.tmx_path
            )

    def death_menu_move(self, direction):
        self.death_choice_index += direction

        if self.death_choice_index < 0:
            self.death_choice_index = 2

        if self.death_choice_index > 2:
            self.death_choice_index = 0

    def confirm_death_choice(self):
        if self.death_choice_index == 0:
            if self.magic >= self.max_magic:
                self.revive_player()
        elif self.death_choice_index == 1:
            self.restart_battle()
        elif self.death_choice_index == 2:
            self.return_to_town()

    def handle_death_menu_input(self):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()
        move_direction = 0
        confirm_pressed = keys[pygame.K_SPACE] or keys[pygame.K_RETURN]

        if current_time - self.death_last_move_time >= self.death_move_delay:
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                move_direction = -1
            elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
                move_direction = 1

        if pygame.joystick.get_count() > 0:
            joystick = pygame.joystick.Joystick(0)

            if current_time - self.death_last_move_time >= self.death_move_delay:
                if joystick.get_numhats() > 0:
                    hat_x, hat_y = joystick.get_hat(0)

                    if hat_y > 0:
                        move_direction = -1
                    elif hat_y < 0:
                        move_direction = 1

                if joystick.get_numaxes() > 1:
                    stick_y = joystick.get_axis(1)

                    if stick_y < -0.5:
                        move_direction = -1
                    elif stick_y > 0.5:
                        move_direction = 1

            if joystick.get_numbuttons() > 0:
                if joystick.get_button(0):
                    confirm_pressed = True

        if move_direction != 0:
            self.death_menu_move(move_direction)
            self.death_last_move_time = current_time

        if confirm_pressed and not self.death_confirm_held:
            self.confirm_death_choice()

        self.death_confirm_held = confirm_pressed

    def draw_death_screen(self):
        screen_copy = self.display_surface.copy()
        small_width = max(1, screen_width // 8)
        small_height = max(1, screen_height // 8)
        small_surface = pygame.transform.smoothscale(
            screen_copy,
            (small_width, small_height)
        )
        blur_surface = pygame.transform.smoothscale(
            small_surface,
            (screen_width, screen_height)
        )
        self.display_surface.blit(blur_surface, (0, 0))

        overlay = pygame.Surface(
            (screen_width, screen_height),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 130))
        self.display_surface.blit(overlay, (0, 0))

        box_rect = pygame.Rect(
            screen_width // 2 - 280,
            185,
            560,
            330
        )
        pygame.draw.rect(self.display_surface, (20, 20, 30), box_rect)
        pygame.draw.rect(self.display_surface, (220, 220, 230), box_rect, 4)

        title_font = pygame.font.Font(None, 56)
        option_font = pygame.font.Font(None, 38)
        hint_font = pygame.font.Font(None, 28)

        title = title_font.render(
            "Eira has fallen",
            True,
            (255, 255, 255)
        )
        title_rect = title.get_rect(
            center=(box_rect.centerx, box_rect.y + 55)
        )
        self.display_surface.blit(title, title_rect)

        options = [
            "Revive - Full magic required",
            "Restart battle",
            "Return to town"
        ]

        for index, option in enumerate(options):
            y = box_rect.y + 125 + index * 52

            if index == 0 and self.magic < self.max_magic:
                color = (100, 100, 100)
            elif index == self.death_choice_index:
                color = (255, 230, 120)
            else:
                color = (230, 230, 230)

            label = "> " + option if index == self.death_choice_index else "  " + option
            text = option_font.render(label, True, color)
            self.display_surface.blit(text, (box_rect.x + 55, y))

        if self.magic < self.max_magic:
            message = "Magic not full: revive unavailable"
            message_color = (150, 150, 150)
        else:
            message = "Revive keeps boss progress but uses all magic"
            message_color = (180, 255, 180)

        hint = hint_font.render(
            message,
            True,
            message_color
        )
        self.display_surface.blit(
            hint,
            (box_rect.x + 55, box_rect.y + 285)
        )

    def cancel_boss_healing_cycle(self):
        if not self.boss_healing:
            return

        self.boss_healing = False
        self.boss_heal_amount_remaining = 0
        self.boss_heal_rate = 0
        self.boss_last_heal_time = pygame.time.get_ticks()

    def update_boss_healing(self):
        if self.boss.dying or self.victory_active or self.death_active or self.ending_state != "fight":
            return

        current_time = pygame.time.get_ticks()

        if not self.boss_healing:
            if current_time - self.boss_last_heal_time >= self.boss_heal_interval:
                missing_health = self.boss.max_health - self.boss.health

                if missing_health <= 0:
                    self.boss_last_heal_time = current_time
                    return

                self.boss_healing = True
                self.boss_heal_start_time = current_time
                self.boss_heal_last_update = current_time
                self.boss_heal_amount_remaining = min(
                    self.boss.max_health * self.boss_heal_percent,
                    missing_health
                )
                self.boss_heal_rate = self.boss_heal_amount_remaining / (self.boss_heal_duration / 1000.0)

            return

        delta_time = (current_time - self.boss_heal_last_update) / 1000.0
        self.boss_heal_last_update = current_time
        heal_amount = self.boss_heal_rate * delta_time

        if heal_amount > self.boss_heal_amount_remaining:
            heal_amount = self.boss_heal_amount_remaining

        self.boss.health += heal_amount
        self.boss_heal_amount_remaining -= heal_amount

        if self.boss.health > self.boss.max_health:
            self.boss.health = self.boss.max_health
            self.boss_heal_amount_remaining = 0

        if (
            self.boss_heal_amount_remaining <= 0
            or current_time - self.boss_heal_start_time >= self.boss_heal_duration
        ):
            self.boss_healing = False
            self.boss_last_heal_time = current_time

    def start_ending_music(self):
        if self.credits_music_started:
            return

        self.credits_music_started = True
        pygame.mixer.stop()

        try:
            self.credits_music = pygame.mixer.Sound(self.credits_music_path)
            self.credits_music.set_volume(0.5)
            self.credits_music.play(loops=-1)
        except:
            print("Credits music not found:", self.credits_music_path)

    def start_ending_dialogue(self):
        self.victory_active = True
        self.ending_state = "dialogue"
        self.ending_dialogue_index = 0
        self.ending_dialogue_start_time = pygame.time.get_ticks()
        self.player.direction.x = 0
        self.player.direction.y = 0
        self.player.attacking = False
        self.player.spell_casting = False
        self.player.shielding = False
        self.player.status = "idle"
        self.player.frame_index = 0
        self.start_ending_music()

    def start_credits(self):
        self.ending_state = "credits"
        self.credits_scroll_y = screen_height + 90
        self.credits_finished_time = 0

    def update_ending_scene(self):
        current_time = pygame.time.get_ticks()

        if self.ending_state == "dialogue":
            if current_time - self.ending_dialogue_start_time >= self.ending_dialogue_line_duration:
                self.ending_dialogue_index += 1

                if self.ending_dialogue_index >= len(self.ending_dialogue):
                    self.start_credits()
                else:
                    self.ending_dialogue_start_time = current_time

        elif self.ending_state == "credits":
            self.credits_scroll_y -= self.credits_scroll_speed

            final_line_y = self.credits_scroll_y + len(self.credits_lines) * 52

            if final_line_y < screen_height // 2 and self.credits_finished_time == 0:
                self.credits_finished_time = current_time

            if (
                self.credits_finished_time != 0
                and current_time - self.credits_finished_time >= self.credits_end_delay
            ):
                if self.credits_music is not None:
                    self.credits_music.stop()

                self.return_to_town()

    def check_boss_defeated(self):
        if self.boss.death_finished and self.ending_state == "fight":
            self.start_ending_dialogue()

    def update_camera(self):
        target_x = self.player.hitbox.centerx - screen_width // 2
        target_y = self.player.hitbox.centery - screen_height // 2
        max_x = max(0, self.level_width - screen_width)
        max_y = max(0, self.world_height - screen_height)
        self.camera_offset.x = max(0, min(target_x, max_x))
        self.camera_offset.y = max(0, min(target_y, max_y))

        current_time = pygame.time.get_ticks()

        if current_time < self.screen_shake_end:
            shake_x = random.randint(
                -self.screen_shake_intensity,
                self.screen_shake_intensity
            )
            shake_y = random.randint(
                -self.screen_shake_intensity,
                self.screen_shake_intensity
            )
            self.camera_offset.x = max(0, min(self.camera_offset.x + shake_x, max_x))
            self.camera_offset.y = max(0, min(self.camera_offset.y + shake_y, max_y))

    def draw_sprite_group(self, group):
        for sprite in group:
            offset_x = sprite.rect.x - self.camera_offset.x
            offset_y = sprite.rect.y - self.camera_offset.y
            self.display_surface.blit(sprite.image, (offset_x, offset_y))

    def draw_potions(self):
        for potion in self.health_potion_sprites:
            if potion.active:
                offset_x = potion.rect.x - self.camera_offset.x
                offset_y = potion.rect.y - self.camera_offset.y
                self.display_surface.blit(potion.image, (offset_x, offset_y))

        for potion in self.magic_potion_sprites:
            if potion.active:
                offset_x = potion.rect.x - self.camera_offset.x
                offset_y = potion.rect.y - self.camera_offset.y
                self.display_surface.blit(potion.image, (offset_x, offset_y))

    def draw_player_bars(self):
        bar_x = 30
        bar_y = 25
        bar_width = 220
        bar_height = 18
        gap = 8

        health_ratio = self.health / self.max_health
        magic_ratio = self.magic / self.max_magic
        stamina_ratio = self.stamina / self.max_stamina

        pygame.draw.rect(
            self.display_surface,
            (35, 35, 45),
            (bar_x, bar_y, bar_width, bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (180, 40, 40),
            (bar_x, bar_y, int(bar_width * health_ratio), bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (230, 230, 230),
            (bar_x, bar_y, bar_width, bar_height),
            3
        )

        magic_y = bar_y + bar_height + gap
        pygame.draw.rect(
            self.display_surface,
            (35, 35, 45),
            (bar_x, magic_y, bar_width, bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (60, 180, 80),
            (bar_x, magic_y, int(bar_width * magic_ratio), bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (230, 230, 230),
            (bar_x, magic_y, bar_width, bar_height),
            3
        )

        stamina_y = magic_y + bar_height + gap
        pygame.draw.rect(
            self.display_surface,
            (35, 35, 45),
            (bar_x, stamina_y, bar_width, bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (210, 170, 60),
            (bar_x, stamina_y, int(bar_width * stamina_ratio), bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (230, 230, 230),
            (bar_x, stamina_y, bar_width, bar_height),
            3
        )

    def draw_boss_bar(self):
        if self.boss.health <= 0:
            return

        bar_width = 650
        bar_height = 22
        bar_x = screen_width // 2 - bar_width // 2
        bar_y = 25
        health_ratio = self.boss.health / self.boss.max_health

        pygame.draw.rect(
            self.display_surface,
            (25, 20, 28),
            (bar_x, bar_y, bar_width, bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (150, 30, 70),
            (bar_x, bar_y, int(bar_width * health_ratio), bar_height)
        )
        pygame.draw.rect(
            self.display_surface,
            (235, 235, 245),
            (bar_x, bar_y, bar_width, bar_height),
            3
        )

        font = pygame.font.Font(None, 32)
        text = font.render("Ninja Guardian", True, (255, 255, 255))
        text_rect = text.get_rect(center=(screen_width // 2, bar_y + 45))
        self.display_surface.blit(text, text_rect)

    def draw_text_box(self, text):
        box_rect = pygame.Rect(60, 500, 1160, 160)
        pygame.draw.rect(self.display_surface, (20, 20, 30), box_rect)
        pygame.draw.rect(self.display_surface, (200, 200, 220), box_rect, 4)

        font = pygame.font.Font("EagleLake-Regular.ttf", 30)
        small_font = pygame.font.Font("EagleLake-Regular.ttf", 17)

        words = text.split(" ")
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "

            if font.size(test_line)[0] <= box_rect.width - 70:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "

        if current_line.strip() != "":
            lines.append(current_line.strip())

        for index, line in enumerate(lines[:3]):
            text_surface = font.render(line, True, (255, 255, 255))
            self.display_surface.blit(
                text_surface,
                (box_rect.x + 35, box_rect.y + 35 + index * 38)
            )

        hint = small_font.render(
            "The story continues...",
            True,
            (180, 180, 180)
        )
        self.display_surface.blit(hint, (box_rect.right - 285, box_rect.bottom - 35))

    def draw_ending_dialogue(self):
        if self.ending_state != "dialogue":
            return

        if self.ending_dialogue_index < len(self.ending_dialogue):
            self.draw_text_box(
                self.ending_dialogue[self.ending_dialogue_index]
            )

    def draw_credits_screen(self):
        self.display_surface.fill((0, 0, 0))

        title_font = pygame.font.Font("EagleLake-Regular.ttf", 48)
        line_font = pygame.font.Font("EagleLake-Regular.ttf", 30)

        for index, line in enumerate(self.credits_lines):
            y = self.credits_scroll_y + index * 52

            if -80 < y < screen_height + 80:
                if index == 0 or line == "The End":
                    font = title_font
                    color = (255, 255, 255)
                elif line == "":
                    continue
                else:
                    font = line_font
                    color = (220, 220, 230)

                text_surface = font.render(line, True, color)
                text_rect = text_surface.get_rect(
                    center=(screen_width // 2, y)
                )
                self.display_surface.blit(text_surface, text_rect)

    def draw_chamber(self):
        if self.ending_state == "credits":
            self.draw_credits_screen()
            return

        self.draw_parallax_background()
        self.draw_sprite_group(self.background_sprites)
        self.draw_sprite_group(self.terrain_sprites)
        self.draw_sprite_group(self.decoration_sprites)
        self.draw_potions()

        boss_x = self.boss.rect.x - self.camera_offset.x
        boss_y = self.boss.rect.y - self.camera_offset.y
        self.display_surface.blit(self.boss.image, (boss_x, boss_y))

        self.draw_sprite_group(self.spell_sprites)

        player_x = self.player.rect.x - self.camera_offset.x
        player_y = self.player.rect.y - self.camera_offset.y
        self.display_surface.blit(self.player.image, (player_x, player_y))

        self.draw_weather()

        if self.ending_state == "fight":
            self.draw_player_bars()
            self.draw_boss_bar()

        self.draw_ending_dialogue()

    def run(self):
        if self.death_active:
            self.handle_death_menu_input()
            self.update_camera()
            self.draw_chamber()
            self.draw_death_screen()
            return

        if self.ending_state != "fight":
            self.update_ending_scene()
            self.update_camera()
            self.draw_chamber()
            return

        self.handle_zero_stamina_feedback()
        self.handle_spell_input()

        was_attacking = self.player.attacking
        self.player.update()
        self.apply_stamina_lock()
        self.check_attack_sound(was_attacking)
        self.update_stamina()
        self.apply_stamina_lock()

        self.horizontal_movement_collision()
        self.vertical_movement_collision()

        if not self.victory_active:
            self.boss.update(self.player)
            self.boss_horizontal_movement_collision()
            self.boss_vertical_movement_collision()
            self.boss_body_collision()
            self.check_boss_damage()
            self.update_boss_healing()

        self.spell_sprites.update()
        self.health_potion_sprites.update()
        self.magic_potion_sprites.update()

        self.check_spell_boss_collision()
        self.check_player_attack_boss()
        self.check_potions()
        self.reset_player_if_fallen()
        self.check_player_death()
        self.check_boss_defeated()
        self.update_camera()
        self.draw_chamber()
