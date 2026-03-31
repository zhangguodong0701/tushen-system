"""
数据库更新脚本 - 添加 PaymentPhase 新字段
运行方式: python update_db_phases.py
"""
import sqlite3
import os

def update_database():
    db_path = os.path.join(os.path.dirname(__file__), "tushen.db")
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查 payment_phases 表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payment_phases'")
    if not cursor.fetchone():
        print("Table 'payment_phases' does not exist, skipping")
        conn.close()
        return
    
    # 添加 ratio 字段
    try:
        cursor.execute("ALTER TABLE payment_phases ADD COLUMN ratio INTEGER DEFAULT 0")
        print("[OK] Added 'ratio' column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("[SKIP] 'ratio' column already exists")
        else:
            print(f"[ERROR] Failed to add 'ratio' column: {e}")
    
    # 添加 phase_order 字段
    try:
        cursor.execute("ALTER TABLE payment_phases ADD COLUMN phase_order INTEGER DEFAULT 0")
        print("[OK] Added 'phase_order' column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("[SKIP] 'phase_order' column already exists")
        else:
            print(f"[ERROR] Failed to add 'phase_order' column: {e}")
    
    # 为现有记录设置默认值（按创建顺序设置 phase_order）
    cursor.execute("SELECT id FROM payment_phases ORDER BY created_at")
    rows = cursor.fetchall()
    for idx, (row_id,) in enumerate(rows, 1):
        cursor.execute("UPDATE payment_phases SET phase_order = ? WHERE id = ?", (idx, row_id))
    print(f"[OK] Set phase_order for {len(rows)} existing records")
    
    conn.commit()
    conn.close()
    print("Database update completed!")

if __name__ == "__main__":
    update_database()
