import pygame
import math
import os
import random

class Obstacle:
    RADIUS = 30   # collision radius
    SIZE   = 64   # display size in pixels
    _image = None # shared class-level cached image

    @classmethod
    def load_image(cls, assets_dir):
        img = pygame.image.load(os.path.join(assets_dir, 'rock.png')).convert()
        img.set_colorkey((255, 255, 255))   # remove white background
        cls._image = pygame.transform.scale(img, (cls.SIZE, cls.SIZE))

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def move(self, speed):
        self.y += speed

    def draw(self, screen):
        if self._image:
            rect = self._image.get_rect(center=(int(self.x), int(self.y)))
            screen.blit(self._image, rect.topleft)
        else:
            # fallback circle if image not loaded
            pygame.draw.circle(screen, (120, 120, 120), (int(self.x), int(self.y)), self.RADIUS)

    def is_off_screen(self, height):
        return self.y > height + self.RADIUS

    def collides_with(self, car_x, car_y, car_radius=28):
        dist = math.hypot(self.x - car_x, self.y - car_y)
        return dist < (self.RADIUS + car_radius)


class GameEngine:
    TRACK_LEFT  = 150
    TRACK_RIGHT = 650   # Keep car within the visible track

    def __init__(self, width=800, height=600):
        pygame.init()
        self.width  = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Virtual Steering Racing")
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_large = pygame.font.SysFont("Arial", 42, bold=True)
        self.font_small  = pygame.font.SysFont("Arial", 28)

        # Load assets
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.car_img = pygame.image.load(os.path.join(assets_dir, 'car.png')).convert()
        self.car_img.set_colorkey((255, 255, 255))

        car_rect = self.car_img.get_rect()
        scale_factor = 100 / max(car_rect.width, car_rect.height)
        new_size = (int(car_rect.width * scale_factor), int(car_rect.height * scale_factor))
        self.car_img = pygame.transform.scale(self.car_img, new_size)

        # Pre-load shared rock image
        Obstacle.load_image(assets_dir)

        self.track_img = pygame.image.load(os.path.join(assets_dir, 'track.png')).convert()
        self.track_img = pygame.transform.scale(self.track_img, (self.width, self.height))

        self._reset_state()

    # ------------------------------------------------------------------
    def _reset_state(self):
        self.car_x       = self.width / 2
        self.car_y       = self.height - 150
        self.speed       = 5.0
        self.bg_y        = 0
        self.visual_angle = 0

        # Scoring (one hit = game over)
        self.score     = 0
        self.game_over = False

        # Obstacle spawning
        self.obstacles       = []
        self.spawn_timer     = 0
        self.spawn_interval  = 90   # frames between spawns (decreases over time)

        # Invincibility frames after a hit
        self.hit_flash       = 0

    # ------------------------------------------------------------------
    def _spawn_obstacle(self):
        x = random.randint(self.TRACK_LEFT + 30, self.TRACK_RIGHT - 30)
        self.obstacles.append(Obstacle(x, -Obstacle.RADIUS))

    # ------------------------------------------------------------------
    def update(self, steering_angle):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and self.game_over:
                    self._reset_state()

        if self.game_over:
            return True   # keep window open, show game-over screen

        # ---- Steering ------------------------------------------------
        horizontal_speed = steering_angle * 0.15
        self.car_x += horizontal_speed
        self.car_x  = max(self.TRACK_LEFT, min(self.TRACK_RIGHT, self.car_x))
        self.visual_angle = -steering_angle * 0.5

        # ---- Background scroll ---------------------------------------
        self.bg_y += self.speed
        if self.bg_y >= self.height:
            self.bg_y -= self.height

        # ---- Speed ramp-up (makes the game harder over time) ----------
        self.speed = min(5.0 + self.score / 300, 14.0)

        # ---- Spawn obstacles -----------------------------------------
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self._spawn_obstacle()
            self.spawn_timer = 0
            # Gradually reduce spawn interval (more obstacles as score grows)
            self.spawn_interval = max(35, 90 - self.score // 20)

        # ---- Move & check obstacles ----------------------------------
        if self.hit_flash > 0:
            self.hit_flash -= 1

        survived_obstacles = []
        for obs in self.obstacles:
            obs.move(self.speed)
            if obs.is_off_screen(self.height):
                # Dodged! +10 points
                self.score += 10
                continue
            if obs.collides_with(self.car_x, self.car_y):
                # One hit = instant game over
                self.game_over = True
                self.hit_flash = 60
                break
            survived_obstacles.append(obs)

        self.obstacles = survived_obstacles

        # ---- Passive score (distance driven) -------------------------
        self.score += 1

        return True

    # ------------------------------------------------------------------
    def render(self, hands_detected):
        # ---- Scrolling background ------------------------------------
        self.screen.blit(self.track_img, (0,  self.bg_y))
        self.screen.blit(self.track_img, (0,  self.bg_y - self.height))

        # ---- Obstacles -----------------------------------------------
        for obs in self.obstacles:
            obs.draw(self.screen)

        # ---- Car (flash red when hit) --------------------------------
        base_rotation = 90
        total_rotation = base_rotation + self.visual_angle
        rotated_car = pygame.transform.rotate(self.car_img, total_rotation)

        if self.hit_flash > 0 and (self.hit_flash // 6) % 2 == 0:
            # Tint car red during flash
            tinted = rotated_car.copy()
            tinted.fill((255, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
            rect = tinted.get_rect(center=(int(self.car_x), int(self.car_y)))
            self.screen.blit(tinted, rect.topleft)
        else:
            rect = rotated_car.get_rect(center=(int(self.car_x), int(self.car_y)))
            self.screen.blit(rotated_car, rect.topleft)

        # ---- HUD -----------------------------------------------------
        self._draw_hud(hands_detected)

        # ---- Game-over overlay ----------------------------------------
        if self.game_over:
            self._draw_game_over()

        pygame.display.flip()
        self.clock.tick(60)

    # ------------------------------------------------------------------
    def _draw_hud(self, hands_detected):
        # Score (top-left)
        score_surf = self.font_large.render(f"Score: {self.score}", True, (255, 255, 255))
        shadow     = self.font_large.render(f"Score: {self.score}", True, (0, 0, 0))
        self.screen.blit(shadow,     (12, 12))
        self.screen.blit(score_surf, (10, 10))

        # "No hands" warning
        if not hands_detected:
            warn = self.font_small.render("Show BOTH hands to steer!", True, (255, 60, 60))
            pygame.draw.rect(self.screen, (0, 0, 0),
                             (self.width//2 - warn.get_width()//2 - 6, 44,
                              warn.get_width() + 12, warn.get_height() + 6), border_radius=6)
            self.screen.blit(warn, (self.width//2 - warn.get_width()//2, 47))

    # ------------------------------------------------------------------
    def _draw_game_over(self):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        go_surf   = self.font_large.render("GAME OVER", True, (255, 60, 60))
        sc_surf   = self.font_small.render(f"Final Score: {self.score}", True, (255, 255, 255))
        rest_surf = self.font_small.render("Press  R  to Restart", True, (180, 255, 180))

        self.screen.blit(go_surf,   (self.width//2 - go_surf.get_width()//2,   self.height//2 - 80))
        self.screen.blit(sc_surf,   (self.width//2 - sc_surf.get_width()//2,   self.height//2 - 20))
        self.screen.blit(rest_surf, (self.width//2 - rest_surf.get_width()//2, self.height//2 + 30))

    # ------------------------------------------------------------------
    def quit(self):
        pygame.quit()
