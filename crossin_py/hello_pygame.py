#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'eric'

import pygame,random

#向sys借一个exit函数来退出程序
from sys import exit
#定义飞机的类
class Plane():
    #设置重头开始时飞机的位置
    def restart(self):
        self.x = 0
        self.y = background.get_height()/2
    #初始化飞机的位置并加载飞机图片
    def __init__(self):
        self.restart()
        self.image = pygame.image.load('picture/plane.jpg').convert_alpha()
    #定义飞机的运动
    def move(self):
        x,y = pygame.mouse.get_pos()
        #将鼠标置于飞机图片中心
        x -= self.image.get_width()/2
        y -= self.image.get_height()/2
        self.x = x
        self.y = y

#定义子弹的类
class Bullet():
    #初始化成员变量，x,y,image
    def __init__(self):
        self.x = background.get_width() + 1
        self.y = 0
        self.image = pygame.image.load('picture/bullet.jpg').convert_alpha()
        #默认子弹不激活
        self.active = False
    def restart(self):
        #设置子弹的位置,获取鼠标位置
        mouseX, mouseY = pygame.mouse.get_pos()
        self.x = mouseX - self.image.get_width()/2
        self.y = mouseY - self.image.get_height()/2
        #激活子弹
        self.active = True
    def move(self):
        #如果子弹处于激活状态，则每次移动两格
        if self.active:
            self.x = self.x + 1.8
        #如果子弹位置超出屏幕右侧，置子弹状态为不激活
        if self.x > background.get_width():
            self.active = False

#定义敌机的类
class Enemy():
    #随机生成敌机的位置与速度
    def restart(self):
        self.x = background.get_width() + 55
        self.y = random.randint(23,background.get_height()-23)
        self.speed = random.random()+0.1
    #初始化敌人位置，加载敌机图片
    def __init__(self):
        self.restart()
        self.image = pygame.image.load('picture/enemy.png').convert_alpha()
    #设置敌机运动轨迹
    def move(self):
        if self.x > -110:
            self.x = self.x - self.speed
        else:
            self.restart()

#定义是否击中敌机的函数
def checkHit(enemy,bullet):
    #如果子弹图片在敌机图片之内，则认为击中
    if (bullet.x > enemy.x and bullet.x < enemy.x + enemy.image.get_width()) and \
        (bullet.y > enemy.y and bullet.y < enemy.y + enemy.image.get_height()):
        #重置敌机
        enemy.restart()
        #重置子弹
        bullet.active = False
        return True
    return False

#定义是否被敌机撞
def checkCresh(enemy,plane):
    if (plane.x + 0.7 * plane.image.get_width() > enemy.x) and (plane.x + 0.3 *  plane.image.get_width() < enemy.x + enemy.image.get_width()) and \
        (plane.y + 0.7 * plane.image.get_height() > enemy.y) and (plane.y + 0.3 *  plane.image.get_width() < enemy.y + enemy.image.get_height()):
        return True
    return False

#初始化pygame，为使用硬件做准备
pygame.init()
#创建一个窗口，大小与目标图片一样
screen =  pygame.display.set_mode((886,479),0,32)
#设置窗口标题
pygame.display.set_caption("welcome to your first pygame!")
#加载并转换图片
# bg1 = pygame.image.load('1.jpg').convert()
# bg2 = pygame.image.load('2.jpg').convert()
# bg3 = pygame.image.load('3.jpg').convert()
# bglist = [bg1,bg2,bg3]
# background = bg1
background = pygame.image.load('picture/sky.jpeg').convert()
#加载飞机图片
plane = Plane()
#创建子弹的list
bullets = []
#向list中添加5颗子弹
for i in range(3):
    bullets.append(Bullet())
#子弹总数
count_b = len(bullets)
#即将激活的子弹序号
index_b = 0
#发射子弹的间隔
interval_b = 0

#创建敌机的list
enemies = []
for i in range(2):
    enemies.append(Enemy())

#初始分数为0
score = 0
#用以显示文字的Font对象
font = pygame.font.Font(None,32)
text1 = font.render("GAME OVER---click to restart", 1, (0, 0, 0))
#开始游戏
gameover = False

#游戏主循环
while True:
    for event in pygame.event.get():
        #收到退出事件后退出
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        #判断在gameover状态下点了鼠标
        if gameover and event.type == pygame.MOUSEBUTTONDOWN:
            #重置游戏
            plane.restart()
            for e in enemies:
                e.restart()
            for b in bullets:
                b.active = False
            score = 0
            gameover = False
    #画上背景图
    screen.blit(background,(0,0))

    if not gameover:
        #发射间隔递减
        interval_b -= 1
        #当间隔<0时，激活一颗子弹
        if interval_b < 0:
            bullets[index_b].restart()
            #重置间隔时间，即运行多少距离，发射下一颗子弹
            interval_b = 150
            #子弹序号周期递增
            index_b = (index_b + 1) % count_b
        #判断每个子弹的状态
        for b in bullets:
            #处于激活状态的子弹运动，并绘制图像
            if b.active:
                for e in enemies:
                    if checkHit(e,b):
                        score += 100
                b.move()
                screen.blit(b.image,(b.x,b.y))

        #处理敌机运动轨迹
        for e in enemies:
            #如果撞上敌机，设gameover为True
            if checkCresh(e,plane):
                gameover = True
            e.move()
            screen.blit(e.image,(e.x,e.y))

        #定义飞机的运行轨迹，并绘制图像
        plane.move()
        screen.blit(plane.image,(plane.x,plane.y))
        #在屏幕左上角显示分数
        text =  font.render("Score: %d" % score,1,(0,0,0))
        screen.blit(text,(0,0))
    else:
        #游戏结束，在屏幕中央显示分数
        text =  font.render("Score: %d" % score,1,(0,0,0))
        screen.blit(text,(0,0))
        screen.blit(text1,(330,239))

    #刷新页面
    pygame.display.update()
