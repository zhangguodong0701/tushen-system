# -*- coding: utf-8 -*-
"""数据库更新脚本 - 添加缺失的字段"""
import sqlite3
import sys

def update_database():
    conn = sqlite3.connect('tushen.db')
    c = conn.cursor()
    
    # 检查users表结构
    c.execute('PRAGMA table_info(users)')
    cols = [row[1] for row in c.fetchall()]
    print('当前users表字段:', cols)
    
    # 添加缺失字段
    new_fields = [
        ('auth_type', 'TEXT DEFAULT \'none\''),
        ('id_card_front', 'TEXT'),
        ('id_card_back', 'TEXT'),
        ('business_license', 'TEXT'),
        ('is_blacklisted', 'INTEGER DEFAULT 0'),
        ('is_reviewer', 'INTEGER DEFAULT 0'),  # 审核员/客服标记
        ('id_card_number', 'TEXT'),
        ('company_name', 'TEXT'),
    ]
    for field, dtype in new_fields:
        if field not in cols:
            try:
                c.execute(f'ALTER TABLE users ADD COLUMN {field} {dtype}')
                print(f'添加字段: {field}')
            except Exception as e:
                print(f'添加 {field} 失败: {e}')
    
    conn.commit()
    
    # 检查orders表
    c.execute('PRAGMA table_info(orders)')
    order_cols = [row[1] for row in c.fetchall()]
    print('\n当前orders表字段:', order_cols)
    
    if 'escrow_status' not in order_cols:
        c.execute('ALTER TABLE orders ADD COLUMN escrow_status TEXT DEFAULT \'未托管\'')
        print('添加字段: escrow_status')
    
    # 检查demands表
    c.execute('PRAGMA table_info(demands)')
    demand_cols = [row[1] for row in c.fetchall()]
    print('\n当前demands表字段:', demand_cols)
    
    if 'payment_phases' not in demand_cols:
        c.execute('ALTER TABLE demands ADD COLUMN payment_phases TEXT')
        print('添加字段: payment_phases')
    
    if 'filename' not in demand_cols:
        c.execute('ALTER TABLE demands ADD COLUMN filename TEXT')
        print('添加字段: filename')
    
    # 检查disputes表
    c.execute('PRAGMA table_info(disputes)')
    dispute_cols = [row[1] for row in c.fetchall()]
    print('\n当前disputes表字段:', dispute_cols)
    
    if 'evidence_files' not in dispute_cols:
        c.execute('ALTER TABLE disputes ADD COLUMN evidence_files TEXT')
        print('添加字段: evidence_files')
    
    # 检查drawings表
    c.execute('PRAGMA table_info(drawings)')
    drawing_cols = [row[1] for row in c.fetchall()]
    print('\n当前drawings表字段:', drawing_cols)
    
    if 'comment_images' not in drawing_cols:
        c.execute('ALTER TABLE drawings ADD COLUMN comment_images TEXT')
        print('添加字段: comment_images')
    
    # 检查是否有payment_phases表
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payment_phases'")
    if not c.fetchone():
        c.execute('''
            CREATE TABLE payment_phases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                name TEXT,
                amount REAL,
                status TEXT DEFAULT '待验收',
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        print('创建表: payment_phases')
    
    # 检查是否有fund_records表
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='fund_records'")
    if not c.fetchone():
        c.execute('''
            CREATE TABLE fund_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                direction TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print('创建表: fund_records')
    
    # 检查是否有operation_logs表
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='operation_logs'")
    if not c.fetchone():
        c.execute('''
            CREATE TABLE operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                target_type TEXT,
                target_id INTEGER,
                detail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print('创建表: operation_logs')
    
    # 检查是否有feedbacks表
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feedbacks'")
    if not c.fetchone():
        c.execute('''
            CREATE TABLE feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                content TEXT,
                contact TEXT,
                status TEXT DEFAULT '待处理',
                reply TEXT,
                replied_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        print('创建表: feedbacks')
    
    conn.commit()
    conn.close()
    print('\n数据库更新完成！')

if __name__ == '__main__':
    update_database()
