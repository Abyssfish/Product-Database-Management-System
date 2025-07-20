import time
import hashlib
import requests
from .base_adapter import BaseAdapter

class PddAdapter(BaseAdapter):
    """拼多多API适配器"""
    platform = "拼多多"

    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = 'https://gw-api.pinduoduo.com/api/router'

    def search_product(self, keyword):
        """使用拼多多API搜索商品"""
        params = {
            'type': 'pdd.ddk.goods.search',
            'client_id': self.client_id,
            'timestamp': int(time.time()),
            'data_type': 'JSON',
            'version': 'V1',
            'sign_method': 'md5',
            'goods_name': keyword,
            'page': 1,
            'page_size': 20
        }

        # 生成签名
        params['sign'] = self._generate_signature(params)

        # 发送请求
        response = requests.post(self.api_url, json=params)
        result = response.json()

        # 解析响应
        if 'error_response' in result:
            raise Exception(f"拼多多API错误: {result['error_response']['error_msg']}")

        products = self._parse_response(result)
        return self._filter_products(products)

    def _generate_signature(self, params):
        """生成拼多多API签名"""
        # 按照ASCII顺序排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        # 拼接参数
        sign_str = self.client_secret
        for k, v in sorted_params:
            sign_str += f'{k}{v}'
        sign_str += self.client_secret
        # MD5加密并转为大写
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest().upper()

    def _parse_response(self, response):
        """解析拼多多API响应"""
        products = []
        if 'goods_search_response' in response:
            goods_list = response['goods_search_response'].get('goods_list', [])
            for product in goods_list:
                products.append({
                    'title': product.get('goods_name', ''),
                    'price': str(product.get('min_group_price', 0) / 100),  # 价格单位转换为元
                    'url': product.get('goods_detail_url', '#'),
                    'image': product.get('goods_thumbnail_url', '')
                })
        return products