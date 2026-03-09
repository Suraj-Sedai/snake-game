import pygame
import random
import sys
import math
import array

# Initialize Pygame and Mixer
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)

# Constants
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = WINDOW_WIDTH // GRID_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // GRID_SIZE

# Colors
BLACK = (10, 12, 15)
WHITE = (240, 245, 250)
SNAKE_GREEN = (46, 204, 113)
SNAKE_DARK = (30, 130, 70)
TONGUE_RED = (231, 76, 60)
RED = (255, 50, 50)
ORANGE = (255, 150, 0)
YELLOW = (255, 230, 0)
PINK = (255, 100, 200)
PURPLE = (160, 80, 255)
CYAN = (0, 230, 255)
BLUE = (50, 150, 255)
GRID_COLOR = (20, 25, 30)

FOOD_COLORS = [RED, ORANGE, YELLOW, PINK, PURPLE]
SUPER_FOOD_COLOR = CYAN
SLOWER_FOOD_COLOR = BLUE

# Timings
NORMAL_FOOD_TTL = 15000 
SUPER_FOOD_TTL = 5000
SLOWER_FOOD_TTL = 10000
SUPER_FOOD_CHANCE = 0.12
SLOWER_FOOD_CHANCE = 0.18

def generate_sound(freq, duration, type='sine'):
    """Generate a simple synthetic sound buffer"""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = float(i) / sample_rate
        if type == 'sine':
            val = math.sin(2.0 * math.pi * freq * t)
        elif type == 'square':
            val = 1.0 if math.sin(2.0 * math.pi * freq * t) > 0 else -1.0
        else: # noise/crunch
            val = random.uniform(-1, 1)
        
        # Envelope to prevent clicking
        if i < 100: val *= (i / 100.0)
        if i > n_samples - 100: val *= ((n_samples - i) / 100.0)
            
        buf[i] = int(val * 32767 * 0.5)
    return pygame.mixer.Sound(buf)

def generate_slurp_sound(duration=0.15, freq_start=1200, freq_end=300, is_super=False):
    """Generate a 'shucck' or 'slurp' organic swallowing sound"""
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    buf = array.array('h', [0] * n_samples)
    
    for i in range(n_samples):
        t = float(i) / sample_rate
        progress = i / n_samples
        freq = freq_start - (progress * (freq_start - freq_end))
        
        # Combine a sine wave with noise for 'wet' texture
        val = math.sin(2.0 * math.pi * freq * t) * 0.5
        val += random.uniform(-0.15, 0.15) 
        
        if is_super:
            val += math.sin(4.0 * math.pi * freq * t) * 0.2
        
        # 'Shucck' envelope: Sharp onset, quick curved decay
        envelope = (1.0 - progress)**2 
        if i < 200: envelope *= (i / 200.0) 
        
        buf[i] = int(val * envelope * 32767 * 0.8)
    return pygame.mixer.Sound(buf)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.lifetime = 1.0
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 0.05
        return self.lifetime > 0

class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Snake: Reptile Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        
        # Load enhanced organic sounds (the 'shucck' slurp)
        self.snd_eat = generate_slurp_sound(0.12, 1000, 300)
        self.snd_super = generate_slurp_sound(0.25, 1500, 200, is_super=True)
        self.snd_die = generate_sound(100, 0.5, 'noise') # Deep crunch/thud
        
        self.base_speed = 12
        self.reset_game()
    
    def reset_game(self):
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = (1, 0)
        self.score = 0
        self.game_over = False
        self.speed_multiplier = 1.0
        self.slow_effect_until = 0
        self.particles = []
        self.shake_amount = 0
        self.frame_count = 0
        
        self.foods = []
        for _ in range(3):
            self.spawn_food()
    
    def spawn_food(self):
        max_attempts = 100
        for _ in range(max_attempts):
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)
            if (x, y) not in self.snake and not any((x, y) == food['pos'] for food in self.foods):
                rand = random.random()
                if rand < SUPER_FOOD_CHANCE:
                    f_type, color, ttl = 'super', SUPER_FOOD_COLOR, SUPER_FOOD_TTL
                elif rand < SUPER_FOOD_CHANCE + SLOWER_FOOD_CHANCE:
                    f_type, color, ttl = 'slower', SLOWER_FOOD_COLOR, SLOWER_FOOD_TTL
                else:
                    f_type, color, ttl = 'normal', random.choice(FOOD_COLORS), NORMAL_FOOD_TTL
                
                self.foods.append({
                    'pos': (x, y), 'color': color, 'type': f_type,
                    'expires_at': pygame.time.get_ticks() + ttl
                })
                break
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_w] or keys[pygame.K_UP]) and self.direction != (0, 1):
            self.direction = (0, -1)
        elif (keys[pygame.K_s] or keys[pygame.K_DOWN]) and self.direction != (0, -1):
            self.direction = (0, 1)
        elif (keys[pygame.K_a] or keys[pygame.K_LEFT]) and self.direction != (1, 0):
            self.direction = (-1, 0)
        elif (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and self.direction != (-1, 0):
            self.direction = (1, 0)
    
    def update(self):
        if self.game_over:
            return
        
        self.frame_count += 1
        current_time = pygame.time.get_ticks()
        
        # Shake decay
        if self.shake_amount > 0:
            self.shake_amount -= 1
            
        # Particles
        self.particles = [p for p in self.particles if p.update()]
        
        if current_time > self.slow_effect_until:
            self.speed_multiplier = 1.0
        
        # Food expiration
        expired_indices = [i for i, f in enumerate(self.foods) if current_time >= f['expires_at']]
        for i in reversed(expired_indices):
            self.foods.pop(i)
            self.spawn_food()

        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # Collisions
        if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or 
            new_head[1] < 0 or new_head[1] >= GRID_HEIGHT or new_head in self.snake):
            self.game_over = True
            self.shake_amount = 10
            self.snd_die.play()
            return
        
        self.snake.insert(0, new_head)
        
        food_eaten = False
        for i, food in enumerate(self.foods):
            if new_head == food['pos']:
                # Score and Sound
                if food['type'] == 'super':
                    self.score += 50
                    self.snd_super.play()
                elif food['type'] == 'slower':
                    self.score += 20
                    self.speed_multiplier = 0.6
                    self.slow_effect_until = current_time + 7000
                    self.snd_eat.play()
                else:
                    self.score += 10
                    self.snd_eat.play()
                
                # Burst particles
                for _ in range(15):
                    px = food['pos'][0] * GRID_SIZE + GRID_SIZE//2
                    py = food['pos'][1] * GRID_SIZE + GRID_SIZE//2
                    self.particles.append(Particle(px, py, food['color']))
                
                self.foods.pop(i)
                self.spawn_food()
                food_eaten = True
                break
        
        if not food_eaten:
            self.snake.pop()

    def draw_snake(self, surface_offset):
        ox, oy = surface_offset
        for i, segment in enumerate(self.snake):
            x = segment[0] * GRID_SIZE + ox
            y = segment[1] * GRID_SIZE + oy
            
            # Tapered size
            ratio = 1.0 - (i / len(self.snake)) * 0.4
            radius = int((GRID_SIZE // 2) * ratio)
            
            # Color with scales effect
            color = SNAKE_GREEN if i % 2 == 0 else SNAKE_DARK
            if self.speed_multiplier < 1.0:
                color = tuple(max(0, min(255, c + (BLUE[j]-c)*0.4)) for j, c in enumerate(color))
            
            # Draw segment
            pygame.draw.circle(self.screen, color, (x + GRID_SIZE//2, y + GRID_SIZE//2), radius)
            
            # Draw scale detail
            scale_color = tuple(min(255, c + 20) for c in color)
            pygame.draw.circle(self.screen, scale_color, (x + GRID_SIZE//2, y + GRID_SIZE//2), radius - 4)

            # Head features
            if i == 0:
                # Flickering Tongue
                if (self.frame_count // 5) % 3 == 0:
                    tx, ty = x + GRID_SIZE//2, y + GRID_SIZE//2
                    dx, dy = self.direction
                    pygame.draw.line(self.screen, TONGUE_RED, 
                                   (tx + dx*radius, ty + dy*radius),
                                   (tx + dx*(radius+10), ty + dy*(radius+10)), 2)
                
                # Eyes
                eye_color = WHITE
                eye_radius = 3
                for side in [-1, 1]:
                    # Perpendicular vector for eyes
                    ex = x + GRID_SIZE//2 + (self.direction[0]*5) + (-self.direction[1]*side*5)
                    ey = y + GRID_SIZE//2 + (self.direction[1]*5) + (self.direction[0]*side*5)
                    pygame.draw.circle(self.screen, eye_color, (int(ex), int(ey)), eye_radius)
                    pygame.draw.circle(self.screen, BLACK, (int(ex), int(ey)), 1)

    def render(self):
        # Shake offset
        ox = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        oy = random.randint(-self.shake_amount, self.shake_amount) if self.shake_amount > 0 else 0
        
        self.screen.fill(BLACK)
        
        # Grid
        for x in range(0, WINDOW_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x+ox, 0), (x+ox, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y+oy), (WINDOW_WIDTH, y+oy))

        # Food (Breathing effect)
        breath = math.sin(self.frame_count * 0.2) * 2
        for food in self.foods:
            fx, fy = food['pos'][0] * GRID_SIZE + ox, food['pos'][1] * GRID_SIZE + oy
            # Glow for special food
            if food['type'] in ['super', 'slower']:
                glow_size = GRID_SIZE + int(breath * 2)
                s = pygame.Surface((glow_size*2, glow_size*2), pygame.SRCALPHA)
                pygame.draw.circle(s, (*food['color'], 60), (glow_size, glow_size), glow_size)
                self.screen.blit(s, (fx + GRID_SIZE//2 - glow_size, fy + GRID_SIZE//2 - glow_size))
            
            pygame.draw.circle(self.screen, food['color'], (fx + GRID_SIZE//2, fy + GRID_SIZE//2), GRID_SIZE//2 - 2 + int(breath))

        # Snake
        self.draw_snake((ox, oy))
        
        # Particles
        for p in self.particles:
            alpha = int(p.lifetime * 255)
            s = pygame.Surface((p.size, p.size))
            s.set_alpha(alpha)
            s.fill(p.color)
            self.screen.blit(s, (p.x + ox, p.y + oy))

        # UI
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))
        if self.speed_multiplier < 1.0:
            pygame.draw.rect(self.screen, BLUE, (20, 55, 100, 5), border_radius=2)
            
        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0,0))
            txt = self.font.render("WASTED", True, RED)
            self.screen.blit(txt, txt.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2)))
            
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset_game()
                if event.key == pygame.K_ESCAPE if hasattr(event, 'key') else False: running = False
            
            self.handle_input()
            self.update()
            self.render()
            self.clock.tick(int(self.base_speed * self.speed_multiplier))
        pygame.quit()

if __name__ == "__main__":
    SnakeGame().run()