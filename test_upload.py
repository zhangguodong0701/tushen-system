# 测试图纸上传
import requests
import json

API = 'http://localhost:8000/api'

# 登录获取token (OAuth2PasswordRequestForm格式)
r = requests.post(API + '/auth/login', data={'username':'13800000000','password':'admin123'})
print('登录响应:', r.status_code)
data = r.json()
if r.status_code != 200:
    print('登录失败:', data)
    exit(1)
token = data.get('access_token', '')
print('Token:', token[:20] + '...' if token else 'None')
headers = {'Authorization': 'Bearer ' + token}

# 直接测试上传API到已完成订单#8
order_id = 8
print('\n直接测试上传图纸到订单#%d...' % order_id)
# 使用实际存在的文件
test_file = 'backend/uploads'
import os
files_list = os.listdir(test_file) if os.path.exists(test_file) else []
print('uploads目录文件:', files_list[:5])
if files_list:
    with open(os.path.join(test_file, files_list[0]), 'rb') as f:
        files = {'file': ('test.dwg', f, 'application/octet-stream')}
        data = {'version': 'V1'}
        r = requests.post(API + '/orders/' + str(order_id) + '/drawings',
                        headers=headers,
                        files=files, data=data)
        print('上传响应: %d' % r.status_code)
        print('响应内容:', r.json())

# 查询图纸
drawings = requests.get(API + '/orders/' + str(order_id) + '/drawings').json()
print('订单图纸: %d 个' % len(drawings))
for d in drawings:
    print('  - %s (%s)' % (d['filename'], d['version']))
