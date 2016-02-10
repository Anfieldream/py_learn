#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'eric'

import logging
logging.basicConfig(level=logging.INFO)

import asyncio,os,json,time
from datetime import datetime
from aiohttp import web

#这是一个handle函数，用于绑定在指定的请求类型或格式上，用于响应此特定请求
#param：request 是收到的请求
def index(request):
    return web.Response(body = b'<h1>Awesome</h1>')

@asyncio.coroutine
def init(event_loop):
    #创建web.app实例，参数为event_loop
    app = web.Application(loop = event_loop)
    #把index函数注册到webapp里，并指定对应响应类型为get请求且访问根目录
    app.router.add_route('GET','/',index)
    #创建server，并指定server地址和服务端口
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return srv

#获取处理事件的loop
loop = asyncio.get_event_loop()
#init server
loop.run_until_complete(init(loop))
loop.run_forever()