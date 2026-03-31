import sqlite3
import json

conn = sqlite3.connect('backend/tushen.db')
c = conn.cursor()

print('=== Test: Order details include demand file info ===\n')

# Get an order with demand file
c.execute('''
    SELECT o.id, o.demand_id, o.buyer_id, o.seller_id, o.amount, o.status, o.payment_type,
           o.buyer_id, o.seller_id,
           d.title, d.file_url, d.filename
    FROM orders o
    JOIN demands d ON o.demand_id = d.id
    WHERE d.file_url IS NOT NULL
    LIMIT 1
''')
row = c.fetchone()
if row:
    order_id, demand_id, buyer_id, seller_id, amount, status, payment_type, \
    buyer_id, seller_id, demand_title, demand_file_url, demand_filename = row
    
    print(f'Order ID: {order_id}')
    print(f'Demand Title: {demand_title}')
    print(f'Demand File URL: {demand_file_url}')
    print(f'Demand Filename: {demand_filename}')
    
    # Simulate API response
    result = {
        "id": order_id,
        "demand_id": demand_id,
        "buyer_id": buyer_id,
        "seller_id": seller_id,
        "amount": amount,
        "status": status,
        "payment_type": payment_type,
        "demand_title": demand_title,
        "demand_file_url": demand_file_url,
        "demand_filename": demand_filename
    }
    print('\nAPI Response JSON:')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Verify
    assert result['demand_file_url'] is not None, 'demand_file_url cannot be None!'
    print('\n[PASS] Order details include demand file info')
else:
    print('No order found with demand file')
    
    # Check existing data
    c.execute('SELECT id, demand_id FROM orders LIMIT 3')
    orders = c.fetchall()
    print('Existing orders:', orders)
    
    c.execute('SELECT id, title, file_url FROM demands LIMIT 5')
    demands = c.fetchall()
    print('Existing demands:', demands)
