import tkinter as tk
from tkinter import messagebox
import threading
import requests
import random
import pygame
import sys

class FlappyBird:
    def __init__(self, token):
        pygame.init()
        self.screen = pygame.display.set_mode((400, 708))
        self.token = token
        self.bird = pygame.Rect(65, 50, 50, 50)
        
        # Загрузка изображений
        try:
            self.background = pygame.image.load("./assets/background.png").convert()
            self.birdSprites = [
                pygame.image.load("./assets/1.png").convert_alpha(),  # Птица летит вниз
                pygame.image.load("./assets/2.png").convert_alpha(),  # Птица летит вверх
                pygame.image.load("./assets/dead.png").convert_alpha()  # Мёртвая птица
            ]
            self.wallUp = pygame.image.load("./assets/bottom.png").convert_alpha()
            self.wallDown = pygame.image.load("./assets/top.png").convert_alpha()
        except pygame.error as e:
            print(f"Ошибка загрузки изображений: {e}")
            print("Убедитесь, что все файлы находятся в папке assets:")
            print("- background.png (задний фон)")
            print("- 1.png (птица летит вниз)")
            print("- 2.png (птица летит вверх)")
            print("- dead.png (мёртвая птица)")
            print("- bottom.png (нижняя труба)")
            print("- top.png (верхняя труба)")
            sys.exit(1)

        self.gap = 130
        self.wallx = 400
        self.birdY = 350
        self.jump = 0
        self.jumpSpeed = 10
        self.gravity = 5
        self.dead = False
        self.sprite = 0  # Индекс текущего спрайта
        self.counter = 0
        self.offset = random.randint(-110, 110)
        self.show_leaderboard = False
        self.leaderboard_data = []
        self.update_leaderboard()
        self.reset_game()  # Вызываем reset_game при инициализации

    def update_leaderboard(self):
        try:
            response = requests.get("http://127.0.0.1:8001/leaderboard")
            self.leaderboard_data = response.json()
        except requests.RequestException:
            self.leaderboard_data = []

    def save_score(self):
        try:
            # Проверяем наличие токена
            if not self.token:
                print("Error: No authentication token")
                return

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            # Отправляем счет как JSON
            data = {"score": self.counter}
            response = requests.post(
                "http://127.0.0.1:8001/scores",
                json=data,  # Изменяем params на json
                headers=headers
            )
            
            print(f"Score saved response: {response.status_code}, {response.text}")
            if response.status_code != 200:
                print(f"Error saving score: {response.json()}")
        except requests.RequestException as e:
            print(f"Error saving score: {e}")

    def draw_leaderboard(self):
        font = pygame.font.SysFont("Arial", 25)
        y = 50
        
        # Заголовок таблицы
        title = font.render("ТАБЛИЦА ЛИДЕРОВ", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.screen.get_width() // 2, y=y)
        self.screen.blit(title, title_rect)
        y += 50
        
        # Если данных нет
        if not self.leaderboard_data:
            text = font.render("Нет рекордов", True, (255, 255, 255))
            text_rect = text.get_rect(centerx=self.screen.get_width() // 2, y=y)
            self.screen.blit(text, text_rect)
            return
        
        # Отображение результатов
        medals = ["🥇", "🥈", "🥉"]
        for item in self.leaderboard_data:
            position = item["position"]
            if position <= 3:
                medal = medals[position - 1]
                text = f"{medal} {item['username']}"
                score = f"{item['score']}"
                
                # Отрисовка имени игрока
                name_text = font.render(text, True, (255, 255, 255))
                name_rect = name_text.get_rect(centerx=self.screen.get_width() // 2 - 50, y=y)
                self.screen.blit(name_text, name_rect)
                
                # Отрисовка счета
                score_text = font.render(score, True, (255, 255, 255))
                score_rect = score_text.get_rect(left=name_rect.right + 20, centery=name_rect.centery)
                self.screen.blit(score_text, score_rect)
                
                y += 40

    def reset_game(self):
        # Сбрасываем все параметры игры
        self.birdY = 350
        self.wallx = 400
        self.jump = 0
        self.jumpSpeed = 10
        self.gravity = 5
        self.dead = False
        self.sprite = 0
        self.counter = 0
        self.offset = random.randint(-110, 110)
        self.show_leaderboard = False

    def run(self):
        pygame.init()
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Игровой цикл
            while not self.dead:
                self.game_loop()
                clock.tick(60)
            
            # После смерти
            self.sprite = 2  # Показываем спрайт мёртвой птицы
            self.screen.blit(self.birdSprites[self.sprite], (70, self.birdY))
            pygame.display.update()
            
            # Небольшая задержка перед показом экрана окончания игры
            pygame.time.wait(500)
            
            # Сохраняем результат
            self.save_score()
            self.update_leaderboard()
            
            # Показываем экран окончания игры
            if self.show_game_over():  # Если игрок нажал Enter
                self.reset_game()  # Сбрасываем игру
            else:  # Если игрок нажал ESC или закрыл окно
                running = False
                pygame.quit()

    def game_loop(self):
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or event.type == pygame.MOUSEBUTTONDOWN:
                    self.jump = 17
                    self.gravity = 5
                    self.jumpSpeed = 10
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    self.show_leaderboard = not self.show_leaderboard
                    if self.show_leaderboard:
                        self.update_leaderboard()

        # Обновление позиции птицы
        if self.jump:
            self.jumpSpeed -= 1
            self.birdY -= self.jumpSpeed
            self.jump -= 1
            self.sprite = 1  # Птица летит вверх
        else:
            self.birdY += self.gravity
            self.gravity += 0.2
            self.sprite = 0  # Птица летит вниз

        # Проверка столкновений
        self.bird[1] = self.birdY
        upRect = pygame.Rect(self.wallx, 360 + self.gap - self.offset + 10,
                           self.wallUp.get_width() - 10, self.wallUp.get_height())
        downRect = pygame.Rect(self.wallx, 0 - self.gap - self.offset - 10,
                             self.wallDown.get_width() - 10, self.wallDown.get_height())

        if upRect.colliderect(self.bird) or downRect.colliderect(self.bird):
            self.dead = True
        if not 0 < self.bird[1] < 720:
            self.dead = True

        # Отрисовка
        self.screen.fill((255, 255, 255))
        self.screen.blit(self.background, (0, 0))

        if self.show_leaderboard:
            self.draw_leaderboard()
        else:
            # Обновление позиции труб
            self.wallx -= 2
            if self.wallx < -80:
                self.wallx = 400
                self.counter += 1
                self.offset = random.randint(-110, 110)

            self.screen.blit(self.wallUp, (self.wallx, 360 + self.gap - self.offset))
            self.screen.blit(self.wallDown, (self.wallx, 0 - self.gap - self.offset))
            self.screen.blit(self.birdSprites[self.sprite], (70, self.birdY))

            font = pygame.font.SysFont("Arial", 50)
            score_text = font.render(str(self.counter), True, (255, 255, 255))
            self.screen.blit(score_text, (200, 50))

        pygame.display.update()

    def show_game_over(self):
        clock = pygame.time.Clock()
        self.update_leaderboard()  # Обновляем таблицу лидеров сразу
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        return True
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return False
            
            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))
            
            # Шрифты
            title_font = pygame.font.SysFont("Arial", 50)
            font = pygame.font.SysFont("Arial", 30)
            
            # Тексты
            game_over = title_font.render("ИГРА ОКОНЧЕНА!", True, (255, 255, 255))
            score = font.render(f"ВАШ СЧЁТ: {self.counter}", True, (255, 255, 255))
            continue_text = font.render("ENTER - НОВАЯ ИГРА", True, (255, 255, 255))
            exit_text = font.render("ESC - ВЫХОД", True, (255, 255, 255))
            
            # Позиционирование (изменяем координаты y)
            game_over_rect = game_over.get_rect(centerx=self.screen.get_width() // 2, y=50)
            score_rect = score.get_rect(centerx=self.screen.get_width() // 2, y=120)
            
            # Отрисовка заголовка и счета
            self.screen.blit(game_over, game_over_rect)
            self.screen.blit(score, score_rect)
            
            # Отрисовка таблицы лидеров со смещенной позицией y
            font = pygame.font.SysFont("Arial", 25)
            leaderboard_title = font.render("ТАБЛИЦА ЛИДЕРОВ", True, (255, 255, 255))
            leaderboard_rect = leaderboard_title.get_rect(centerx=self.screen.get_width() // 2, y=200)
            self.screen.blit(leaderboard_title, leaderboard_rect)
            
            # Отображение результатов таблицы лидеров
            y = 250  # Начальная позиция для записей таблицы лидеров
            if not self.leaderboard_data:
                text = font.render("Нет рекордов", True, (255, 255, 255))
                text_rect = text.get_rect(centerx=self.screen.get_width() // 2, y=y)
                self.screen.blit(text, text_rect)
            else:
                medals = ["🥇", "🥈", "🥉"]
                for item in self.leaderboard_data:
                    position = item["position"]
                    if position <= 3:
                        medal = medals[position - 1]
                        text = f"{medal} {item['username']}"
                        score = f"{item['score']}"
                        
                        name_text = font.render(text, True, (255, 255, 255))
                        name_rect = name_text.get_rect(centerx=self.screen.get_width() // 2 - 50, y=y)
                        self.screen.blit(name_text, name_rect)
                        
                        score_text = font.render(score, True, (255, 255, 255))
                        score_rect = score_text.get_rect(left=name_rect.right + 20, centery=name_rect.centery)
                        self.screen.blit(score_text, score_rect)
                        
                        y += 40
            
            # Отрисовка кнопок внизу
            continue_rect = continue_text.get_rect(centerx=self.screen.get_width() // 2, y=550)
            exit_rect = exit_text.get_rect(centerx=self.screen.get_width() // 2, y=600)
            
            self.screen.blit(continue_text, continue_rect)
            self.screen.blit(exit_text, exit_rect)
            
            pygame.display.update()
            clock.tick(60)

class AuthApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Авторизация")
        self.token = None

        tk.Label(self.root, text="Логин").pack(pady=5)
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack(pady=5)

        tk.Label(self.root, text="Пароль").pack(pady=5)
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack(pady=5)

        tk.Button(self.root, text="Войти", command=self.login).pack(pady=5)
        tk.Button(self.root, text="Регистрация", command=self.open_registration).pack(pady=5)
        tk.Button(self.root, text="Закрыть", command=self.root.quit).pack(pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        try:
            response = requests.post("http://127.0.0.1:8001/login", 
                json={"username": username, "password": password})
            response.raise_for_status()
            self.token = response.json().get("token")
            print(f"Received token: {self.token}")  # Для отладки
            messagebox.showinfo("Успех", "Вы вошли в систему!")
            self.root.destroy()
            self.start_game()
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка входа: {e}")

    def open_registration(self):
        reg_window = tk.Toplevel(self.root)
        reg_window.title("Регистрация")

        tk.Label(reg_window, text="Логин").pack(pady=5)
        username_entry = tk.Entry(reg_window)
        username_entry.pack(pady=5)

        tk.Label(reg_window, text="Пароль").pack(pady=5)
        password_entry = tk.Entry(reg_window, show="*")
        password_entry.pack(pady=5)

        tk.Label(reg_window, text="Подтверждение пароля").pack(pady=5)
        confirm_password_entry = tk.Entry(reg_window, show="*")
        confirm_password_entry.pack(pady=5)

        def register():
            username = username_entry.get()
            password = password_entry.get()
            confirm_password = confirm_password_entry.get()

            if password != confirm_password:
                messagebox.showerror("Ошибка", "Пароли не совпадают!")
                return

            try:
                # Создаем правильную структуру данных для запроса
                data = {
                    "username": username,
                    "password": password
                }
                response = requests.post(
                    "http://127.0.0.1:8001/register", 
                    json=data,  # Используем json вместо params
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Регистрация успешна! Теперь вы можете войти.")
                    reg_window.destroy()
                else:
                    error_message = response.json().get("detail", "Неизвестная ошибка")
                    messagebox.showerror("Ошибка", f"Ошибка регистрации: {error_message}")
                    
            except requests.RequestException as e:
                messagebox.showerror("Ошибка", f"Ошибка регистрации: {str(e)}")

        tk.Button(reg_window, text="Зарегистрироваться", command=register).pack(pady=5)

    def start_game(self):
        if not self.token:
            messagebox.showerror("Ошибка", "Не удалось получить токен авторизации")
            return
        
        try:
            # Проверяем валидность токена
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get("http://127.0.0.1:8001/me", headers=headers)
            
            if response.status_code == 200:
                game = FlappyBird(self.token)
                game.run()
            else:
                error_message = response.json().get("detail", "Неизвестная ошибка")
                messagebox.showerror("Ошибка", f"Ошибка авторизации: {error_message}")
                # Можно добавить перенаправление на окно входа
                self.__init__()
                self.run()
                
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка проверки токена: {str(e)}")
            return

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AuthApp()
    app.run()
