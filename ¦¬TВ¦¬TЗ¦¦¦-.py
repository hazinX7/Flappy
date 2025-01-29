import pygame
from pygame.locals import *  # noqa
import sys
import random

class FlappyBird:
    def __init__(self):
        self.screen = pygame.display.set_mode((400, 708))
        self.bird = pygame.Rect(65, 50, 50, 50)
        self.background = pygame.image.load("PycharmProjects/¦ЪTГTАTБ¦-¦-¦-TП/.venv/assets/background.png").convert()
        self.birdSprites = [pygame.image.load("PycharmProjects/¦ЪTГTАTБ¦-¦-¦-TП/.venv/assets/1.png").convert_alpha(),
                            pygame.image.load("PycharmProjects/¦ЪTГTАTБ¦-¦-¦-TП/.venv/assets/2.png").convert_alpha(),
                            pygame.image.load("PycharmProjects/¦ЪTГTАTБ¦-¦-¦-TП/.venv/assets/dead.png")]
        self.wallUp = pygame.image.load("PycharmProjects/¦ЪTГTАTБ¦-¦-¦-TП/.venv/assets/bottom.png").convert_alpha()
        self.wallDown = pygame.image.load("PycharmProjects/¦ЪTГTАTБ¦-¦-¦-TП/.venv/assets/top.png").convert_alpha()

        self.gap = 130
        self.gapx = 50
        self.wallx = 400
        self.birdY = 350
        self.jump = 0
        self.jumpSpeed = 10
        self.gravity = 5
        self.dead = False
        self.sprite = 0
        self.counter = 0
        self.offset = random.randint(-110, 110)
        self.menu_counter = 0
        self.game_over_time = 0

    def updateWalls(self):
        self.wallx -= 2
        if self.wallx < -80:
            self.wallx = 400
            self.counter += 1
            self.offset = random.randint(-110, 110)

    def birdUpdate(self):
        if self.jump:
            self.jumpSpeed -= 1
            self.birdY -= self.jumpSpeed
            self.jump -= 1
        else:
            self.birdY += self.gravity
            self.gravity += 0.2
        self.bird[1] = self.birdY
        upRect = pygame.Rect(self.wallx,
                             360 + self.gapx - self.offset + 10,
                             self.wallUp.get_width() - 10,
                             self.wallUp.get_height())
        downRect = pygame.Rect(self.wallx,
                               0 - self.gapx - self.offset - 10,
                               self.wallDown.get_width() - 10,
                               self.wallDown.get_height())
        if upRect.colliderect(self.bird):
            self.dead = True
        if downRect.colliderect(self.bird):
            self.dead = True
        if not 0 < self.bird[1] < 720:
            self.dead = True

    def show_menu(self):
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 20)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.menu_counter += 1
                        return

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))

            text = font.render("Чтобы начать играть, нажмите (ENTER)", True, (255, 255, 255))
            text_rect = text.get_rect(center=(200, 350))
            self.screen.blit(text, text_rect)

            menu_count_text = font.render(f"Предыдущий счет: {self.menu_counter}", True, (255, 255, 255))
            menu_count_rect = menu_count_text.get_rect(center=(200, 400))
            self.screen.blit(menu_count_text, menu_count_rect)

            pygame.display.update()
            clock.tick(60)

    def game_over_screen(self):
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 20)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))

            text = font.render("Нажмите ENTER для продолжения.", True, (255, 255, 255))
            text_rect = text.get_rect(center=(200, 400))
            self.screen.blit(text, text_rect)

            score_text = font.render(f"Ваш счет: {self.counter}", True, (255, 255, 255))
            score_rect = score_text.get_rect(center=(200, 350))
            self.screen.blit(score_text, score_rect)

            pygame.display.update()
            clock.tick(60)

    def run(self):
        pygame.font.init()
        font = pygame.font.SysFont("Arial", 50)

        self.show_menu()

        while True:
            self.game_loop()
            self.game_over_screen()
            self.reset_game()

    def game_loop(self):
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 30)
        while not self.dead:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if (event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN) and not self.dead:
                    self.jump = 17
                    self.gravity = 5
                    self.jumpSpeed = 10

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))

            if self.counter < 3:
                self.gapx = 190  # Увеличиваем gap между колоннами

            elif self.counter == 3 or self.counter > 3 and self.counter < 6:
                self.gapx = 165
            else:
                self.gapx = 140

            self.screen.blit(self.wallUp,
                             (self.wallx, 360 + self.gapx - self.offset))
            self.screen.blit(self.wallDown,
                             (self.wallx, 0 - self.gapx - self.offset))
            self.screen.blit(font.render(str(self.counter),
                                         -1,
                                         (255, 255, 255)),
                             (200, 50))

            if self.dead:
                self.sprite = 2
            elif self.jump:
                self.sprite = 1
            self.screen.blit(self.birdSprites[self.sprite], (70, self.birdY))
            if not self.dead:
                self.sprite = 0
            self.updateWalls()
            self.birdUpdate()
            pygame.display.update()

        # Добавляем задержку перед отображением экрана окончания игры
        self.game_over_time = pygame.time.get_ticks() + 1500  # 1000 миллисекунд = 1 секунда
        while pygame.time.get_ticks() < self.game_over_time:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))
            font = pygame.font.SysFont("Arial", 30)
            text = font.render("Игра окончена!", True, (255, 255, 255))
            text_rect = text.get_rect(center=(200, 350))
            self.screen.blit(text, text_rect)
            pygame.display.update()

    def reset_game(self):
        self.bird.y = 50
        self.birdY = 50
        self.dead = False
        self.counter = 0
        self.wallx = 400
        self.offset = random.randint(-110, 110)
        self.gravity = 5

if __name__ == "__main__":
    FlappyBird().run()
