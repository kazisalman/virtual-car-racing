import pygame
import math
import os

class GameEngine:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Virtual Steering Racing")
        self.clock = pygame.time.Clock()
        
        # Load assets
        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        self.car_img = pygame.image.load(os.path.join(assets_dir, 'car.png')).convert()
        self.car_img.set_colorkey((255, 255, 255)) # Remove white background
        
        # Scale car image
        car_rect = self.car_img.get_rect()
        scale_factor = 100 / max(car_rect.width, car_rect.height)
        new_size = (int(car_rect.width * scale_factor), int(car_rect.height * scale_factor))
        self.car_img = pygame.transform.scale(self.car_img, new_size)
        
        self.track_img = pygame.image.load(os.path.join(assets_dir, 'track.png')).convert()
        self.track_img = pygame.transform.scale(self.track_img, (self.width, self.height))

        # Car state
        self.car_x = self.width / 2
        self.car_y = self.height - 150
        # Start facing upwards. The car sprite might be facing right (0 degrees)
        self.car_angle = 90 
        self.speed = 8.0
        
        # Background scroll
        self.bg_y = 0

    def update(self, steering_angle):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

        # Apply steering to car angle.
        # Negative steering angle (left) should increase car angle (rotate counter-clockwise in pygame math usually, but let's see).
        # We will directly map the hand angle to a visual turning, or accumulate it.
        # Let's accumulate it like a real steering wheel turning the wheels.
        turn_speed = steering_angle * 0.05 
        
        # We want the car to generally stay facing up, maybe drifting a bit left or right.
        # Or we can make it an endless runner where steering moves it left and right horizontally.
        # Actually, endless runner moving left/right is much better for this type of game!
        
        # Limit the steering horizontal movement speed based on angle
        horizontal_speed = steering_angle * 0.15
        self.car_x += horizontal_speed
        
        # Keep car on the track bounds (rough estimation)
        self.car_x = max(150, min(self.width - 150, self.car_x))
        
        # Scroll background down to simulate forward movement
        self.bg_y += self.speed
        if self.bg_y >= self.height:
            self.bg_y -= self.height
            
        # Tilt the car slightly based on steering
        self.visual_angle = -steering_angle * 0.5 
            
        return True

    def render(self, hands_detected):
        # Draw scrolling background
        self.screen.blit(self.track_img, (0, self.bg_y))
        self.screen.blit(self.track_img, (0, self.bg_y - self.height))
        
        # If the generated car image faces right, we need to rotate it 90 degrees to face up first.
        # Then add our visual tilt.
        base_rotation = 90 
        total_rotation = base_rotation + self.visual_angle
        
        rotated_car = pygame.transform.rotate(self.car_img, total_rotation)
        rect = rotated_car.get_rect(center=(int(self.car_x), int(self.car_y)))
        self.screen.blit(rotated_car, rect.topleft)
        
        # Status text
        font = pygame.font.SysFont(None, 36)
        if not hands_detected:
            text = font.render("Please place both hands in view to steer!", True, (255, 0, 0))
            self.screen.blit(text, (self.width//2 - text.get_width()//2, 50))
            
        pygame.display.flip()
        self.clock.tick(60)

    def quit(self):
        pygame.quit()
