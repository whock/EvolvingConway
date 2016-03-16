import pygame, sys

white = (255, 255, 255)
red = (255, 0, 0)

pygame.init()
pygame.display.set_caption('Keyboard Example')
size = [640, 480]
screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()

x = 100
y = 100

# using this to set the size of the rectange
# using this to also move the rectangle
step = 20

# by default the key repeat is disabled
# call set_repeat() to enable it
pygame.key.set_repeat(50, 50)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        # check if key is pressed
        # if you use event.key here it will give you error at runtime
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                x -= step
            if event.key == pygame.K_RIGHT:
                x += step
            if event.key == pygame.K_UP:
                y -= step
            if event.key == pygame.K_DOWN:
                y += step
            # checking if left modifier is pressed
            if pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                if event.key == pygame.K_LEFT:
                    x = 0
                if event.key == pygame.K_RIGHT:
                    x = 640 - step
                if event.key == pygame.K_UP:
                    y = 0
                if event.key == pygame.K_DOWN:
                    y = 480 - step

    # limit the rectangle from going out of the visible area
    if (x < 0): x = 0
    elif (x > (640-step)): x = 640-step
    if (y < 0): y = 0
    elif (y > (480-step)): y = 480-step

    screen.fill(white)

    # draw a rectangle
    pygame.draw.rect(screen, red, ((x, y), (step, step)), 0)

    pygame.display.update()
    clock.tick(20)
