import pyxel
import pyaudio
import numpy as np
import random
from threading import Thread

class Main:

	def __init__(self):

		pyxel.init(144, 144, caption="Meut")
		pyxel.load("my_resource.pyxres")

		self.screen = 0
		# 0 : home, 1 : game

		self.tm = []

		self.player_x = 50
		self.player_y = 50

		self.map_init()

		self.move = 0
		# 0 : left, 1 : right

		self.moving = False

		self.made_noise = False
		self.noise_amt = 0
		self.ping_list = {}

		self.curr_dir = 0
		#0 : down, 1 : left, 2 : up, 3 : right

		self.audio_obj = pyaudio.PyAudio()
		self.audio_stream = self.audio_obj.open(format=pyaudio.paInt16,channels=1,rate=12000,input=True,frames_per_buffer=1024)

		self.audio_thread = Thread(target = self.listen)
		self.audio_thread.start()

		pyxel.run(self.update, self.draw)

	# def home_screen(self):
	# 	pyxel.blt(42,40,0,0,80,64,32)

	# 	pyxel.blt(42,100,0,0,112,64,16)

	# def start(self):
	# 	if pyxel.btn(pyxel.MOUSE_LEFT_BUTTON) and (pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 13 or pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 6):
	# 		self.screen = 1
	# 		pyxel.mouse(False)

	def map_init(self):
		self.tm = [[False for j in range(100)] for i in range(100)]

		for i in range(100):
			self.tm[0][i] = True
			self.tm[i][0] = True
			self.tm[99][i] = True
			self.tm[i][99] = True

		for i in range(98):
			for j in range(98):

				l = [self.tm[i+1][j],self.tm[i][j],self.tm[i][j+1]]
				l = [0 for x in l if x]
				if len(l) <= 1 and random.random() > 0.7:
					self.tm[i+1][j+1] = True

	def listen(self):
		while(True):
			data = np.frombuffer(self.audio_stream.read(1024),dtype=np.int16)

			mx = max(data)
			if mx > 800:
				self.made_noise = True
				self.noise_amt = mx

	def ping(self):
		if self.made_noise:
			self.made_noise = False
			self.ping_list[self.noise_amt] = 0

		for x in self.ping_list:
			pyxel.circb(72,72,self.ping_list[x]/300,13)
			self.ping_list[x] += 300
			
		for key in [key for key in self.ping_list if self.ping_list[key] > key]: del self.ping_list[key] 

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
			if self.curr_dir == 0 and not self.tm[self.player_x][self.player_y + 1]:
				self.player_y += 1

			elif self.curr_dir == 1 and not self.tm[self.player_x - 1][self.player_y]:
				self.player_x -= 1

			elif self.curr_dir == 2 and not self.tm[self.player_x][self.player_y - 1]:
				self.player_y -= 1

			elif self.curr_dir == 3 and not self.tm[self.player_x + 1][self.player_y]:
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
				elif self.tm[self.player_x + i][self.player_y + j]:
					pyxel.blt(x*16,y*16,0,0,64,16,16)

	def update(self):
		if pyxel.btnp(pyxel.KEY_Q):
			pyxel.quit()

		self.move_btn()

	def draw(self):
	    pyxel.cls(0)

	    self.display_map()
	    self.char_model()
	    self.ping()

Main()