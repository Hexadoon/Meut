import pyxel
import pyaudio
import numpy as np
import random
from threading import Thread
import math
import time

tmap = []

def map_init():
	global tmap
	tmap = [[False for j in range(100)] for i in range(100)]

	for i in range(100):
		tmap[0][i] = True
		tmap[i][0] = True
		tmap[99][i] = True
		tmap[i][99] = True

	for i in range(98):
		for j in range(98):

			l = [tmap[i+1][j],tmap[i][j],tmap[i][j+1]]
			l = [0 for x in l if x]
			if len(l) <= 2 and random.random() > 0.7:
				tmap[i+1][j+1] = True

	for i in range(96):
		for j in range(96):
			if not tmap[i+2][j+2] and \
			tmap[i+1][j+2] and \
			tmap[i+2][j+1] and \
			tmap[i+3][j+2] and \
			tmap[i+2][j+3]:
				t = random.randint(0,3)
				if t == 0:
					tmap[i+1][j+2] = False
				elif t == 1:
					tmap[i+2][j+1] = False
				elif t == 2:
					tmap[i+3][j+2] = False
				else:
					tmap[i+2][j+3] = False

	tmap[50][50] = False

map_init()

def dist(x1, y1, x2, y2):
	return math.sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1))

class Monster:

	def __init__(self, x_loc, y_loc):

		self.x = x_loc
		self.y = y_loc

		self.active = False

		self.target_loc_x = 0
		self.target_loc_y = 0
		self.target_latest = 0

		self.path = []

		self.eye_dir = 0

	def move(self):
		if self.active:
			self.move_to_target()
		else:
			self.wander()

	def move_to_target(self):
		if len(self.path) > 0:
			if self.path[0] == 0:
				self.x += 1
			elif self.path[0] == 1:
				self.y += 1
			elif self.path[0] == 2:
				self.x -= 1
			else:
				self.y -= 1

			del self.path[0]
		else:
			self.active = False

	def wander(self):
		all_adj = [[self.x + 1, self.y], [self.x, self.y + 1], [self.x - 1, self.y], [self.x, self.y - 1]]
		poss_pos = []
		for i in all_adj:
			if not tmap[i[0]][i[1]]:
				poss_pos.append(i)

		if len(poss_pos) == 0:
			return
		else:
			next_pos = random.choice(poss_pos)
			self.x = next_pos[0]
			self.y = next_pos[1]

	def calc_path(self):
		futures = {(self.x,self.y,dist(self.x, self.y, self.target_loc_x, self.target_loc_y)):[]}
		visited = set()

		while futures:
			min_key = list(futures.keys())[0]
			min_dist = list(futures.keys())[0][2] + len(futures[list(futures.keys())[0]])
			for t in futures:
				if min_dist > t[2] + len(futures[t]):
					min_key = t
					min_dist = t[2] + len(futures[t])

			if min_key[0] == self.target_loc_x and min_key[1] == self.target_loc_y:
				return futures[min_key]

			curr_path = futures[min_key]
			currx = min_key[0]
			curry = min_key[1]

			del futures[min_key]
			visited.add((min_key[0], min_key[1]))

			all_adj = {0:(currx + 1, curry), 1:(currx, curry + 1), 2:(currx - 1, curry), 3:(currx, curry - 1)}
			poss_pos = {}
			for i in all_adj:
				if not tmap[all_adj[i][0]][all_adj[i][1]] and all_adj[i] not in visited:
					poss_pos[i] = all_adj[i]

			if not bool(poss_pos):
				continue

			for poss in poss_pos:
				futures[(poss_pos[poss][0],poss_pos[poss][1],dist(poss_pos[poss][0],poss_pos[poss][1],self.target_loc_x,self.target_loc_y))] = curr_path + [poss]

		return []

	def trigger(self, target_x, target_y):
		self.target_loc_x = target_x
		self.target_loc_y = target_y
		self.active = True

		self.path = self.calc_path()

	def randomize_eye(self):
		self.eye_dir = random.randint(0,3)

	def tick(self, frame_counter):
		if frame_counter == 0 and not self.active:
			self.wander()
		elif frame_counter % 5 == 0 and self.active:
			self.move()

		if frame_counter % 30 == 0:
			self.randomize_eye()

class Main:

	def __init__(self):

		pyxel.init(144, 144, caption="Meut")
		pyxel.load("my_resource.pyxres")

		self.screen = 0
		# 0 : home, 1 : game

		self.player_x = 50
		self.player_y = 50

		self.monsters = []

		self.monster_spawn()

		self.quit = False

		self.move = 0
		# 0 : left, 1 : right

		self.moving = False

		self.frame = 0

		self.made_noise = False
		self.noise_amt = 0
		self.ping_list = {}

		self.curr_dir = 0
		#0 : down, 1 : left, 2 : up, 3 : right

		self.audio_obj = pyaudio.PyAudio()
		self.audio_stream = self.audio_obj.open(format=pyaudio.paInt16,channels=1,rate=12000,input=True,frames_per_buffer=1024)

		self.audio_thread = Thread(target = self.listen)
		self.audio_thread.start()

		self.monster_thread = Thread(target = self.run_monsters)
		self.monster_thread.start()

		pyxel.run(self.update, self.draw)

	# def home_screen(self):
	# 	pyxel.blt(38,40,0,0,80,64,32)

	# 	pyxel.blt(36,100,0,0,112,80,16)

	# def start(self):
	# 	if pyxel.btnp(pyxel.MOUSE_LEFT_BUTTON) and (pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 13 or pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 6):
	# 		self.screen = 1
	# 		pyxel.mouse(False)

	def monster_spawn(self):
		global tmap
		all_spawns = []
		for x in range(98):
			for y in range(98):
				all_spawns.append([x + 1, y + 1])

		poss_spawns = []
		for l in all_spawns:
			if not tmap[l[0]][l[1]]:
				poss_spawns.append(l)

		for i in range(50):
			l = random.randint(0,len(poss_spawns) - 1)
			self.monsters.append(Monster(poss_spawns[l][0], poss_spawns[l][1]))
			del poss_spawns[l]

	def display_monsters(self):
		for m in self.monsters:
			xdiff = m.x - self.player_x
			ydiff = m.y - self.player_y
			if xdiff < 5 and ydiff < 5:
				if not m.active:
					pyxel.blt(64 + xdiff * 16, 64 + ydiff * 16,0,m.eye_dir * 16, 128, 16, 16)
				else:
					pyxel.blt(64 + xdiff * 16, 64 + ydiff * 16,0,m.eye_dir * 16, 144, 16, 16)

	def check_lose(self):
		for m in self.monsters:
			if m.x == self.player_x and m.y == self.player_y:
				return True

	def run_monsters(self):
		for m in self.monsters:
			if m.x - self.player_x < 30 or m.y - self.player_y < 30 or m.active:
				m.tick(self.frame)

				for p in self.ping_list:
					ping_dist = dist(m.x, m.y, self.ping_list[p][1], self.ping_list[p][2])
					if ping_dist < (self.ping_list[p][0] / 4800) and m.target_latest < self.ping_list[p][3]:
						m.trigger(self.ping_list[p][1],self.ping_list[p][2])
						m.target_latest = self.ping_list[p][3]

	def listen(self):
		while not self.quit:
			data = np.frombuffer(self.audio_stream.read(1024),dtype=np.int16)

			mx = max(data)
			if mx > 800:
				self.made_noise = True
				self.noise_amt = mx

	def count_frame(self):
		self.frame += 1
		self.frame %= 60

	def ping(self):
		if self.made_noise:
			self.made_noise = False
			self.ping_list[self.noise_amt] = [0, self.player_x, self.player_y, time.time()]

		for x in self.ping_list:
			pyxel.circb(72 + 16 * (self.ping_list[x][1] - self.player_x), 72 + 16 * (self.ping_list[x][2] - self.player_y),self.ping_list[x][0]/300,13)
			self.ping_list[x][0] += 300
			
		for key in [key for key in self.ping_list if self.ping_list[key][0] > key]: del self.ping_list[key] 

	def move_btn(self):
		if pyxel.btnp(pyxel.KEY_W):
			self.curr_dir = 2
			self.moving = True
		elif pyxel.btnp(pyxel.KEY_A):
			self.curr_dir = 1
			self.moving = True
		elif pyxel.btnp(pyxel.KEY_S):
			self.curr_dir = 0
			self.moving = True
		elif pyxel.btnp(pyxel.KEY_D):
			self.curr_dir = 3
			self.moving = True
		else:
			self.moving = False

		if self.moving:
			if self.curr_dir == 0 and not tmap[self.player_x][self.player_y + 1]:
				self.player_y += 1

			elif self.curr_dir == 1 and not tmap[self.player_x - 1][self.player_y]:
				self.player_x -= 1

			elif self.curr_dir == 2 and not tmap[self.player_x][self.player_y - 1]:
				self.player_y -= 1

			elif self.curr_dir == 3 and not tmap[self.player_x + 1][self.player_y]:
				self.player_x += 1

	def char_model(self):
		if not self.moving:
			if self.curr_dir == 0:
				pyxel.blt(64,64,0,0,0,16,16)
				# DOWN

			elif self.curr_dir == 1:
				pyxel.blt(64,64,0,0,48,16,16)
				# LEFT

			elif self.curr_dir == 2:
				pyxel.blt(64,64,0,0,16,16,16)
				# UP

			else:
				pyxel.blt(64,64,0,0,32,16,16)
				# RIGHT
		else:
			# DOWN
			if self.curr_dir == 0:
				if self.move == 0:
					pyxel.blt(64,64,0,16,0,16,16)
				else:
					pyxel.blt(64,64,0,32,0,16,16)

			# LEFT
			elif self.curr_dir == 1:
				pyxel.blt(64,64,0,16,48,16,16)

			# UP
			elif self.curr_dir == 2:
				if self.move == 0:
					pyxel.blt(64,64,0,16,16,16,16)
				else:
					pyxel.blt(64,64,0,32,16,16,16)

			# RIGHT
			else:
				pyxel.blt(64,64,0,16,32,16,16)

			self.move = 0 if self.move == 1 else 1

	def display_map(self):
		for x in range(9):
			i = x - 4
			for y in range(9):
				j = y - 4
				if self.player_x + i > 99 or self.player_x + i < 0 or \
				self.player_y + j > 99 or self.player_y + j < 0:
					pyxel.blt(x*16,y*16,0,16,64,16,16)
				elif tmap[self.player_x + i][self.player_y + j]:
					pyxel.blt(x*16,y*16,0,0,64,16,16)

	def isolate_view(self):
		for x in range(75):
			pyxel.circb(72,72,x+50,0)

		pyxel.rect(0,0,22,144,0)
		pyxel.rect(0,0,144,22,0)
		pyxel.rect(122,0,22,144,0)
		pyxel.rect(0,122,144,22,0)

		pyxel.tri(0,144,0,70,74,144,0)
		pyxel.tri(0,0,0,74,74,0,0)
		pyxel.tri(144,0,70,0,144,74,0)
		pyxel.tri(144,144,144,70,70,144,0)

		pyxel.tri(0,144,0,56,60,144,0)
		pyxel.tri(0,144,0,80,88,144,0)
		pyxel.tri(0,0,60,0,0,88,0)
		pyxel.tri(0,0,92,0,0,60,0)
		pyxel.tri(144,0,52,0,144,60,0)
		pyxel.tri(144,0,88,0,144,96,0)
		pyxel.tri(144,144,50,144,144,88,0)
		pyxel.tri(144,144,88,144,144,50,0)

	def update(self):
		if pyxel.btnp(pyxel.KEY_Q) or self.check_lose():
			self.quit = True

			self.audio_thread.join()

			self.audio_stream.stop_stream()
			self.audio_stream.close()
			self.audio_obj.terminate()

			self.monster_thread.join()

			pyxel.quit()

		self.move_btn()
		self.count_frame()
		self.run_monsters()

	def draw(self):
		pyxel.cls(0)

		self.display_map()
		self.char_model()
		self.display_monsters()
		self.ping()
		self.isolate_view()

Main()