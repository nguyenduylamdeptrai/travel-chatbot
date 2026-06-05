# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import requests
from urllib.parse import urlencode
from random import randint
import logging

class TravelSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    async def process_start(self, start):
        # Called with an async iterator over the spider start() method or the
        # maching method of an earlier spider middleware.
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class TravelDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)

class ScrapeOpsFakeBrowserHeaderAgentMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)
    
    def __init__(self, settings):
        self.scrapeops_api_key = settings.get('SCRAPEOPS_API_KEY')
        self.scrapeops_endpoint = settings.get('SCRAPEOPS_FAKE_BROWSER_HEADER_ENDPOINT',
                                               'https://headers.scrapeops.io/v1/browser-headers')
        self.scrapeops_fake_browser_headers_active = settings.get('SCRAPEOPS_FAKE_BROWSER_HEADER_ENABLED', True)
        self.scrapeops_num_results = settings.get('SCRAPEOPS_NUM_RESULTS')
        self.headers_list = []
        self._get_headers_list()
        self._scrapeops_fake_browser_headers_enabled()
    
    def _get_headers_list(self):
        """Lấy danh sách headers từ ScrapeOps API"""
        try:
            payload = {'api_key': self.scrapeops_api_key}
            if self.scrapeops_num_results is not None:
                payload['num_results'] = self.scrapeops_num_results
            
            response = requests.get(self.scrapeops_endpoint, params=urlencode(payload))
            response.raise_for_status()
            
            json_response = response.json()
            self.headers_list = json_response.get('result', [])
            
            if not self.headers_list:
                logging.warning("ScrapeOps: No headers received from API")
            else:
                logging.info(f"ScrapeOps: Successfully loaded {len(self.headers_list)} headers")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"ScrapeOps: Error fetching headers: {e}")
            self.headers_list = []
        except Exception as e:
            logging.error(f"ScrapeOps: Unexpected error: {e}")
            self.headers_list = []
    
    def _get_random_browser_header(self):
        """Lấy một header ngẫu nhiên từ danh sách"""
        if not self.headers_list:
            return None
        
        random_index = randint(0, len(self.headers_list) - 1)
        return self.headers_list[random_index]
    
    def _scrapeops_fake_browser_headers_enabled(self):
        """Kiểm tra xem tính năng Fake Browser Headers có được kích hoạt hay không"""
        if (self.scrapeops_api_key is None or 
            self.scrapeops_api_key == '' or 
            self.scrapeops_fake_browser_headers_active == False):
            self.scrapeops_fake_browser_headers_active = False
            logging.info("ScrapeOps: Fake browser headers disabled")
        else:
            self.scrapeops_fake_browser_headers_active = True
            logging.info("ScrapeOps: Fake browser headers enabled")
    
    def process_request(self, request, spider):
        """Xử lý mỗi yêu cầu HTTP trước khi gửi đi"""
        if self.scrapeops_fake_browser_headers_active:
            random_browser_header = self._get_random_browser_header()
            if random_browser_header:
                # Cập nhật headers với dữ liệu mới
                headers_to_update = {
                    'accept-language': random_browser_header.get('accept-language', ''),
                    'sec-fetch-user': random_browser_header.get('sec-fetch-user', ''),
                    'sec-fetch-mode': random_browser_header.get('sec-fetch-mode', ''),
                    'sec-fetch-site': random_browser_header.get('sec-fetch-site', ''),
                    'sec-ch-ua-platform': random_browser_header.get('sec-ch-ua-platform', ''),
                    'sec-ch-ua-mobile': random_browser_header.get('sec-ch-ua-mobile', ''),
                    'sec-ch-ua': random_browser_header.get('sec-ch-ua', ''),
                    'accept': random_browser_header.get('accept', ''),
                    'user-agent': random_browser_header.get('user-agent', ''),
                    'upgrade-insecure-requests': random_browser_header.get('upgrade-insecure-requests', ''),
                    'sec-fetch-dest': random_browser_header.get('sec-fetch-dest', ''),
                    'cache-control': random_browser_header.get('cache-control', ''),
                }
                
                # Chỉ set header nếu có giá trị
                for header_name, header_value in headers_to_update.items():
                    if header_value:
                        request.headers[header_name] = header_value
                
                logging.debug("ScrapeOps: New headers applied to request")
        
        return None


class RotateUserAgentMiddleware:
    """Middleware backup để rotate User-Agent"""
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/91.0.864.59',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
        ]
    
    def process_request(self, request, spider):
        # Chỉ set User-Agent nếu chưa có (ScrapeOps chưa set)
        if 'user-agent' not in request.headers:
            ua = self.user_agents[randint(0, len(self.user_agents) - 1)]
            request.headers['User-Agent'] = ua
        return None