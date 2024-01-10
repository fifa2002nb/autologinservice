# -*- coding:utf-8 -*-
'''
全局变量文件
'''
import Queue
import thread
import logging
import urllib
import urllib2
import json
import ssl  

#取消ssl自签名验证
ssl._create_default_https_context = ssl._create_unverified_context  

class GlobalVal:
	#登陆任务队列，线程安全不需要锁
    jobQueue 	= None
    #用户信息和状态，map[user] = status (status: init,running,finish)
    userMap 	= None
    #用户验证二维码信息
    QRCodeMap 	= None
    #用户登陆后的cookie传输队列，线程安全不需要锁
    transQueue 	= None
    #用户信息状态查询锁
    userLock 	= None
    #用户验证二维码信息锁
    qrLock 		= None
    #status constants
    INIT 		= 'init'
    RUNNING 	= 'running'
    TRANSFERING = 'transfering'
    FINISH 		= 'finish'

# job queue ops
def setJobQueue(jobQueue):
	GlobalVal.jobQueue = jobQueue

def getJobQueue():
    return GlobalVal.jobQueue

def putJob(item, block = True):
    if None == GlobalVal.jobQueue:
	    setJobQueue(Queue.Queue(maxsize = 100))
    GlobalVal.jobQueue.put(item, block)

def getJob(block = True):
    if None == GlobalVal.jobQueue:
	    setJobQueue(Queue.Queue(maxsize = 100))
    return GlobalVal.jobQueue.get(block)

# user map ops
def setUserMap(userMap):
	GlobalVal.userMap = userMap

def getUserMap():
	return GlobalVal.userMap

def putUserStatus(username, status):
	if None == GlobalVal.userMap:
		setUserMap({})
	GlobalVal.userMap[username] = status

def getUserStatus(username):
	if None == GlobalVal.userMap:
		setUserMap({})
	status = None
	try:
		status = GlobalVal.userMap[username]
	except:
		pass
	return status

# QRCode map ops
def setQRCodeMap(QRCodeMap):
	GlobalVal.QRCodeMap = QRCodeMap

def getQRCodeMap():
	return GlobalVal.QRCodeMap

def putQRCode(username, QRCode):
	if None == GlobalVal.QRCodeMap:
		setQRCodeMap({})
	GlobalVal.QRCodeMap[username] = QRCode

def getQRCode(username):
	if None == GlobalVal.QRCodeMap:
		setQRCodeMap({})
	QRCode = None
	try:
		QRCode = GlobalVal.QRCodeMap[username]
	except:
		pass
	return QRCode

# trans queue ops
def setTransQueue(transQueue):
	GlobalVal.transQueue = transQueue

def getTransQueue():
	return GlobalVal.transQueue

def putTrans(trans, block = True):
	if None == GlobalVal.transQueue:
		setTransQueue(Queue.Queue(maxsize = 100))
	GlobalVal.transQueue.put(trans, block)

def getTrans(block = True):
	if None == GlobalVal.transQueue:
		setTransQueue(Queue.Queue(maxsize = 100))
	return GlobalVal.transQueue.get(block)

# user lock ops
def setUserMapLock(userLock):
	GlobalVal.userLock = userLock

def getUserMapLock():
	return GlobalVal.userLock

def lockUserMap():
	if None == GlobalVal.userLock:
		setUserMapLock(thread.allocate_lock())
	GlobalVal.userLock.acquire()

def unlockUserMap():
	if None == GlobalVal.userLock:
		setUserMapLock(thread.allocate_lock())
	try:
		GlobalVal.userLock.release()
	except:
		pass

# QRCodeMap lock ops
def setQRCodeMapLock(qrLock):
	GlobalVal.qrLock = qrLock

def getQRCodeMapLock():
	return GlobalVal.qrLock

def lockQRCodeMap():
	if None == GlobalVal.qrLock:
		setQRCodeMapLock(thread.allocate_lock())
	GlobalVal.qrLock.acquire()

def unlockQRCodeMap():
	if None == GlobalVal.qrLock:
		setQRCodeMapLock(thread.allocate_lock())
	try:
		GlobalVal.qrLock.release()
	except:
		pass

# job status
def RUNNING():
	return GlobalVal.RUNNING

def INIT():
	return GlobalVal.INIT

def TRANSFERING():
	return GlobalVal.TRANSFERING

def FINISH():
	return GlobalVal.FINISH

# 改变用户信息map状态
def changeUserStatusTo(username, status):
    try:
        lockUserMap()
        if None == getUserStatus(username):
            pass
        else:
            putUserStatus(username, status)
    finally:
        unlockUserMap()
    return

# http请求套件
def _request(url, data, method = 'POST'):
    if data:
        #data = urllib.urlencode(data)
        data = json.dumps(data)
    if 'GET' == method:
        if data:
            url = '{}?{}'.format(url, data)
        data = None
    req = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    return urllib2.urlopen(req)

def get(url, data = None):
    return _request(url, data, method = 'GET')

def post(url, data = None):
    return _request(url, data, method = 'POST')

if __name__ == "__main__":
	data = {"username": "fastorz", "siteid": "20772989", "cookie": "alimamapw=QXsOFiciEnNwQ3h1HHAhRyMFbQgCV1BSVgcFVlsFDgtQAQABBwsAAFcGBgcDAA0BXVcA; login=VT5L2FSpMGV7TQ%3D%3D; alimamapwag=TW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfOV81KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvNDAuMC4yMjE0LjM4IFNhZmFyaS81MzcuMzY%3D; cookie31=MTIxNDc1MTk5LCVFNCVCOCU4QSVFNiVCMCVCNCVFOSU5NyVCNCx4eXNtaXJhY2xlQGdtYWlsLmNvbSxUQg%3D%3D; cookie32=0a074f9276623b7a2e17edbe88a61a21; v=0; t=660ed6f0edbbbef9df1196434cb6182d; _tb_token_=8Rr12s8041Wq; cookie2=a9db747ea5641c4da0f9e8c6c7ca2f49", "adzoneid": str(70412623)}
	response = post("http://127.0.0.1:8001/v1/cookie/update", data)
	content = response.read()
	print(content)
