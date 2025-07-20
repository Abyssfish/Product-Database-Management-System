from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    """电商平台API适配器基类"""
    platform = "未知平台"

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def search_product(self, keyword):
        """
        根据关键词搜索商品
        :param keyword: 搜索关键词
        :return: 商品列表，每个商品包含platform, title, price, url等字段
        """
        pass

    @abstractmethod
    def _generate_signature(self, params):
        """生成API请求签名"""
        pass

    def _parse_response(self, response):
        """解析API响应，子类可重写"""
        return response

    def _filter_products(self, products):
        """过滤和标准化商品数据"""
        filtered = []
        for product in products:
            # 基础过滤逻辑，子类可扩展
            if not product.get('price') or not product.get('title'):
                continue
            filtered.append({
                'platform': self.platform,
                'title': product.get('title', ''),
                'price': product.get('price', '0'),
                'url': product.get('url', '#'),
                'image': product.get('image', '')
            })
        return filtered