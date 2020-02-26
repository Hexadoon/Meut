import pyxel
import pyaudio
import numpy as np
from threading import Thread

class Main:

	def __init__(self):

		pyxel.init(160, 160, caption="Meut")
		pyxel.load("my_resource.pyxres")

		self.screen = 0
		# 0 : home, 1 : game

		self.move = 0
		# 0 : left, 1 : right

		self.moving = False

		self.curr_dir = 0
		#0 : down, 1 : left, 2 : up, 3 : right

		self.audio_obj = pyaudio.PyAudio()
		self.audio_stream = self.audio_obj.open(format=pyaudio.paInt16,channels=1,rate=3000,input=True,frames_per_buffer=1024)

		self.audio_thread = Thread(target = self.listen)
		self.audio_thread.start()

		pyxel.run(self.update, self.draw)

	def home_screen(self):
		pyxel.blt(42,40,0,0,80,72,32)

		pyxel.blt(42,100,0,0,112,72,16)

	def start(self):
		if pyxel.btn(pyxel.MOUSE_LEFT_BUTTON) and (pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 13 or pyxel.pget(pyxel.mouse_x, pyxel.mouse_y) == 6):
			self.screen = 1
			pyxel.mouse(False)

	def listen(self):
		while(True):
			data = np.frombuffer(self.audio_stream.read(1024),dtype=np.int16)

			mx = max(data)
			if mx > 500:
				print("trigger" + str(mx))

	def move_btn(self):
		if pyxel.btn(pyxel.KEY_W):
			self.curr_dir = 2
			self.moving = True
		elif pyxel.btn(pyxel.KEY_A):
			self.curr_dir = 1
			self.moving = True
		elif pyxel.btn(pyxel.KEY_S):
			self.curr_dir = 0
			self.moving = True
		elif pyxel.btn(pyxel.KEY_D):
			self.curr_dir = 3
			self.moving = True
		else:
			self.moving = False

	def char_model(self):
		if not self.moving:
			if self.curr_dir == 0:
				pyxel.blt(72,72,0,0,0,16,16)
				# DOWN

			elif self.curr_dir == 1:
				pyxel.blt(72,72,0,0,48,16,16)
				# LEFT

			elif self.curr_dir == 2:
				pyxel.blt(72,72,0,0,16,16,16)
				# UP

			else:
				pyxel.blt(72,72,0,0,32,16,16)
				# RIGHT
		else:
			# DOWN
			if self.curr_dir == 0:
				if self.move == 0:
					pyxel.blt(72,72,0,16,0,16,16)
				else:
					pyxel.blt(72,72,0,32,0,16,16)

			# LEFT
			elif self.curr_dir == 1:
				if self.move == 0:
					pyxel.blt(72,72,0,16,48,16,16)
				else:
					pyxel.blt(72,72,0,0,48,16,16)

			# UP
			elif self.curr_dir == 2:
				if self.move == 0:
					pyxel.blt(72,72,0,16,16,16,16)
				else:
					pyxel.blt(72,72,0,32,16,16,16)

			# RIGHT
			else:
				if self.move == 0:
					pyxel.blt(72,72,0,0,32,16,16)
				else:
					pyxel.blt(72,72,0,16,32,16,16)

			self.move = 0 if self.move == 1 else 1

	def update(self):
		if pyxel.btnp(pyxel.KEY_Q):
			pyxel.quit()

		self.move_btn()

	def draw(self):
	    pyxel.cls(0)

	    self.char_model()

Main()