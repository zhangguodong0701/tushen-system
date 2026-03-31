# -*- coding: utf-8 -*-
"""手动创建审核员账号"""
import sqlite3
from passlib.hash import bcrypt

conn = sqlite3.connect('tushen.db')
c = conn.cursor()

# 检查是否已有审核员
c.execute('SELECT id FROM users WHERE phone = "13900000000"')
if c.fetchone():
    print('审核员账号已存在')
else:
    hashed = bcrypt.hash('reviewer123')
    c.execute('''INSERT INTO users (phone, email, hashed_password, real_name, user_type, status, is_reviewer, company_name)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
               ('13900000000', 'reviewer@tushen.com', hashed, '平台审核员', '设计师', '通过', 1, '图审平台'))
    conn.commit()
    print('审核员账号创建成功！')

# 显示所有用户
c.execute('SELECT id, phone, real_name, is_admin, is_reviewer FROM users')
print('所有用户:', c.fetchall())
conn.close()
