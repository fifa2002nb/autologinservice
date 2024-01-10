# -*- coding:utf-8 -*-
import tornado.web
import globalVal as GlobalVal
import json
import logging

# /
class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(403)

    def post(self):
        self.set_status(403)

# /cookie
class CookieHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_status(403)

    #curl --data "data={\"username\":\"fastorz\",\"status\":\"init\"}" "http://127.0.0.1:8000/cookie"
    def post(self):
        postData = None
        respData = {
            "code" : 0, 
            "result" : None
        }
        postData = self.get_argument('data', None)
        if None != postData and "" != postData:
            try:
                postData = json.loads(postData)
                username = postData['username']
                status = postData['status']
                if None == username or None == status:
                    respData['code'] = 2
                else:
                    GlobalVal.lockUserMap()
                    userStatus = GlobalVal.getUserStatus(username)
                    if None == userStatus:
                        respData['code'] = 1
                        respData['result'] = "permission denied."
                    elif None != userStatus and (GlobalVal.RUNNING() == userStatus or GlobalVal.TRANSFERING() == userStatus):
                        respData['code'] = 1
                        respData['result'] = "username:%s status:%s" %(username, GlobalVal.RUNNING())
                    else:
                        GlobalVal.putUserStatus(username, status)
                        try:
                            GlobalVal.putJob({"username": username}, block = False)
                            respData['code'] = 0
                            logging.info("putJob username:%s." %username)
                        except Queue.Full:
                            respData['code'] = 1
                            logging.error('jobQueue is full.')
                    GlobalVal.unlockUserMap()
            except Exception, e:
                respData['code'] = 1
                logging.error(e.reason)
        else:
            respData['code'] = 2

        try:
            self.set_status(200)
            self.write(json.dumps(respData))
        except Exception, e:
            logging.error(e)
            self.set_status(500)
            self.write(None)

# /qrcode
class QRCodeHandler(tornado.web.RequestHandler):
    #curl "http://127.0.0.1:8000/qrcode?username=fastorz"
    def get(self):
        respData = {
            "code" : 0, 
            "result" : None
        }
        username = self.get_argument('username', None)
        if None != username and "" != username:
            try:
                GlobalVal.lockQRCodeMap()
                QRCode = GlobalVal.getQRCode(username)
                if None == QRCode:
                    respData['code'] = 0
                    respData['result'] = "everything is ok."
                else:
                    respData['code'] = 0
                    respData['result'] = QRCode
                    self.redirect(QRCode)
                    return
            finally:
                GlobalVal.unlockQRCodeMap()
        else:
            respData['code'] = 1
            respData['result'] = "username is required."
        self.write(json.dumps(respData))

    def post(self):
        self.set_status(403)

# /alert
class AlertHandler(tornado.web.RequestHandler):
    #curl "http://127.0.0.1:8000/alert?username=fastorz"
    def get(self):
        username = self.get_argument('username', None)
        if None != username and "" != username:
            GlobalVal.lockUserMap()
            userStatus = GlobalVal.getUserStatus(username)
            if None != userStatus and (GlobalVal.RUNNING() == userStatus or GlobalVal.TRANSFERING() == userStatus):
                self.set_status(404)
            else:
                self.set_status(200)
            GlobalVal.unlockUserMap()
        else:
            self.set_status(200)

    def post(self):
        self.set_status(403)
