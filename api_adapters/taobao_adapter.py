import time
import hashlib
import requests
from .base_adapter import BaseAdapter
from dotenv import load_dotenv
import os

load_dotenv()

class TaobaoAdapter(BaseAdapter):
    """淘宝API适配器"""
    platform = "淘宝"

    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.api_url = 'https://eco.taobao.com/router/rest'

    def search_product(self, keyword):
        """使用淘宝API搜索商品"""
        params = {
            'method': 'taobao.tbk.item.search',  # 更换为淘宝客商品搜索接口
            'app_key': self.app_key,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'format': 'json',
            'v': '2.0',
            'sign_method': 'md5',
            'q': keyword,
            'page_no': 1,
            'page_size': 20,
            'platform': 1  # 添加平台参数（1=PC，2=无线）
        }

    def _parse_response(self, response):
        """解析淘宝API响应"""
        products = []
        if 'tbk_item_search_response' in response and 'results' in response['tbk_item_search_response']:
            for item in response['tbk_item_search_response']['results']['n_tbk_item']:
                products.append({
                    'title': item.get('title', ''),
                    'price': item.get('zk_final_price', '0'),
                    'url': f'https://item.taobao.com/item.htm?id={item.get("num_iid")}',
                    'image': item.get('pict_url', '')
                })
        return products

        # 生成签名
        params['sign'] = self._generate_signature(params)

        # 发送请求
        response = requests.get(self.api_url, params=params)
        result = response.json()

        # 解析响应
        if 'error_response' in result:
            raise Exception(f"淘宝API错误: {result['error_response']['msg']}")

        products = self._parse_response(result)
        return self._filter_products(products)

    def _generate_signature(self, params):
        """生成淘宝API签名"""
        # 按照ASCII顺序排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接参数
        sign_str = self.app_secret
        for k, v in sorted_params:
            sign_str += f'{k}{v}'
        sign_str += self.app_secret
        # MD5加密并转为大写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()