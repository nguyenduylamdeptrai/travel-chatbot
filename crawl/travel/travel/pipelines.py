import scrapy
from scrapy.exceptions import DropItem
import re
from datetime import datetime

class VietnamTourismPipeline:
    def __init__(self):
        self.items_count = 0
    
    def process_item(self, item, spider):
        self.items_count += 1
        
        # Làm sạch dữ liệu
        if item.get('name'):
            item['name'] = item['name'].strip().lower()
        
        if item.get('address'):
            # Xử lý địa chỉ để chỉ giữ lại tỉnh
            cleaned_address = self._extract_province_from_address(item['address'])
            item['address'] = cleaned_address.lower()
        
        if item.get('content') and isinstance(item['content'], list):
            item['content'] = [text.strip().lower() for text in item['content'] if text.strip()]
        
        # Thêm timestamp
        item['scraped_at'] = datetime.now().isoformat()
        
        spider.logger.info(f"Processed item {self.items_count}: {item.get('name', '')}")
        
        return item
    
    def _extract_province_from_address(self, address):
        """
        Trích xuất tỉnh từ địa chỉ đầy đủ
        Ví dụ: "Địa chỉ: Khu 1A, Phường Quang Hanh, thành phố Cẩm Phả, Phường Quang Hanh, Thành phố Cẩm Phả, Quảng Ninh"
        -> "Quảng Ninh"
        """
        if not address:
            return ""
        
        # Loại bỏ prefix "Địa chỉ:" nếu có
        address = re.sub(r'^Địa chỉ:\s*', '', address.strip())
        
        # Tách địa chỉ thành các phần bằng dấu phẩy
        parts = [part.strip() for part in address.split(',')]
        
        if not parts:
            return ""
        
        # Lấy phần cuối cùng (thường là tỉnh)
        province = parts[-1].strip()
        
        # Loại bỏ các từ khóa phổ biến không cần thiết
        province = re.sub(r'^(tỉnh|thành phố)\s+', '', province, flags=re.IGNORECASE)
        
        return province
    
    def close_spider(self, spider):
        spider.logger.info(f"Spider closed. Total items processed: {self.items_count}")