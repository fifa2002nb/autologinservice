# -*- coding:utf-8 -*-
import urlparse
import urllib
import urllib2
import time
import json
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
import logging
import globalVal as GlobalVal

logging.basicConfig(
    level       = logging.INFO,
    format      = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt     = '[%Y-%m-%d %H:%M:%S]',
    #filename    ='myapp.log',
    #filemode    ='w'
)

class TaobaoCookieHandler:
    def __init__(self, username):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.38 Safari/537.36'
        )
        self.driver = webdriver.PhantomJS(desired_capabilities = dcap)
        self.driver.set_window_size(1920,1080)
        #self.driver = webdriver.Chrome("/usr/local/bin/chromedriver")
        self.Headers = {
            'Content-Type'      :   'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie'            :   None,
            'User-Agent'        :   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }
        self.username = username
        self.url = 'https://login.taobao.com/member/login.jhtml'
        self.query = 'style=mini&newMini2=true&css_style=alimama&from=alimama&redirectURL=http%3A%2F%2Fwww.alimama.com&full_redirect=true&disableQuickLogin=true'
        self.siteid = None
        self.adzoneid = None

    def _request(self, url, data, method = 'POST'):
        if data:
            data = urllib.urlencode(data)
        if 'GET' == method:
            if data:
                url = '{}?{}'.format(url, data)
            data = None
        req = urllib2.Request(url, data, self.Headers)
        return urllib2.urlopen(req)

    def get(self, url, data=None):
        return self._request(url, data, method = 'GET')

    def post(self, url, data=None):
        return self._request(url, data, method = 'POST')

    def setCookies(self, cookies):
        self.Headers['Cookie'] = cookies

    def getCookies(self):
        return self.Headers['Cookie']

    def setSiteidAndAdzoneid(self, siteid, adzoneid):
        self.siteid = siteid
        self.adzoneid = adzoneid

    def getSiteidAndAdzoneid(self):
        return self.siteid, self.adzoneid

    # export
    def Request4Cookies(self):
        if None != self.getCookies():
            return True
        try:
            url = self.url + '?' + self.query
            self.driver.delete_all_cookies()
            self.driver.get(url)
            element = WebDriverWait(self.driver, 30).until(
                lambda driver :
                    self.driver.find_element_by_xpath("//*[@id='J_QRCodeImg']/img"))
            self.driver.implicitly_wait(20)
            logging.info("[QRCode]:%s" %element.get_attribute("src"))
            waitTimes = 1200 
            while True:
                if 0 >= waitTimes:
                    return False
                # 放到全局map中，提供httpHandler下载  
                try:
                    qrcode = element.get_attribute("src")
                    GlobalVal.lockQRCodeMap()
                    GlobalVal.putQRCode(self.username, qrcode)
                    GlobalVal.unlockQRCodeMap()
                except:
                    pass
                result = urlparse.urlparse(self.driver.current_url)
                if result.hostname != 'login.taobao.com':
                    break
                qrrefreshElement = self.driver.find_element_by_css_selector("#J_QRCodeLogin > div.qrcode-mod > div.qrcode-main > div.msg-err > a")
                if "" != qrrefreshElement.text:
                    self.driver.implicitly_wait(20)
                    qrrefreshElement.click()
                    self.driver.implicitly_wait(20)
                    time.sleep(2)
                    element = self.driver.find_element_by_xpath("//*[@id='J_QRCodeImg']/img")
                    self.driver.implicitly_wait(20)
                    logging.info("[New QRCode]:%s" %element.get_attribute("src"))

                time.sleep(0.5)
                waitTimes = waitTimes - 1
            cookie = "; ".join([item["name"] + "=" + item["value"] for item in self.driver.get_cookies()])
            self.setCookies(cookie)
        except Exception, e:
            logging.error(e)
            self.driver.save_screenshot('screenshot.png')
            return False
        finally:
            self.driver.close()
            self.driver.quit()
            logging.info("taobaoOpsHandler closed.")
        return True

    # export
    def ParseSiteidAndAdzoneid(self):
        if None != self.siteid and None != self.adzoneid:
            return True

        if True == self.Request4Cookies():
            logging.info("[NewCookie]:%s" %self.getCookies())
        else:
            logging.error("cookie not found.")
            return False

	# tmp plan
	self.setSiteidAndAdzoneid('20772989', '70412623')	
	return True

        retryTimes = 10 
        while True:
            if 0 >= retryTimes:
                break
            retryTimes = retryTimes - 1
            #try:
            res = self.get('http://pub.alimama.com/common/adzone/newSelfAdzone2.json', {
                'tag'   :   '29'
                })
            content = res.read()
            adzoneData = None
            adzoneData = json.loads(content)
            if adzoneData and adzoneData['data'] and adzoneData['data']['otherAdzones']:
                if 0 < len(adzoneData['data']['otherAdzones']) and adzoneData['data']['otherAdzones'][0]['id'] and adzoneData['data']['otherAdzones'][0]['sub']:
                    if 0 < len(adzoneData['data']['otherAdzones'][0]['sub']) and adzoneData['data']['otherAdzones'][0]['sub'][0]['id']:
                        self.siteid = adzoneData['data']['otherAdzones'][0]['id']
                        self.adzoneid = adzoneData['data']['otherAdzones'][0]['sub'][0]['id']
            #except Exception, e:
            #    logging.error(e)
            #    return False
            if None == self.siteid or None == self.adzoneid:
                logging.error("siteid or adzoneid not found.")
                logging.error(adzoneData)
                time.sleep(10)
                continue
            else:
                break

        if None == self.siteid or None == self.adzoneid:
            return False
        self.setSiteidAndAdzoneid(self.siteid, self.adzoneid)
        return True

    # export
    def ParsePromotionInfo(self):
        if False == self.ParseSiteidAndAdzoneid():
            logging.error("[GetPromotionInfo]fail to GetSiteidAndAdzoneid.")
            return False

        #itemURL = 'https://detail.tmall.com/item.htm?spm=a230r.1.14.6.ygcdOg&id=544867006078&cm_id=140105335569ed55e27b&abbucket=7'
        itemURL = 'http://c.b1wt.com/h.4MeE2r?cv=yV0FLlmoV5&sm=190b49'
        res = self.get('http://pub.alimama.com/urltrans/urltrans.json', {
                'siteid'        :   self.siteid,
                'adzoneid'      :   self.adzoneid,
                'promotionURL'  :   itemURL,
            })
        logging.info("[User]:%s [TaoKey]:%s" %(self.username, res.read()))

if __name__ == "__main__":
    handler = TaobaoCookieHandler("xuye")
    handler.ParsePromotionInfo()
