# -*- coding: utf-8 -*-
import sqlite3
conn = sqlite3.connect('tushen.db')
c = conn.cursor()
c.execute('SELECT id, phone, real_name, is_admin, is_reviewer FROM users WHERE phone IN ("13800000000", "13900000000")')
print('用户列表:', c.fetchall())
conn.close()
