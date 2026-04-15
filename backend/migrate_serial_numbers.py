"""
migrate_serial_numbers.py - 存量数据流水号迁移脚本

功能：
  1. 为 users/demands/orders/disputes/quotes 表添加 serial_number 列（如尚不存在）
  2. 为现有记录生成统一格式流水号：PREFIX-YYYYMMDD-XXXX

执行方式：
  cd tushen-system/backend
  python migrate_serial_numbers.py

说明：
  - 会检测现有最大 ID，保证新增流水号不与已有流水号冲突
  - 使用 getattr + getattr(d, 'serial_number', None) 兼容新旧字段
  - 幂等执行：已有流水号的记录跳过，不会重复生成
"""

import os
import sys
import random
import string
import sqlite3
from datetime import datetime

# ---------- 配置 ----------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///./tushen.db")

# 从 DATABASE_URL 解析路径（支持 mysql:// 和 sqlite:/// 两种格式）
if DB_PATH.startswith("mysql"):
    print("[SKIP] MySQL 数据库请手动执行 ALTER TABLE 添加列，然后使用 MySQL 客户端生成流水号")
    sys.exit(0)
else:
    # sqlite:///./tushen.db -> ./tushen.db
    DB_PATH = DB_PATH.replace("sqlite:///", "")

DB_PATH = os.path.join(BASE_DIR, DB_PATH)
print(f"数据库路径: {DB_PATH}")

# ---------- 工具函数 ----------
def generate_serial_number(prefix: str, existing: set) -> str:
    """生成唯一流水号，避免与已有流水号冲突"""
    date_part = datetime.utcnow().strftime("%Y%m%d")
    chars = string.ascii_uppercase + string.digits
    chars = chars.replace('I', '').replace('O', '')
    for _ in range(100):
        random_part = ''.join(random.choices(chars, k=4))
        sn = f"{prefix}-{date_part}-{random_part}"
        if sn not in existing:
            return sn
    raise RuntimeError(f"无法为前缀 {prefix} 生成唯一流水号（已尝试100次）")


def column_exists(cursor, table: str, column: str) -> bool:
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def add_column(cursor, table: str, column: str, col_type: str = "TEXT"):
    """安全添加列（SQLite 不支持 IF NOT EXISTS）"""
    if not column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"  [+ 新增列] {table}.{column}")


def get_existing(cursor, table: str, column: str) -> set:
    """获取某列已有值（非空）"""
    try:
        cursor.execute(f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL AND {column} != ''")
        return {row[0] for row in cursor.fetchall()}
    except sqlite3.OperationalError:
        return set()


def migrate_table(cursor, table: str, prefix: str, id_column: str = "id"):
    """迁移单个表：生成缺失的流水号"""
    # 确保列存在
    add_column(cursor, table, "serial_number", "TEXT")

    # 获取已有流水号（用于去重）
    existing = get_existing(cursor, table, "serial_number")

    # 查询需要补号的记录
    cursor.execute(f"SELECT {id_column} FROM {table} WHERE serial_number IS NULL OR serial_number = ''")
    rows = cursor.fetchall()

    if not rows:
        print(f"  [* {table}] 全部记录已有流水号，无需迁移")
        return

    updated = 0
    for (row_id,) in rows:
        new_sn = generate_serial_number(prefix, existing)
        existing.add(new_sn)  # 防止同批次生成重复
        cursor.execute(f"UPDATE {table} SET serial_number = ? WHERE {id_column} = ?", (new_sn, row_id))
        updated += 1

    print(f"  [OK {table}] 已为 {updated} 条记录生成流水号")
    return updated


# ---------- 主逻辑 ----------
def main():
    print("=" * 50)
    print("图审云平台 - 存量数据流水号迁移")
    print(f"执行时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    if not os.path.exists(DB_PATH):
        print(f"[ERROR] 数据库文件不存在: {DB_PATH}")
        print("提示：请确认后端已启动过，或当前工作目录是否正确")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 逐表迁移
    total_updated = 0
    total_updated += migrate_table(cursor, "users",      "U") or 0
    total_updated += migrate_table(cursor, "demands",    "D") or 0
    total_updated += migrate_table(cursor, "quotes",     "Q") or 0
    total_updated += migrate_table(cursor, "orders",     "O") or 0
    total_updated += migrate_table(cursor, "disputes",    "J") or 0

    conn.commit()

    # 打印样本
    print("\n" + "-" * 50)
    print("生成样本（每表前3条）：")
    for table, prefix in [("users", "U"), ("demands", "D"), ("quotes", "Q"), ("orders", "O"), ("disputes", "J")]:
        try:
            cursor.execute(f"SELECT serial_number FROM {table} WHERE serial_number IS NOT NULL LIMIT 3")
            rows = [r[0] for r in cursor.fetchall()]
            if rows:
                print(f"  {table}: {rows}")
            else:
                print(f"  {table}: (空)")
        except Exception as e:
            print(f"  {table}: 查询失败 - {e}")

    conn.close()

    print("\n" + "=" * 50)
    print(f"迁移完成！共更新 {total_updated} 条记录")
    print("=" * 50)


if __name__ == "__main__":
    main()
