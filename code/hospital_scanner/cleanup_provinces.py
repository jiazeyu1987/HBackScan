#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import json

def cleanup_provinces():
    """清理省份数据中的JSON格式"""
    db_path = 'data/hospital_scanner_new.db'

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print('=== 清理JSON格式数据 ===')

        # 删除所有JSON格式的省份记录
        cursor.execute('DELETE FROM provinces WHERE name LIKE "{%"')
        deleted_count = cursor.rowcount
        print(f'删除了 {deleted_count} 条JSON格式的省份记录')

        # 查看剩余数据
        cursor.execute('SELECT COUNT(*) FROM provinces')
        total_count = cursor.fetchone()[0]
        print(f'剩余省份数量: {total_count}')

        # 显示前10个省份样本
        cursor.execute('SELECT id, name FROM provinces LIMIT 10')
        print('\n=== 剩余省份样本 ===')
        for row in cursor.fetchall():
            print(f'ID: {row[0]}, Name: "{row[1]}"')

        conn.commit()
        conn.close()

        print('数据清理完成！')
        return True

    except Exception as e:
        print(f'清理失败: {e}')
        return False

if __name__ == "__main__":
    cleanup_provinces()