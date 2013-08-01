AutoCrawler
===========

This is a simple crawler with a timer and cookie support implemented by python.

Install
-----------------------

    git clone https://github.com/nekonanu/AutoCrawler.git
    

Quick Start
---------------------
###Sample1
    
    import AutoCrawler
    
    #define a handler
    def handler(msg): 
      print msg
      
    #define the cookie dictionary
    cookieDict = { 
      'token':'23897SADFJ23497YASDFKU23',
      'uid':'nekosama'
    }
    
    #define the interval
    interval = 3
    
    #define the url
    url = "http://www.example.com/crawpage?page=1"
    
    crawler = AutoCrawler.CookieCrawler(url,interval,cookieDict)
    
    #set the pre-defined handler below
    crawler.start(handler)
    
