import pyxel
import pyaudio
import numpy as np
import random
from threading import Thread
import math
import time
from playsound import playsound

tmap = [] # map array of booleans (True is a wall, False is space)

level = 1 # level counter
map_size = 100 * level # increase map size on level increment

exit = (0,0) # exit is randomized on each level

def map_init():
	global tmap
	global exit

	map_size = 100 * level

	tmap = [[False for j in range(map_size)] for i in range(map_size)] # initialize empty map

	for i in range(map_size): # make walls
		tmap[0][i] = True
		tmap[i][0] = True
		tmap[map_size - 1][i] = True
		tmap[i][map_size - 1] = True

	for i in range(map_size - 2):
		for j in range(map_size - 2): 

			l = [tmap[i+1][j],tmap[i][j],tmap[i][j+1]] # generate walls randomly based on previous blocks + chance
			l = [0 for x in l if x]
			if len(l) <= 2 and random.random() > 0.7:
				tmap[i+1][j+1] = True

	for i in range(map_size - 4):
		for j in range(map_size - 4):
			if not tmap[i+2][j+2] and \ # removes some walls that create unreachable spaces
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

	visitable = set()
	nextposs = {(int(map_size / 2),int(map_size / 2))}

	while len(nextposs) > 0:
		currpos = next(iter(nextposs))
		nextposs.remove(currpos)

		possnext = [(currpos[0] + 1, currpos[1]), (currpos[0] - 1, currpos[1]), (currpos[0], currpos[1] + 1), (currpos[0], currpos[1] - 1)]
		for p in possnext:
			if not tmap[p[0]][p[1]] and p not in visitable and p not in nextposs:
				nextposs.add(p)

		visitable.add(currpos)

	maxdist = 0
	furthest = (map_size / 2,map_size / 2)
	for pos in visitable:
		if abs(pos[0] - map_size / 2) + abs(pos[1] - map_size / 2) > maxdist:
			maxdist = abs(pos[0] - map_size / 2) + abs(pos[1] - map_size / 2)
			furthest = pos

	exit = furthest # use pathfinding to get farthest reachable point for exit
	print(exit)

	tmap[int(map_size / 2)][int(map_size / 2)] = False # ensure spawn point is a space

map_init() # create map on startup

def dist(x1, y1, x2, y2):
	return math.sqrt((x2 - x1) * (x2 - x1) + (y2 - y1) * (y2 - y1)) # euclidean distance determination

class Monster: # Monster class

	def __init__(self, x_loc, y_loc): 

		self.x = x_loc # location initialization
		self.y = y_loc

		self.active = False # is tracking a sound?
		self.active_timer = 12 # stops tracking target 12 frames after hearing latest sound

		self.target_loc_x = 0 # target location of last heard sound origin
		self.target_loc_y = 0
		self.target_latest = 0 # time of latest sound heard

		self.path = [] # path to target of last heard sound origin

		self.eye_dir = 0 # eye direction of graphic

	def move_to_target(self): # follow path
		if len(self.path) > 0: # only if there is still a path to follow
			if self.path[0] == 0:
				self.x += 1
			elif self.path[0] == 1:
				self.y += 1
			elif self.path[0] == 2:
				self.x -= 1
			else:
				self.y -= 1

			del self.path[0]
		elif self.active_timer > 0: # move randomly quickly if end of path reached and player not found
			self.wander()
			self.active_timer -= 1
		else:
			self.active = False # end active phase if active timer reaches 0

	def wander(self): # move randomly
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

	def calc_path(self): # A-star algorithm for finding shortest path to last heard sound origin
		futures = {(self.x,self.y,dist(self.x, self.y, self.target_loc_x, self.target_loc_y)):[]} # potential paths
		visited = set() # visited paths

		while futures:
			min_key = list(futures.keys())[0] # min_key is 
			min_dist = list(futures.keys())[0][2] + len(futures[list(futures.keys())[0]])
			for t in futures:
				if min_dist > t[2] + len(futures[t]): # min_dist is smallest sum of distance from current monster location to last heard sound origin
					min_key = t
					min_dist = t[2] + len(futures[t])

			if min_key[0] == self.target_loc_x and min_key[1] == self.target_loc_y: # get highest priority path to continue
				return futures[min_key]

			curr_path = futures[min_key]
			currx = min_key[0]
			curry = min_key[1] # current location in path

			del futures[min_key] # take it off the dictionary
			visited.add((min_key[0], min_key[1])) # mark it as visited

			all_adj = {0:(currx + 1, curry), 1:(currx, curry + 1), 2:(currx - 1, curry), 3:(currx, curry - 1)} # all adjacent locations to current location in path
			poss_pos = {} # possible future positions
			for i in all_adj:
				if not tmap[all_adj[i][0]][all_adj[i][1]] and all_adj[i] not in visited:
					poss_pos[i] = all_adj[i]

			if not bool(poss_pos): # check if empty
				continue

			for poss in poss_pos: # add possible future positions to dictionary
				futures[(poss_pos[poss][0],poss_pos[poss][1],dist(poss_pos[poss][0],poss_pos[poss][1],self.target_loc_x,self.target_loc_y))] = curr_path + [poss]

		return [] # if no path found return empty list

	def trigger(self, target_x, target_y): # begin active phase if sound is heard
		self.target_loc_x = target_x
		self.target_loc_y = target_y
		self.active = True
		self.active_timer = 12

		self.path = self.calc_path()

	def randomize_eye(self): # move eye randomly
		self.eye_dir = random.randint(0,3)

	def tick(self, frame_counter): # frame based tick
		if frame_counter == 0 and not self.active:
			self.wander()
		elif frame_counter % 5 == 0 and self.active:
			self.move_to_target()

		if frame_counter % 30 == 0:
			self.randomize_eye()

class Main:

	def __init__(self):

		pyxel.init(144, 144, caption="Meut") # screen + title
		pyxel.load("my_resource.pyxres") # load pyxel assets

		self.screen = -1
		# -1 : company screen, 0 : home, 1 : game, 2: level, 3: end

		self.player_x = int(map_size / 2) # spawn in middle of map
		self.player_y = int(map_size / 2)

		self.monsters = [] # list of all monsters

		self.monster_spawn() # populate monster list

		self.quit = False 

		self.move = 0 # animating legs
		# 0 : left, 1 : right

		self.moving = False # animate legs if player moving

		self.frame = 0 # frame counter
		self.frame_diff = 0

		self.made_noise = False 
		self.noise_amt = 0
		self.ping_list = {} # dictionary of sounds made based on microphone input

		self.curr_dir = 0 # player model facing direction
		#0 : down, 1 : left, 2 : up, 3 : right

		self.audio_obj = pyaudio.PyAudio()
		self.audio_stream = self.audio_obj.open(format=pyaudio.paInt16,channels=1,rate=12000,input=True,frames_per_buffer=1024)

		self.audio_thread = Thread(target = self.listen) # start thread for microphone input
		self.audio_thread.start()

		self.monster_thread = Thread(target = self.run_monsters) # start another thread for monster manipulation
		self.monster_thread.start()

		pyxel.image(1).load(0, 0, "assets/hexadoon_logo.png") # load company logo

		pyxel.run(self.update, self.draw) # start pyxel engine

	def home_screen(self):
		pyxel.blt(38,40,0,0,80,64,32) # load title text

		pyxel.blt(36,100,0,0,112,80,16) # load start button

	def start(self): # check for start button click
		if pyxel.btnr(pyxel.MOUSE_LEFT_BUTTON) and (pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 13 or pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 6):
			playsound("assets/switch2.mp3")
			self.screen = 2
			pyxel.mouse(False)

	def company_card_screen(self): # company card screen display
		self.frame_diff += 1
		pyxel.cls(0)

		company_text = "Hexadoon Studios LLC"

		if self.frame_diff == 30:
			playsound("assets/switch1.mp3")

		if self.frame_diff == 90:
			playsound("assets/switch2.mp3")

		if self.frame_diff >= 30 and self.frame_diff <= 90:
			pyxel.image(1).copy(32,24,1,0,0,80,80)
			pyxel.text(32,120,company_text,7)

		if self.frame_diff >= 120:
			self.screen = 0
			playsound("assets/switch1.mp3")
			self.frame_diff = 0

	def lvl_screen(self): # show level screen
		self.frame_diff += 1
		pyxel.cls(0)

		global level
		lvl_text = "Level " + str(level)

		if self.frame_diff == 30:
			playsound("assets/switch1.mp3")

		if self.frame_diff == 90:
			playsound("assets/switch2.mp3")

		if self.frame_diff >= 30 and self.frame_diff <= 90:
			pyxel.text(40,64,lvl_text,7)

		if self.frame_diff >= 120:
			self.screen = 1
			self.frame_diff = 0

	def monster_spawn(self): # populate monster lists
		global tmap
		all_spawns = []
		for x in range(map_size - 2):
			for y in range(map_size - 2):
				all_spawns.append([x + 1, y + 1])

		poss_spawns = []
		for l in all_spawns:
			if not tmap[l[0]][l[1]]:
				poss_spawns.append(l)

		for i in range(50 * level):
			l = random.randint(0,len(poss_spawns) - 1)
			self.monsters.append(Monster(poss_spawns[l][0], poss_spawns[l][1]))
			del poss_spawns[l]

	def display_monsters(self): # display monsters on screen
		for m in self.monsters:
			xdiff = m.x - self.player_x
			ydiff = m.y - self.player_y
			if xdiff < 5 and ydiff < 5:
				if not m.active:
					pyxel.blt(64 + xdiff * 16, 64 + ydiff * 16,0,m.eye_dir * 16, 128, 16, 16)
				else:
					pyxel.blt(64 + xdiff * 16, 64 + ydiff * 16,0,m.eye_dir * 16, 144, 16, 16)

	def check_lose(self): # check if monster on player location
		for m in self.monsters:
			if m.x == self.player_x and m.y == self.player_y:
				return True

	def next_level(self): # increment level
		global level
		if self.player_x == exit[0] and self.player_y == exit[1]:
			level += 1
			self.screen = 2
			self.reset(2)

#	def animate_end(self):

	def run_monsters(self): # tick monsters within 30 cells of player
		for m in self.monsters:
			if m.x - self.player_x < 30 or m.y - self.player_y < 30 or m.active:
				m.tick(self.frame)

				for p in self.ping_list:
					ping_dist = dist(m.x, m.y, self.ping_list[p][1], self.ping_list[p][2])
					if ping_dist < (self.ping_list[p][0] / 3200) and m.target_latest < self.ping_list[p][3]:
						m.trigger(self.ping_list[p][1],self.ping_list[p][2])
						m.target_latest = self.ping_list[p][3]

	def listen(self): # listen for mic input above certain threshold
		while not self.quit:
			data = np.frombuffer(self.audio_stream.read(1024),dtype=np.int16)

			mx = max(data)
			if mx > 800 and self.screen == 1:
				self.made_noise = True
				self.noise_amt = mx

	def count_frame(self): # tick frame counter
		self.frame += 1
		self.frame %= 60

	def ping(self): # draw sound wave and insert mic input into sound wave list
		if self.made_noise:
			self.made_noise = False
			self.ping_list[self.noise_amt] = [0, self.player_x, self.player_y, time.time()]

		for x in self.ping_list:
			pyxel.circb(72 + 16 * (self.ping_list[x][1] - self.player_x), 72 + 16 * (self.ping_list[x][2] - self.player_y),self.ping_list[x][0]/200,13)
			self.ping_list[x][0] += 200
			
		for key in [key for key in self.ping_list if self.ping_list[key][0] > key]: del self.ping_list[key] 

	def move_btn(self): # move buttons W A S D
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

		if self.moving: # adaptive for button pressing and holding
			if self.curr_dir == 0 and not tmap[self.player_x][self.player_y + 1]:
				self.player_y += 1

			elif self.curr_dir == 1 and not tmap[self.player_x - 1][self.player_y]:
				self.player_x -= 1

			elif self.curr_dir == 2 and not tmap[self.player_x][self.player_y - 1]:
				self.player_y -= 1

			elif self.curr_dir == 3 and not tmap[self.player_x + 1][self.player_y]:
				self.player_x += 1

	def char_model(self): # display player model
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

	def display_map(self): # draw map
		global exit
		for x in range(9):
			i = x - 4
			for y in range(9):
				j = y - 4
				if self.player_x + i == exit[0] and self.player_y + j == exit[1]:
					pyxel.blt(x*16,y*16,0,32,64,16,16)
				elif self.player_x + i > map_size - 1 or self.player_x + i < 0 or \
				self.player_y + j > map_size - 1 or self.player_y + j < 0:
					pyxel.blt(x*16,y*16,0,16,64,16,16)
				elif tmap[self.player_x + i][self.player_y + j]:
					pyxel.blt(x*16,y*16,0,0,64,16,16)

	def isolate_view(self): # vignette game screen to isolate vision
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

	def reset(self, scrn_num = 0): # reset game on game over or switch screen
		self.screen = scrn_num;
		map_init()
		self.monsters = []
		self.ping_list = {}
		self.curr_dir = 0
		self.player_x = int(map_size / 2)
		self.player_y = int(map_size / 2)

	def update(self): # pyxel update method 
		if pyxel.btnp(pyxel.KEY_Q): # quit
			self.quit = True

			self.audio_thread.join()

			self.audio_stream.stop_stream()
			self.audio_stream.close()
			self.audio_obj.terminate()

			self.monster_thread.join()

			pyxel.quit()

		if self.check_lose():
			self.reset()

		if self.screen == 0: # allow click on main menu
			pyxel.mouse(True)
		elif self.screen == 1: # game screen
			self.move_btn()
			self.count_frame()
			self.run_monsters()
			self.next_level()

	def draw(self): # pyxel draw method
		pyxel.cls(0) # draw black background

		if self.screen == -1:
			self.company_card_screen()
		elif self.screen == 0:
			self.home_screen()
			self.start()
		elif self.screen == 2:
			self.lvl_screen()
		# elif self.screen == 3:
		# 	self.animate_end()
		else:
			self.display_map()
			self.char_model()
			self.display_monsters()
			self.ping()
			self.isolate_view()

Main()
