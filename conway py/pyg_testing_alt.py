# -*- coding: utf-8 -*-
"""
Created on Thu Dec 10 23:31:24 2015

@author: Will
"""
import pygame,random, numpy as np
from sys import argv
import sys

script,h,w,dt = argv


class eca_viewer():
    '''Class using pygame to view and interact with conway GoL patterns
    '''
    def __init__(self,h,w,dt):
        self.h = h # height of environment in pixels
        self.w = w # width of environment in pixels
        self.dt = dt # number of timesteps to simulate
        self.ch = 2 # cell height
        self.cw = 2 # cell width
        self.t = 0
        self.gen = 0
        
        
    def pyg_init(self):
        '''Initialize pygame and GUI structure
        '''
        pygame.init()
        self.screen = pygame.display.set_mode([self.h*self.ch,self.w*self.cw])
        pygame.display.set_caption("Conway Game of Life Simulator")
        clock = pygame.time.Clock()
        clock.tick(10) # FPS
        self.running = True # is sim paused or playing?
        self.done = False # are we totally done with sim?
        
        
    def get_pattern(self):
        '''Get the cGoL pattern
        '''
        return np.asarray([[random.randrange(0,2) for i in range(self.h)] for j in range(self.w)]).T

 
    def paused(self):
        '''pause program, unpause on keypress = r'''
        while self.running == False:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.K_r:
                    self.running = True
            pygame.display.update()
 
    def mainloop(self):
        '''Main simulation loop and event detection function
        CLI functionality - 
        r - run
        p - pause
        '''
        self.t = 0
        while not self.done:
            while self.running:
                if pygame.key.get_pressed()[pygame.K_a] != 0:
                    print('test')
                for event in pygame.event.get():  
                    if event.type == pygame.QUIT:  
                       pygame.quit()
                       sys.exit()
                    elif event.type == pygame.K_SPACE:
                        self.running = False
                        while self.running == False:
                             for event in pygame.event.get():  
                                if event.type == pygame.QUIT:  
                                   pygame.quit()
                                   sys.exit()
                                elif event.type == pygame.K_SPACE:
                                    print('pressed space')
                                    self.running = True
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        print('Timestep: ',self.t)
                    elif event.type == pygame.K_LEFT:
                        print('Timestep: ',self.t)

                conpatt = self.get_pattern()
                for row in range(self.h):
                    for column in range(self.w):
                        if conpatt[row][column] == 1:
                            color = (255,255,255)
                        if conpatt[row][column] == 0:
                            color = (0,0,0)
                        pygame.draw.rect(self.screen,
                                         color,
                                         [(0 + self.cw) * column + 0,
                                          (0 + self.ch) * row + 0,
                                          self.cw,
                                          self.ch])
             
                self.t += 1
                pygame.display.update()

eca = eca_viewer(int(h),int(w),int(dt))
eca.pyg_init()
eca.mainloop()