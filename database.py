import sqlite3
import os
from flask import g

DATABASE = 'products.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def close_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    if not os.path.exists(DATABASE):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            # 创建商品表
            cursor.execute('''
            CREATE TABLE products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specifications TEXT,
                unit TEXT,
                quantity INTEGER,
                price REAL NOT NULL,
                amount REAL,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            conn.commit()
            print('数据库初始化成功')

def query_products(keyword):
    db = get_db()
    cursor = db.cursor()
    if keyword:
        cursor.execute('''
            SELECT * FROM products 
            WHERE name LIKE ? OR specifications LIKE ?
            ORDER BY created_at DESC
        ''', (f'%{keyword}%', f'%{keyword}%'))
    else:
        cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
    return [dict(row) for row in cursor.fetchall()]

def add_product(product_data):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO products (name, specifications, unit, quantity, price, amount, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        product_data['name'],
        product_data.get('specifications', ''),
        product_data.get('unit', ''),
        # 将quantity转换为整数
        int(product_data.get('quantity', 1)),
        # 将price转换为浮点数
        float(product_data['price']),
        # 计算金额时确保数值类型
        float(product_data.get('amount', float(product_data['price']) * int(product_data.get('quantity', 1)))),
        product_data.get('image_url', '')
    ))
    db.commit()
    return cursor.lastrowid

def update_product(product_id, product_data):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        UPDATE products SET name=?, specifications=?, unit=?, quantity=?, price=?, amount=?, image_url=?
        WHERE id=?
    ''', (
        product_data['name'],
        product_data.get('specifications', ''),
        product_data.get('unit', ''),
        int(product_data.get('quantity', 1)),
        float(product_data['price']),
        float(product_data.get('amount', float(product_data['price']) * int(product_data.get('quantity', 1)))),
        product_data.get('image_url', ''),
        product_id
    ))
    db.commit()
    return cursor.rowcount > 0

def get_product_by_id(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
    product = cursor.fetchone()
    if product:
        columns = ['id', 'name', 'specifications', 'unit', 'quantity', 'price', 'amount', 'image_url', 'created_at']
        return dict(zip(columns, product))
    return None

def delete_product(product_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
    db.commit()
    return cursor.rowcount > 0