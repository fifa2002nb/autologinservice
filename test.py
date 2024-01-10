# -*- coding:utf-8 -*-
import unittest
import platform
import urlparse
import urllib
import urllib2
import time
import json
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains    
from bs4 import BeautifulSoup

class seleniumTest(unittest.TestCase):
    def setUp(self):
        dcap = dict(DesiredCapabilities.PHANTOMJS)
        dcap["phantomjs.page.settings.userAgent"] = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/40.0.2214.38 Safari/537.36'
        )
        #self.driver = webdriver.PhantomJS(desired_capabilities=dcap)
        self.driver = webdriver.Chrome("/usr/local/bin/chromedriver")
        self.Headers = {
            'Content-Type'      :   'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie'            :   '',
            'User-Agent'        :   'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
        }
        self.username = u'上水间'
        self.password = 'fifa2002nb'
        self.url = 'https://login.taobao.com/member/login.jhtml'
        self.query = 'style=mini&newMini2=true&css_style=alimama&from=alimama&redirectURL=http%3A%2F%2Fwww.alimama.com&full_redirect=true&disableQuickLogin=true'
        self.siteid = ""
        self.adzoneid = ""
        print("------------------- [%-4s] -------------------" %"up")

    def _request(self, url, data, method='POST'):
        if data:
            data = urllib.urlencode(data)
        if 'GET' == method:
            if data:
                url = '{}?{}'.format(url, data)
            data = None
        req = urllib2.Request(url, data, self.Headers)
        return urllib2.urlopen(req)

    def get(self, url, data=None):
        return self._request(url, data, method='GET')

    def post(self, url, data=None):
        return self._request(url, data, method='POST')

    def login_taobao(self):
        url = self.url + '?' + self.query
        self.driver.delete_all_cookies()
        self.driver.get(url)
        element = WebDriverWait(self.driver,60).until(
            lambda driver :
                self.driver.find_element_by_xpath("//*[@id='J_QRCodeImg']/img"))
        self.driver.implicitly_wait(20)
        print("[QRCode]:%s" %element.get_attribute("src"))
 
        while True:
            result = urlparse.urlparse(self.driver.current_url)
            if result.hostname != 'login.taobao.com':
                break;
            qrrefreshElement = self.driver.find_element_by_css_selector("#J_QRCodeLogin > div.qrcode-mod > div.qrcode-main > div.msg-err > a")
            if "" != qrrefreshElement.text:
                self.driver.implicitly_wait(20)
                qrrefreshElement.click()
                self.driver.implicitly_wait(20)
                time.sleep(2)
                element = self.driver.find_element_by_xpath("//*[@id='J_QRCodeImg']/img")
                self.driver.implicitly_wait(20)
                print("[New QRCode]:%s" %element.get_attribute("src"))
            time.sleep(0.5)
        cookie = "; ".join([item["name"] + "=" + item["value"] for item in self.driver.get_cookies()])
        self.driver.close()
        return cookie

    def test_taobao(self):
        #self.Headers['Cookie'] = "alimamapw=HXIIQHQjQ3EgFycjQXogHXcFMQEEAQNTBwVVAgRTUwFRW1QBWwIGVgQHVwVTVFJXAF0B; alimamapwag=TW96aWxsYS81LjAgKE1hY2ludG9zaDsgSW50ZWwgTWFjIE9TIFggMTBfMTJfMykgQXBwbGVXZWJLaXQvNTM3LjM2IChLSFRNTCwgbGlrZSBHZWNrbykgQ2hyb21lLzU2LjAuMjkyNC44NyBTYWZhcmkvNTM3LjM2; cna=mJBmEeKYKBICAWXluuhGk779; login=VFC%2FuZ9ayeYq2g%3D%3D; cookie31=MTIxNDc1MTk5LCVFNCVCOCU4QSVFNiVCMCVCNCVFOSU5NyVCNCx4eXNtaXJhY2xlQGdtYWlsLmNvbSxUQg%3D%3D; t=356ee9ab35fed38ee6cacd681840d8cf; cookie32=0a074f9276623b7a2e17edbe88a61a21; v=0; _tb_token_=IZ7j1ELf56Vq; cookie2=f7daec85f9f4324e2a4f989c5649bfcb"
        if "" == self.Headers['Cookie']:
            #self.driver = webdriver.Chrome("/usr/local/bin/chromedriver")
            self.Headers['Cookie'] = self.login_taobao()
            print("[NewCookie]:%s" %self.Headers['Cookie'])
        if "" == self.Headers['Cookie']:
            print("cookie not found.")
            return

        if "" == self.siteid or "" == self.adzoneid:
            res = self.get('http://pub.alimama.com/common/adzone/newSelfAdzone2.json', {
                    'tag'   :   '29'
                })
            content = res.read()
            adzoneData = None
            try:
                adzoneData = json.loads(content)
            except:
                print(content)
                return
            if adzoneData and adzoneData['data'] and adzoneData['data']['otherAdzones']:
                if 0 < len(adzoneData['data']['otherAdzones']) and adzoneData['data']['otherAdzones'][0]['id'] and adzoneData['data']['otherAdzones'][0]['sub']:
                    if 0 < len(adzoneData['data']['otherAdzones'][0]['sub']) and adzoneData['data']['otherAdzones'][0]['sub'][0]['id']:
                        self.siteid = adzoneData['data']['otherAdzones'][0]['id']
                        self.adzoneid = adzoneData['data']['otherAdzones'][0]['sub'][0]['id']
        if "" == self.siteid or "" == self.adzoneid:
            print("siteid or adzoneid not found.")
            return

        itemURL = 'https://detail.tmall.com/item.htm?spm=a230r.1.14.6.ygcdOg&id=544867006078&cm_id=140105335569ed55e27b&abbucket=7'
        res = self.get('http://pub.alimama.com/urltrans/urltrans.json', {
                'siteid'        :   self.siteid,
                'adzoneid'      :   self.adzoneid,
                'promotionURL'  :   itemURL,
            })
        print("[TaoKey]:%s" %res.read())

    def tearDown(self):
        print("------------------- [%-4s] -------------------" %"down")

if __name__ == "__main__":
    unittest.main()
