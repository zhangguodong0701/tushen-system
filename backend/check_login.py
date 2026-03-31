# -*- coding: utf-8 -*-
"""检查用户登录状态"""
import sqlite3
conn = sqlite3.connect('tushen.db')
c = conn.cursor()

# 检查管理员和审核员账号状态
c.execute('SELECT id, phone, real_name, status, is_admin, is_reviewer, created_at FROM users WHERE phone IN ("13800000000", "13900000000")')
users = c.fetchall()
print("管理员/审核员账号状态:")
for u in users:
    print(f"  ID: {u[0]}, 手机: {u[1]}, 姓名: {u[2]}, 状态: {u[3]}, 是否管理员: {u[4]}, 是否审核员: {u[5]}, 创建时间: {u[6]}")

conn.close()
