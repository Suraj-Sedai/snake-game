#!/usr/bin/env python3
"""
Snake Game - Backup Demo Version
Simple, reliable implementation for workshop demos
"""

import pygame
import random
import sys

# Initialize Pygame
pygame.init()

# Constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# Colors
BLACK = (15, 15, 20)
WHITE = (230, 230, 240)
GREEN = (46, 204, 113)   # Emerald
DARK_GREEN = (39, 174, 96) # Nephritis
RED = (231, 76, 60)      # Alizarin
ORANGE = (230, 126, 34)  # Carrot
YELLOW = (241, 196, 15)  # Sun Flower
PINK = (255, 105, 180)
PURPLE = (155, 89, 182)  # Amethyst
CYAN = (52, 152, 219)    # Peter River (Super)
BLUE = (41, 128, 185)    # Belize Hole (Slower)
GRID_COLOR = (25, 25, 35)

FOOD_COLORS = [RED, ORANGE, YELLOW, PINK, PURPLE]
SUPER_FOOD_COLOR = CYAN
SLOWER_FOOD_COLOR = (100, 200, 255) # Bright Ice Blue

# Timings (in milliseconds)
NORMAL_FOOD_TTL = 15000 
SUPER_FOOD_TTL = 5000
SLOWER_FOOD_TTL = 10000
SUPER_FOOD_CHANCE = 0.10
SLOWER_FOOD_CHANCE = 0.15

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake Game - Ultra Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.base_speed = 12
        self.speed_multiplier = 1.0
        self.slow_effect_until = 0
        
        self.reset_game()
    
    def reset_game(self):
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.score = 0
        self.game_over = False
        self.speed_multiplier = 1.0
        self.slow_effect_until = 0
        
        self.foods = []
        for _ in range(3):
            self.spawn_food()
    
    def spawn_food(self):
        """Spawn a food item: Normal, Super, or Slower"""
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            
            if (x, y) not in self.snake and not any((x, y) == food['pos'] for food in self.foods):
                rand = random.random()
                if rand < SUPER_FOOD_CHANCE:
                    f_type = 'super'
                    color = SUPER_FOOD_COLOR
                    ttl = SUPER_FOOD_TTL
                elif rand < SUPER_FOOD_CHANCE + SLOWER_FOOD_CHANCE:
                    f_type = 'slower'
                    color = SLOWER_FOOD_COLOR
                    ttl = SLOWER_FOOD_TTL
                else:
                    f_type = 'normal'
                    color = random.choice(FOOD_COLORS)
                    ttl = NORMAL_FOOD_TTL
                
                self.foods.append({
                    'pos': (x, y),
                    'color': color,
                    'type': f_type,
                    'expires_at': pygame.time.get_ticks() + ttl
                })
                break
    
    def handle_input(self):
        """Handle WASD key input with prevention of 180-degree turns"""
        keys = pygame.key.get_pressed()
        
        # WASD controls - check if not moving in opposite direction
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and self.direction != (0, 1):
            self.direction = (0, -1)
        elif (keys[pygame.K_s] or keys[pygame.K_DOWN]) and self.direction != (0, -1):
            self.direction = (0, 1)
        elif (keys[pygame.K_a] or keys[pygame.K_LEFT]) and self.direction != (1, 0):
            self.direction = (-1, 0)
        elif (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and self.direction != (-1, 0):
            self.direction = (1, 0)
    
    def update(self):
        """Update game state"""
        if self.game_over:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Check slow effect expiration
        if current_time > self.slow_effect_until:
            self.speed_multiplier = 1.0
        
        # Check for expired food
        expired_indices = []
        for i, food in enumerate(self.foods):
            if current_time >= food['expires_at']:
                expired_indices.append(i)
        
        for i in reversed(expired_indices):
            self.foods.pop(i)
            self.spawn_food()

        # Move snake
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # Check wall collision
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT):
            self.game_over = True
            return
        
        # Check self collision
        if new_head in self.snake:
            self.game_over = True
            return
        
        # Add new head
        self.snake.insert(0, new_head)
        
        # Check food collision
        food_eaten = False
        for i, food in enumerate(self.foods):
            if new_head[0] == food['pos'][0] and new_head[1] == food['pos'][1]:
                if food['type'] == 'super':
                    self.score += 50
                elif food['type'] == 'slower':
                    self.score += 20
                    self.speed_multiplier = 0.6  # 40% slower
                    self.slow_effect_until = current_time + 7000 # 7 seconds slow
                else:
                    self.score += 10
                
                self.foods.pop(i)
                self.spawn_food()
                food_eaten = True
                break
        
        if not food_eaten:
            self.snake.pop()
    
    def draw_3d_food(self, x, y, color, food_type):
        """Draw food with 3D effect and special glow for super/slower food"""
        pixel_x = x * GRID_SIZE
        pixel_y = y * GRID_SIZE
        
        # Special effects for Super/Slower food
        if food_type in ['super', 'slower']:
            # Pulsing glow
            pulse = (pygame.time.get_ticks() // 150) % 6
            glow_radius = GRID_SIZE // 2 + pulse
            s = pygame.Surface((GRID_SIZE * 3, GRID_SIZE * 3), pygame.SRCALPHA)
            alpha = 120 - pulse * 15
            pygame.draw.circle(s, (*color, alpha), (GRID_SIZE*1.5, GRID_SIZE*1.5), glow_radius + 4)
            self.screen.blit(s, (pixel_x - GRID_SIZE, pixel_y - GRID_SIZE))

        # Main food circle
        pygame.draw.circle(self.screen, color, 
                         (pixel_x + GRID_SIZE//2, pixel_y + GRID_SIZE//2), 
                         GRID_SIZE//2 - 2)
        
        # Glossy highlight
        pygame.draw.circle(self.screen, (255, 255, 255), 
                         (pixel_x + GRID_SIZE//2 - 4, pixel_y + GRID_SIZE//2 - 4), 
                         GRID_SIZE//6)
    
    def render(self):
        """Render the game with enhanced graphics"""
        self.screen.fill(BLACK)
        
        # Draw subtle grid
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WINDOW_WIDTH, y))

        # Draw snake with tapered body
        snake_len = len(self.snake)
        for i, segment in enumerate(self.snake):
            x, y = segment
            pixel_x = x * GRID_SIZE
            pixel_y = y * GRID_SIZE
            
            # Taper effect: segments get smaller towards tail
            size_offset = min(i // 2, GRID_SIZE // 3)
            rect_size = GRID_SIZE - 2 - size_offset
            offset = (GRID_SIZE - rect_size) // 2
            
            color = GREEN if i == 0 else DARK_GREEN
            if self.speed_multiplier < 1.0: # Blue tint when slowed
                color = tuple(max(0, min(255, c + (BLUE[j]-c)*0.5)) for j, c in enumerate(color))

            pygame.draw.rect(self.screen, color, 
                           (pixel_x + offset, pixel_y + offset, rect_size, rect_size), 
                           border_radius=max(2, 6 - i))
            
            # Head eyes
            if i == 0:
                eye_color = WHITE
                eye_size = 3
                if self.direction == (1, 0): # Right
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 14, pixel_y + 6), eye_size)
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 14, pixel_y + 14), eye_size)
                elif self.direction == (-1, 0): # Left
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 6, pixel_y + 6), eye_size)
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 6, pixel_y + 14), eye_size)
                elif self.direction == (0, -1): # Up
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 6, pixel_y + 6), eye_size)
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 14, pixel_y + 6), eye_size)
                elif self.direction == (0, 1): # Down
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 6, pixel_y + 14), eye_size)
                    pygame.draw.circle(self.screen, eye_color, (pixel_x + 14, pixel_y + 14), eye_size)

        # Draw food
        for food in self.foods:
            self.draw_3d_food(food['pos'][0], food['pos'][1], food['color'], food['type'])
        
        # UI
        score_bg = pygame.Surface((160, 45), pygame.SRCALPHA)
        pygame.draw.rect(score_bg, (40, 40, 50, 180), score_bg.get_rect(), border_radius=10)
        self.screen.blit(score_bg, (10, 10))
        
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (25, 18))
        
        if self.speed_multiplier < 1.0:
            slow_text = self.small_font.render("SLOWED", True, SLOWER_FOOD_COLOR)
            self.screen.blit(slow_text, (25, 60))
        
        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0,0))
            go_text = self.font.render("GAME OVER", True, RED)
            re_text = self.small_font.render("Press R to Restart", True, WHITE)
            self.screen.blit(go_text, go_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 20)))
            self.screen.blit(re_text, re_text.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 30)))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        print("Snake Game: WASD/Arrows to move, R to restart, ESC to quit")
        
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            self.handle_input()
            self.update()
            self.render()
            
            # Clock tick uses current speed multiplier
            self.clock.tick(int(self.base_speed * self.speed_multiplier))
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = SnakeGame()
    game.run()