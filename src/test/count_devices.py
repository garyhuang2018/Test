
"""

# 计算设备数

"""

import pymysql
from sshtunnel import SSHTunnelForwarder


class SumDevices:

    def __init__(self):
        self.digital_num = 0
        self.android_num = 0

    def fetch_devices_num(self, zone_id):
        db = pymysql.connect(

            host='127.0.0.1',

            port=server.local_bind_port,

            user='root',

            passwd='root',

            db=zone_id

        )

        cur = db.cursor()

        cur.execute('select count(1),dev_type from bean_sipdev where dev_type in(10,14) group by dev_type;')

        data = cur.fetchall()

        for i in data:
            if i[1] == 10:
                self.digital_num = self.digital_num + i[0]
            else:
                if i[1] == 14:
                    self.android_num = self.android_num + i[0]
        db.close()
        print('安卓机数量：', self.digital_num)
        print('数字机数量：', self.android_num)


if __name__ == '__main__':
    sum = SumDevices()
    server = SSHTunnelForwarder(

        ssh_address_or_host=('120.79.32.221', 22),  # 指定ssh登录的跳转机的address

        ssh_username='root',  # 跳转机的用户

        ssh_password='root',  # 跳转机的密码

        remote_bind_address=('127.0.0.1', 3306)

    )
    server.start()
    with open(r'db_list') as f:
        zone_id = f.read().splitlines()
    for i in zone_id:
        sum.fetch_devices_num(i)
    server.close()
