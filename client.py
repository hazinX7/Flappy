import tkinter as tk
from tkinter import messagebox
import threading
import requests
import random
import pygame
import sys
import time

class FlappyBird:
    def __init__(self, token):
        pygame.init()
        self.screen = pygame.display.set_mode((400, 708))
        self.token = token
        self.bird = pygame.Rect(65, 50, 50, 50)
        
        try:
            self.background = pygame.image.load("./assets/background.png").convert()
            self.birdSprites = [
                pygame.image.load("./assets/1.png").convert_alpha(),
                pygame.image.load("./assets/2.png").convert_alpha(),
                pygame.image.load("./assets/dead.png").convert_alpha()
            ]
            self.wallUp = pygame.image.load("./assets/bottom.png").convert_alpha()
            self.wallDown = pygame.image.load("./assets/top.png").convert_alpha()
            
            self.medals = [
                pygame.image.load("./assets/first.png").convert_alpha(),
                pygame.image.load("./assets/second.png").convert_alpha(),
                pygame.image.load("./assets/3rd.png").convert_alpha()
            ]
            self.medals = [pygame.transform.scale(medal, (30, 30)) for medal in self.medals]
            
        except pygame.error as e:
            print(f"Ошибка загрузки изображений: {e}")
            sys.exit(1)

        self.gap = 130
        self.wallx = 400
        self.birdY = 350
        self.jump = 0
        self.jumpSpeed = 10
        self.gravity = 5
        self.dead = False
        self.sprite = 0
        self.counter = 0
        self.offset = random.randint(-110, 110)
        self.show_leaderboard = False
        self.leaderboard_data = []
        self.update_leaderboard()
        self.reset_game()

    def update_leaderboard(self):
        try:
            response = requests.get("http://127.0.0.1:8001/leaderboard")
            self.leaderboard_data = response.json()
        except requests.RequestException:
            self.leaderboard_data = []

    def save_score(self):
        try:
            if not self.token:
                print("Error: No authentication token")
                return

            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            
            data = {
                "score": self.counter,
                "timestamp": int(time.time())
            }
            response = requests.post(
                "http://127.0.0.1:8001/scores",
                json=data,
                headers=headers
            )
            
            if response.status_code != 200:
                print(f"Error saving score: {response.json()}")
            
        except requests.RequestException as e:
            print(f"Error saving score: {e}")

    def draw_leaderboard(self):
        font = pygame.font.SysFont("Arial", 25)
        y = 50
        
        title = font.render("ТАБЛИЦА ЛИДЕРОВ", True, (255, 255, 255))
        title_rect = title.get_rect(centerx=self.screen.get_width() // 2, y=y)
        self.screen.blit(title, title_rect)
        y += 50
        
        if not self.leaderboard_data:
            text = font.render("Нет рекордов", True, (255, 255, 255))
            text_rect = text.get_rect(centerx=self.screen.get_width() // 2, y=y)
            self.screen.blit(text, text_rect)
            return
        
        for item in self.leaderboard_data:
            position = item["position"]
            if position <= 3:
                medal = self.medals[position - 1]
                medal_rect = medal.get_rect(
                    right=self.screen.get_width() // 2 - 70,
                    centery=y + 15
                )
                self.screen.blit(medal, medal_rect)
                
                name_text = font.render(item['username'], True, (255, 255, 255))
                name_rect = name_text.get_rect(
                    centerx=self.screen.get_width() // 2 - 20,
                    centery=y + 15
                )
                self.screen.blit(name_text, name_rect)
                
                score_text = font.render(str(item['score']), True, (255, 255, 255))
                score_rect = score_text.get_rect(
                    left=name_rect.right + 20,
                    centery=y + 15
                )
                self.screen.blit(score_text, score_rect)
                
                y += 40

    def reset_game(self):
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
        clock = pygame.time.Clock()
        self.show_menu()
        
        while True:
            self.reset_game()  # Сбрасываем состояние игры
            
            # Отсчет перед началом игры
            countdown_font = pygame.font.SysFont("Arial", 80)
            for i in range(3, 0, -1):
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
            
            self.screen.fill((255, 255, 255))
            self.screen.blit(self.background, (0, 0))
            self.screen.blit(self.birdSprites[0], (70, self.birdY))
            self.screen.blit(self.wallUp, (self.wallx, 360 + self.gap - self.offset))
            self.screen.blit(self.wallDown, (self.wallx, 0 - self.gap - self.offset))
            
            countdown_text = countdown_font.render(str(i), True, (255, 255, 255))
            countdown_rect = countdown_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            self.screen.blit(countdown_text, countdown_rect)
            
            pygame.display.update()
            pygame.time.wait(1000)
        
            # Игровой цикл
            while not self.dead:
                self.game_loop()
                clock.tick(60)
            
            # После смерти птицы
            self.sprite = 2
            self.screen.blit(self.birdSprites[self.sprite], (70, self.birdY))
            pygame.display.update()
            
            self.save_score()
            self.update_leaderboard()
            
            # Экран окончания игры
            result = self.game_over_screen()
            if result == "restart":
                continue  # Теперь continue находится в правильном месте
            elif result == "profile":
                pygame.quit()
                return "profile"
            else:
                pygame.quit()
                return "quit"

    def game_loop(self):
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

        if self.jump:
            self.jumpSpeed -= 1
            self.birdY -= self.jumpSpeed
            self.jump -= 1
            self.sprite = 1
        else:
            self.birdY += self.gravity
            self.gravity += 0.2
            self.sprite = 0

        self.bird[1] = self.birdY
        upRect = pygame.Rect(self.wallx, 360 + self.gap - self.offset + 10,
                            self.wallUp.get_width() - 10, self.wallUp.get_height())
        downRect = pygame.Rect(self.wallx, 0 - self.gap - self.offset - 10,
                              self.wallDown.get_width() - 10, self.wallDown.get_height())

        if upRect.colliderect(self.bird) or downRect.colliderect(self.bird):
            self.dead = True
        if not 0 < self.bird[1] < 720:
            self.dead = True

        self.screen.fill((255, 255, 255))
        self.screen.blit(self.background, (0, 0))

        if self.show_leaderboard:
            self.draw_leaderboard()
        else:
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
        self.update_leaderboard()
        
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
            
            title_font = pygame.font.SysFont("Arial", 50)
            font = pygame.font.SysFont("Arial", 30)
            
            game_over = title_font.render("ИГРА ОКОНЧЕНА!", True, (255, 255, 255))
            score = font.render(f"ВАШ СЧЁТ: {self.counter}", True, (255, 255, 255))
            continue_text = font.render("ENTER - НОВАЯ ИГРА", True, (255, 255, 255))
            exit_text = font.render("ESC - ВЫХОД", True, (255, 255, 255))
            
            game_over_rect = game_over.get_rect(centerx=self.screen.get_width() // 2, y=50)
            score_rect = score.get_rect(centerx=self.screen.get_width() // 2, y=120)
            
            self.screen.blit(game_over, game_over_rect)
            self.screen.blit(score, score_rect)
            
            font = pygame.font.SysFont("Arial", 25)
            leaderboard_title = font.render("ТАБЛИЦА ЛИДЕРОВ", True, (255, 255, 255))
            leaderboard_rect = leaderboard_title.get_rect(centerx=self.screen.get_width() // 2, y=200)
            self.screen.blit(leaderboard_title, leaderboard_rect)
            
            y = 250
            if not self.leaderboard_data:
                text = font.render("Нет рекордов", True, (255, 255, 255))
                text_rect = text.get_rect(centerx=self.screen.get_width() // 2, y=y)
                self.screen.blit(text, text_rect)
            else:
                for item in self.leaderboard_data:
                    position = item["position"]
                    if position <= 3:
                        medal = self.medals[position - 1]
                        medal_rect = medal.get_rect(
                            right=self.screen.get_width() // 2 - 70,
                            centery=y + 15
                        )
                        self.screen.blit(medal, medal_rect)
                        
                        name_text = font.render(item['username'], True, (255, 255, 255))
                        name_rect = name_text.get_rect(
                            centerx=self.screen.get_width() // 2 - 20,
                            centery=y + 15
                        )
                        self.screen.blit(name_text, name_rect)
                        
                        score_text = font.render(str(item['score']), True, (255, 255, 255))
                        score_rect = score_text.get_rect(
                            left=name_rect.right + 20,
                            centery=y + 15
                        )
                        self.screen.blit(score_text, score_rect)
                        
                        y += 40
            
            continue_rect = continue_text.get_rect(centerx=self.screen.get_width() // 2, y=550)
            exit_rect = exit_text.get_rect(centerx=self.screen.get_width() // 2, y=600)
            
            self.screen.blit(continue_text, continue_rect)
            self.screen.blit(exit_text, exit_rect)
            
            pygame.display.update()
            clock.tick(60)

    def show_menu(self):
        clock = pygame.time.Clock()
        font = pygame.font.SysFont("Arial", 30)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
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

            title_font = pygame.font.SysFont("Arial", 45)
            font = pygame.font.SysFont("Arial", 30)
            small_font = pygame.font.SysFont("Arial", 25)

            game_over = title_font.render("ИГРА ОКОНЧЕНА!", True, (255, 255, 255))
            score = font.render(f"ВАШ СЧЁТ: {self.counter}", True, (255, 255, 255))
            
            game_over_rect = game_over.get_rect(centerx=self.screen.get_width() // 2, y=50)
            score_rect = score.get_rect(centerx=self.screen.get_width() // 2, y=120)
            
            self.screen.blit(game_over, game_over_rect)
            self.screen.blit(score, score_rect)

            leaderboard_title = small_font.render("ТАБЛИЦА ЛИДЕРОВ", True, (255, 255, 255))
            leaderboard_rect = leaderboard_title.get_rect(centerx=self.screen.get_width() // 2, y=200)
            self.screen.blit(leaderboard_title, leaderboard_rect)

            y = 250
            if self.leaderboard_data:
                for item in self.leaderboard_data:
                    if item["position"] <= 3:
                        medal = self.medals[item["position"] - 1]
                        medal_rect = medal.get_rect(
                            right=self.screen.get_width() // 2 - 70,
                            centery=y
                        )
                        self.screen.blit(medal, medal_rect)
                        
                        name = small_font.render(item['username'], True, (255, 255, 255))
                        name_rect = name.get_rect(
                            centerx=self.screen.get_width() // 2 - 20,
                            centery=y
                        )
                        self.screen.blit(name, name_rect)
                        
                        score = small_font.render(str(item['score']), True, (255, 255, 255))
                        score_rect = score_rect = score.get_rect(
                            left=name_rect.right + 20,
                            centery=y
                        )
                        self.screen.blit(score, score_rect)
                        
                        y += 40

            continue_text = font.render("ENTER - НОВАЯ ИГРА", True, (255, 255, 255))
            profile_text = font.render("TAB - ВЕРНУТЬСЯ В ПРОФИЛЬ", True, (255, 255, 255))
            exit_text = font.render("ESC - ВЫХОД", True, (255, 255, 255))

            continue_rect = continue_text.get_rect(centerx=self.screen.get_width() // 2, y=580)
            profile_rect = profile_text.get_rect(centerx=self.screen.get_width() // 2, y=620)
            exit_rect = exit_text.get_rect(centerx=self.screen.get_width() // 2, y=660)

            self.screen.blit(continue_text, continue_rect)
            self.screen.blit(profile_text, profile_rect)
            self.screen.blit(exit_text, exit_rect)

            pygame.display.update()
            clock.tick(60)

    def show_statistics(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                "http://127.0.0.1:8001/user-stats",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data["players"]:
                    stats_text = "Нет данных о играх"
                else:
                    stats_text = "Статистика игроков:\n"
                    stats_text += "-" * 60 + "\n"
                    stats_text += f"{'Игрок':<15} | {'Игр':^4} | {'Лучший':^7} | {'Средний':^7} | {'Последние 5':<15}\n"
                    stats_text += "-" * 60 + "\n"
                    
                    total_games = 0
                    global_best = 0
                    all_scores = []
                    
                    for player in data["players"]:
                        last_scores = player.get('last_scores', [])
                        last_scores_str = ", ".join(map(str, last_scores[:5]))
                        if not last_scores_str:
                            last_scores_str = "[]"
                        
                        stats_text += f"{player['username']:<15} | "
                        stats_text += f"{player['games_played']:^4} | "
                        stats_text += f"{player['best_score']:^7} | "
                        stats_text += f"{player['average_score']:^7.1f} | "
                        stats_text += f"[{last_scores_str}]\n"
                        
                        total_games += player['games_played']
                        global_best = max(global_best, player['best_score'])
                        if player.get('last_scores'):
                            all_scores.extend(player['last_scores'])
                    
                    stats_text += "\nОбщая статистика:\n"
                    stats_text += "-" * 30 + "\n"
                    stats_text += f"Всего игр: {total_games}\n"
                    stats_text += f"Лучший результат: {global_best}\n"
                    if all_scores:
                        global_average = sum(all_scores) / len(all_scores)
                        stats_text += f"Средний результат: {global_average:.1f}\n"
                    else:
                        stats_text += "Средний результат: 0\n"
            else:
                stats_text = "Не удалось загрузить статистику"
            
        except requests.RequestException:
            stats_text = "Ошибка подключения к серверу"
        except Exception as e:
            stats_text = f"Ошибка при обработке данных: {str(e)}"
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Общая статистика")
        stats_window.geometry("700x500")
        stats_window.resizable(False, False)
        
        screen_width = stats_window.winfo_screenwidth()
        screen_height = stats_window.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 500) // 2
        stats_window.geometry(f"700x500+{x}+{y}")
        
        frame = tk.Frame(stats_window, padx=40, pady=20)
        frame.pack(expand=True, fill='both')
        
        tk.Label(
            frame,
            text="Статистика игроков",
            font=("Arial", 16, "bold")
        ).pack(pady=20)
        
        text_widget = tk.Text(
            frame,
            font=("Courier New", 12),
            height=20,
            width=70,
            wrap=tk.NONE,
            bg=frame.cget("bg"),
            relief=tk.FLAT
        )
        text_widget.insert("1.0", stats_text)
        text_widget.configure(state='disabled')
        text_widget.pack(pady=10)

class AuthApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Flappy Bird - Авторизация")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f"500x600+{x}+{y}")
        
        main_frame = tk.Frame(self.root, padx=50, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        title_label = tk.Label(
            main_frame, 
            text="Добро пожаловать\nв Flappy Bird!", 
            font=("Arial", 24, "bold"),
            pady=30,
            justify=tk.CENTER
        )
        title_label.pack()
        
        form_frame = tk.Frame(main_frame, pady=20)
        form_frame.pack()
        
        tk.Label(form_frame, text="Логин:", font=("Arial", 12)).pack()
        self.username_entry = tk.Entry(
            form_frame, 
            font=("Arial", 12),
            width=30
        )
        self.username_entry.pack(pady=(5, 15))
        
        tk.Label(form_frame, text="Пароль:", font=("Arial", 12)).pack()
        self.password_entry = tk.Entry(
            form_frame, 
            show="•",
            font=("Arial", 12),
            width=30
        )
        self.password_entry.pack(pady=(5, 20))
        
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(pady=20)
        
        login_btn = tk.Button(
            buttons_frame,
            text="Войти",
            command=self.login,
            width=15,
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        login_btn.pack(pady=5)
        
        register_btn = tk.Button(
            buttons_frame,
            text="Регистрация",
            command=self.open_registration,
            width=15,
            font=("Arial", 11),
            bg="#2196F3",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        register_btn.pack(pady=5)
        
        exit_btn = tk.Button(
            buttons_frame,
            text="Выход",
            command=self.root.quit,
            width=15,
            font=("Arial", 11),
            bg="#f44336",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        exit_btn.pack(pady=5)
        
        self.token = None

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля")
            return
        
        try:
            response = requests.post(
                "http://127.0.0.1:8001/login", 
                json={"username": username, "password": password}
            )
            
            if response.status_code == 200:
                self.token = response.json().get("token")
                self.root.destroy()
                ProfileWindow(self.token, username).run()
            elif response.status_code == 401:
                messagebox.showerror("Ошибка", "Неверный логин или пароль")
            else:
                messagebox.showerror("Ошибка", "Ошибка сервера. Попробуйте позже")
            
        except requests.ConnectionError:
            messagebox.showerror(
                "Ошибка подключения", 
                "Не удалось подключиться к серверу.\nПроверьте подключение к интернету или попробуйте позже."
            )
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def open_registration(self):
        reg_window = tk.Toplevel(self.root)
        reg_window.title("Flappy Bird - Регистрация")
        reg_window.geometry("400x550")
        reg_window.resizable(False, False)
        
        screen_width = reg_window.winfo_screenwidth()
        screen_height = reg_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 550) // 2
        reg_window.geometry(f"400x550+{x}+{y}")
        
        main_frame = tk.Frame(reg_window, padx=40, pady=20)
        main_frame.pack(expand=True, fill='both')
        
        title_label = tk.Label(
            main_frame,
            text="Регистрация нового игрока",
            font=("Arial", 16, "bold"),
            pady=20
        )
        title_label.pack()
        
        form_frame = tk.Frame(main_frame)
        form_frame.pack(pady=20)
        
        tk.Label(
            form_frame,
            text="Логин (минимум 3 символа):",
            font=("Arial", 12)
        ).pack()
        username_entry = tk.Entry(
            form_frame,
            font=("Arial", 12),
            width=30
        )
        username_entry.pack(pady=(5, 15))
        
        tk.Label(
            form_frame,
            text="Пароль (минимум 4 символа):",
            font=("Arial", 12)
        ).pack()
        password_entry = tk.Entry(
            form_frame,
            show="•",
            font=("Arial", 12),
            width=30
        )
        password_entry.pack(pady=(5, 15))
        
        tk.Label(
            form_frame,
            text="Подтверждение пароля:",
            font=("Arial", 12)
        ).pack()
        confirm_password_entry = tk.Entry(
            form_frame,
            show="•",
            font=("Arial", 12),
            width=30
        )
        confirm_password_entry.pack(pady=(5, 20))
        
        def register():
            username = username_entry.get()
            password = password_entry.get()
            confirm_password = confirm_password_entry.get()
            
            if not username or not password or not confirm_password:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля")
                return
            
            if len(username) < 3:
                messagebox.showerror("Ошибка", "Логин должен содержать минимум 3 символа")
                return
            
            if len(password) < 4:
                messagebox.showerror("Ошибка", "Пароль должен содержать минимум 4 символа")
                return

            if password != confirm_password:
                messagebox.showerror("Ошибка", "Пароли не совпадают")
                return

            try:
                data = {
                    "username": username,
                    "password": password
                }
                response = requests.post(
                    "http://127.0.0.1:8001/register", 
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    messagebox.showinfo(
                        "Успех", 
                        "Регистрация успешна!\nТеперь вы можете войти в игру."
                    )
                    reg_window.destroy()
                else:
                    try:
                        error_detail = response.json().get("detail", "")
                        if "Username already exists" in error_detail:
                            messagebox.showerror(
                                "Ошибка регистрации", 
                                "Пользователь с таким именем уже существует.\nПожалуйста, выберите другое имя пользователя."
                            )
                        else:
                            messagebox.showerror(
                                "Ошибка регистрации", 
                                "Не удалось зарегистрировать пользователя.\nПожалуйста, попробуйте позже."
                            )
                    except ValueError:
                        messagebox.showerror(
                            "Ошибка сервера", 
                            "Произошла ошибка при обработке запроса.\nПожалуйста, попробуйте позже."
                        )
                
            except requests.ConnectionError:
                messagebox.showerror(
                    "Ошибка подключения", 
                    "Не удалось подключиться к серверу.\nПроверьте подключение к интернету или попробуйте позже."
                )
            except requests.RequestException as e:
                messagebox.showerror(
                    "Ошибка соединения", 
                    "Произошла ошибка при подключении к серверу.\nПожалуйста, попробуйте позже."
                )

        register_btn = tk.Button(
            form_frame,
            text="Зарегистрироваться",
            command=register,
            width=20,
            font=("Arial", 11),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        register_btn.pack(pady=20)

    def start_game(self):
        if not self.token:
            messagebox.showerror("Ошибка", "Не удалось получить токен авторизации")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get("http://127.0.0.1:8001/me", headers=headers)
            
            if response.status_code == 200:
                game = FlappyBird(self.token)
                result = game.run()
                
                if result == "profile":
                    ProfileWindow(self.token, self.username).run()
                elif result == "quit":
                    AuthApp().run()
            else:
                error_message = response.json().get("detail", "Неизвестная ошибка")
                messagebox.showerror("Ошибка", f"Ошибка авторизации: {error_message}")
                self.__init__()
                self.run()
                
        except requests.RequestException as e:
            messagebox.showerror("Ошибка", f"Ошибка проверки токена: {str(e)}")
            return

    def run(self):
        self.root.mainloop()

class ProfileWindow:
    def __init__(self, token, username):
        self.token = token
        self.username = username
        
        self.root = tk.Tk()
        self.root.title("Flappy Bird - Личный кабинет")
        self.root.geometry("400x600")
        self.root.resizable(False, False)
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 600) // 2
        self.root.geometry(f"400x600+{x}+{y}")
        
        main_frame = tk.Frame(self.root, padx=40, pady=30)
        main_frame.pack(expand=True, fill='both')
        
        welcome_frame = tk.Frame(main_frame)
        welcome_frame.pack(fill='x', pady=(0, 40))
        
        welcome_text = f"Добро пожаловать,\n{self.username}!"
        tk.Label(
            welcome_frame,
            text=welcome_text,
            font=("Arial", 24, "bold"),
            justify=tk.CENTER
        ).pack(expand=True)
        
        buttons_frame = tk.Frame(main_frame)
        buttons_frame.pack(fill='x')
        
        play_btn = tk.Button(
            buttons_frame,
            text="Начать игру",
            command=self.start_game,
            width=20,
            font=("Arial", 14),
            bg="#4CAF50",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        play_btn.pack(pady=10)
        
        change_pass_btn = tk.Button(
            buttons_frame,
            text="Сменить пароль",
            command=self.change_password,
            width=20,
            font=("Arial", 14),
            bg="#2196F3",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        change_pass_btn.pack(pady=10)
        
        stats_btn = tk.Button(
            buttons_frame,
            text="Общая статистика",
            command=self.show_statistics,
            width=20,
            font=("Arial", 14),
            bg="#FF9800",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        stats_btn.pack(pady=10)
        
        exit_btn = tk.Button(
            buttons_frame,
            text="Выйти",
            command=self.logout,
            width=20,
            font=("Arial", 14),
            bg="#f44336",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        exit_btn.pack(pady=10)

        delete_btn = tk.Button(
            buttons_frame,
            text="Удалить аккаунт",
            command=self.delete_account,
            width=20,
            font=("Arial", 14),
            bg="#b71c1c",
            fg="white",
            relief=tk.RAISED,
            cursor="hand2"
        )
        delete_btn.pack(pady=10)

    def start_game(self):
        self.root.destroy()
        game = FlappyBird(self.token)
        result = game.run()
        
        if result == "profile":
            ProfileWindow(self.token, self.username).run()
        elif result == "quit":
            AuthApp().run()

    def change_password(self):
        change_window = tk.Toplevel(self.root)
        change_window.title("Смена пароля")
        change_window.geometry("400x300")
        change_window.resizable(False, False)
        
        screen_width = change_window.winfo_screenwidth()
        screen_height = change_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 300) // 2
        change_window.geometry(f"400x300+{x}+{y}")
        
        frame = tk.Frame(change_window, padx=40, pady=20)
        frame.pack(expand=True, fill='both')
        
        tk.Label(frame, text="Текущий пароль:", font=("Arial", 12)).pack()
        current_pass = tk.Entry(frame, show="•", font=("Arial", 12))
        current_pass.pack(pady=(5, 15))
        
        tk.Label(frame, text="Новый пароль:", font=("Arial", 12)).pack()
        new_pass = tk.Entry(frame, show="•", font=("Arial", 12))
        new_pass.pack(pady=(5, 15))
        
        tk.Label(frame, text="Подтвердите пароль:", font=("Arial", 12)).pack()
        confirm_pass = tk.Entry(frame, show="•", font=("Arial", 12))
        confirm_pass.pack(pady=(5, 15))
        
        def submit_change():
            current = current_pass.get()
            new = new_pass.get()
            confirm = confirm_pass.get()
            
            if not current or not new or not confirm:
                messagebox.showerror("Ошибка", "Пожалуйста, заполните все поля")
                return
            
            if new != confirm:
                messagebox.showerror("Ошибка", "Новые пароли не совпадают")
                return
            
            if len(new) < 4:
                messagebox.showerror("Ошибка", "Новый пароль должен содержать минимум 4 символа")
                return
            
            try:
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                }
                response = requests.patch(
                    "http://127.0.0.1:8001/change-password",
                    json={
                        "current_password": current,
                        "new_password": new
                    },
                    headers=headers
                )
                
                if response.status_code == 200:
                    messagebox.showinfo("Успех", "Пароль успешно изменен")
                    change_window.destroy()
                elif response.status_code == 400:
                    messagebox.showerror("Ошибка", "Неверный текущий пароль")
                else:
                    messagebox.showerror("Ошибка", "Не удалось изменить пароль")
                
            except requests.RequestException:
                messagebox.showerror(
                    "Ошибка",
                    "Не удалось подключиться к серверу"
                )
        
        submit_btn = tk.Button(
            frame,
            text="Сменить пароль",
            command=submit_change,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white"
        )
        submit_btn.pack(pady=20)

    def show_statistics(self):
        try:
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.get(
                "http://127.0.0.1:8001/user-stats",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if not data["players"]:
                    stats_text = "Нет данных о играх"
                else:
                    stats_text = "Статистика игроков:\n"
                    stats_text += "-" * 60 + "\n"
                    stats_text += f"{'Игрок':<15} | {'Игр':^4} | {'Лучший':^7} | {'Средний':^7} | {'Последние 5':<15}\n"
                    stats_text += "-" * 60 + "\n"
                    
                    total_games = 0
                    global_best = 0
                    all_scores = []
                    
                    for player in data["players"]:
                        last_scores = player.get('last_scores', [])
                        last_scores_str = ", ".join(map(str, last_scores[:5]))
                        if not last_scores_str:
                            last_scores_str = "[]"
                        
                        stats_text += f"{player['username']:<15} | "
                        stats_text += f"{player['games_played']:^4} | "
                        stats_text += f"{player['best_score']:^7} | "
                        stats_text += f"{player['average_score']:^7.1f} | "
                        stats_text += f"[{last_scores_str}]\n"
                        
                        total_games += player['games_played']
                        global_best = max(global_best, player['best_score'])
                        if player.get('last_scores'):
                            all_scores.extend(player['last_scores'])
                    
                    stats_text += "\nОбщая статистика:\n"
                    stats_text += "-" * 30 + "\n"
                    stats_text += f"Всего игр: {total_games}\n"
                    stats_text += f"Лучший результат: {global_best}\n"
                    if all_scores:
                        global_average = sum(all_scores) / len(all_scores)
                        stats_text += f"Средний результат: {global_average:.1f}\n"
                    else:
                        stats_text += "Средний результат: 0\n"
            else:
                stats_text = "Не удалось загрузить статистику"
            
        except requests.RequestException:
            stats_text = "Ошибка подключения к серверу"
        except Exception as e:
            stats_text = f"Ошибка при обработке данных: {str(e)}"
        
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Общая статистика")
        stats_window.geometry("700x500")
        stats_window.resizable(False, False)
        
        screen_width = stats_window.winfo_screenwidth()
        screen_height = stats_window.winfo_screenheight()
        x = (screen_width - 700) // 2
        y = (screen_height - 500) // 2
        stats_window.geometry(f"700x500+{x}+{y}")
        
        frame = tk.Frame(stats_window, padx=40, pady=20)
        frame.pack(expand=True, fill='both')
        
        tk.Label(
            frame,
            text="Статистика игроков",
            font=("Arial", 16, "bold")
        ).pack(pady=20)
        
        text_widget = tk.Text(
            frame,
            font=("Courier New", 12),
            height=20,
            width=70,
            wrap=tk.NONE,
            bg=frame.cget("bg"),
            relief=tk.FLAT
        )
        text_widget.insert("1.0", stats_text)
        text_widget.configure(state='disabled')
        text_widget.pack(pady=10)

    def logout(self):
        if messagebox.askyesno("Выход", "Вы уверены, что хотите выйти?"):
            self.root.destroy()
            AuthApp().run()

    def delete_account(self):
        if not messagebox.askyesno(
            "Подтверждение удаления",
            "Вы уверены, что хотите удалить свой аккаунт?\n\nЭто действие необратимо и приведет к потере всех данных и статистики.",
            icon='warning'
        ):
            return
            
        if not messagebox.askyesno(
            "Финальное подтверждение",
            "Вы действительно хотите удалить свой аккаунт?\n\nПосле удаления восстановление будет невозможно.",
            icon='warning'
        ):
            return
        
        try:
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
            response = requests.delete(
                "http://127.0.0.1:8001/delete-account",
                headers=headers
            )
            
            if response.status_code == 200:
                messagebox.showinfo(
                    "Успех",
                    "Ваш аккаунт был успешно удален."
                )
                self.root.destroy()
                AuthApp().run()
            else:
                messagebox.showerror(
                    "Ошибка",
                    "Не удалось удалить аккаунт. Попробуйте позже."
                )
                
        except requests.RequestException:
            messagebox.showerror(
                "Ошибка",
                "Не удалось подключиться к серверу. Проверьте подключение к интернету."
            )

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AuthApp()
    app.run()
