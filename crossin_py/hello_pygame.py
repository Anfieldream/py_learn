#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'eric'

import pygame,random

#向sys借一个exit函数来退出程序
from sys import exit
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
plane = pygame.image.load('picture/plane.jpg').convert_alpha()

#游戏主循环
while True:
    for event in pygame.event.get():
        #获取鼠标状态，点击则切换背景图
        # if event.type == pygame.MOUSEBUTTONDOWN:
        #     background = random.choice(bglist)
        #收到退出事件后退出
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
    #画上背景图
    screen.blit(background,(0,0))

    #获取鼠标坐标
    x,y = pygame.mouse.get_pos()
    #将鼠标置于图片中心
    x = x - plane.get_width()/2
    y = y - plane.get_height()/2
    #画上飞机位置
    screen.blit(plane,(x,y))

    #刷新页面
    pygame.display.update()