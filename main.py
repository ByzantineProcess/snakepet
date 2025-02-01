import displayio
from blinka_displayio_pygamedisplay import PyGameDisplay
import pygame
import time, random

state = 0
score = 0
grayscale = displayio.Palette(2)
grayscale[0] = 0x000000
grayscale[1] = 0xFFFFFF

snekscale = displayio.Palette(3)
snekscale[0] = 0x000000
snekscale[1] = 0x00FF00
snekscale[2] = 0xFF0000
snekscale.make_transparent(0)

treatscale = displayio.Palette(7)
treatscale[0] = 0x00FFFF
treatscale[1] = 0xFF0000
treatscale[2] = 0x00FF00
treatscale[3] = 0x0000FF
treatscale[4] = 0xFFFF00
treatscale[5] = 0xFF00FF
treatscale[6] = 0x000000
treatscale.make_transparent(6)

print("\nHackapet button mappings are z, x, c. Press Ctrl+C to exit...")
# time.sleep(0.5) # read my message!!

snek_history = {0: (32, 30), 1: (32, 31), 2: (32, 32)}

hurtpixels = []
treatpixels = [(40, 32)]
treatcolour = 0

hurtboxes = [(16, 16, 32, 32)]

evilsneksS = []
evilsneksN = []

class SnakeDirection:
    STRAIGHT = 0
    LEFT = 1
    RIGHT = 2

class CardinalDirection:
    N = 0
    E = 1
    S = 2
    W = 3

last_direction = CardinalDirection.N

class BetterInputs:
    def __init__(self):
        self.betterkeys = {'z': False, 'x': False, 'c': False}
        self.keylock = {'z': False, 'x': False, 'c': False}
        self.update()

    def update(self):
        self.keys = pygame.key.get_pressed()
        self.betterkeys['z'] = self.keys[pygame.K_z]
        self.betterkeys['x'] = self.keys[pygame.K_x]
        self.betterkeys['c'] = self.keys[pygame.K_c]

        # if the keylock is enabled, but the key is not pressed, unlock it
        for key in self.keylock:
            if self.keylock[key] and not self.betterkeys[key]:
                # print(f"unlocking key {key}")
                self.keylock[key] = False

    def get_key(self, key):
        if not self.keylock[key]:
            if self.betterkeys[key]:
                # print(f"locking key {key}")
                self.keylock[key] = True
                return True
            else:
                # print(f"key {key} is not pressed")
                return False
        else:
            # print(f"key {key} is locked")
            return False

    def any_key(self):
        # if any key that isn't locked is pressed, return True
        return any(self.betterkeys[key] and not self.keylock[key] for key in self.betterkeys)


frames = 0
last_time = time.monotonic()
def measure_fps():
    global last_time, frames
    current_time = time.monotonic()
    frames += 1
    if current_time - last_time >= 1:
        print("FPS:", frames, end="\r")
        last_time = current_time
        frames = 0

def draw_rect_on_bitmap(bitmap, x, y, width, height, color):
    for i in range(width):
        for j in range(height):
            bitmap[x+i, y+j] = color
            draw_hollow_hurting_rect_on_bitmap(x, y, width, height)

def draw_hollow_hurting_rect_on_bitmap(x, y, width, height):
    for i in range(width):
        hurtpixels.append((x+i, y))
        hurtpixels.append((x+i, y+height-1))
    for j in range(height):
        hurtpixels.append((x, y+j))
        hurtpixels.append((x+width-1, y+j))

def draw_hollow_rect_on_bitmap(bitmap, x, y, width, height, color):
    for i in range(width):
        bitmap[x+i, y] = color
        bitmap[x+i, y+height-1] = color 
    for j in range(height):
        bitmap[x, y+j] = color
        bitmap[x+width-1, y+j] = color
    for i in range(width):
        hurtpixels.append((x+i, y))
        hurtpixels.append((x+i, y+height-1))
    for j in range(height):
        hurtpixels.append((x, y+j))
        hurtpixels.append((x+width-1, y+j))

def draw_treat_on_bitmap():
    global treatcolour
    treets = displayio.Bitmap(64, 64, 7)
    treets.fill(6)
    treatcolour += 1
    treatcolour = treatcolour % 6
    for i in treatpixels:
        treets[i] = treatcolour
    return displayio.TileGrid(treets, pixel_shader=treatscale)

def gen_treatpixel():
    x = random.randrange(16, 48)
    y = random.randrange(16, 48)
    if (x, y) in snek_history.values() or (x, y) in treatpixels or (x, y) in hurtpixels:
        gen_treatpixel()
    else:
        treatpixels.append((x, y))

def gen_hurtboxes():
    x = random.randrange(16, 48)
    y = random.randrange(16, 48)
    if (x, y) in snek_history.values() or (x, y) in treatpixels or (x, y) in hurtpixels:
        gen_hurtboxes()
    else:
        hurtboxes.append((x, y, 2, 2))

def create_evilsnekS():
    x = random.randrange(16, 48)
    evilsneksS.append({0: (x, 0), 1: (x, -1), 2: (x, -2)})

def create_evilsnekN():
    print("creating evilsnekN")
    x = random.randrange(16, 48)
    evilsneksN.append({0: (x, 64), 1: (x, 65), 2: (x, 66)})

def draw_snake_on_bitmap(snek_history:dict, direction = SnakeDirection.STRAIGHT):
    global last_direction, state, score
    snek = displayio.Bitmap(64, 64, 3)
    # pop the oldest element
    snek_history.pop(max(snek_history.keys()))
    # shift all elements up
    snek_history = {k+1: v for k, v in snek_history.items()}
    # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
    # yknow i think i understand why the original snake used 4 buttons
    if direction == SnakeDirection.STRAIGHT:
        if last_direction == CardinalDirection.N:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] - 1)
        elif last_direction == CardinalDirection.S:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] + 1)
        elif last_direction == CardinalDirection.W:
            snek_history[0] = (snek_history[1][0] - 1, snek_history[1][1])
        elif last_direction == CardinalDirection.E:
            snek_history[0] = (snek_history[1][0] + 1, snek_history[1][1])
    elif direction == SnakeDirection.LEFT:
        if last_direction == CardinalDirection.N:
            snek_history[0] = (snek_history[1][0] - 1, snek_history[1][1])
            last_direction = CardinalDirection.W
        elif last_direction == CardinalDirection.S:
            snek_history[0] = (snek_history[1][0] + 1, snek_history[1][1])
            last_direction = CardinalDirection.E
        elif last_direction == CardinalDirection.W:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] + 1)
            last_direction = CardinalDirection.S
        elif last_direction == CardinalDirection.E:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] - 1)
            last_direction = CardinalDirection.N
    elif direction == SnakeDirection.RIGHT:
        if last_direction == CardinalDirection.N:
            snek_history[0] = (snek_history[1][0] + 1, snek_history[1][1])
            last_direction = CardinalDirection.E
        elif last_direction == CardinalDirection.S:
            snek_history[0] = (snek_history[1][0] - 1, snek_history[1][1])
            last_direction = CardinalDirection.W
        elif last_direction == CardinalDirection.W:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] - 1)
            last_direction = CardinalDirection.N
        elif last_direction == CardinalDirection.E:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] + 1)
            last_direction = CardinalDirection.S
        
    # sort snek_history by key
    snek_history = dict(sorted(snek_history.items()))
    for i in snek_history.values():
        snek[i] = 1

    # is the most recent element in the snek_history touching a hurtpixel?
    # print(snek_history[0])
    if snek_history[0] in hurtpixels:
        print("you died")
        state = 2
    if snek_history[0] in treatpixels:
        # score += 1
        create_evilsnekS()
        print("you ate a treat")
        treatpixels.remove(snek_history[0])
        gen_treatpixel()
        gen_hurtboxes()
    for i in evilsneksS:
        if snek_history[0] in i.values():
            print("you died")
            state = 2
    for i in evilsneksN:
        if snek_history[0] in i.values():
            print("you died")
            state = 2

    return (displayio.TileGrid(snek, pixel_shader=snekscale), snek_history)

def draw_evil_snake_on_bitmap(bitmap, snek_history:dict, direction = CardinalDirection.S):
    snek = bitmap
    old_snek = snek_history
    # pop the oldest element
    snek_history.pop(max(snek_history.keys()))
    # shift all elements up
    snek_history = {k+1: v for k, v in snek_history.items()}

    try:
        if direction == CardinalDirection.N:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] - 1)
        elif direction == CardinalDirection.S:
            snek_history[0] = (snek_history[1][0], snek_history[1][1] + 1)
        
        # sort snek_history by key
        snek_history = dict(sorted(snek_history.items()))
        for i in snek_history.values():
            snek[i] = 2
    except IndexError:
        # it's probably out of bounds
        return snek, old_snek, True
    
    return snek, snek_history, False

pygame.init()

display = PyGameDisplay(width=128, height=128, flags=pygame.SCALED)
splash = displayio.Group()
display.show(splash)

jungle = displayio.OnDiskBitmap("assets/bg-rev3.bmp")
bg_sprite = displayio.TileGrid(jungle, pixel_shader=jungle.pixel_shader)
splash.append(bg_sprite)

snek = displayio.OnDiskBitmap("assets/snake.bmp")
snake_sprite = displayio.TileGrid(snek, pixel_shader=snek.pixel_shader)
splash.append(snake_sprite)

def draw_borders_and_boxes():
    border = displayio.Bitmap(64, 64, 1)
    for i in hurtboxes:
        draw_hollow_rect_on_bitmap(border, *i, 1)
    border_sprite = displayio.TileGrid(border, pixel_shader=grayscale)
    return border_sprite

def handle_evil_snakes():
    esneks = displayio.Bitmap(64, 64, 3)
    for i in evilsneksS:
        esneks, evilsneksS[evilsneksS.index(i)], tmp = draw_evil_snake_on_bitmap(esneks, i, direction=CardinalDirection.S)
        if tmp:
            evilsneksS.pop(evilsneksS.index(i))
            create_evilsnekN()
    for i in evilsneksN:
        esneks, evilsneksN[evilsneksN.index(i)], tmp = draw_evil_snake_on_bitmap(esneks, i, direction=CardinalDirection.N)
        if tmp:
            evilsneksN.remove(i)
            create_evilsnekS()
    return displayio.TileGrid(esneks, pixel_shader=snekscale)

def make_gamegroup():
    gamegroup = displayio.Group()
    gamegroup.scale = 2
    gamegroup.append(draw_borders_and_boxes())
    return gamegroup

keys = BetterInputs()
direction = SnakeDirection.STRAIGHT
while True:
    try:
        keys.update()
        measure_fps()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
        if keys.any_key():
            if state == 0:
                print("starting game")
                state = 1
                gamegroup = make_gamegroup()
                snakeframe, snek_history = draw_snake_on_bitmap(snek_history)
                gamegroup.append(snakeframe)
                gamegroup.append(draw_treat_on_bitmap())
                gamegroup.append(handle_evil_snakes())
                display.show(gamegroup)
                # print(hurtpixels)
                ft = time.monotonic()
                oft = time.monotonic()
        if state == 1:
            ft = time.monotonic()
            
            if keys.get_key('z'):
                direction = SnakeDirection.LEFT
            elif keys.get_key('c'):
                direction = SnakeDirection.RIGHT
            if ft - oft >= 0.1:
                oft = ft
                if score > 5:
                    if random.random() > 0.5:
                        create_evilsnekS()
                gamegroup.pop()
                gamegroup.pop()
                gamegroup.pop()
                gamegroup.pop()
                gamegroup.append(draw_borders_and_boxes())
                gamegroup.append(draw_treat_on_bitmap())
                gamegroup.append(handle_evil_snakes())
                snakeframe, snek_history = draw_snake_on_bitmap(snek_history, direction=direction)
                direction = SnakeDirection.STRAIGHT
                gamegroup.append(snakeframe)
        if state == 2:
            time.sleep(3)
            state = 0
            # reset snek_history
            snek_history = {0: (32, 30), 1: (32, 31), 2: (32, 32)}
            # reset keys
            keys = BetterInputs()
            # reset direction
            direction = SnakeDirection.STRAIGHT
            # reset last_direction
            last_direction = CardinalDirection.N
            # reset hurtpixels
            hurtpixels = []
            # reset treatpixels
            treatpixels = [(40, 32)]
            # reset treatcolour
            treatcolour = 0
            # reset hurtboxes
            hurtboxes = [(16, 16, 32, 32)]
            # reset evilsneksS
            evilsneksS = []
            # reset evilsneksN
            evilsneksN = []
            display.show(splash)
        

        time.sleep(0.01)
    except KeyboardInterrupt:
        exit(0)
