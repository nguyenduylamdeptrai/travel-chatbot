import scrapy
import os

class Mainspider(scrapy.Spider):
    name = "mainspider"
    allowed_domains = ["csdl.vietnamtourism.gov.vn"]
    start_urls = ["https://csdl.vietnamtourism.gov.vn/cslt"]

    custom_settings = {
        'FEEDS': {
            '../../../data/travel_data_1.jsonl': {
                'format': 'jsonlines',
                'overwrite': True
            }
        }
    }

    travel_cnt = 0
    valid_detail_travel = 0

    def parse(self, response):
        # Tìm tất cả các items du lịch
        travels = response.css('div.verticle-listing-caption')
        
        for travel in travels:
            self.travel_cnt += 1
            
            # Lấy thông tin cơ bản
            name = travel.css('h4 a::text').get()
            url = travel.css('h4 a::attr(href)').get()
            address = travel.css('span.d-block::text').get()
            
            print(f"Found item: {name} at {url}")
            
            if url:
                self.valid_detail_travel += 1
                # Theo dõi URL để lấy thông tin chi tiết
                yield response.follow(url, self.parse_travel)

        # Tìm trang tiếp theo dựa vào thẻ active và li kế tiếp
        active_li = response.css('ul.pagination li.page-item.active')
        next_li = active_li.xpath('following-sibling::li[1]')
        next_page = next_li.css('a::attr(href)').get()
        if next_page and next_page != '#':
            # Tạo url tuyệt đối nếu cần
            print(f"Next page found: {next_page}")
            yield response.follow(next_page, self.parse)

    def parse_travel(self, response):
        # Debug: Print the URL being processed
        print("*"*20)
        print(f"Processing URL: {response.url}")
        
        detail = response.css('div.cslt-detail')
        content_details = response.css('div.content-detail')
        
        name = detail.css('h4 a::text').get()
        
        address = ''.join(detail.css('span.d-block *::text, span.d-block::text').getall()).strip()
        content = []
        for div in content_details:
            direct_texts = [
                text.strip() for text in div.xpath('.//text()[not(parent::p)]').getall()
                if text.strip() and text.strip() != '&nbsp;'
            ]
            
            p_texts = [
                text.strip() for text in div.css('p::text, p *::text').getall()
                if text.strip() and text.strip() != '&nbsp;'
            ]
            
            content.extend(direct_texts + p_texts)
        
        content = [text for text in content if text and not text.isspace()]

        yield {
            'url': response.url,
            'name': name,
            'content': content,
            'address': address
        }