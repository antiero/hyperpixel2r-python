#!/usr/bin/env python3
import os
import sys
import signal
import pygame
import math
from colorsys import hsv_to_rgb
from hyperpixel2r import Touch

"""
HyperPixel 2 Base Screen Object

Run with: sudo python3 hue.py
"""


class Hyperpixel2r:
    screen = None

    def __init__(self):
        self._init_display()

        self.screen.fill((0, 0, 0))

        if self._rawfb:
            self._updatefb()
        else:
            pygame.display.update()

        self.center = (240, 240)
        self.radius = 240
        self.inner_radius = 150

        self._running = False
        self._origin = pygame.math.Vector2(*self.center)
        self._clock = pygame.time.Clock()

        # Draw a White Circle to indicate the edge of the display
        # we overdraw 3x as many lines to get a nice solid fill... horribly inefficient but it works
        pygame.draw.circle(self.screen, (0, 0, 0), self.center, self.radius)

    def _exit(self, sig, frame):
        self._running = False
        print("\nExiting!...\n")

    def _init_display(self):
        self._rawfb = False
        # Based on "Python GUI in Linux frame buffer"
        # http://www.karoltomala.com/blog/?p=679
        DISPLAY = os.getenv("DISPLAY")
        if DISPLAY:
            print("Display: {0}".format(DISPLAY))

        if os.getenv('SDL_VIDEODRIVER'):
            print("Using driver specified by SDL_VIDEODRIVER: {}".format(os.getenv('SDL_VIDEODRIVER')))
            pygame.display.init()
            size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
            self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.NOFRAME | pygame.HWSURFACE)
            return
        else:
            # Iterate through drivers and attempt to init/set_mode
            for driver in ['rpi', 'kmsdrm', 'fbcon', 'directfb', 'svgalib']:
                os.putenv('SDL_VIDEODRIVER', driver)
                try:
                    pygame.display.init()
                    size = (pygame.display.Info().current_w, pygame.display.Info().current_h)
                    self.screen = pygame.display.set_mode(size, pygame.FULLSCREEN | pygame.DOUBLEBUF | pygame.NOFRAME | pygame.HWSURFACE)
                    print("Using driver: {0}, Framebuffer size: {1:d} x {2:d}".format(driver, *size))
                    return
                except pygame.error as e:
                    print('Driver "{0}" failed: {1}'.format(driver, e))
                    continue
                break

        print("All SDL drivers failed, falling back to raw framebuffer access.")
        self._rawfb = True
        os.putenv('SDL_VIDEODRIVER', 'dummy')
        pygame.display.init()  # Need to init for .convert() to work
        self.screen = pygame.Surface((480, 480))

    def __del__(self):
        "Destructor to make sure pygame shuts down, etc."

    def _updatefb(self):
        fbdev = os.getenv('SDL_FBDEV', '/dev/fb0')
        with open(fbdev, 'wb') as fb:
            fb.write(self.screen.convert(16, 0).get_buffer())

    def touch(self, x, y, state):
        target = pygame.math.Vector2(x, y)
        distance = self._origin.distance_to(target)
        angle = pygame.Vector2().angle_to(self._origin - target)

        if distance < self.inner_radius and distance > self.inner_radius - 40:
            return

        angle %= 360
        angle /= 360.0

        if distance < self.inner_radius:
            self._val = angle
        else:
            self._hue = angle

    # OVERRIDE THIS CLASS FOR THE MAIN RUN LOOP
    def run(self):
        self._running = True
        signal.signal(signal.SIGINT, self._exit)
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self._running = False
                        break

            # DRAW CODE GOES HERE

            if self._rawfb:
                self._updatefb()
            else:
                pygame.display.flip()
            self._clock.tick(30)

        pygame.quit()
        sys.exit(0)


@touch.on_touch
def handle_touch(touch_id, x, y, state):
    display.touch(x, y, state)
    # uncomment to set colour on rgbmatrix,
    # or try it with Mote USB or something!
    # rgbmatrix.set_all(*display.get_colour())
    # rgbmatrix.show()

# USAGE:
display = Hyperpixel2r()
touch = Touch()
display.run()
