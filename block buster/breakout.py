"""
Breakout -- pause menu, main menu, power-ups, multi-hit bricks.
Setup:  pip install pygame
Run:    python breakout.py
"""
import pygame
import random

# ---------- Config ----------
WIDTH, HEIGHT = 800, 600
FPS = 60

PADDLE_W, PADDLE_H = 100, 15
PADDLE_SPEED = 7

BALL_RADIUS = 8
BALL_SPEED = 5
MAX_SPEED = 10
LAUNCH_ANGLE_RANGE = 40   # degrees left/right of straight up, on a fresh launch
MAX_BOUNCE_ANGLE = 75     # degrees left/right of straight up, on a paddle bounce

BRICK_ROWS, BRICK_COLS = 5, 10
BRICK_W = WIDTH // BRICK_COLS
BRICK_H = 25

LIVES = 3

POWERUP_RADIUS = BALL_RADIUS + 6

BG = (20, 20, 30)
PADDLE_COLOR = (230, 230, 240)
BALL_COLOR = (255, 200, 60)
BRICK_COLORS = [(220, 60, 60), (230, 130, 50), (230, 200, 50),
                (80, 190, 90), (70, 130, 220)]

# ui colors
UI_BG_COLOR = '#222222'
UI_BG_COLOR_SELECTED = 'green'
UI_BORDER_COLOR = '#111111'
TEXT_COLOR = '#EEEEEE'
UI_BORDER_COLOR_ACTIVE = 'gold'
TEXT_COLOR_SELECTED = '#111111'

class BaseMenu:
    """Shared selection logic for menu-like UI screens (pause menu, main menu, ...)."""

    cooldown_ms = 300  # subclasses can override

    def __init__(self, selection_list):
        self.display_surface = pygame.display.get_surface()
        self.selection_list = selection_list
        self.selection_index = 0
        self.selection_time = None
        self.can_move = True
        self.item_list = []
        self.create_items()  # subclass fills self.item_list

    def create_items(self):
        raise NotImplementedError  # subclass builds self.item_list from self.selection_list

    def input(self):
        if not self.can_move:
            return None
        keys = pygame.key.get_pressed()
        if keys[pygame.K_DOWN] and self.selection_index < len(self.selection_list) - 1:
            self.selection_index += 1
            self.can_move = False
            self.selection_time = pygame.time.get_ticks()
        elif keys[pygame.K_UP] and self.selection_index > 0:
            self.selection_index -= 1
            self.can_move = False
            self.selection_time = pygame.time.get_ticks()
        elif keys[pygame.K_SPACE] or keys[pygame.K_RETURN]:
            self.can_move = False
            self.selection_time = pygame.time.get_ticks()
            return self.execute()
        return None

    def selection_cooldown(self):
        if not self.can_move and pygame.time.get_ticks() - self.selection_time >= self.cooldown_ms:
            self.can_move = True

    def arm_cooldown(self):
        self.can_move = False
        self.selection_time = pygame.time.get_ticks()

    def execute(self):
        return self.selection_list[self.selection_index].lower()

    def run(self):
        selection = self.input()
        self.selection_cooldown()
        return selection

    def display(self):
        raise NotImplementedError  # subclass draws its own panel/title/items
        
class UIPause(BaseMenu):
    cooldown_ms = 300

    def __init__(self):
        self.font = pygame.font.Font(None, 36)
        surface = pygame.display.get_surface()
        self.height = surface.get_height() * 0.6
        self.width = surface.get_width() * 0.6
        self.rect = pygame.Rect(
            surface.get_width() // 2 - self.width // 2,
            surface.get_height() // 2 - self.height // 2,
            self.width, self.height,
        )
        super().__init__(['Resume', 'Restart', 'Quit', 'Quit to Menu'])
        # NOTE: self.rect must exist BEFORE super().__init__() runs, since
        # that call triggers create_items(), which reads self.rect.

    def create_items(self):
        self.item_list = []
        for index, item in enumerate(self.selection_list):
            full_width = self.width * 0.5
            left = self.rect.left + (self.width - full_width) // 2
            item_height = self.height / len(self.selection_list)
            top = self.rect.top + item_height * index
            self.item_list.append({'rect': pygame.Rect(left, top, full_width, item_height),
                                    'text': item})

    def display(self):
        pygame.draw.rect(self.display_surface, UI_BG_COLOR, self.rect)
        pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, self.rect, 4)
        for i, item in enumerate(self.item_list):
            if i == self.selection_index:
                pygame.draw.rect(self.display_surface, UI_BG_COLOR_SELECTED, item['rect'])
                pygame.draw.rect(self.display_surface, UI_BORDER_COLOR_ACTIVE, item['rect'], 4)
                text_color = TEXT_COLOR_SELECTED
            else:
                pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, item['rect'], 4)
                text_color = TEXT_COLOR
            text_surf = self.font.render(item['text'], True, text_color)
            self.display_surface.blit(text_surf, text_surf.get_rect(center=item['rect'].center))


class UIMenu(BaseMenu):
    cooldown_ms = 500

    def __init__(self):
        self.font_title = pygame.font.Font(None, 64)
        self.font = pygame.font.Font(None, 36)
        super().__init__(['Play', 'Levels', 'Quit'])

    def create_items(self):
        self.item_list = []
        for i, text in enumerate(self.selection_list):
            rect = pygame.Rect(0, 0, 200, 50)
            rect.center = self.display_surface.get_rect().center
            rect.y += (i - len(self.selection_list) / 2) * 60
            self.item_list.append({'text': text, 'rect': rect})

    def display(self):
        title = self.font_title.render("BREAKOUT", True, (255, 255, 255))
        self.display_surface.blit(title, title.get_rect(center=(self.display_surface.get_width() // 2, 100)))
        for i, item in enumerate(self.item_list):
            if i == self.selection_index:
                pygame.draw.rect(self.display_surface, UI_BG_COLOR_SELECTED, item['rect'])
                pygame.draw.rect(self.display_surface, UI_BORDER_COLOR_ACTIVE, item['rect'], 4)
                text_color = TEXT_COLOR_SELECTED
            else:
                pygame.draw.rect(self.display_surface, UI_BG_COLOR, item['rect'])
                pygame.draw.rect(self.display_surface, UI_BORDER_COLOR, item['rect'], 4)
                text_color = TEXT_COLOR
            text = self.font.render(item['text'], True, text_color)
            self.display_surface.blit(text, text.get_rect(center=item['rect'].center))

class UILevelSelect(BaseMenu):
    cooldown_ms = 300

    def __init__(self, num_levels):
        self.num_levels = num_levels
        self.unlocked_level = 0  # Game syncs this in each frame before run()
        self.font_title = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 32)
        labels = [f"Level {i + 1}" for i in range(num_levels)] + ['Back']
        super().__init__(labels)

    def create_items(self):
        self.item_list = []
        surface = self.display_surface
        top, spacing = 150, 50
        for i, text in enumerate(self.selection_list):
            rect = pygame.Rect(0, 0, 220, 42)
            rect.center = (surface.get_width() // 2, top + i * spacing)
            self.item_list.append({'text': text, 'rect': rect})

    def execute(self):
        # 'Back' is always the last row
        if self.selection_index == len(self.selection_list) - 1:
            return 'back'
        # FIX: block confirming a locked level -- moving the cursor over it
        # is fine, but pressing Enter/Space on it should do nothing.
        if self.selection_index > self.unlocked_level:
            return None
        return f'level:{self.selection_index}'

    def display(self):
        title = self.font_title.render("SELECT LEVEL", True, (255, 255, 255))
        self.display_surface.blit(title, title.get_rect(
            center=(self.display_surface.get_width() // 2, 70)))

        for i, item in enumerate(self.item_list):
            is_back = (i == len(self.item_list) - 1)
            locked = (not is_back) and (i > self.unlocked_level)

            if i == self.selection_index:
                bg, border, txt = UI_BG_COLOR_SELECTED, UI_BORDER_COLOR_ACTIVE, TEXT_COLOR_SELECTED
            elif locked:
                bg, border, txt = '#1a1a1a', UI_BORDER_COLOR, '#555555'
            else:
                bg, border, txt = UI_BG_COLOR, UI_BORDER_COLOR, TEXT_COLOR

            pygame.draw.rect(self.display_surface, bg, item['rect'])
            pygame.draw.rect(self.display_surface, border, item['rect'], 3)
            label = item['text'] + (' (locked)' if locked else '')
            text_surf = self.font.render(label, True, txt)
            self.display_surface.blit(text_surf, text_surf.get_rect(center=item['rect'].center))

class UILevelCleared(BaseMenu):
    cooldown_ms = 300

    def __init__(self):
        self.font_title = pygame.font.Font(None, 56)
        self.font = pygame.font.Font(None, 36)
        super().__init__(['Next Level', 'Replay Level', 'Main Menu'])

    def create_items(self):
        self.item_list = []
        surface = self.display_surface
        for i, text in enumerate(self.selection_list):
            rect = pygame.Rect(0, 0, 240, 50)
            rect.center = (surface.get_width() // 2, surface.get_height() // 2 + i * 65)
            self.item_list.append({'text': text, 'rect': rect})

    # execute() is inherited as-is: returns 'next level' / 'replay level' /
    # 'main menu' -- exactly what BaseMenu.execute() already does.

    def display(self, level_index):
        title = self.font_title.render(f"LEVEL {level_index + 1} CLEARED!", True, (255, 255, 255))
        self.display_surface.blit(title, title.get_rect(
            center=(self.display_surface.get_width() // 2, 150)))
        for i, item in enumerate(self.item_list):
            if i == self.selection_index:
                bg, border, txt = UI_BG_COLOR_SELECTED, UI_BORDER_COLOR_ACTIVE, TEXT_COLOR_SELECTED
            else:
                bg, border, txt = UI_BG_COLOR, UI_BORDER_COLOR, TEXT_COLOR
            pygame.draw.rect(self.display_surface, bg, item['rect'])
            pygame.draw.rect(self.display_surface, border, item['rect'], 3)
            text_surf = self.font.render(item['text'], True, txt)
            self.display_surface.blit(text_surf, text_surf.get_rect(center=item['rect'].center))

PROJECTILE_SPEED = 8

class Projectile:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 2, y - 10, 4, 10)

    def update(self):
        self.rect.y -= PROJECTILE_SPEED

    @property
    def offscreen(self):
        return self.rect.bottom < 0

    def draw(self, surf):
        pygame.draw.rect(surf, (255, 255, 0), self.rect)

# ---------- Power-ups ----------
class PowerUp:
    """A falling pickup spawned when a brick is destroyed."""

    KINDS = ['wide_paddle', 'multi_ball', 'slow_ball', 'fast_ball', 
             'double_paddle', 'shooter', 'floor_bounce']
    # LABELS = ['WP', 'MB', 'SB', 'FB', 'DP', 'SH', 'B']
    # LABELS = ['↔️',          '🔮',         '⏳',        '⚡',        '⏸️',            '🚀',      '🛡️']
    LABELS = ['[<>]',        '[oO]',       '[v]',       '[!]',       '[||]',          '[^ ]',     '[__]']
    # LABELS = ['⇔',          '⁕',          '⇓',        '⇑',         '⦀',            '⇪',       '☳']

    label_map = dict(zip(KINDS, LABELS))
    TEMPORARY_KINDS = ['wide_paddle', 'slow_ball', 'fast_ball', 
                     'double_paddle', 'shooter', 'floor_bounce']

    def __init__(self, pos, kind):
        self.pos = pygame.Vector2(pos)
        self.font = pygame.font.Font(None, 22)
        self.kind = kind
        self.speed = 3
        self.expiry_time = None
        self.display_surface = pygame.display.get_surface()

    @property
    def rect(self):
        # FIX: uses POWERUP_RADIUS (the actual drawn size) instead of
        # BALL_RADIUS, so the paddle-collision box matches what's on screen.
        return pygame.Rect(self.pos.x - POWERUP_RADIUS, self.pos.y - POWERUP_RADIUS,
                            POWERUP_RADIUS * 2, POWERUP_RADIUS * 2)

    def update(self):
        self.pos.y += self.speed * 0.7

    def draw(self, surf):
        if self.kind == 'wide_paddle':
            color = (0, 200, 0)
        elif self.kind == 'multi_ball':
            color = (220, 40, 40)
        elif self.kind == 'slow_ball':
            color = (50, 100, 230)
        elif self.kind == 'fast_ball':
            color = (230, 200, 50)
        elif self.kind == 'double_paddle':
            color = (0, 150, 0)
        elif self.kind == 'shooter':
            color = (200, 0, 200)
        elif self.kind == 'floor_bounce':
            color = (230, 50, 50)

        center = (int(self.pos.x), int(self.pos.y))
        # FIX: draw one filled circle instead of a filled square rect with a
        # small circle stacked on top -- that combination is what was
        # reading as "square" powerups.
        pygame.draw.circle(surf, color, center, POWERUP_RADIUS)
        pygame.draw.circle(surf, UI_BORDER_COLOR, center, POWERUP_RADIUS, 2)  # outline

        # FIX: label text now uses a fixed light color instead of the same
        # `color` as the circle -- same-color-on-same-color text was
        # invisible once the background became a solid circle.
        text = self.font.render(self.label_map.get(self.kind, ''), True, 'white')
        text_rect = text.get_rect(center=center)
        self.display_surface.blit(text, text_rect)

    def apply(self, game):
        self.expiry_time = pygame.time.get_ticks()  + 5000  # 5 seconds

        if self.kind == 'wide_paddle':
            if game.paddle.rect.width == game.paddle.base_width:
                game.paddle.rect.width = int(game.paddle.base_width * 1.5)
            elif game.paddle.rect.width == int(game.paddle.base_width * 1.5):
                game.paddle.rect.width = int(game.paddle.base_width * 2)
            self.expiry_time += 2000
            game.paddle.wide_until = self.expiry_time 

        elif self.kind == 'multi_ball':
            # --- TOGGLE HARDCODED ---
            # True: duplica TUTTE le palline in gioco
            # False: duplica SOLO la prima pallina (comportamento originale)
            MULTIPLY_ALL_BALLS = True
            # ------------------------

            if MULTIPLY_ALL_BALLS:
                # Creiamo una lista temporanea per non modificare la lista 
                # su cui stiamo ciclando (evita loop infiniti)
                current_balls = list(game.balls)
                
                for original_ball in current_balls:
                    new_ball_lf = Ball()
                    new_ball_rt = Ball()
                    
                    new_ball_lf.pos = original_ball.pos.copy()
                    vel = original_ball.vel.copy()
                    new_ball_lf.vel = vel.rotate(-30)
                    new_ball_lf.launched = True
                    
                    new_ball_rt.pos = original_ball.pos.copy()
                    new_ball_rt.vel = vel.rotate(30)
                    new_ball_rt.launched = True
                    
                    game.balls.append(new_ball_lf)
                    game.balls.append(new_ball_rt)
            else:
                # Comportamento originale: duplica solo la prima pallina
                if game.balls:  # Controllo di sicurezza che esista almeno una pallina
                    new_ball_lf = Ball()
                    new_ball_rt = Ball()
                    new_ball_lf.pos = game.balls[0].pos.copy()
                    vel = game.balls[0].vel.copy()
                    new_ball_lf.vel = vel.rotate(-30)
                    new_ball_lf.launched = True
                    new_ball_rt.pos = game.balls[0].pos.copy()
                    new_ball_rt.vel = vel.rotate(30)
                    new_ball_rt.launched = True
                    game.balls.append(new_ball_lf)
                    game.balls.append(new_ball_rt)

        elif self.kind == 'slow_ball':
            if game.slow_times < 2:  # limit the number of slow effects 
                game.slow_times += 1
                for ball in game.balls:
                    ball.vel *= 0.5
                    # self.expiry_time += 5000
                game.slow_expiry = self.expiry_time

        elif self.kind == 'fast_ball':
            if game.fast_times < 2:  # limit the number of fast effects
                game.fast_times += 1
                for ball in game.balls:
                    ismax = ball.vel.length()  * 1.01 >= MAX_SPEED
                    ball.vel = ball.vel.normalize() * MAX_SPEED if ismax else ball.vel * 1.01  # Limit the maximum speed
                    # self.expiry_time += 5000
                game.fast_expiry = self.expiry_time
        elif self.kind == 'double_paddle':
            game.paddle.split_until = self.expiry_time + 3000
        elif self.kind == 'shooter':
            game.paddle.can_shoot_until = self.expiry_time
        elif self.kind == 'floor_bounce':
            game.floor_bounce_until = self.expiry_time
        if self.kind in self.TEMPORARY_KINDS:
            game.active_powerups.append((self, self.expiry_time))


# ---------- Sound ----------
class SoundManager:
    """Central place for sound effects so Ball/Game don't touch pygame.mixer directly."""

    def __init__(self):
        # TODO 24: pygame.mixer.init() and load your .wav/.ogg files here, e.g.
        #          self.hit_brick = pygame.mixer.Sound('assets/hit.wav')
        #          self.hit_paddle = pygame.mixer.Sound('assets/paddle.wav')
        #          self.lose_life = pygame.mixer.Sound('assets/lose.wav')
        #          Keep a volume control too: sound.set_volume(0.5)
        pass

    def play(self, name):
        try:
            sound = getattr(self, name)
            sound.play()
        except AttributeError:
            print(f"Sound not found: {name}")


# ---------- Level loading ----------
def load_level(pattern):
    """
    pattern: lista di righe (può contenere stringhe di cifre o liste di numeri), es.:
        ["12301",        # Riga come stringa, # Riga come lista di numeri
         "00111"]        # Riga come stringa
    Valore/Cifra = hp del mattone in quel punto (0 o '0' = spazio vuoto).
    """
    bricks = []
    for row_index, row in enumerate(pattern):
        for col_index, item in enumerate(row):
            hp_val = None
            
            # Caso 1: L'elemento è già un numero (int o float)
            if isinstance(item, (int, float)):
                hp_val = int(item)
            
            # Caso 2: L'elemento è una stringa (singolo carattere o cifra)
            elif isinstance(item, str) and item.isdigit():
                hp_val = int(item)
            
            # Se abbiamo trovato un HP valido e maggiore di 0, creiamo il mattone
            if hp_val is not None and hp_val > 0:
                bricks.append(Brick(col_index, row_index, hp=hp_val))
                
    return bricks


# ---------- Game objects ----------
class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(
            WIDTH // 2 - PADDLE_W // 2, HEIGHT - 40, PADDLE_W, PADDLE_H
        )
        self.base_width = PADDLE_W
        self.wide_until = 0
        self.split_until = 0      # NEW
        self.can_shoot_until = 0  # NEW
        self.left_rect = None
        self.right_rect = None
        self.last_shot_time = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= PADDLE_SPEED
            # for r in self.get_rects():
            #     r.x -= PADDLE_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PADDLE_SPEED
            # for r in rs:
            #     r.x += PADDLE_SPEED
        if pygame.time.get_ticks() > self.split_until:
            self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        else:
            half_width = (self.rect.width) / 2
            self.rect.clamp_ip(pygame.Rect(half_width, 0, WIDTH - self.rect.width, HEIGHT))

        # self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))
        if self.wide_until and pygame.time.get_ticks() > self.wide_until:
            self.rect.width = self.base_width
            self.wide_until = 0
        if self.split_until and pygame.time.get_ticks() > self.split_until:
            self.split_until = 0
            self.left_rect = None
            self.right_rect = None
        if self.can_shoot_until and pygame.time.get_ticks() > self.can_shoot_until:
            self.can_shoot_until = 0

    def get_rects(self):
        """Returns the paddle as one rect normally, or two when split is active."""
        if not self.split_until:
            return [self.rect]
        half_width = (self.rect.width) / 2
        self.left_rect = pygame.Rect(self.rect.left - half_width, self.rect.top, half_width, self.rect.height)
        self.right_rect = pygame.Rect(self.rect.right, self.rect.top, half_width, self.rect.height)
        return [self.left_rect, self.right_rect]

    def draw(self, surf):
        for r in self.get_rects():
            pygame.draw.rect(surf, PADDLE_COLOR, r, border_radius=6)

class Ball:
    def __init__(self):
        self.pos = pygame.Vector2(WIDTH // 2, HEIGHT - 40 - BALL_RADIUS)
        self.vel = pygame.Vector2(0, 0)
        self.reset()

    def reset(self):
        self.launched = False
        # FIX: clear velocity too, not just the launched flag. Previously a
        # ball that fell off-screen kept its old (nonzero) velocity while
        # sitting on the paddle waiting to relaunch. If a multi-ball
        # power-up was collected during that wait, the two new balls copied
        # that stale leftover velocity -- direction looked arbitrary and
        # unrelated to anything currently on screen.
        self.vel = pygame.Vector2(0, 0)

    def launch(self):
        # FIX: launching now always picks a fixed-length vector (BALL_SPEED)
        # and rotates it by a random angle, instead of picking vel.x and
        # vel.y independently. Independent random components meant the
        # actual launch SPEED (the vector's length) varied between ~5 and
        # ~7 depending on luck -- "uneven" speed started right at launch.
        angle = random.uniform(-LAUNCH_ANGLE_RANGE, LAUNCH_ANGLE_RANGE)
        self.vel = pygame.Vector2(0, -BALL_SPEED).rotate(angle)
        self.launched = True

    @property
    def rect(self):
        return pygame.Rect(
            self.pos.x - BALL_RADIUS, self.pos.y - BALL_RADIUS,
            BALL_RADIUS * 2, BALL_RADIUS * 2,
        )

    def update(self, paddle, bricks, powerups=None, speedups=0, particles=None):
        # if self.slow_until and pygame.time.get_ticks() > self.slow_until:
        #     if self.vel.length() > 0:
        #         self.vel = self.vel.normalize() * BALL_SPEED * 1.01 ** speedups  # restore to normal speed
        #     self.slow_until = 0

        if self.launched:
            self.pos += self.vel
        else:
            self.pos.x = paddle.rect.centerx
            self.pos.y = paddle.rect.top - BALL_RADIUS

        if self.pos.x - BALL_RADIUS <= 0 or self.pos.x + BALL_RADIUS >= WIDTH:
            self.vel.x *= -1
        elif self.pos.y - BALL_RADIUS <= 0:
            self.vel.y *= -1

        if self.vel.y > 0:
            for prect in paddle.get_rects():
                if self.rect.colliderect(prect):
                    speed = self.vel.length() or BALL_SPEED
                    offset = (self.pos.x - prect.centerx) / (prect.width / 2)
                    offset = max(-1, min(1, offset))
                    angle = offset * MAX_BOUNCE_ANGLE
                    self.vel = pygame.Vector2(0, -speed).rotate(angle)
                    break

        for brick in bricks:
            if self.rect.colliderect(brick.rect):
                brick.hit()
                if brick.hp <= 0:
                    bricks.remove(brick)
                    if particles is not None:
                        for _ in range(12):
                            particles.append(Particle(brick.rect.center, brick.color))

                if abs(self.rect.bottom - brick.rect.top) < BALL_RADIUS and self.vel.y > 0:
                    self.vel.y *= -1
                elif abs(self.rect.top - brick.rect.bottom) < BALL_RADIUS and self.vel.y < 0:
                    self.vel.y *= -1
                elif abs(self.rect.right - brick.rect.left) < BALL_RADIUS and self.vel.x > 0:
                    self.vel.x *= -1
                elif abs(self.rect.left - brick.rect.right) < BALL_RADIUS and self.vel.x < 0:
                    self.vel.x *= -1

                if random.random() < 0.6:  # xx% chance to spawn a power-up
                    kind = random.choice(PowerUp.KINDS)
                    powerup = PowerUp(brick.rect.center, kind)
                    if powerups is not None:
                        powerups.append(powerup)

                break

    def draw(self, surf):
        pygame.draw.circle(
            surf, BALL_COLOR, (int(self.pos.x), int(self.pos.y)), BALL_RADIUS
        )


class Brick:
    def __init__(self, col, row, hp=1):
        self.rect = pygame.Rect(col * BRICK_W, 60 + row * BRICK_H,
                                BRICK_W - 2, BRICK_H - 2)
        self.color = BRICK_COLORS[row % len(BRICK_COLORS)]
        self.hp = hp
        self.font = pygame.font.Font(None, 24)

    def hit(self):
        self.hp -= 1
        self.color = tuple(max(0, c - 30) for c in self.color)

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect, border_radius=3)
        if self.hp > 1:
            text = self.font.render(str(self.hp), True, (255, 255, 255))
            surf.blit(text, text.get_rect(center=self.rect.center))

class Particle:
    def __init__(self, pos, color):
        self.pos = pygame.Vector2(pos)
        angle = random.uniform(0, 360)
        speed = random.uniform(1, 4)
        self.vel = pygame.Vector2(speed, 0).rotate(angle)  # fly outward in a random direction
        self.color = color
        self.max_life = random.randint(20, 40)  # frames it survives
        self.life = self.max_life
        self.radius = random.uniform(2, 4)

    def update(self):
        self.pos += self.vel
        self.vel *= 0.95  # friction — slows down over time instead of flying forever
        self.life -= 1

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surf):
        t = self.life / self.max_life          # 1.0 → 0.0 over its lifetime
        radius = max(1, int(self.radius * t))   # shrinks as it fades
        pygame.draw.circle(surf, self.color, (int(self.pos.x), int(self.pos.y)), radius)

# Gli HP diminuiscono man mano che si scende di riga
piramide_layout = [
    [max(1, 3 - (r // 2)) for c in range(BRICK_COLS)]
    for r in range(BRICK_ROWS)
]
# Alterna tra 1 e 2 HP in base alla somma di riga e colonna
scacchiera_layout = [
    [2 if (r + c) % 2 == 0 else 1 for c in range(BRICK_COLS)]
    for r in range(BRICK_ROWS)
]
fortezza_layout = [
    [
        3 if (r == 0 or c == 0 or c == BRICK_COLS - 1)  # Bordi esterni corazzati
        else (0 if c in (3, 6) else 1)                 # Fessure vuote, altrimenti 1 HP
        for c in range(BRICK_COLS)
    ]
    for r in range(BRICK_ROWS)
]


PATTERNS = [
    # [""],
    ["1111111111",
    "0111111110",
    "1111111111",
    "0111111110",
    "1111111111"],
    ["1" * BRICK_COLS for _ in range(BRICK_ROWS)],
    piramide_layout,
    scacchiera_layout,
    fortezza_layout,

]

def scaled_speed(speedups):
    return min(BALL_SPEED * 1.01 ** speedups, MAX_SPEED)

# ---------- Game ----------
class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Breakout")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 32)

        self.ui_pause = UIPause()
        self.ui_menu = UIMenu()
        self.ui_level_select = UILevelSelect(len(PATTERNS))
        self.ui_level_cleared = UILevelCleared()
        # TODO: self.sounds = SoundManager()

        self.app_state = "menu"  # "menu" | "playing" | "paused"
        self.level = 0
        self.unlocked_level = 0
        self.new_game()

    def new_game(self):
        self.paddle = Paddle()
        self.balls = [Ball()]
        self.bricks = load_level(PATTERNS[self.level])
        # self.bricks = [Brick(c, r)
        #                for r in range(BRICK_ROWS) for c in range(BRICK_COLS)]
        self.max_num_bricks = len(self.bricks)
        self.particles = []
        self.powerups = []
        self.active_powerups = []
        self.shake_frames = 0
        self.fast_expiry = 0
        self.slow_expiry = 0
        self.slow_times = 0
        self.fast_times = 0
        self.speedups = 0
        self.previous_speedups = 0
        self.show_speedup_message = False
        self.show_speedup_message_until = 0
        self.score = 0
        self.combo = 0
        self.shake_frames = 0
        self.broken_bricks = 0
        self.last_broken_bricks = 0
        self.lives = LIVES
        self.state = "playing"  # "playing" | "won" | "lost"
        self.can_select = True
        self.selection_time = None
        self.floor_bounce_until = 0
        self.projectiles = []

    def selection_cooldown(self):
        if not self.can_select:
            current_time = pygame.time.get_ticks()
            if current_time - self.selection_time >= 1000:
                self.can_select = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    return False
                if event.key == pygame.K_r and self.state != "playing" and self.app_state == "playing":
                    print("Restarting game")  # for debugging
                    self.new_game()
                if event.key == pygame.K_SPACE and self.app_state == "playing":
                    # FIX: used to require `len(self.balls) == 1` to launch.
                    # With multi-ball active there can be 3 balls at once;
                    # if the ORIGINAL ball falls and respawns while the
                    # other two are still flying, that count is never back
                    # down to 1, so Space would silently do nothing and the
                    # respawned ball just sat glued to the paddle forever.
                    # Now every ball checks itself: launch whichever ball(s)
                    # currently have launched == False, regardless of how
                    # many balls total are in play.
                    for ball in self.balls:
                        if not ball.launched:
                            ball.launch()
                if event.key == pygame.K_p:
                    if self.app_state == "playing":
                        self.app_state = "paused"
                    elif self.app_state == "paused":
                        print("Resuming game")  # for debugging
                        self.app_state = "playing"

                # if event.key == pygame.K_f and self.app_state == "playing":
                #     if pygame.time.get_ticks() < self.paddle.can_shoot_until:
                #         self.projectiles.append(Projectile(self.paddle.rect.left + 5, self.paddle.rect.top))
                #         self.projectiles.append(Projectile(self.paddle.rect.right - 5, self.paddle.rect.top))

        return True

    def update(self):
        if self.app_state == "menu":
            selection = self.ui_menu.run()
            if selection == 'play' and self.can_select:
                self.level = self.unlocked_level   # resume from furthest progress
                self.new_game()
                self.app_state = "playing"
                self.can_select = False
                self.selection_time = pygame.time.get_ticks()
            elif selection == 'levels' and self.can_select:          # NEW
                self.app_state = "level_select"
                self.can_select = False
                self.selection_time = pygame.time.get_ticks()
                self.ui_level_select.selection_index = 0
                self.ui_level_select.arm_cooldown()   # <- same fix as before: the
                # held Enter/Space that just confirmed "Levels" would otherwise be
                # read again on the very next frame by ui_level_select's OWN
                # can_move, which starts True. Arm it so it ignores that echo.
            elif selection == 'quit' and self.can_select:
                self.can_select = False
                self.selection_time = pygame.time.get_ticks()
                return 'quit'
            else:
                self.selection_cooldown()
            return
        elif self.app_state == "level_select":                       # NEW branch
            self.ui_level_select.unlocked_level = self.unlocked_level
            selection = self.ui_level_select.run()
            if selection == 'back':
                self.app_state = "menu"
                self.ui_menu.selection_index = 0
                self.ui_menu.arm_cooldown()
            elif selection and selection.startswith('level:'):
                self.level = int(selection.split(':')[1])
                self.new_game()
                self.app_state = "playing"
            return
        elif self.app_state == "paused":
            selection = self.ui_pause.run()

            if selection == 'resume':
                self.app_state = "playing"
            elif selection == 'restart':
                print("Restarting game")  # for debugging
                self.new_game()
                self.app_state = "playing"
            elif selection == 'quit':
                return 'quit'
            elif selection == 'quit to menu':
                self.new_game()
                self.app_state = "menu"
                self.ui_menu.selection_index = 0
                print("Returning to menu")
                # FIX: arm the menu's own cooldown right as it becomes
                # active. Without this, holding down Enter/Space to pick
                # "Quit to Menu" meant the SAME held key was read again on
                # the very next frame -- but by the fresh ui_menu object,
                # whose can_move was still True (it hadn't been touched by
                # the pause menu's cooldown). That instantly re-selected
                # "Play" and bounced straight back into the game, so the
                # menu only ever showed for a single frame.
                self.ui_menu.arm_cooldown()
            return

        elif self.app_state == "level_cleared":
            selection = self.ui_level_cleared.run()
            if selection == 'next level':
                if self.level < len(PATTERNS) - 1:
                    self.level += 1
                self.new_game()
                self.app_state = "playing"
            elif selection == 'replay level':
                self.new_game()
                self.app_state = "playing"
            elif selection == 'main menu':
                self.new_game()
                self.app_state = "menu"
                self.ui_menu.selection_index = 0
                self.ui_menu.arm_cooldown()
            return
        
        if self.state != "playing":
            return
        self.paddle.update()
        for ball in self.balls:
            ball.update(self.paddle, self.bricks, self.powerups, self.speedups, self.particles)
        if self.slow_times and pygame.time.get_ticks() > self.slow_expiry: #self.balls[0].slow_until:
            self.slow_times = 0
        if self.fast_times and pygame.time.get_ticks() > self.fast_expiry: #self.balls[0].fast_until:
            self.fast_times = 0

        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.rect.colliderect(self.paddle.rect):
                powerup.apply(self)
                self.powerups.remove(powerup)
            elif powerup.pos.y - POWERUP_RADIUS > HEIGHT:
                self.powerups.remove(powerup)

        SHOOT_INTERVAL_MS = 250  # tune to taste — 20ms (50 shots/sec) is probably too fast anyway
        if pygame.time.get_ticks() < self.paddle.can_shoot_until:
            if pygame.time.get_ticks() - self.paddle.last_shot_time >= SHOOT_INTERVAL_MS:
                self.projectiles.append(Projectile(self.paddle.rect.left + 5, self.paddle.rect.top))
                self.projectiles.append(Projectile(self.paddle.rect.right - 5, self.paddle.rect.top))
                self.paddle.last_shot_time = pygame.time.get_ticks()

        for proj in self.projectiles[:]:
            proj.update()
            hit = False
            for brick in self.bricks[:]:
                if proj.rect.colliderect(brick.rect):
                    brick.hit()
                    if brick.hp <= 0:
                        self.bricks.remove(brick)
                        for _ in range(12):
                            self.particles.append(Particle(brick.rect.center, brick.color))
                    hit = True
                    break
            if hit or proj.offscreen:
                self.projectiles.remove(proj)

        for particle in self.particles[:]:
            particle.update()
            if not particle.alive:
                self.particles.remove(particle)

        for ball in self.balls[:]:
            if ball.pos.y - BALL_RADIUS > HEIGHT:
                if self.floor_bounce_until and pygame.time.get_ticks() < self.floor_bounce_until:
                    ball.pos.y = HEIGHT - BALL_RADIUS
                    ball.vel.y *= -1
                    continue  # skip the life-loss/removal logic below entirely
                if len(self.balls) == 1:
                    self.lives -= 1
                    if self.lives <= 0:
                        self.state = "lost"
                    else:
                        self.balls[0].reset()
                else:
                    self.balls.remove(ball)

        broken_bricks = self.max_num_bricks - len(self.bricks)
        self.broken_bricks = broken_bricks
        self.score = broken_bricks * 10
        if broken_bricks > 0 and broken_bricks % 10 == 0 and broken_bricks != self.last_broken_bricks:
            self.speedups += 1
            for ball in self.balls:
                if ball.vel.length() > 0:
                    ball.vel = ball.vel.normalize() * scaled_speed(self.speedups)
            print(f"Speeding up balls to {self.balls[0].vel.length():.2f} after {broken_bricks} bricks broken")

        if broken_bricks != self.last_broken_bricks:
            self.shake_frames = 6  # Trigger screen shake effect
        self.last_broken_bricks = broken_bricks

        if not self.bricks:
            print("Level cleared!")  # for debugging
            self.state = "won"
            # FIX: unlock the NEXT level only the first time this one is cleared --
            # otherwise replaying an already-unlocked level would keep bumping
            # unlocked_level even though nothing new was actually cleared.
            if self.level == self.unlocked_level and self.unlocked_level < len(PATTERNS) - 1:
                self.unlocked_level += 1
            self.app_state = "level_cleared"
            self.ui_level_cleared.selection_index = 0
            self.ui_level_cleared.arm_cooldown()

        self.active_powerups = [(p, t) for p, t in self.active_powerups 
                                if pygame.time.get_ticks() < t]

    def draw(self):
        self.screen.fill(BG)

        if self.app_state == "menu":
            self.ui_menu.display()
            pygame.display.flip()
            return
        if self.app_state == "level_select":
            self.ui_level_select.display()
            pygame.display.flip()
            return

        for brick in self.bricks:
            brick.draw(self.screen)
        self.paddle.draw(self.screen)
        for ball in self.balls:
            ball.draw(self.screen)
        for powerup in self.powerups:
            powerup.draw(self.screen)
        for particle in self.particles:
            particle.draw(self.screen)
        for proj in self.projectiles:
            proj.draw(self.screen)

        hud = self.font.render(
            f"Score: {self.score}   Lives: {self.lives}   " 
            f"Speedups: {self.speedups}   Speed: {self.balls[0].vel.length():.2f}", True, PADDLE_COLOR
        )
        self.screen.blit(hud, (10, 10))

        if self.state == "lost":
            text = self.font.render("GAME OVER - press R to restart", True, PADDLE_COLOR)
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        if self.previous_speedups != self.speedups:
            self.show_speedup_message = True
            self.show_speedup_message_until = pygame.time.get_ticks() + 3000  # Show for 3 seconds
        if self.state == "playing" and (self.previous_speedups != self.speedups or self.show_speedup_message):
            self.show_speedup_message = True
            text = self.font.render(f"Speedups: {self.speedups}   Speed: {self.balls[0].vel.length():.2f}",
                                    True, PADDLE_COLOR)
            self.screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40)))
        self.previous_speedups = self.speedups
        if self.show_speedup_message_until and pygame.time.get_ticks() > self.show_speedup_message_until:
            self.show_speedup_message = False
            self.show_speedup_message_until = None

        if self.shake_frames > 0:
            self.shake_frames -= 1
            offset_x = random.randint(-4, 4)
            offset_y = random.randint(-4, 4)
            self.screen.scroll(offset_x, offset_y)

        if self.app_state == "paused":
            self.ui_pause.display()
        if self.app_state == "level_cleared":          # NEW
            self.ui_level_cleared.display(self.level)

        if self.floor_bounce_until and pygame.time.get_ticks() < self.floor_bounce_until:
            pygame.draw.line(self.screen, (0, 200, 255), (0, HEIGHT - 2), (WIDTH, HEIGHT - 2), 4)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            result = self.update()
            self.draw()
            self.clock.tick(FPS)
            if result == 'quit':
                break
        pygame.quit()


if __name__ == "__main__":
    Game().run()

