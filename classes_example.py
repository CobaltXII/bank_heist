class Bullet:
	def __init__(self, x, y, vx, vy, sender, color):
		self.pos = (x, y)
		self.vel = (vx, vy)
		self.sender = sender
		self.color = color

bullets = []
bullets.append(Bullet(0, 1, 2, 3, 'mr. r', (13, 14, 15)))
print(bullets[0].sender)