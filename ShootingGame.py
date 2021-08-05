import numpy
import pygame
import random
import sys
from pygame import mixer


class Crosshair(pygame.sprite.Sprite):  # define a Crosshair class
    def __init__(self, picture_path):
        super().__init__()
        self.image = pygame.image.load(picture_path).convert_alpha()
        self.rect = self.image.get_rect()

    def update(self):  # keep the crosshair sprite following the mouse
        self.rect.center = pygame.mouse.get_pos()

    def check_shooting(self, group, score_amplifier):  # check if the sprites are shot
        global score
        rect_collide_list = pygame.sprite.spritecollide(self, group, False)
        real_shot_list = []
        mouse_pos = pygame.mouse.get_pos()  # get mouse position

        for rect_collide_sprite in rect_collide_list:
            if rect_collide_sprite.rect.collidepoint(mouse_pos):
                pos_in_mask = mouse_pos[0] - rect_collide_sprite.rect.x, mouse_pos[1] - rect_collide_sprite.rect.y  # local position of the mouse in the sprite rect
                if rect_collide_sprite.mask.get_at(pos_in_mask):  # accuratly check if the mouse position is within the mask
                    real_shot_list.append(rect_collide_sprite)  # shot sprites are added into the real_shot_list

        if real_shot_list: #if any sprite is shot
            if not real_shot_list[-1].is_quit_trigger():
                real_shot_list[-1].set_quit_trigger()  # quitting initialization of the sprite

                score += 1 * score_amplifier  # score counting

                position, height, color_index = real_shot_list[-1].require_parameters()  # obtain peremeters from the shot sprite
                scoring_ani_group.add(ScoringAnimation(position, height / 2, color_index, score_amplifier))  # adding scoring animation sprites into a group

                real_shot_list[-1].remove()  # removed the sprite from the list
            return True
        return False


class ScoringAnimation(pygame.sprite.Sprite):  # define a ScoringAnimation class
    def __init__(self, position, offset_Y, ColorIndex, scoring_amplifier):
        super().__init__()
        self.image = Score_font.render(f'+{scoring_amplifier}', True, pygame.Color(ColorList[ColorIndex]))
        self.rect = self.image.get_rect()
        self.position = numpy.asarray(position, dtype=numpy.float64) + (0, -offset_Y)
        self.rect.center = self.position
        self.ani_step = -2
        self.ani_distance = 0

    def update(self):
        self.position += (0, self.ani_step)  # the sprite moves -2 pixels in y-axis per frame
        self.rect.center = self.position

        self.ani_distance += self.ani_step  # the sprite is removed after it moved -80 pixels
        if self.ani_distance <= -60:
            self.kill()


class Target(pygame.sprite.Sprite):  # define a Target(Balloon) class
    def __init__(self, RanNum, position, velocity, scale):
        super().__init__()
        img_idle_list = Balloon_idle_Set[RanNum]  # image list initialization for idle animation
        img_quit_list = Balloon_quit_Set[RanNum]  # image list initialization for quitting animation
        img_width, img_height = img_idle_list[0].get_rect().size
        img_width = int(img_width * scale)
        img_height = int(img_height * scale)  # scale the image width and height
        self.ColorIndex = RanNum
        self.ImgIdle_list_scaled = []
        self.ImgQuit_list_scaled = []

        for list_num in range(len(img_idle_list)):  # scale all the images in the list
            Tmp_img = img_idle_list[list_num]
            Tmp_img = pygame.transform.smoothscale(Tmp_img, (img_width, img_height))
            self.ImgIdle_list_scaled.append(Tmp_img)

        for list_num in range(len(img_quit_list)):  # scale all the images in the list
            Tmp_img = img_quit_list[list_num]
            Tmp_img = pygame.transform.smoothscale(Tmp_img, (img_width, img_height))
            self.ImgQuit_list_scaled.append(Tmp_img)

        self.image = self.ImgIdle_list_scaled[0]
        self.rect = self.image.get_rect()
        self.position = numpy.asarray(position, dtype=numpy.float64)
        self.velocity = numpy.asarray(velocity, dtype=numpy.float64)
        self.rect.center = self.position
        self.mask = pygame.mask.from_surface(self.image)  # create a mask from the given surface
        self.quit_trigger = False
        self.time_counter = 0
        self.frame = 0
        self.ani_speed = 8

    def update(self, env_velocity):
        if self.quit_trigger:  # if triggered to quit, run quitting animation
            self.quit_animation()
        else:  # otherwise run idle animation and keep the sprite flowing upwards
            self.idle_animation()
            self.position += self.velocity

        self.position += env_velocity  # adding the environment velocity(scrolling velocity) to the position value
        self.rect.center = self.position

        if self.rect.center[1] < -50:  # sprite is removed if it is out of the top screen
            self.kill()

    def set_quit_trigger(self):
        self.quit_trigger = True
        self.time_counter = 0
        self.frame = 0
        # print("Hit! Score: ", score)
        channel3.play(hit_sound)

    def require_parameters(self):
        return self.position, self.rect.height, self.ColorIndex

    def idle_animation(self):
        self.time_counter += 1
        if self.time_counter >= self.ani_speed:
            self.frame += 1
            self.time_counter = 0
        if self.frame > len(self.ImgIdle_list_scaled) - 1:
            self.frame = 0
        self.image = self.ImgIdle_list_scaled[self.frame]

    def quit_animation(self):
        self.time_counter += 1
        if self.frame <= len(self.ImgQuit_list_scaled) - 1:
            self.image = self.ImgQuit_list_scaled[self.frame]
            if self.time_counter >= self.ani_speed / 3:
                self.frame += 1
                self.time_counter = 0

            int_sign = bool(self.velocity[0] > 0) - bool(self.velocity[0] < 0)  # get the sign of self.velocity[0]
            self.position += numpy.asarray([int_sign, 1], dtype=numpy.float64)  # a slower flowing velocity

        elif self.frame > len(self.ImgQuit_list_scaled) - 1:
            self.kill()
            self.time_counter = 0
            self.frame = 0
            self.quit_trigger = False

    def is_quit_trigger(self):
        return self.quit_trigger


class BulletIcon(pygame.sprite.Sprite):  # define a BulletIcon class
    def __init__(self, position):
        super().__init__()
        self.img_list = [pygame.image.load("res/bullet_icon.png").convert_alpha(),
                         pygame.image.load("res/bullet_shell_icon.png").convert_alpha()]

        self.image = self.img_list[0]
        self.rect = self.image.get_rect()
        self.rect.center = numpy.asarray(position, dtype=numpy.float64)
        self.quit_trigger = False
        self.rotate_angle = 0
        self.d_angle = 0  # angular velocity
        self.trajectory_dx = random.randint(2, 8)  # velocity
        self.trajectory_dy = random.randint(-12, 0)
        self.trajectory_ddy = 1  # acceleration

    def update(self):
        if self.quit_trigger:
            self.quit_animation()

    def quit_animation(self):
        self.rotate_angle += self.d_angle
        self.image = pygame.transform.rotozoom(self.img_list[1], self.rotate_angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.trajectory_dy += self.trajectory_ddy
        self.rect.center += numpy.asarray([self.trajectory_dx, self.trajectory_dy], dtype=numpy.float64)

        if self.rect.center[1] > screen_height + 20:  # if the sprite is out of the bottom screen, it is removed
            self.kill()
            self.quit_trigger = False

    def set_quit_trigger(self):
        self.quit_trigger = True
        self.rotate_angle = random.randint(-30, 30)
        self.d_angle = random.randint(-30, 30)
        self.image = pygame.transform.rotozoom(self.img_list[1], self.rotate_angle, 1)
        self.rect = self.image.get_rect(center=self.rect.center)

    def is_quit_trigger(self):
        return self.quit_trigger


def add_target(group, env_x, scale, number):  # add Target sprites into a group
    count = len(group)
    if count < number:
        position = start_position_generation()
        position[0] += env_x
        velocity = start_velocity_generation(scale)
        RanNum = random.randint(0, len(Balloon_idle_Set) - 1)
        target = Target(RanNum, position, velocity, scale)
        group.add(target)


def start_position_generation():  # initial positions of the target sprites
    pos_x = random.randint(0, 3000)
    pos_y = screen_height+random.randint(0, 100)
    return [pos_x, pos_y]


def start_velocity_generation(scale):  # initial velocities of the target sprites
    vel_x = int(random.randint(-2, 2))
    vel_y = int(random.randint(1, 4) * -1 * scale)
    if vel_y > -1:
        vel_y = -1
    return [vel_x, vel_y]


def bullet_reload(group):  # bullet reload
    group.empty()
    ammo_number = 10
    position = [screen_width - 20 * ammo_number, screen_height - 40]
    for bullet_count in range(ammo_number):
        bullet_icon = BulletIcon(position)
        position[0] += 20
        group.add(bullet_icon)
    # print("Ammo reloaded")
    channel2.play(reload_sound)
    return True


def bullet_reduction(group):  # bullet reduction
    bullet_list = group.sprites()
    bullet_index = len(bullet_list) - 1
    if bullet_list:
        while bullet_list[bullet_index].is_quit_trigger():
            bullet_index -= 1
            if bullet_index < 0:
                # print("Out of ammo!!")
                channel2.play(no_ammo_sound)
                return False
        bullet_list[bullet_index].set_quit_trigger()
        channel2.play(shoot_sound)
        # print("Biu~")
        return True
    else:
        # print("Out of ammo!!")
        channel2.play(no_ammo_sound)
        return False


def update_fps():
    fps = str(int(clock.get_fps()))
    fps_text = FPS_font.render(f'FPS: {fps}', True, pygame.Color(WHITE))
    return fps_text


def update_time(seconds):
    is_end = False
    time_limit = 60
    countdown = int((time_limit - seconds)*10)/10   # 1 decimal remained
    time_text = Score_font.render(f'TIME LEFT: {countdown} s', True, pygame.Color(WHITE))

    if countdown < 10 and (int(countdown)+1) % 2 == 0:  # flash effect on the text if time is less than 10s
        time_text = Score_font.render(f'TIME LEFT: {countdown} s', True, pygame.Color(DARK_RED))

    if countdown <= 0:
        is_end = True

    return time_text, is_end


def update_score():
    score_text = Score_font.render(f'SCORE: {score}', True, pygame.Color(WHITE))
    return score_text


def require_state(prepare_trigger, start_trigger, end_trigger):
    if not prepare_trigger and not start_trigger and not end_trigger:
        state = 0  # initial state, not playing
    elif prepare_trigger and not start_trigger and not end_trigger:
        state = 1  # countdown state, get ready to play
    elif not prepare_trigger and start_trigger and not end_trigger:
        state = 2  # playing state
    elif not prepare_trigger and not start_trigger and end_trigger:
        state = 3  # end state
    else:
        state = 4  # error
        print("Error")
    return state


pygame.init()
clock = pygame.time.Clock()

# load sounds and define channels
announce_sound = mixer.Sound('res/audio/announce.mp3')
hit_sound = mixer.Sound('res/audio/Hit.ogg')
shoot_sound = mixer.Sound('res/audio/LaserGun.ogg')
no_ammo_sound = mixer.Sound('res/audio/NoAmmo.ogg')
reload_sound = mixer.Sound('res/audio/GunCocking.ogg')

channel1 = pygame.mixer.Channel(0)
channel1.set_volume(0.3)
channel1.set_endevent(pygame.USEREVENT + 1)  # define the event that's sent when a sound stops playing
channel2 = pygame.mixer.Channel(1)
channel2.set_volume(0.5)
channel3 = pygame.mixer.Channel(2)

# create screen
pygame.mouse.set_visible(False)
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))  # optional:   pygame.FULLSCREEN

# load images
RedBalloon_idle_list = [pygame.image.load("res/balloon/idle_red_1.png").convert_alpha(),
                        pygame.image.load("res/balloon/idle_red_2.png").convert_alpha(),
                        pygame.image.load("res/balloon/idle_red_3.png").convert_alpha(),
                        pygame.image.load("res/balloon/idle_red_4.png").convert_alpha()]
RedBalloon_quit_list = [pygame.image.load("res/balloon/explode_red_1.png").convert_alpha(),
                        pygame.image.load("res/balloon/explode_red_2.png").convert_alpha(),
                        pygame.image.load("res/balloon/explode_red_3.png").convert_alpha(),
                        pygame.image.load("res/balloon/explode_red_4.png").convert_alpha()]
BlueBalloon_idle_list = [pygame.image.load("res/balloon/idle_blue_1.png").convert_alpha(),
                         pygame.image.load("res/balloon/idle_blue_2.png").convert_alpha(),
                         pygame.image.load("res/balloon/idle_blue_3.png").convert_alpha(),
                         pygame.image.load("res/balloon/idle_blue_4.png").convert_alpha()]
BlueBalloon_quit_list = [pygame.image.load("res/balloon/explode_blue_1.png").convert_alpha(),
                         pygame.image.load("res/balloon/explode_blue_2.png").convert_alpha(),
                         pygame.image.load("res/balloon/explode_blue_3.png").convert_alpha(),
                         pygame.image.load("res/balloon/explode_blue_4.png").convert_alpha()]
GreenBalloon_idle_list = [pygame.image.load("res/balloon/idle_lightgreen_1.png").convert_alpha(),
                          pygame.image.load("res/balloon/idle_lightgreen_2.png").convert_alpha(),
                          pygame.image.load("res/balloon/idle_lightgreen_3.png").convert_alpha(),
                          pygame.image.load("res/balloon/idle_lightgreen_4.png").convert_alpha()]
GreenBalloon_quit_list = [pygame.image.load("res/balloon/explode_lightgreen_1.png").convert_alpha(),
                          pygame.image.load("res/balloon/explode_lightgreen_2.png").convert_alpha(),
                          pygame.image.load("res/balloon/explode_lightgreen_3.png").convert_alpha(),
                          pygame.image.load("res/balloon/explode_lightgreen_4.png").convert_alpha()]

Balloon_idle_Set = [RedBalloon_idle_list, BlueBalloon_idle_list, GreenBalloon_idle_list]
Balloon_quit_Set = [RedBalloon_quit_list, BlueBalloon_quit_list, GreenBalloon_quit_list]

bg_sky = pygame.image.load("res/background/BG_sky.png").convert()
bg_mountain = pygame.image.load("res/background/BG_mountain.png").convert_alpha()
mg_hill = pygame.image.load("res/background/MG_hill.png").convert_alpha()
mg_bush = pygame.image.load("res/background/MG_bush.png").convert_alpha()
fg_grass = pygame.image.load("res/background/FG_grass.png").convert_alpha()
bg_sky = pygame.transform.smoothscale(bg_sky, (screen_width, screen_height))
W_fg_grass, H_fg_grass = fg_grass.get_rect().size

# define sprites and groups
crosshair = Crosshair("res/crosshair.png")
crosshair_group = pygame.sprite.Group()
crosshair_group.add(crosshair)

scoring_ani_group = pygame.sprite.Group()

target_group1 = pygame.sprite.Group()
target_group2 = pygame.sprite.Group()
target_group3 = pygame.sprite.Group()
target_group4 = pygame.sprite.Group()

bullet_group = pygame.sprite.Group()

# define colors
ColorList = []
for i in range(len(Balloon_idle_Set)):
    tmp_img = Balloon_idle_Set[i][0]
    pixel_position = (32, 1)  # get a particular pixel on the image
    ColorList.append(tmp_img.get_at(pixel_position))
WHITE = (255, 255, 255)
DARK_RED = (205, 70, 80)

# define texts
FPS_font = pygame.font.SysFont("Arial", 18)
Score_font = pygame.font.SysFont("Showcard Gothic", 25)
Info_font = pygame.font.SysFont("Showcard Gothic", 30)

text_Ammo_Unavailable = Info_font.render(f'Out Of Ammo!!', True, pygame.Color(WHITE))
text_initial = Info_font.render(f'=== Click To Start ===', True, pygame.Color(DARK_RED))
text_initial_control1 = Info_font.render(f'Left: A                 Right: D', True, pygame.Color(WHITE))
text_initial_control2 = Info_font.render(f'Fire: L Click   Reload: R Click', True, pygame.Color(WHITE))
text_ready = Info_font.render(f'Ready?', True, pygame.Color(WHITE))
text_go = Info_font.render(f'GO!!', True, pygame.Color(DARK_RED))
text_end = Info_font.render(f'=== Game Over ===', True, pygame.Color(DARK_RED))
text_restart = Info_font.render(f'Press SPACE To Restart', True, pygame.Color(WHITE))

# define variables for scrolling effect
x = -300
v = 0
scrolling_velocity = 3

# score initialization
score = 0

# define variables for timer
Start_Time = 0
Current_Time = 0

# reload bullets
ammo_available = bullet_reload(bullet_group)

# define triggers in game loop
edge_trigger = False
Prepare_trigger = False
StartPlay_trigger = False
EndPlay_trigger = False
MoveLeft_Flag = False
MoveRight_Flag = False

# initial state for game loop
Loop_State = require_state(Prepare_trigger, StartPlay_trigger, EndPlay_trigger)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if Loop_State == 0:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:   # initialization for state 1. If clicked, go to state 1
                    Prepare_trigger = True
                    channel1.play(announce_sound)

        elif Loop_State == 1:
            if event.type == pygame.USEREVENT + 1:  # initialization for state 2. If sound done play, go to state 2
                Prepare_trigger = False
                StartPlay_trigger = True
                Start_Time = pygame.time.get_ticks()
                mixer.music.load("res/audio/PlayMusic.mp3")
                pygame.mixer.music.set_volume(0.5)
                mixer.music.play(-1)

        elif Loop_State == 2:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # left click return 1
                    ammo_available = bullet_reduction(bullet_group)  # if left clicked, reduce 1 bullet
                    if ammo_available:  # if ammo is not empty, check if targets are shot sequently
                        if not crosshair.check_shooting(target_group1, 1):
                            if not crosshair.check_shooting(target_group2, 2):
                                if not crosshair.check_shooting(target_group3, 5):
                                    crosshair.check_shooting(target_group4, 10)
                elif event.button == 3:  # right click return 3
                    ammo_available = bullet_reload(bullet_group)  # if right clicked, reload ammo

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:  # scrolling left
                    MoveLeft_Flag = True
                if event.key == pygame.K_d:  # scrolling left
                    MoveRight_Flag = True
                v = -scrolling_velocity * (MoveRight_Flag - MoveLeft_Flag)
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    MoveLeft_Flag = False
                if event.key == pygame.K_d:
                    MoveRight_Flag = False
                v = -scrolling_velocity * (MoveRight_Flag - MoveLeft_Flag)

        elif Loop_State == 3:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:  # initialization for state 0. If SPACE pressed, go to state 0
                    EndPlay_trigger = False
                    x = -300
                    v = 0
                    score = 0
                    Start_Time = 0
                    Current_Time = 0
                    ammo_available = bullet_reload(bullet_group)
                    mixer.music.stop()

    Loop_State = require_state(Prepare_trigger, StartPlay_trigger, EndPlay_trigger)

    if channel2.get_busy() or channel3.get_busy():  # adjustment of volume for music
        pygame.mixer.music.set_volume(0.3)
    else:
        pygame.mixer.music.set_volume(0.5)

    x += v

    if x < -600:  # boundary condition update
        x = -600
        edge_trigger = True
    elif x > 0:
        x = 0
        edge_trigger = True
    else:
        edge_trigger = False

    if edge_trigger:
        target_group1.update([0, 0])
        target_group2.update([0, 0])
        target_group3.update([0, 0])
        target_group4.update([0, 0])
    else:
        target_group1.update([v * 6.8, 0])
        target_group2.update([v * 4.5, 0])
        target_group3.update([v * 3.6, 0])
        target_group4.update([v * 2, 0])

    screen.blit(bg_sky, (0, 0))

    if Loop_State == 2:  # rendering background scene with target sprites (playing state)
        add_target(target_group4, x, 0.2, 5)
        target_group4.draw(screen)

        screen.blit(bg_mountain, (x * 2, 150))

        add_target(target_group3, x * 2, 0.4, 5)
        target_group3.draw(screen)

        screen.blit(mg_hill, (x * 3.6, 350))

        add_target(target_group2, x * 3.6, 0.6, 5)
        target_group2.draw(screen)

        screen.blit(mg_bush, (x * 4.5, 350))

        add_target(target_group1, x * 4.5, 1, 10)
        target_group1.draw(screen)
    else:  # rendering background scene WITHOUT target sprites
        screen.blit(bg_mountain, (x * 2, 150))
        screen.blit(mg_hill, (x * 3.6, 350))
        screen.blit(mg_bush, (x * 4.5, 350))

    screen.blit(fg_grass, (x * 6.8, screen_height - H_fg_grass))

    bullet_group.draw(screen)  # rendering bullet icons
    bullet_group.update()

    scoring_ani_group.draw(screen)  # rendering the scoring text animations
    scoring_ani_group.update()

    if Loop_State == 0:  # rendering initial text
        screen.blit(text_initial, (250, 150))
        screen.blit(text_initial_control1, (180, 300))
        screen.blit(text_initial_control2, (180, 340))

    if Loop_State == 1:    # rendering 'ready' text
        screen.blit(text_ready, (350, 150))

    if Loop_State == 2:
        Current_Time = pygame.time.get_ticks()  # time counting starts

        if Current_Time - Start_Time <= 500:  # rendering 'Go' text
            screen.blit(text_go, (380, 150))

        screen.blit(update_score(), (20, 20))  # rendering the score text

        if not ammo_available:  # if no ammo, rendering the reminder text
            screen.blit(text_Ammo_Unavailable, (screen_width - 230, screen_height - 40))

        Time_text, EndPlay_trigger = update_time((Current_Time - Start_Time) / 1000)  # count down text and trigger
        screen.blit(Time_text, (screen_width - 220, 20))

        if EndPlay_trigger and StartPlay_trigger:  # initialization for State 3
            MoveLeft_Flag = False
            MoveRight_Flag = False
            StartPlay_trigger = False
            v = -0.5
            target_group1.empty()
            target_group2.empty()
            target_group3.empty()
            target_group4.empty()
            mixer.music.load("res/audio/EndMusic.mp3")
            pygame.mixer.music.set_volume(0.5)
            mixer.music.play(-1)

    if Loop_State == 3:
        screen.blit(text_end, (290, 150))  # rendering the end state text
        screen.blit(text_restart, (220, 280))
        screen.blit(update_score(), (350, 220))

        if edge_trigger:
            v *= -1

    crosshair_group.draw(screen)  # rendering the crosshair
    crosshair_group.update()

    screen.blit(update_fps(), (20, screen_height - 30))  # rendering the fps text

    pygame.display.flip()
    clock.tick(60)
