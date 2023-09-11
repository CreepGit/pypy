import pygame

GRID_WIDTH = 640
GRID_HEIGHT = 480

BLACK = (30, 30, 30)
WHITE = (160, 120, 110)

GRID_LINE_WIDTH = 1

def draw(screen):
    # Draw the grid lines
    for x in range(0, GRID_WIDTH, 20):
        pygame.draw.line(screen, WHITE, (x, 0), (x, GRID_HEIGHT), GRID_LINE_WIDTH)
    for y in range(0, GRID_HEIGHT, 20):
        pygame.draw.line(screen, WHITE, (0, y), (GRID_WIDTH, y), GRID_LINE_WIDTH)

def click_grid(x,y):
    print(x,y)

def main():
    pygame.init()
    screen = pygame.display.set_mode((GRID_WIDTH, GRID_HEIGHT))
    pygame.display.set_caption('Grid')
    clock = pygame.time.Clock()
    done = False
    while not done:
        # Process events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                grid_x = pos[0] // 20
                grid_y = pos[1] // 20
                click_grid(grid_x, grid_y)
        screen.fill(BLACK)
        draw(screen)
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()

main()
