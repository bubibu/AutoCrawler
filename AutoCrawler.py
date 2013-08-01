__author__ = 'liangrui.hlr'

import urllib2
import threading

class CookieStr:
    def __init__(self):
        self.cookieDict = dict()
    def addCookie(self,key,value):
        self.cookieDict[key] = value

    def replaceCookie(self,key,value):
        self.addCookie(key,value)

    def addAsDict(self,cookieDict):
        for key,value in cookieDict.items():
            self.cookieDict[key] = value

    def toStr(self):
        str = ""
        for key,value in self.cookieDict.items():
            str += (key+"="+value+";")
        return str

class CookieCrawler:
    def __init__(self,url,interval,cookieDict):
        self.cookieStr = CookieStr()
        self.request = self.__initRequest(url,cookieDict)
        self.interval = interval

    def start(self,func):
        res = urllib2.urlopen(self.request)
        # func(res.read())
        self.__mainLoop(self.request,res,self.cookieStr,self.interval,func)

    def craw(self,url = None):
        if url is None:
            res = urllib2.urlopen(self.request)
            return res.read()
        else:
            self.request = urllib2.Request(url)
            self.request.add_header('Cookie',self.cookieStr.toStr())
            res = urllib2.urlopen(self.request)
            return res.read()

    def end(self):
        t.cancel()

    def __initRequest(self,url,cookieDict):
        self.cookieStr.addAsDict(cookieDict)
        request = urllib2.Request(url)
        request.add_header('Cookie',self.cookieStr.toStr())
        return request

    def __maintainCookie(self,request,response,cookieStr):
        headers = response.info()
        if 'Set-Cookie' in headers:
            ckDict = self.__getCookieFromHeadStr(headers['Set-Cookie'])
            for key,value in ckDict.items():
                cookieStr.replaceCookie(key,value)

            request.add_header('Cookie',cookieStr.toStr())
            print ckDict
        return request

    def __getCookieFromHeadStr(self,setCookieStr):
        resDict = dict()
        ckItem = str(setCookieStr).split(',')
        for item in ckItem:
            ckKeyValue = item.split(';')
            if ckKeyValue[0].find("=") != -1:
                keyValueList = ckKeyValue[0].split('=')
                resDict[keyValueList[0]] = keyValueList[1]
        return resDict

    def __mainLoop(self,request,response,cookieStr,interval,func):
        self.__maintainCookie(request,response,cookieStr)
        res = urllib2.urlopen(request)
        func(res.read())
        global t
        t = threading.Timer(interval,self.__mainLoop,(request,res,cookieStr,interval,func))
        t.start()
