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

    def _generate_signature(self, params):
        """生成京东API签名"""
        # 按照参数名ASCII码从小到大排序
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接参数为key=value形式
        sign_str = self.app_secret + ''.join([f'{k}{v}' for k, v in sorted_params]) + self.app_secret
        # MD5加密并转为大写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def search_product(self, keyword):
        """使用京东API搜索商品"""
        params = {
            'method': 'jingdong.ware.search',  # 更换为商品搜索接口<mcreference link="https://open.jd.com/v2/#/doc/guide?listId=533）" index="0">0</mcreference>
            'app_key': self.app_key,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'format': 'json',
            'v': '1.0',
            'sign_method': 'md5',
            'keyword': keyword,
            'page': 1,  # 参数名修正为page
            'page_size': 20
        }
        # 生成签名
        params['sign'] = self._generate_signature(params)
        # 发送POST请求
        response = requests.post(self.api_url, data=params)
        # 解析响应
        return self._parse_response(response.json())

    def _parse_response(self, response):
        """解析京东API响应"""
        products = []
        if 'ware_search_response' in response:
            result = response['ware_search_response'].get('ware_info', {})
            if 'ware_list' in result:
                for product in result['ware_list']:
                    products.append({
                        'title': product.get('ware_name', ''),
                        'price': product.get('jd_price', '0'),
                        'url': f'https://item.jd.com/{product.get("ware_id")}.html',
                        'image': product.get('image_url', '')
                    })
        return products