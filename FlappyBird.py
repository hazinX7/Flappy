import pygame
from pygame.locals import *
import sys
import random

class FlappyBird:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((400, 708))
        self.bird = pygame.Rect(65, 50, 50, 50)
        
        self.background = pygame.image.load("./assets/background.png").convert()
        self.birdSprites = [
            pygame.image.load("./assets/1.png").convert_alpha(),
            pygame.image.load("./assets/2.png").convert_alpha(),
            pygame.image.load("./assets/dead.png")
        ]
        self.wallUp = pygame.image.load("./assets/bottom.png").convert_alpha()
        self.wallDown = pygame.image.load("./assets/top.png").convert_alpha()
        
        self.medals = [
            pygame.image.load("./assets/first.png").convert_alpha(),
            pygame.image.load("./assets/second.png").convert_alpha(),
            pygame.image.load("./assets/3rd.png").convert_alpha()
        ]
        self.medals = [pygame.transform.scale(medal, (30, 30)) for medal in self.medals]
        
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
        self.leaderboard_data = []

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
        
        upRect = pygame.Rect(
            self.wallx,
            360 + self.gapx - self.offset + 10,
            self.wallUp.get_width() - 10,
            self.wallUp.get_height()
        )
        downRect = pygame.Rect(
            self.wallx,
            0 - self.gapx - self.offset - 10,
            self.wallDown.get_width() - 10,
            self.wallDown.get_height()
        )
        if upRect.colliderect(self.bird):
            self.dead = True
        if downRect.colliderect(self.bird):
            self.dead = True
        if not 0 < self.bird[1] < 720:
            self.dead = True

    def show_menu(self):
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 30)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))

            text = font.render("ENTER - НОВАЯ ИГРА", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(text, text_rect)

            pygame.display.update()
            clock.tick(60)

    def game_loop(self):
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 30)
        countdown_font = pygame.font.SysFont("Arial", 80)
        
        # Отсчет перед началом игры
        for i in range(3, 0, -1):
            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))
            
            # Отрисовка птицы в начальной позиции
            self.screen.blit(self.birdSprites[0], (70, self.birdY))
            
            # Отрисовка стен
            self.screen.blit(self.wallUp, (self.wallx, 360 + self.gapx - self.offset))
            self.screen.blit(self.wallDown, (self.wallx, 0 - self.gapx - self.offset))
            
            # Отрисовка счетчика
            countdown_text = countdown_font.render(str(i), True, (255, 255, 255))
            countdown_rect = countdown_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(countdown_text, countdown_rect)
            
            pygame.display.update()
            pygame.time.wait(1000)
        
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
                self.gapx = 190
            elif self.counter == 3 or self.counter > 3 and self.counter < 6:
                self.gapx = 165
            else:
                self.gapx = 140

            self.screen.blit(self.wallUp, (self.wallx, 360 + self.gapx - self.offset))
            self.screen.blit(self.wallDown, (self.wallx, 0 - self.gapx - self.offset))
            self.screen.blit(font.render(str(self.counter), -1, (255, 255, 255)), (200, 50))

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

    def update_leaderboard(self):
        pass

    def game_over_screen(self):
        clock = pygame.time.Clock()
        self.update_leaderboard()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return "restart"
                    elif event.key == pygame.K_ESCAPE:
                        return "quit"
                    elif event.key == pygame.K_TAB:
                        return "profile"

            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))

            title_font = pygame.font.SysFont("Arial", 40)
            font = pygame.font.SysFont("Arial", 30)

            game_over = title_font.render("ИГРА ОКОНЧЕНА!", True, (255, 255, 255))
            score = font.render(f"ВАШ СЧЁТ: {self.counter}", True, (255, 255, 255))
            enter_text = font.render("ENTER - НОВАЯ ИГРА", True, (255, 255, 255))
            exit_text = font.render("ESC - ВЫХОД", True, (255, 255, 255))

            game_over_rect = game_over.get_rect(centerx=self.screen.get_width() // 2, y=50)
            score_rect = score.get_rect(centerx=self.screen.get_width() // 2, y=150)
            enter_rect = enter_text.get_rect(centerx=self.screen.get_width() // 2, y=500)
            exit_rect = exit_text.get_rect(centerx=self.screen.get_width() // 2, y=550)

            self.screen.blit(game_over, game_over_rect)
            self.screen.blit(score, score_rect)
            self.screen.blit(enter_text, enter_rect)
            self.screen.blit(exit_text, exit_rect)

            pygame.display.update()
            clock.tick(60)

    def reset_game(self):
        self.bird.y = 50
        self.birdY = 50
        self.dead = False
        self.counter = 0
        self.wallx = 400
        self.offset = random.randint(-110, 110)
        self.gravity = 5

    def run(self):
        clock = pygame.time.Clock()
        self.show_menu()
        
        while True:
            while not self.dead:
                self.game_loop()
                clock.tick(60)
            
            self.sprite = 2
            self.screen.blit(self.birdSprites[self.sprite], (70, self.birdY))
            pygame.display.update()
            
            self.save_score()
            
            result = self.game_over_screen()
            if result == "restart":
                self.reset_game()
                continue
            elif result == "profile":
                pygame.quit()
                return "profile"
            else:
                pygame.quit()
                return "quit"

if __name__ == "__main__":
    FlappyBird().run()
