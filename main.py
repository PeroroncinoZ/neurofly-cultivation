import pygame

from fly import Fly
from spiritual_fruit import SpiritualFruit


def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("NeuroFly: Cultivation")
    clock = pygame.time.Clock()
    fly = Fly(400, 300)
    fruit = SpiritualFruit(600, 200)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not running:
            break

        keys = pygame.key.get_pressed()
        fly.move(keys)

        # Clear the previous frame before drawing the fruit and fly again.
        screen.fill((30, 30, 30))
        fruit.draw(screen)
        fly.draw(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
