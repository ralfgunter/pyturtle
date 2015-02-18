import pygame
from math import radians, sin, cos

class TurtleState(object):
    screen = pygame.display.set_mode((800,600))

    def __init__(self):
        self.x = 400
        self.y = 300
        self.theta = 270
        self.pen = 'down'

    def __repr__(self):
        return str((self.x, self.y, self.theta, self.pen))

    def rotate(self, angle):
        self.theta = (self.theta + angle) % 360

    def forward(self, distance):
        nx = self.x + distance * cos(radians(self.theta))
        ny = self.y + distance * sin(radians(self.theta))

        if self.pen == 'down':
            pygame.draw.lines(TurtleState.screen, 0xffffffff, False, [(self.x, self.y), (nx, ny)], 1)
            pygame.display.flip()

        self.x = nx
        self.y = ny

    def pen(self, st):
        self.pen = st

    def clearscreen(self):
        TurtleState.screen.fill((0,0,0))
        pygame.display.flip()
