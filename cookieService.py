# -*- coding:utf-8 -*-
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options
import Queue
import thread
import threadpool
import threading
import time
import json
import logging
import globalVal as GlobalVal
from taobaoOps import TaobaoCookieHandler
from httpHandler import CookieHandler
from httpHandler import IndexHandler
from httpHandler import QRCodeHandler
from httpHandler import AlertHandler

define("port", default = 8001, help="run on the given port", type = int)

class Application:
    def __init__(self, port = 8000, queueSize = 10, remoteAddr = "http://127.0.0.1:8000/cookie"):
        tornado.options.parse_command_line()
        self.queueSize = queueSize
        self.port = port
        self.httpServer = options.port 
        self.remoteAddr = remoteAddr
        self.cookieService = None
        self.transService = None
        self.initGlobalVals()
        self.initTornadoSetting()

    def initTornadoSetting(self):
        handlers = [
            (r"/"       ,   IndexHandler),
            (r"/cookie" ,   CookieHandler),
            (r"/qrcode" ,   QRCodeHandler),
            (r"/alert"  ,   AlertHandler),
        ]
        app = tornado.web.Application(handlers = handlers, debug = True)
        self.httpServer = tornado.httpserver.HTTPServer(app)
        self.httpServer.listen(self.port)

    def initGlobalVals(self):
        # 暂时只允许一个用户使用, 后期会从数据库中读取用户信息做初始化
        GlobalVal.setUserMap({"fastorz": GlobalVal.INIT()})
        GlobalVal.setJobQueue(Queue.Queue(self.queueSize))
        GlobalVal.setTransQueue(Queue.Queue(self.queueSize))

    def initLoggingSetting(self):
        logging.basicConfig(
            level       = logging.INFO,
            format      = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
            datefmt     = '[%y-%m-%d %H:%M:%S]',
            #filename    ='myapp.log',
            #filemode    ='w'
        )
    # main loop
    def Start(self):
        self.cookieService = threading.Thread(target = cookieService)
        self.transService = threading.Thread(target = transService, args = (self.remoteAddr,))
        self.cookieService.setDaemon(True)
        self.cookieService.start()
        self.transService.setDaemon(True)
        self.transService.start()
        if None != self.httpServer:
            tornado.ioloop.IOLoop.instance().start()

# 处理登陆获取cookie
def cookieService():
    logging.info("cookieService started.")
    while True:
        job = GlobalVal.getJob(block = True)
        logging.info("get [%s]'s cookie job." %job['username'])
        if None == job or None == job['username']:
            continue
        username = job['username']
        GlobalVal.changeUserStatusTo(username, GlobalVal.RUNNING())
        taobaoHandler = TaobaoCookieHandler(username)
        cookie = None
        try:
            if True == taobaoHandler.Request4Cookies():
                cookie = taobaoHandler.getCookies()
            else:
                logging.error("request [%s] cookies error." %username)
                GlobalVal.putJob(job, block = True)
                continue
        except Exception, e:
            logging.error(e)
            GlobalVal.putJob(job, block = True)
            continue
        if None == cookie:
            continue
        # retry 10 times
        retrys = 11
        for i in range(0, retrys):
            try:
                if True == taobaoHandler.ParseSiteidAndAdzoneid():
                    siteid, adzoneid = taobaoHandler.getSiteidAndAdzoneid()
                    GlobalVal.putTrans({'username': username, 'cookie': cookie, 'siteid': siteid, 'adzoneid': str(adzoneid)}, block = True)
                    break
                else:
                    logging.error("request [%s] siteid/adzoneid error." %username)
                    break
            except Exception, e:
                logging.error(e)
            if retrys - 1 == i:
                GlobalVal.putJob(job, block = True)
                break


# cookie传回给api模块,失败/异常则放回队列重新发送
def transService(remoteAddr):
    logging.info("transService started.[%s]" %remoteAddr)
    while True:
        trans = GlobalVal.getTrans(block = True)
        if None == trans or None == trans['username'] or None == trans['cookie']:
            continue
        username = trans['username']
        cookie = trans['cookie']
        siteid = trans['siteid']
        adzoneid = trans['adzoneid']
        GlobalVal.changeUserStatusTo(username, GlobalVal.TRANSFERING())
        respData = None
        content = None
        try:
            response = GlobalVal.post(remoteAddr, trans)
            content = response.read()
            respData = json.loads(content)
        except Exception, e:
            # put back transQueue
            GlobalVal.putTrans({'username': username, 'cookie': cookie, 'siteid': siteid, 'adzoneid': adzoneid}, block = True)
            logging.error(e)
            time.sleep(5)
            continue
        if None != respData and 0 == respData['code']:
            logging.info("username:%s cookie:%s" %(username, cookie))
            GlobalVal.changeUserStatusTo(username, GlobalVal.FINISH())
            GlobalVal.lockQRCodeMap()
            GlobalVal.putQRCode(username, None)
            GlobalVal.unlockQRCodeMap()
        else:
            logging.error("username:%s remoteRespone:%s" %(username, content))
            GlobalVal.putTrans({'username': username, 'cookie': cookie, 'siteid': siteid, 'adzoneid': adzoneid}, block = True)
            time.sleep(5)


if __name__ == "__main__":
    app = Application(8000, 100, "https://127.0.0.1:1443/v1/cookie/update")
    app.Start()


