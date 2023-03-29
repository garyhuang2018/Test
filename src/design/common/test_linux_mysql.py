# encoding= utf-8
# __author__= gary

import pymysql.cursors

# 连接数据库
connect = pymysql.Connect(
    host='192.192.10.10',
    port=3306,
    user='root',  # 数据库用户名
    passwd='root',  # 密码
    charset='utf8',
    db='test_tool'
)

# 获取游标
cursor = connect.cursor()

# 执行SQL查询
cursor.execute("SELECT VERSION()")

cursor.execute("""create table if not exists reboot_test_result(
                    id int primary key auto_increment not null,
                    tester varchar(32) not null,
                    test_device varchar(32) not null,
                    test_id varchar(128) not null,
                    start_time datetime,
                    end_time datetime,
                    test_result varchar(128) not null)
                    engine=InnoDB default charset=utf8
                """)
# 获取单条数据
version = cursor.fetchone()

# 打印输出
print("MySQL数据库版本是：%s" % version)

# 关闭数据库连接
connect.close()