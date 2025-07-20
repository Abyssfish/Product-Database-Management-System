import time
import hashlib
import requests
from .base_adapter import BaseAdapter

class JdAdapter(BaseAdapter):
    """京东API适配器"""
    platform = "京东"

    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.api_url = 'https://api.jd.com/routerjson'

    def search_product(self, keyword):
        """使用京东API搜索商品"""
        params = {
            'method': 'jingdong.service.promotion.search',
            'app_key': self.app_key,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'format': 'json',
            'v': '1.0',
            'sign_method': 'md5',
            'keyword': keyword,
            'page_index': 1,
            'page_size': 20
        }

        # 生成签名
        params['sign'] = self._generate_signature(params)

        # 发送请求
        response = requests.post(self.api_url, data=params)
        result = response.json()

        # 解析响应
        if 'error_response' in result:
            raise Exception(f"京东API错误: {result['error_response']['zh_desc']}")

        products = self._parse_response(result)
        return self._filter_products(products)

    def _generate_signature(self, params):
        """生成京东API签名"""
        # 按照ASCII顺序排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接参数
        sign_str = self.app_secret
        for k, v in sorted_params:
            sign_str += f'{k}{v}'
        sign_str += self.app_secret
        # MD5加密并转为大写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _parse_response(self, response):
        """解析京东API响应"""
        products = []
        # 根据京东API实际返回结构调整解析逻辑
        if 'jingdong_service_promotion_search_responce' in response:
            result = response['jingdong_service_promotion_search_responce'].get('result', {})
            if 'data' in result:
                for product in result['data']:
                    products.append({
                        'title': product.get('sku_name', ''),
                        'price': product.get('price', '0'),
                        'url': product.get('material_url', '#'),
                        'image': product.get('image_url', '')
                    })
        return products