# encoding= utf-8
# __author__= gary
import sys
import json
import requests
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
import pymysql


class Product:
    def __init__(self, model, name, record):
        self.model = model
        self.name = name
        self.record = record

    @staticmethod
    def insert_product(model, name, record):
        try:
            connection = pymysql.connect(
                host='192.192.10.10',
                port=3306,
                user='root',  # 数据库用户名
                passwd='root',  # 密码
                charset='utf8',
                db='test_tool'
            )
            
            cursor = connection.cursor()
            insert_query = "INSERT INTO records (model, name, record) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (model, name, record))
            connection.commit()
        
        except pymysql.MySQLError as err:
            print(f"Database Error: {err}")
        
        finally:
            if connection:
                cursor.close()
                connection.close()

    @staticmethod
    def load_records():
        try:
            connection = pymysql.connect(
                host='192.192.10.10',
                port=3306,
                user='root',  # 数据库用户名
                passwd='root',  # 密码
                charset='utf8',
                db='test_tool'
            )
            with connection.cursor() as cursor:
                sql = "SELECT model, name, record  FROM records"
                cursor.execute(sql)
                records = cursor.fetchall()

                # Populate the combo box with names
                for record in records:
                    print(record)

                # # Store records for later use
                # self.records = {record['name']: record['info'] for record in records}
        except Exception as e:
            print(e)


if __name__ == "__main__":
    # product = Product("CS-86TG", "调光开关", "还在测试中")
    # Product.insert_product("CS-86TG", "调光开关", "testing")
    Product.load_records()
