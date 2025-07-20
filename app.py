import os
import base64
import json
import datetime
from flask import Flask, request, jsonify
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.exceptions import HTTPException
from flask_cors import CORS
from dotenv import load_dotenv
from aip import AipOcr
from api_adapters.taobao_adapter import TaobaoAdapter
from api_adapters.jd_adapter import JdAdapter
from api_adapters.pdd_adapter import PddAdapter
from database import init_db, get_db, close_db, add_product, query_products, delete_product, get_product_by_id, update_product

# 加载环境变量
load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': '资源未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    try:
        db = get_db()
        db.rollback()  # 回滚未提交的事务
    except Exception as e:
        app.logger.error(f'回滚事务失败: {str(e)}')
    return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(400)
def bad_request_error(error):
    return jsonify({'error': '请求参数错误'}), 400

@app.errorhandler(HTTPException)
def handle_http_exception(error):
    response = {
        'error': error.description,
        'status_code': error.code
    }
    return jsonify(response), error.code

@app.errorhandler(Exception)
def handle_general_exception(error):
    app.logger.error(f'未捕获的异常: {str(error)}')
    return jsonify({
        'error': '服务器内部错误',
        'details': str(error)
    }), 500

# 初始化数据库
init_db()

# 关闭数据库连接
app.teardown_appcontext(close_db)

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

# 添加关键词搜索接口
### 1. 确认接口是否已添加

@app.route('/api/search', methods=['POST'])
def search_handler():
    """处理关键词搜索请求"""
    try:
        data = request.get_json()
        if not data or 'keyword' not in data:
            return jsonify({'error': '缺少搜索关键词'}), 400
        
        # 添加商品搜索逻辑
        keyword = data['keyword']
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
        app.logger.error(f'搜索商品失败: {str(e)}')
        return jsonify({'error': str(e)}), 500
        
@app.route('/api/add_product', methods=['POST'])
def handle_add_product():
    """添加商品到数据库"""
    try:
        # 获取表单数据
        name = request.form.get('name')
        price = request.form.get('price')
        
        # 验证必填字段
        if not name or not price:
            return jsonify({'error': '商品名称和单价为必填项'}), 400
        
        # 处理图片上传
        image_url = ''
        image = request.files.get('image')
        if image and image.filename:
            # 确保images目录存在
            images_dir = os.path.join(app.static_folder, 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # 生成唯一文件名
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            filename = secure_filename(image.filename)
            unique_filename = f"{timestamp}_{filename}"
            image_path = os.path.join(images_dir, unique_filename)
            
            # 保存图片
            image.save(image_path)
            image_url = f'images/{unique_filename}'
        
        # 构建商品数据
        product_data = {
            'name': name,
            'specifications': request.form.get('specifications', ''),
            'unit': request.form.get('unit', '个'),
            'quantity': request.form.get('quantity', 1),
            'price': price,
            'amount': request.form.get('amount', 0),
            'image_url': image_url
        }
        
        product_id = add_product(product_data)
        return jsonify({'success': True, 'product_id': product_id})
    except Exception as e:
        app.logger.error(f'添加商品失败: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_products', methods=['GET'])
def handle_search_products():
    """搜索数据库中的商品"""
    try:
        keyword = request.args.get('keyword', '')
        products = query_products(keyword)
        return jsonify(products)
    except Exception as e:
        app.logger.error(f'搜索商品失败: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_product/<int:product_id>', methods=['PUT'])
def handle_update_product(product_id):
    """更新数据库中的商品"""
    try:
        # 获取表单数据
        product_data = request.form.to_dict()
        if not product_data or 'name' not in product_data or 'price' not in product_data:
            return jsonify({'error': '商品名称和单价为必填项'}), 400
        
        # 转换数值类型
        if 'quantity' in product_data and product_data['quantity']:
            product_data['quantity'] = int(product_data['quantity'])
        if 'price' in product_data and product_data['price']:
            product_data['price'] = float(product_data['price'])
        if 'amount' in product_data and product_data['amount']:
            product_data['amount'] = float(product_data['amount'])
        
        # 处理图片上传
        image_url = product_data.get('image_url', '')
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            if image.filename == '':
                return jsonify({'error': '未选择图片'}), 400
            
            # 生成唯一文件名
            filename = secure_filename(image.filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            unique_filename = f'{timestamp}_{filename}'
            
            # 保存图片
            images_dir = os.path.join(app.static_folder, 'images')
            os.makedirs(images_dir, exist_ok=True)
            image_path = os.path.join(images_dir, unique_filename)
            image.save(image_path)
            
            # 更新图片URL
            product_data['image_url'] = f'images/{unique_filename}'
            
            # 删除旧图片
            if image_url:
                old_image_path = os.path.join(app.static_folder, image_url)
                if os.path.exists(old_image_path):
                    try:
                        os.remove(old_image_path)
                        app.logger.info(f'旧图片已删除: {old_image_path}')
                    except Exception as e:
                        app.logger.error(f'删除旧图片失败: {str(e)}')
        
        success = update_product(product_id, product_data)
        return jsonify({'success': success})
    except Exception as e:
        app.logger.error(f'更新商品失败: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_product/<int:product_id>', methods=['DELETE'])
def handle_delete_product(product_id):
    """从数据库中删除商品及关联图片"""
    try:
        # 获取商品信息
        product = get_product_by_id(product_id)
        if not product:
            return jsonify({'error': '商品不存在'}), 404

        # 删除关联图片
        if product.get('image_url'):
            image_path = os.path.join(app.static_folder, product['image_url'])
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    app.logger.info(f'图片已删除: {image_path}')
                except Exception as e:
                    app.logger.error(f'删除图片失败: {str(e)}')

        # 删除商品记录
        success = delete_product(product_id)
        return jsonify({'success': success})
    except Exception as e:
        app.logger.error(f'删除商品失败: {str(e)}')
        return jsonify({'error': str(e)}), 500

# // 删除从这里开始的重复代码
# // @app.route('/api/search', methods=['POST'])
# // def search_handler():
# //     """处理关键词搜索请求"""
# //     try:
# //         data = request.get_json()
# //         if not data or 'keyword' not in data:
# //             return jsonify({'error': '缺少搜索关键词'}), 400
# //
# //         keyword = data['keyword'].strip()
# //         if not keyword:
# //             return jsonify({'error': '搜索关键词不能为空'}), 400
# //
# //         # 调用各平台API搜索商品
# //         all_products = []
# //         for adapter in adapters:
# //             try:
# //                 products = adapter.search_product(keyword)
# //                 all_products.extend(products)
# //             except Exception as e:
# //                 app.logger.error(f"{adapter.platform}搜索失败: {str(e)}")
# //                 continue
# //
# //         # 按价格排序
# //         all_products.sort(key=lambda x: float(x['price']))
# //
# //         return jsonify({
# //             'keyword': keyword,
# //             'products': all_products[:20]  # 返回前20个结果
# //         })
# //
# //     except Exception as e:
# //         app.logger.error(f"请求处理失败: {str(e)}")
# //         return jsonify({'error': '服务器内部错误'}), 500
# //


if __name__ == '__main__':
    # 创建必要的目录
    os.makedirs('api_adapters', exist_ok=True)
    # 启用HTTPS
    # app.run(host='0.0.0.0', port=5000, ssl_context=('cert.pem', 'key.pem'), debug=True, use_reloader=False)
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)