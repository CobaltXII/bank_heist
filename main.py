# Bank Heist by Adam Sidat

import os
import math
import time
import pygame
import random
import pickle
import colorsys
import datetime

# local settings and preferences
default_preferences = {
	'levels_unlocked': 1,
	'highscores': [-666, -666, -666]
}
preferences = {}

# load preferences if possible
if (os.path.exists('./preferences.dat')):
	with open('./preferences.dat', 'rb') as f:
		preferences = pickle.load(f)
else:
	# create new preferences
	preferences = default_preferences
	with open('./preferences.dat', 'wb') as f:
		pickle.dump(preferences, f, pickle.HIGHEST_PROTOCOL)

# returns True if a level is unlocked
def level_unlocked(level):
	return level <= preferences['levels_unlocked']

# the following are math functions. these are used all over the program so it
# makes sense to define them first

# checks if a point is within an axis-aligned bounding box (AABB)
def in_aabb_raw(x, y, aabbx, aabby, aabbw, aabbh):
	# do 1-dimensional overlap checks
	x1d = x >= aabbx and x <= aabbx + aabbw
	y1d = y >= aabby and y <= aabby + aabbh
	return x1d and y1d

# checks if a point is within an axis-aligned bounding box (AABB), but uses an
# object-oriented approach instead
def in_aabb(point, aabb):
	# do 1-dimensional overlap checks
	x1d = point[0] >= aabb[0] and point[0] <= aabb[0] + aabb[2]
	y1d = point[1] >= aabb[1] and point[1] <= aabb[1] + aabb[3]
	return x1d and y1d

# gets the time in milliseconds (for timing)
def ms():
	return datetime.datetime.now().microsecond / 1000.0

# gets the time in seconds (for timing)
def seconds():
	return int(time.time())

# gets the time in seconds with high precision
def seconds_float():
	return time.time()

# clamp a value so it is not less than min or greater than max
def clamp(x, _min, _max):
	if (x < _min):
		x = _min
	elif (x > _max):
		x = _max
	return x

# linearly interpolate between two points
def lerp(p0, p1, x):
	_x = p0[0] + (p1[0] - p0[0]) * x
	_y = p0[1] + (p1[1] - p0[1]) * x
	return (_x, _y)

# get an angle (p) in radians such that sin(p)=x and cos(p)=y
def angle(x, y):
	return math.atan2(x, y)

# find the squared distance between two points
def dist2(a, b):
	dx = b[0] - a[0]
	dy = b[1] - a[1]
	return dx * dx + dy * dy

# find the distance between two points
def dist(a, b):
	dx = b[0] - a[0]
	dy = b[1] - a[1]
	return math.sqrt(dx * dx + dy * dy)

# find the normal/unit vector to get from one point to another. this is
# defined for a normal/unit vector (u) such that a+u*dist(a,b)=b
def unit(a, b):
	dx = b[0] - a[0]
	dy = b[1] - a[1]
	l = math.sqrt(dx * dx + dy * dy)
	return (dx / l, dy / l)

# find the angle from one point to another
def angle_to(a, b):
	u = unit(a, b)
	return math.atan2(u[0], u[1])

# get a signed random number
def signed_rand():
	return random.random() * 2.0 - 1.0

# find the index of the nearest point in the array (a) to the point (p). as an
# optimization to avoid calling math.sqrt(), the dist2() function is used
# instead of dist()
def nearest_to(p, a):
	lowest_distance = 999999999.0
	lowest_index = -1
	for i in range(0, len(a)):
		d = dist2(p, a[i])
		if (d < lowest_distance):
			lowest_distance = d
			lowest_index = i
	return lowest_index

# format an integer so that it takes up n decimal places (right-aligned) and
# return the result as a string. this is difficult to explain in a comment, so
# please ask me if it's required to explain this
def format_int(x, n):
	unpadded = str(int(x) % 10 ** n)
	return ' ' * (n - len(unpadded)) + unpadded

# get the first v*len(s) characters of s
def portion_of_text(s, v):
	v = clamp(v, 0.0, 1.0)
	c = int(v * len(s))
	return s[:c]

# return '???' if a number is negative and the number as a string if it is
# positive
def obfuscate_if_negative(x):
	if (x < 0):
		return '???'
	return str(x)

# general constants
gfx_scale = 2

# tile sizing constants
tile_w = 16
tile_h = 16

# level sizing constants
level_w = 20
level_h = 15

# window sizing constants
window_border_x = 4
window_border_y = 4
window_tile_w = 25
window_tile_h = 20
window_w = window_border_x * 2 + window_tile_w * tile_w
window_h = window_border_y * 2 + window_tile_h * tile_h

# initialize pygame
pygame.init()
screen = pygame.display.set_mode((window_w * gfx_scale, window_h * gfx_scale))
pygame.display.set_caption('Bank Heist')

# have some global state variables so that querying the mouse is simpler
mouse = (0, 0)
mouse_left_pressed = False
mouse_right_pressed = False

# create a surface to draw to. draw to this instead of the main surface
# since that makes scaling a lot easier
surface = pygame.Surface((window_w, window_h))

# the following are wrapper functions, because pygame's naming convention is
# horrendous and inconsistent

# load an image
def load_image(path):
	return pygame.image.load(path)

# draw an image
def draw_image(image, x, y):
	surface.blit(image, (x, y))

# draw a progress bar
def draw_progress_bar(x, y, low, high, value):
	# convert the progress bar value to a scalar
	f = clamp((value - low) / (high - low), 0.0, 1.0)
	pb_w = 14.0
	pb_h = 3.0
	pygame.draw.rect(surface, (15, 15, 15), (x, y, pb_w, pb_h))
	# make the progress bar fade from green to yellow to red, using HSV to RGB
	# conversions should make this a lot easier
	color = colorsys.hsv_to_rgb(1.0 / 3.0 * f, 1.0, 1.0)
	color_rgb = (color[0] * 255, color[1] * 255, color[2] * 255)
	pygame.draw.rect(surface, color_rgb, (x, y, pb_w * f, pb_h))

# a subset of an image
class Subimage:
	def __init__(self, source, x, y, w, h):
		self.source = source
		self.area = (x, y, w, h)

# draw a subset of an image
def draw_subimage(subimage, x, y):
	surface.blit(subimage.source, (x, y), subimage.area)

# load a sound
def load_sound(path):
	return pygame.mixer.Sound(path)

# play a sound
def play_sound(sound):
	sound.play()

# load tileset
tileset_image = load_image('tileset.png')

# generate a subimage for a given tile
def generate_tile_image(i, j=0):
	return Subimage(tileset_image, i * tile_w, j * tile_h, tile_w, tile_h)

# generate tiles
tiles = []
for i in range(0, 10):
	tiles.append(generate_tile_image(i))

# generate enumeration values for each tile
TILE_WALL = 0
TILE_FLOOR = 1
TILE_PISTOL_TURRET = 2
TILE_SHOTGUN_TURRET = 3
TILE_UZI_TURRET = 4
TILE_GOLD = 5
TILE_SPIKE_TRAP = 6
TILE_BOMB_TRAP = 7
TILE_SPAWN = 8
TILE_NOPE = 9

# returns True if a turret/trap can be placed on a wall
def can_be_placed_on_wall(t):
	return t == TILE_PISTOL_TURRET or \
	       t == TILE_SHOTGUN_TURRET or \
	       t == TILE_UZI_TURRET or \
	       t == TILE_WALL

# returns True if a turret/trap can be placed on the floor
def can_be_placed_on_floor(t):
	return t == TILE_SPIKE_TRAP or \
	       t == TILE_BOMB_TRAP or \
	       t == TILE_FLOOR

# generate numeric tiles
numeric = []
for i in range(0, 10):
	numeric.append(generate_tile_image(i, 1))

# load buttons
buttons_pistol_turret = load_image('button_pistol_turret.png')
buttons_shotgun_turret = load_image('button_shotgun_turret.png')
buttons_uzi_turret = load_image('button_uzi_turret.png')
buttons_health_up = load_image('button_health_up.png')
buttons_spike_trap = load_image('button_spike_trap.png')
buttons_bomb_trap = load_image('button_bomb_trap.png')

# generate a subimage for a given button
def generate_button_image(image, j):
	size = image.get_size()
	return Subimage(image, 0, j * 16, size[0], size[1] / 3)

# generate a list of button subimages for a given button
def generate_buttons(image):
	out = []
	out.append(generate_button_image(image, 0))
	out.append(generate_button_image(image, 1))
	out.append(generate_button_image(image, 2))
	return out

# generate subimages for each button
btn_pistol_turret = generate_buttons(buttons_pistol_turret)
btn_shotgun_turret = generate_buttons(buttons_shotgun_turret)
btn_uzi_turret = generate_buttons(buttons_uzi_turret)
btn_health_up = generate_buttons(buttons_health_up)
btn_spike_trap = generate_buttons(buttons_spike_trap)
btn_bomb_trap = generate_buttons(buttons_bomb_trap)

# generate enumeration values for each button type
BUTTON_DEFAULT = 0
BUTTON_HOVERED = 1
BUTTON_PRESSED = 2

# draw a button. returns True if the button was pressed
def draw_button(btn, x, y):
	global mouse_left_pressed

	# kind of hacky way to get the dimensions, but it works fine
	w = btn[0].area[2]
	h = btn[0].area[3]

	# get the button type based on the mouse's state
	if (in_aabb(mouse, (x, y, w, h))):
		if (mouse_left_pressed):
			btn_state = BUTTON_PRESSED
		else:
			btn_state = BUTTON_HOVERED
	else:
		btn_state = BUTTON_DEFAULT

	# draw the button
	draw_subimage(btn[btn_state], x, y)

	# return True if the button was pressed
	if (btn_state == BUTTON_PRESSED):
		# set the mouse state to unpressed, so that multiple actions cannot
		# be invoked by a single mouse press
		mouse_left_pressed = False
		return True
	else:
		return False

# draw a disabled button
def draw_disabled_button(btn, x, y):
	# kind of hacky way to get the dimensions, but it works fine
	w = btn[0].area[2]
	h = btn[0].area[3]

	# draw the button
	draw_subimage(btn[BUTTON_PRESSED], x, y)

# load other GUI images
gui_pricing = load_image('pricing.png')
gui_pricing2 = load_image('pricing2.png')
gui_heads_up = load_image('heads_up.png')
gui_title_tile = load_image('title_tile.png')

# load the title image as a list of tiles
title_tiles = []
title_image = load_image('title.png')
title_size = title_image.get_size()
for i in range(0, title_size[0]):
	for j in range(0, title_size[1]):
		color = title_image.get_at((i, j))
		if (color[0] > 0):
			# not black, it's a background pixel
			pass
		else:
			# probably black, it's a foreground pixel
			title_tiles.append((i - (title_size[0] - 1) / 2, j - (title_size[1] - 1) / 2))

# load the you win image as a list of tiles
you_win_tiles = []
you_win_image = load_image('you_win.png')
you_win_size = you_win_image.get_size()
for i in range(0, you_win_size[0]):
	for j in range(0, you_win_size[1]):
		color = you_win_image.get_at((i, j))
		if (color[0] > 0):
			# not black, it's a background pixel
			pass
		else:
			# probably black, it's a foreground pixel
			you_win_tiles.append((i - (you_win_size[0] - 1) / 2, j - (you_win_size[1] - 1) / 2))

# load the you lose image as a list of tiles
you_lose_tiles = []
you_lose_image = load_image('you_lose.png')
you_lose_size = you_lose_image.get_size()
for i in range(0, you_lose_size[0]):
	for j in range(0, you_lose_size[1]):
		color = you_lose_image.get_at((i, j))
		if (color[0] > 0):
			# not black, it's a background pixel
			pass
		else:
			# probably black, it's a foreground pixel
			you_lose_tiles.append((i - (you_lose_size[0] - 1) / 2, j - (you_lose_size[1] - 1) / 2))

# calculate the title offset
title_offset_x = window_w / 2
title_offset_y = 100
center_title_offset_y = 75

# load a file as a list of strings (one for each line)
def load_file(path):
	return open(path).readlines()

# a level
class Level:
	# load a level from a file
	def __init__(self, path):
		lines = load_file(path)
		self.data = []
		self.original_data = []
		for j in range(0, level_h):
			line = lines[j]
			for i in range(0, level_w):
				character = line[i]
				if (character == '#'):
					self.data.append(TILE_WALL)
					self.original_data.append(TILE_WALL)
				elif (character == 'G'):
					self.data.append(TILE_GOLD)
					self.original_data.append(TILE_GOLD)
				elif (character == 'S'):
					self.data.append(TILE_SPAWN)
					self.original_data.append(TILE_SPAWN)
				else:
					self.data.append(TILE_FLOOR)
					self.original_data.append(TILE_FLOOR)

		# calculate the path to traverse the level
		self.calculate_path()

		# create a surface for the blood effects
		self.blood = pygame.Surface((window_w, window_h), flags=pygame.SRCALPHA)
		self.clear_up_the_bloody_floor_please_and_thank_you()

	# don't ask
	def clear_up_the_bloody_floor_please_and_thank_you(self):
		# fill the blood effect surface with a transparent color
		self.blood.fill((0, 0, 0, 0), (0, 0, window_w, window_h))
  
	# reset the level
	def reset(self):
		self.clear_up_the_bloody_floor_please_and_thank_you()
		self.data = []
		for i in range(0, len(self.original_data)):
			self.data.append(self.original_data[i])

	# calculate the path to traverse this level
	def calculate_path(self):
		# find the spawn tile
		for j in range(0, level_h):
			for i in range(0, level_w):
				if (self.peek(i, j) == TILE_SPAWN):
					spawn_x = i
					spawn_y = j
		# store the current previous tile position
		prev_x = spawn_x
		prev_y = spawn_y
		curr_x = spawn_x
		curr_y = spawn_y
		# keep going until the gold tile is found
		pathway = []
		while True:
			# generate tile coordinates
			left_x = curr_x - 1
			left_y = curr_y
			right_x = curr_x + 1
			right_y = curr_y
			top_x = curr_x
			top_y = curr_y - 1
			bottom_x = curr_x
			bottom_y = curr_y + 1
			# get the tile types of each of these tiles
			left = self.peek(left_x, left_y)
			right = self.peek(right_x, right_y)
			top = self.peek(top_x, top_y)
			bottom = self.peek(bottom_x, bottom_y)
			# check if any of these are gold
			found_gold = False
			if (left == TILE_GOLD): found_gold = True; gold_x = left_x; gold_y = left_y
			if (right == TILE_GOLD): found_gold = True; gold_x = right_x; gold_y = right_y
			if (top == TILE_GOLD): found_gold = True; gold_x = top_x; gold_y = top_y
			if (bottom == TILE_GOLD): found_gold = True; gold_x = bottom_x; gold_y = bottom_y
			# check if gold was found
			if (found_gold):
				# done
				pathway.append((gold_x, gold_y))
				self.gold_x = gold_x
				self.gold_y = gold_y
				break
			# guess no gold was found, check if there is an empty tile that is
			# not the previous tile
			floor_x = -1
			floor_y = -1
			if (left == TILE_FLOOR and not (left_x == prev_x and left_y == prev_y)):
				floor_x = left_x; floor_y = left_y
			if (right == TILE_FLOOR and not (right_x == prev_x and right_y == prev_y)):
				floor_x = right_x; floor_y = right_y
			if (top == TILE_FLOOR and not (top_x == prev_x and top_y == prev_y)):
				floor_x = top_x; floor_y = top_y
			if (bottom == TILE_FLOOR and not (bottom_x == prev_x and bottom_y == prev_y)):
				floor_x = bottom_x; floor_y = bottom_y
			# check if there was an empty tile
			if (floor_x != -1):
				prev_x = curr_x
				prev_y = curr_y
				pathway.append((prev_x, prev_y))
				curr_x = floor_x
				curr_y = floor_y
			else:
				print('bad level')
				exit()

		# store the pathway
		self.pathway = pathway

	# get the position along the pathway based on a scalar x. that is, if x is
	# 0, the the first position along the pathway will be returned. if x is 1,
	# the last position along the pathway will be returned. if x is somewhere
	# in the middle, it's value is interpolated from given data
	def pos(self, x):
		i = clamp(x * (len(self.pathway) - 1), 0, len(self.pathway) - 1)
		j = clamp(x * (len(self.pathway) - 1) + 1, 0, len(self.pathway) - 1)
		return lerp(self.pathway[int(j)], self.pathway[int(i)], math.floor(j) - i)

	# fetch a tile
	def peek(self, i, j):
		if (i < 0 or i >= level_w or j < 0 or j >= level_h):
			return TILE_WALL
		# this array is 'flattened', this is the C-way of doing 2-dimensional
		# arrays
		return self.data[j * level_w + i]

	# set a tile
	def poke(self, i, j, tile):
		if (not (i < 0 or i >= level_w or j < 0 or j >= level_h)):
			self.data[j * level_w + i] = tile

	# set a blood pixel
	def set_blood(self, x, y, color):
		global level_offset_x, level_offset_y
		global game_level
		# get the tile coordinates
		tx = int((x - level_offset_x) / tile_w)
		ty = int((y - level_offset_y) / tile_h)
		# make sure it's in bounds
		if (tx < 0 or ty < 0 or tx >= level_w or ty >= level_h):
			return
		# only set the pixel if it is on a floor tile
		if (can_be_placed_on_floor(game_level.peek(tx, ty))):
			s = 16
			alpha = (color[0] / s, color[1] / s, color[2] / s, 8)
			self.blood.fill(alpha, (int(x), int(y), 1, 1), pygame.BLEND_RGBA_ADD)

# load enemies
enemy_grunt = load_image('enemy_grunt.png')
enemy_speedy = load_image('enemy_speedy.png')
enemy_bulk = load_image('enemy_bulk.png')

# all enemy types
ENEMY_GRUNT = 0
ENEMY_SPEEDY = 1
ENEMY_BULK = 2

# enemy speed multipliers. index by enemy type
E_BASE_SPEED = 0.001
E_SPEED = [1.0, 1.75, 0.6]
# enemy damage multipliers. index by enemy type
E_BASE_DAMAGE = 7.5
E_DAMAGE = [1.0, 0.75, 3.0]
# enemy health multipliers. index by enemy type
E_BASE_HEALTH = 5.0
E_HEALTH = [1.5, 1.25, 5.5]

# enemy loot drops
E_LOOT = [15, 20, 25]

# enemy sprites. index by enemy type
E_SPRITE = [enemy_grunt, enemy_speedy, enemy_bulk]

# enemy colors. index by enemy type
E_COLOR = [(255, 153, 35), (119, 179, 0), (0, 74, 179)]

# an enemy
class Enemy:
	# create an enemy
	def __init__(self, variation):
		self.variation = variation
		self.position = 0.0
		self.speed = E_BASE_SPEED * E_SPEED[variation]
		self.damage = E_BASE_DAMAGE * E_DAMAGE[variation]
		self.health = E_BASE_HEALTH * E_HEALTH[variation]
		self.max_health = E_BASE_HEALTH * E_HEALTH[variation]
		self.id = random.randint(0x0, 0xDEADBEEF)

	# tick the enemy
	def tick(self):
		self.position += self.speed

		# periodically damage the gold if we're sitting on it
		global iteration
		if ((iteration + self.id) % 60 == 0):
			global game_gold
			global game_level
			global level_offset_x, level_offset_y
			global stat_damage
			pos = self.pos()
			px = level_offset_x + pos[0] * tile_w
			py = level_offset_y + pos[1] * tile_h
			aabbx = game_level.gold_x * tile_w + level_offset_x
			aabby = game_level.gold_y * tile_h + level_offset_y
			if (in_aabb_raw(px, py, aabbx, aabby, tile_w, tile_h)):
				add_gold_explosion(px + signed_rand() * tile_w + 8.0, py + signed_rand() * tile_h + 8.0)
				game_gold -= E_BASE_DAMAGE * E_DAMAGE[self.variation]
				stat_damage += E_BASE_DAMAGE * E_DAMAGE[self.variation]
				do_sound('gold_damage')

	# get the position
	def pos(self):
		global game_level
		return game_level.pos(self.position)

	# get the position a little bit in the future
	def next_pos(self):
		global game_level
		global BULLET_SPEED
		# this prediction function is extremely accurate
		return game_level.pos(self.position + self.speed * (1.0 / BULLET_SPEED))

	# draw the enemy
	def draw(self):
		global game_level
		global level_offset_x, level_offset_y
		pos = self.pos()
		px = level_offset_x + pos[0] * tile_w
		py = level_offset_y + pos[1] * tile_h
		draw_image(E_SPRITE[self.variation], px, py)
		draw_progress_bar(px + 1, py + 16, 0.0, self.max_health, self.health)

# all the enemies
game_enemies = []

# spawn an enemy
def spawn_enemy(variation):
	game_enemies.append(Enemy(variation))

# all turret types
TURRET_PISTOL = 0
TURRET_SHOTGUN = 1
TURRET_UZI = 2

# turret cooldowns
TURRET_COOLDOWN = [35, 85, 10]
# turret accuracy (low is better)
TURRET_ACCURACY = [0.0, 19.0, 4.0]
# turret bullets per shot
TURRET_BULLETS = [1, 10, 1]
# turret damage modifiers
TURRET_DAMAGE = [0.5, 0.35, 0.1]
# turret ranges
TURRET_RANGE = [80.0, 50.0, 100.0]

# turret base damage
TURRET_BASE_DAMAGE = 2.5

# a turret
class Turret:
	# create a turret
	def __init__(self, variation, x, y):
		self.variation = variation
		self.x = x
		self.y = y
		self.direction = 13.14

	# tick the turret
	def tick(self):
		self.direction += 0.0123

	# draw the turret (it's literally a line)
	def draw(self):
		global level_offset_x, level_offset_y
		x0 = level_offset_x + self.x * tile_w + tile_w / 2 - 1
		y0 = level_offset_y + self.y * tile_h + tile_h / 2 - 1
		t_len = 10.0
		x1 = x0 + math.sin(self.direction) * t_len
		y1 = y0 + math.cos(self.direction) * t_len
		pygame.draw.line(surface, (255, 255, 255), (x0, y0), (x1, y1), 2)

# all the turrets
game_turrets = []

# add a turret
def add_turret(variation, x, y):
	game_turrets.append(Turret(variation, x, y))

# all trap types
TRAP_SPIKE = 0
TRAP_BOMB = 1

# a trap
class Trap:
	# create a trap
	def __init__(self, variation, x, y):
		self.variation = variation
		self.x = x
		self.y = y
		# damage dealt, used by spike traps only
		self.dealt = 0.0
		self.dead = False

# all the traps
game_traps = []

# add a trap
def add_trap(variation, x, y):
	game_traps.append(Trap(variation, x, y))

# bullet constants
BULLET_SPEED = 0.05
BULLET_LENGTH = 10.0

# a bullet. these bullets are completely fake. since the game is fast paced,
# it suffices to draw a ray that zooms in on a target, but the target is
# damaged even before the ray hits it. in gameplay, these 'fake' bullets are
# unnoticeable
class Bullet:
	# create a bullet
	def __init__(self, x0, y0, x1, y1):
		self.x0 = x0
		self.y0 = y0
		self.x1 = x1
		self.y1 = y1
		self.t = 0.0
		self.length = dist((x0, y0), (x1, y1))

	# tick the bullet
	def tick(self):
		self.t += BULLET_SPEED

	# draw the bullet
	def draw(self):
		tc0 = clamp(self.t, 0.0, 1.0)
		tc1 = clamp(self.t + BULLET_LENGTH / self.length, 0.0, 1.0)
		x0 = self.x0 + (self.x1 - self.x0) * tc0
		y0 = self.y0 + (self.y1 - self.y0) * tc0
		x1 = self.x0 + (self.x1 - self.x0) * tc1
		y1 = self.y0 + (self.y1 - self.y0) * tc1
		pygame.draw.line(surface, (255, 255, 255), (x0, y0), (x1, y1), random.randint(1, 3))

# all the bullets
game_bullets = []

# add a bullet
def add_bullet(x0, y0, x1, y1):
	game_bullets.append(Bullet(x0, y0, x1, y1))

# a particle
class Particle:
	# create a particle
	def __init__(self, x, y, direction, color, power):
		self.x = x
		self.y = y
		# self.sx and self.sy are tracer positions used for blood tracing
		self.sx = x
		self.sy = y
		self.color = color
		length = random.random() * power
		self.dx = math.sin(direction) * length
		self.dy = math.cos(direction) * length
		self.life = random.randint(10, 50)

	# tick the particle
	def tick(self):
		global level_offset_x, level_offset_y
		global game_level
		drag = 0.9
		self.dx *= drag
		self.dy *= drag
		self.x += self.dx
		self.y += self.dy
		# don't move the tracer if it's in a wall
		tx = int((self.sx - level_offset_x) / tile_w)
		ty = int((self.sy - level_offset_y) / tile_h)
		if (can_be_placed_on_floor(game_level.peek(tx, ty))):
			self.sx += self.dx
			self.sy += self.dy
		self.life -= 1

	# draw the particle
	def draw(self):
		pygame.draw.line(surface, self.color, (self.x, self.y), (self.x + self.dx, self.y + self.dy))

# all the particles
game_particles = []

# add a particle
def add_particle(x, y, direction, color=(255, 255, 255), power=5.0):
	game_particles.append(Particle(x, y, direction, color, power))

# add a random ambient particle
def add_random_ambient_particle(color=(255, 255, 255), power=5.0):
	game_particles.append(Particle(random.randint(0, window_w), random.randint(0, window_h), random.random() * 360.0, color, power))

# add a particle burst
def add_particle_burst(x, y, color=(255, 255, 255), power=5.0):
	for i in range(0, 100):
		game_particles.append(Particle(x, y, random.random() * 360.0, color, power))

# add a tiny particle burst
def add_tiny_particle_burst(x, y, color=(255, 255, 255), power=2.0):
	for i in range(0, 10):
		game_particles.append(Particle(x, y, random.random() * 360.0, color, power))

# add an enemy explosion
def add_enemy_explosion(x, y, color=(255, 255, 255), power=5.0):
	for i in range(0, 300):
		game_particles.append(Particle(x, y, random.random() * 360.0, color, power))

# add an explosion
def add_explosion(x, y):
	global game_screenshake_x, game_screenshake_y
	SHAKE_POWER = 100.0
	game_screenshake_x = signed_rand() * SHAKE_POWER
	game_screenshake_y = signed_rand() * SHAKE_POWER
	for i in range(0, 500):
		g = random.randint(0, 255)
		color = (clamp(g * 10, 0, 255), clamp(g * 2, 0, 255), g)
		game_particles.append(Particle(x, y, random.random() * 360.0, color, random.random() * 15.0))

# add a gold explosion
def add_gold_explosion(x, y):
	global game_screenshake_x, game_screenshake_y
	SHAKE_POWER = 25.0
	game_screenshake_x = signed_rand() * SHAKE_POWER
	game_screenshake_y = signed_rand() * SHAKE_POWER
	for i in range(0, 250):
		g = random.randint(0, 255)
		color = (clamp(g * 5, 0, 255), clamp(g * 5, 0, 255), g)
		game_particles.append(Particle(x, y, random.random() * 360.0, color, random.random() * 7.5))

# load the levels
level1 = Level('level1.txt')
level2 = Level('level2.txt')
level3 = Level('level3.txt')
levels = [level1, level2, level3]

# render a level to the display
def draw_level(level, x, y):
	for j in range(0, level_h):
		for i in range(0, level_w):
			tile = level.peek(i, j)
			if (tile < 0):
				continue
			else:
				offset_x = x + i * tile_w
				offset_y = y + j * tile_h
				draw_subimage(tiles[tile], offset_x, offset_y)

# calculate the offset at which to draw any level
level_offset_x = window_w / 2 - (level_w * tile_w) / 2
level_offset_y = window_h / 2 - ((level_h - 3) * tile_h) / 2

# render a numeric string to the display
def draw_numeric(string, x, y):
	for i in range(0, len(string)):
		character = string[i]
		if (character == ' '):
			continue
		draw_subimage(numeric[int(character)], x + i * tile_w, y)

# load music and start playing it
if (True):
	pygame.mixer.music.load('220620_technoremix.wav')
	pygame.mixer.music.set_volume(1.0)
	pygame.mixer.music.play(-1)

# define all the sound names
sound_names = [
	'ambience', # unused
	'begin', # unused
	'enemy_die', # used
	'enemy_hit', # used
	'enemy_spawn', # used
	'failed_heal', # used
	'failed_purchase', # used
	'gold_damage', # used
	'heal', # used
	'level_fail', # used
	'level_pass', # used
	'menu_select', # used
	'place_trap', # used
	'place_turret', # used
	'purchase', # used
	'text_beep', # unused
	'turret_pistol', # used
	'turret_shotgun', # used
	'turret_uzi' # used
]

# load all the sounds
sounds = {}
for i in range(0, len(sound_names)):
	sounds[sound_names[i]] = load_sound('snd_' + sound_names[i] + '.wav')

# play a sound
def do_sound(sound_name):
	# doesn't seem to work on my computer
	play_sound(sounds[sound_name])
	pass

# load the font
pygame.font.init()
font_default = pygame.font.Font('ProggyClean.ttf', 16)

# render some text
def render_text(font, text, color, x, y):
	paste = font.render(text, False, color)
	surface.blit(paste, (x, y))

# render some inverted text
def render_inverted_text(font, text, color, x, y):
	paste = font.render(text, False, (0, 0, 0), color)
	surface.blit(paste, (x, y))

# measure some text
def measure_text(font, text):
	return font.size(text)

# render some horizontally centered text
def render_horizontal_text(font, text, color, y):
	size = measure_text(font, text)
	x = window_w / 2 - size[0] / 2
	render_text(font, text, color, x, y)

# render some picked horizontally centered text
def render_picked_horizontal_text(font, text, color, y):
	size = measure_text(font, text)
	x = window_w / 2 - size[0] / 2
	render_inverted_text(font, text, color, x, y)

# create a clock for frame rate capping
clock = pygame.time.Clock()

# the state machine for the shops
currently_placing_turret = False
currently_placing_turret_type = -1

# the game state
game_level = level3
game_level_num = 3
game_gold = 100
game_time = 0
game_cash = 150
game_time_started = seconds()
game_health_cooldown = 0
game_screenshake_x = 0.0
game_screenshake_y = 0.0
game_spawn = 0

# the game statistics
stat_kills = 0
stat_turrets = 0
stat_traps = 0
stat_money = 0
stat_damage = 0

# initialize a level
def init_level(x):
	global game_level
	global game_level_num
	global game_gold
	global game_time
	global game_cash
	global game_time_started
	global game_health_cooldown
	global game_screenshake_x
	global game_screenshake_y
	global game_spawn
	global game_enemies
	global game_bullets
	global game_turrets
	global game_traps
	global game_particles
	global stat_kills
	global stat_turrets
	global stat_traps
	global stat_money
	global stat_damage
	game_level = levels[x - 1]
	game_level_num = x
	game_gold = 100
	game_time = 0
	game_cash = 150
	game_time_started = seconds()
	game_health_cooldown = 0
	game_screenshake_x = 0.0
	game_screenshake_y = 0.0
	game_spawn = 0
	game_enemies = []
	game_bullets = []
	game_turrets = []
	game_traps = []
	game_particles = []
	stat_kills = 0
	stat_turrets = 0
	stat_traps = 0
	stat_money = 0
	stat_damage = 0
	game_level.reset()

# the title/you win/you lose animations
game_title_tiles = []
game_you_win_tiles = []
game_you_lose_tiles = []
game_title_iteration = 0

# all screens
SCREEN_TITLE = 0
SCREEN_GAME = 1
SCREEN_THANKS = 2
SCREEN_HOW = 3
SCREEN_WIN = 4
SCREEN_LOSE = 5

# thank you text
thank_you = [
'Bank Heist by Adam Sidat in 2019',
'',
'*** Graphics ***',
'All graphics made by me in Aseprite,',
'but inspired by classic games like',
'Microsoft Minesweeper',
'',
'*** Sounds ***',
'All sounds made by me on www.bfxr.net,',
'so thanks to increpare, it\'s developer',
'',
'*** Music ***',
'The song is \'Only When - DEMO\'',
'composed by arcanedragon-2004 from',
'Newgrounds',
'',
'*** Extras ***',
'Thanks to all people who gave feedback',
'and tested the game'
]

# how to play text
how_to_play = [
'How To Play',
'',
'Oh no! The bank is under attack by',
'robbers. Thankfully, we have an',
'advanced security system. Use the',
'buttons at the top of the screen to',
'purchase traps and turrets to deter',
'the robbers. Once you purchase',
'something, click anywhere to deploy',
'it. You can earn cash to buy things',
'with by killing robbers. If you can',
'stop the robbers for 100 seconds,',
'they\'ll give up. But don\'t let them',
'get all the gold first!',
]

# the current screen
current_screen = SCREEN_TITLE

# purchase an item for x dollars if there is at least that much cash
# available. return True if the item was purchased
def purchase_if_possible(x):
	global game_cash
	global stat_money
	if (game_cash >= x):
		game_cash -= x
		stat_money += x
		do_sound('purchase')
		return True
	do_sound('failed_purchase')
	return False

# game loop
iteration = 0
quit = False
while not quit:
	# for timing
	ms0 = ms()

	# poll events
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			# quit
			quit = True
		elif event.type == pygame.KEYDOWN:
			if (current_screen == SCREEN_THANKS or current_screen == SCREEN_HOW or current_screen == SCREEN_WIN or current_screen == SCREEN_LOSE):
				game_title_iteration = len(title_tiles)
				current_screen = SCREEN_TITLE
			else:
				if event.key == pygame.K_t:
					game_title_tiles.clear()

	# update state
	mouse_unscaled = pygame.mouse.get_pos()
	mouse = (mouse_unscaled[0] / gfx_scale, mouse_unscaled[1] / gfx_scale)
	mouse_left_pressed = pygame.mouse.get_pressed()[0]
	mouse_right_pressed = pygame.mouse.get_pressed()[2]

	# do whatever the current screen needs to do
	if (current_screen == SCREEN_TITLE):
		# clear the screen
		surface.fill((0, 0, 0))

		# add title tiles if all of them haven't been added yet
		if (len(game_title_tiles) != len(title_tiles)):
			tile = title_tiles[len(game_title_tiles)]
			tx = tile[0]
			ty = tile[1]
			add_tiny_particle_burst(title_offset_x + tx * 6, title_offset_y + ty * 6)
			game_title_tiles.append(tile)

		# draw all the title tiles
		for i in range(0, len(game_title_tiles)):
			tile = title_tiles[i]
			tx = tile[0]
			ty = tile[1]
			draw_image(gui_title_tile, title_offset_x + tx * 6, title_offset_y + ty * 6)

		# do buttons
		buttons = ['How To Play', 'Play Level 1', 'Play Level 2', 'Play Level 3', 'Credits']
		for i in range(0, 3):
			if (not level_unlocked(i + 1)):
				buttons[i + 1] = 'Complete previous level to unlock'
			else:
				buttons[i + 1] += ' | High Score: ' + obfuscate_if_negative(preferences['highscores'][i])
		button_height = 19
		for i in range(0, len(buttons)):
			text = portion_of_text(buttons[i], (game_title_iteration - i * 25) / 25)
			size = measure_text(font_default, text)
			y = 50 + window_h / 2 - button_height * len(buttons) / 2 + i * button_height
			aabbx = window_w / 2 - size[0] / 2
			aabby = y
			aabbw = size[0]
			aabbh = button_height - 3
			if (in_aabb_raw(mouse[0], mouse[1], aabbx, aabby, aabbw, aabbh)):
				render_picked_horizontal_text(font_default, text, (255, 255, 255), y)
				if (mouse_left_pressed):
					do_sound('menu_select')
					if (i == 0):
						# How To Play
						game_title_iteration = 0
						current_screen = SCREEN_HOW
					elif (i == 1):
						# Play Level 1
						if (level_unlocked(1)):
							game_you_win_tiles.clear()
							game_you_lose_tiles.clear()
							game_title_iteration = 0
							current_screen = SCREEN_GAME
							init_level(1)
					elif (i == 2):
						# Play Level 2
						if (level_unlocked(2)):
							game_you_win_tiles.clear()
							game_you_lose_tiles.clear()
							game_title_iteration = 0
							current_screen = SCREEN_GAME
							init_level(2)
					elif (i == 3):
						# Play Level 3
						if (level_unlocked(3)):
							game_you_win_tiles.clear()
							game_you_lose_tiles.clear()
							game_title_iteration = 0
							current_screen = SCREEN_GAME
							init_level(3)
					elif (i == 4):
						# Credits
						game_title_iteration = 0
						current_screen = SCREEN_THANKS
			else:
				render_horizontal_text(font_default, text, (255, 255, 255), y)

		# add ambient explosions
		if (game_title_iteration > len(title_tiles) and random.randint(0, 25) == 0):
			a = 10
			add_explosion(random.randint(-a, window_w + a - 1), random.randint(-a, window_h + a - 1))

		# draw the particles
		for i in range(0, len(game_particles)):
			p = game_particles[i]
			p.tick()
			p.draw()
			game_level.set_blood(p.sx, p.sy, p.color)

		# remove dead particles
		game_particles = [i for i in game_particles if i.life >= 0]

		# increment the iteration counter
		game_title_iteration += 1
	elif (current_screen == SCREEN_THANKS):
		# clear the screen
		surface.fill((0, 0, 0))

		# draw the thank you text
		for i in range(0, len(thank_you)):
			y = window_h / 2 - len(thank_you) * 8 + i * 16
			render_horizontal_text(font_default, portion_of_text(thank_you[i], (game_title_iteration - i * 15) / 15), (255, 255, 255), y)

		# increment the iteration counter
		game_title_iteration += 1
	elif (current_screen == SCREEN_HOW):
		# clear the screen
		surface.fill((0, 0, 0))

		# draw the how to play text
		for i in range(0, len(how_to_play)):
			y = window_h / 2 - len(how_to_play) * 8 + i * 16
			render_horizontal_text(font_default, portion_of_text(how_to_play[i], (game_title_iteration - i * 15) / 15), (255, 255, 255), y)

		# increment the iteration counter
		game_title_iteration += 1
	elif (current_screen == SCREEN_WIN):
		# clear the screen
		surface.fill((0, 0, 0))

		# add title tiles if all of them haven't been added yet
		if (len(game_you_win_tiles) != len(you_win_tiles)):
			tile = you_win_tiles[len(game_you_win_tiles)]
			tx = tile[0]
			ty = tile[1]
			add_tiny_particle_burst(title_offset_x + tx * 6, center_title_offset_y + ty * 6)
			game_you_win_tiles.append(tile)

		# draw all the title tiles
		for i in range(0, len(game_you_win_tiles)):
			tile = you_win_tiles[i]
			tx = tile[0]
			ty = tile[1]
			draw_image(gui_title_tile, title_offset_x + tx * 6, center_title_offset_y + ty * 6)

		# draw summary
		summary = [
			'You killed ' + str(stat_kills) + ' enemies',
			'You deployed ' + str(stat_turrets) + ' turrets',
			'You placed ' + str(stat_traps) + ' traps',
			'You spent ' + str(stat_money) + ' dollars',
			'You took ' + str(stat_damage) + ' damage',
			'',
			'Press any key to continue'
		]
		for i in range(0, len(summary)):
			y = center_title_offset_y + 75 + i * 16
			render_horizontal_text(font_default, portion_of_text(summary[i], (game_title_iteration - i * 15) / 15), (255, 255, 255), y)

		# add ambient explosions
		if (game_title_iteration > len(you_win_tiles) and random.randint(0, 25) == 0):
			a = 10
			add_explosion(random.randint(-a, window_w + a - 1), random.randint(-a, window_h + a - 1))

		# draw the particles
		for i in range(0, len(game_particles)):
			p = game_particles[i]
			p.tick()
			p.draw()
			game_level.set_blood(p.sx, p.sy, p.color)

		# remove dead particles
		game_particles = [i for i in game_particles if i.life >= 0]

		# increment the iteration counter
		game_title_iteration += 1
	elif (current_screen == SCREEN_LOSE):
		# clear the screen
		surface.fill((0, 0, 0))

		# add title tiles if all of them haven't been added yet
		if (len(game_you_lose_tiles) != len(you_lose_tiles)):
			tile = you_lose_tiles[len(game_you_lose_tiles)]
			tx = tile[0]
			ty = tile[1]
			add_tiny_particle_burst(title_offset_x + tx * 6, center_title_offset_y + ty * 6)
			game_you_lose_tiles.append(tile)

		# draw all the title tiles
		for i in range(0, len(game_you_lose_tiles)):
			tile = you_lose_tiles[i]
			tx = tile[0]
			ty = tile[1]
			draw_image(gui_title_tile, title_offset_x + tx * 6, center_title_offset_y + ty * 6)

		# draw summary
		summary = [
			'You killed ' + str(stat_kills) + ' enemies',
			'You deployed ' + str(stat_turrets) + ' turrets',
			'You placed ' + str(stat_traps) + ' traps',
			'You spent ' + str(stat_money) + ' dollars',
			'You took ' + str(stat_damage) + ' damage',
			'',
			'Press any key to continue'
		]
		for i in range(0, len(summary)):
			y = center_title_offset_y + 75 + i * 16
			render_horizontal_text(font_default, portion_of_text(summary[i], (game_title_iteration - i * 15) / 15), (255, 255, 255), y)

		# add ambient explosions
		if (game_title_iteration > len(you_win_tiles) and random.randint(0, 25) == 0):
			a = 10
			add_explosion(random.randint(-a, window_w + a - 1), random.randint(-a, window_h + a - 1))

		# draw the particles
		for i in range(0, len(game_particles)):
			p = game_particles[i]
			p.tick()
			p.draw()
			game_level.set_blood(p.sx, p.sy, p.color)

		# remove dead particles
		game_particles = [i for i in game_particles if i.life >= 0]

		# increment the iteration counter
		game_title_iteration += 1
	elif (current_screen == SCREEN_GAME):
		# go to the lose screen if we lost
		if (game_gold < 0):
			game_you_lose_tiles.clear()
			game_title_iteration = 0
			current_screen = SCREEN_LOSE
			do_sound('level_fail')
   
		# get the elapsed time
		game_time = seconds() - game_time_started
   
		# go to the win screen if we won
		if (game_time >= 100):
			game_you_win_tiles.clear()
			game_title_iteration = 0
			current_screen = SCREEN_WIN
			do_sound('level_pass')
			# unlock following levels, if any
			preferences['levels_unlocked'] = max(preferences['levels_unlocked'], game_level_num + 1)
			# set highscore
			preferences['highscores'][game_level_num - 1] = max(preferences['highscores'][game_level_num - 1], game_gold)

		# clear the screen
		surface.fill((0, 0, 0))

		# draw the level
		draw_level(game_level, level_offset_x, level_offset_y)

		# draw the blood effects
		surface.blit(game_level.blood, (0, 0))

		# draw the enemies
		for i in range(0, len(game_enemies)):
			e = game_enemies[i]
			e.tick()
			e.draw()
			if (e.health <= 0):
				# if the enemy died, do an explosion and give the player some
				# money
				pos = e.pos()
				add_enemy_explosion(pos[0] * tile_w + level_offset_x + 8, pos[1] * tile_h + level_offset_y + 8, E_COLOR[e.variation])
				game_cash += E_LOOT[e.variation]
				do_sound('enemy_die')
				stat_kills += 1

		# remove dead enemies
		game_enemies = [i for i in game_enemies if i.health > 0.0]

		# draw the turrets
		for i in range(0, len(game_turrets)):
			game_turrets[i].tick()
			game_turrets[i].draw()

		# draw the bullets
		for i in range(0, len(game_bullets)):
			game_bullets[i].tick()
			game_bullets[i].draw()

		# remove dead bullets
		game_bullets = [i for i in game_bullets if i.t < 1.0]

		# get the positions of each enemy
		enemy_positions = []
		for i in range(0, len(game_enemies)):
			pos = game_enemies[i].pos()
			x = pos[0] * tile_w + level_offset_x + 8
			y = pos[1] * tile_h + level_offset_y + 8
			enemy_positions.append((x, y))

		# do turret AI
		for i in range(0, len(game_turrets)):
			turret = game_turrets[i]
			tv = turret.variation
			if (len(enemy_positions) > 0):
				tx = turret.x * tile_w + level_offset_x + 8
				ty = turret.y * tile_h + level_offset_y + 8
				t = (tx, ty)
				# find the index of the nearest enemy
				e = nearest_to(t, enemy_positions)
				# find the distance to the nearest enemy's future position
				prediction = game_enemies[e].next_pos()
				u = prediction[0] * tile_w + level_offset_x + 8
				v = prediction[1] * tile_h + level_offset_y + 8
				p = (u, v)
				d = dist(t, p)
				# point towards that enemy
				turret.direction = angle_to(t, p)
				# check if the enemy is in range
				if (d < TURRET_RANGE[tv]):
					# check if the turret can shoot. this is basically checking
					# if the iteration number plus a scrambled offset is a
					# multiple of (cooldown), which makes the turret shoot every
					# (cooldown) iterations
					cooldown = TURRET_COOLDOWN[tv]
					if ((iteration + i * 1337) % cooldown == 0):
						# shoot as many bullets as required
						for z in range(0, TURRET_BULLETS[tv]):
							# shoot a bullet and weaken the enemy
							add_bullet(t[0], t[1], p[0] + signed_rand() * TURRET_ACCURACY[tv], p[1] + signed_rand() * TURRET_ACCURACY[tv])
							game_enemies[e].health -= TURRET_BASE_DAMAGE * TURRET_DAMAGE[tv]
						# play the correct sound
						if (tv == TURRET_PISTOL):
							do_sound('turret_pistol')
						elif (tv == TURRET_SHOTGUN):
							do_sound('turret_shotgun')
						elif (tv == TURRET_UZI):
							do_sound('turret_uzi')

		# do trap AI
		for i in range(0, len(game_traps)):
			trap = game_traps[i]
			aabbx = trap.x * tile_w + level_offset_x
			aabby = trap.y * tile_h + level_offset_y
			for j in range(0, len(game_enemies)):
				enemy = game_enemies[j]
				pos = enemy.pos()
				px = pos[0] * tile_w + level_offset_x + 8
				py = pos[1] * tile_h + level_offset_y + 8
				if (in_aabb_raw(px, py, aabbx, aabby, tile_w, tile_h)):
					# activate the trap
					if (trap.variation == TRAP_SPIKE):
						# deal out some damage
						enemy.health -= 1.0
						trap.dealt += 1.0
						# if the trap dealt enough damage, kill it
						if (trap.dealt > 10.0):
							add_particle_burst(px, py)
							trap.dead = True
						do_sound('enemy_hit')
					elif (trap.variation == TRAP_BOMB):
						# cause an explosion and obliterate the enemy
						add_explosion(px, py)
						enemy.health -= 9999.0
						trap.dead = True
			# if the trap was killed then remove it from the map
			if (trap.dead):
				game_level.poke(trap.x, trap.y, TILE_FLOOR)

		# remove dead traps
		game_traps = [i for i in game_traps if i.dead == False]

		# draw the particles
		for i in range(0, len(game_particles)):
			p = game_particles[i]
			p.tick()
			p.draw()
			game_level.set_blood(p.sx, p.sy, p.color)

		# remove dead particles
		game_particles = [i for i in game_particles if i.life >= 0]

		# draw the gun shop
		wants_pistol_turret = draw_button(btn_pistol_turret, level_offset_x - 32, level_offset_y - tile_h * 3)
		wants_shotgun_turret = draw_button(btn_shotgun_turret, level_offset_x - 32, level_offset_y - tile_h * 2)
		wants_uzi_turret = draw_button(btn_uzi_turret, level_offset_x - 32, level_offset_y - tile_h * 1)
		draw_image(gui_pricing, level_offset_x + tile_w * 6 - 32, level_offset_y - tile_h * 3)

		# draw the misc. shop
		if (game_health_cooldown == 0):
			wants_health_up = draw_button(btn_health_up, level_offset_x + tile_w * 14 + 32, level_offset_y - tile_h * 3)
			if (wants_health_up):
				do_sound('heal')
		else:
			wants_health_up = draw_disabled_button(btn_health_up, level_offset_x + tile_w * 14 + 32, level_offset_y - tile_h * 3)
		wants_spike_trap = draw_button(btn_spike_trap, level_offset_x + tile_w * 14 + 32, level_offset_y - tile_h * 2)
		wants_bomb_trap = draw_button(btn_bomb_trap, level_offset_x + tile_w * 14 + 32, level_offset_y - tile_h * 1)
		draw_image(gui_pricing2, level_offset_x + tile_w * 12 + 32, level_offset_y - tile_h * 3)

		# allow interaction with the shop if something is not already in the
		# player's 'hand'
		if (not currently_placing_turret):
			if wants_pistol_turret:
				if (purchase_if_possible(50)):
					currently_placing_turret = True
					currently_placing_turret_type = TILE_PISTOL_TURRET
			elif wants_shotgun_turret:
				if (purchase_if_possible(100)):
					currently_placing_turret = True
					currently_placing_turret_type = TILE_SHOTGUN_TURRET
			elif wants_uzi_turret:
				if (purchase_if_possible(150)):
					currently_placing_turret = True
					currently_placing_turret_type = TILE_UZI_TURRET
			elif wants_health_up:
				if (game_health_cooldown == 0 and purchase_if_possible(50)):
					game_gold += 15
					if (game_gold > 100):
						game_gold = 100
					# set the health cooldown so that you can't use a ton of
					# health-ups in a row
					game_health_cooldown = 600
			elif wants_spike_trap:
				if (purchase_if_possible(100)):
					currently_placing_turret = True
					currently_placing_turret_type = TILE_SPIKE_TRAP
			elif wants_bomb_trap:
				if (purchase_if_possible(150)):
					currently_placing_turret = True
					currently_placing_turret_type = TILE_BOMB_TRAP

		# lower the health cooldown
		if (game_health_cooldown > 0):
			game_health_cooldown -= 1

		# draw the interaction 'silhouette' so that the player can see where they
		# are placing something
		if (currently_placing_turret):
			# get tile coordinates at mouse position
			tx = int((mouse[0] - level_offset_x) / tile_w)
			ty = int((mouse[1] - level_offset_y) / tile_h)
			if (not (tx < 0 or tx >= level_w or ty < 0 or ty >= level_h)):
				# not out of bounds, proceed
				tile = game_level.peek(tx, ty)
				if (can_be_placed_on_wall(currently_placing_turret_type)):
					# make sure the hovered tile is a wall tile
					if (tile == TILE_WALL):
						draw_subimage(tiles[currently_placing_turret_type], mouse[0], mouse[1])
						# place the turret/trap if clicked
						if (mouse_left_pressed or mouse_right_pressed):
							do_sound('place_turret')
							stat_turrets += 1
							add_particle_burst(mouse[0], mouse[1])
							# note that the turret type enumerations are
							# sequential, so doing this is kind of hacky but still
							# valid
							add_turret(currently_placing_turret_type - TILE_PISTOL_TURRET, tx, ty)
							game_level.poke(tx, ty, currently_placing_turret_type)
							# a cheat, right click to place as many as you want
							if (not mouse_right_pressed):
								currently_placing_turret = False
					else:
						draw_subimage(tiles[TILE_NOPE], mouse[0], mouse[1])
				elif (can_be_placed_on_floor(currently_placing_turret_type)):
					# make sure the hovered tile is a floor tile
					if (tile == TILE_FLOOR):
						draw_subimage(tiles[currently_placing_turret_type], mouse[0], mouse[1])
						# place the turret/trap if clicked
						if (mouse_left_pressed or mouse_right_pressed):
							do_sound('place_trap')
							stat_traps += 1
							add_particle_burst(mouse[0], mouse[1])
							# note that the trap type enumerations are sequential,
							# so doing this is kind of hacky but still valid
							add_trap(currently_placing_turret_type - TILE_SPIKE_TRAP, tx, ty)
							game_level.poke(tx, ty, currently_placing_turret_type)
							# a cheat, right click to place as many as you want
							if (not mouse_right_pressed):
								currently_placing_turret = False
					else:
						draw_subimage(tiles[TILE_NOPE], mouse[0], mouse[1])

		# draw the heads-up display
		draw_image(gui_heads_up, level_offset_x + tile_w * 7, level_offset_y - tile_h * 3)
		draw_numeric(format_int(game_gold, 3), level_offset_x + tile_w * 9, level_offset_y - tile_h * 3)
		draw_numeric(format_int(game_time, 3), level_offset_x + tile_w * 9, level_offset_y - tile_h * 2)
		draw_numeric(format_int(game_cash, 3), level_offset_x + tile_w * 9, level_offset_y - tile_h * 1)

		# do spawning
		spawner = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 1, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 1, 2, 1, 2, 1, 2, 0, 0, 0, 0, 2, 2, 2, 2, 1, 1, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]
		if ((iteration - 1) % 50 == 0):
			game_spawn += 1
			spawn_enemy(spawner[(game_spawn - 1) % len(spawner)])

	# do screenshake
	SHAKE_DISSIPATE = 0.5
	game_screenshake_x = -game_screenshake_x * SHAKE_DISSIPATE
	game_screenshake_y = -game_screenshake_y * SHAKE_DISSIPATE

	# copy the surface to the screen
	scaled_surface = pygame.transform.scale(surface, (window_w * gfx_scale, window_h * gfx_scale))
	screen.fill((0, 0, 0), (0, 0, window_w * gfx_scale, window_h * gfx_scale))
	screen.blit(scaled_surface, (int(game_screenshake_x), int(game_screenshake_y)))

	# update the display
	pygame.display.update()
	clock.tick(60)
	iteration += 1

	# do timing
	elapsed = ms() - ms0
	if (iteration % 60 == 0):
		print('frame', iteration + 1, 'took', elapsed, 'ms')

# clean up
pygame.quit()

# save preferences
with open('./preferences.dat', 'wb') as f:
	pickle.dump(preferences, f, pickle.HIGHEST_PROTOCOL)