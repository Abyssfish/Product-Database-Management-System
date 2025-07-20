import os
import base64
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from aip import AipOcr
from api_adapters.taobao_adapter import TaobaoAdapter
from api_adapters.jd_adapter import JdAdapter
from api_adapters.pdd_adapter import PddAdapter

# 加载环境变量
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

# 初始化百度OCR客户端
ocr_client = AipOcr(
    os.getenv('BAIDU_APP_ID'),
    os.getenv('BAIDU_API_KEY'),
    os.getenv('BAIDU_SECRET_KEY')
)

# 初始化电商平台适配器
adapters = [
    TaobaoAdapter(
        app_key=os.getenv('TAOBAO_APP_KEY'),
        app_secret=os.getenv('TAOBAO_APP_SECRET')
    ),
    JdAdapter(
        app_key=os.getenv('JD_APP_KEY'),
        app_secret=os.getenv('JD_APP_SECRET')
    ),
    PddAdapter(
        client_id=os.getenv('PDD_CLIENT_ID'),
        client_secret=os.getenv('PDD_CLIENT_SECRET')
    )
]

def extract_keywords(image_data):
    """从图片中提取关键词"""
    try:
        # 解码base64图片
        img_data = base64.b64decode(image_data.split(',')[1])
        # 调用百度OCR
        result = ocr_client.general(img_data)
        if 'words_result' in result:
            words = [item['words'] for item in result['words_result']]
            # 简单关键词提取逻辑，实际应用中可优化
            return ' '.join(words)[:100]  # 取前100字符作为关键词
        return ''
    except Exception as e:
        app.logger.error(f"OCR识别失败: {str(e)}")
        return ''

@app.route('/api/ocr', methods=['POST'])
def ocr_handler():
    """处理OCR识别请求"""
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': '缺少图片数据'}), 400

        # 提取关键词
        keyword = extract_keywords(data['image'])
        if not keyword:
            return jsonify({'error': '无法从图片中识别文字'}), 400

        # 调用各平台API搜索商品
        all_products = []
        for adapter in adapters:
            try:
                products = adapter.search_product(keyword)
                all_products.extend(products)
            except Exception as e:
                app.logger.error(f"{adapter.platform}搜索失败: {str(e)}")
                continue

        # 按价格排序
        all_products.sort(key=lambda x: float(x['price']))

        return jsonify({
            'keyword': keyword,
            'products': all_products[:20]  # 最多返回20个结果
        })

    except Exception as e:
        app.logger.error(f"请求处理失败: {str(e)}")
        return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs('api_adapters', exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)