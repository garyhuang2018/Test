# encoding= utf-8
#__author__= gary
import random
import pandas as pd

def generate_phone_number():
    return '13' + str(random.randint(100000000, 999999999))

def generate_chinese_name():
    # Replace this with your own code to generate a random Chinese name
    first_names = ["张", "王", "黄", "李", "赵", "陈", "刘", "杨", "黄", "吴","何", "周", "韩"]
    last_names = ["浩然", "四", "敏", "梅梅", "才", "甜", "如","芙","富", "福",  "立", "柔", "波","晓","丹", "珍", "叔", "玲",
                  "娜", "少", "过","海华", "辉", "五", "六", "七", "八", "萍","平安","九"]
    return random.choice(first_names) + random.choice(last_names)

unit_numbers = []
floor_numbers = []
room_numbers = []
phone_numbers = []
chinese_names = []

for building in range(2, 8):
    for unit in range(1, 5):
        for floor in range(1, 22):
            for room in range(1, 3):
                unit_number = f"01{building:02d}{unit:02d}"
                unit_numbers.append(unit_number)
                floor_numbers.append(f"{floor:02d}".zfill(2))
                room_numbers.append(f"{room:02d}".zfill(2))
                phone_numbers.append(generate_phone_number())
                chinese_names.append(generate_chinese_name())

data = {'Name': chinese_names, 'Phone Number': phone_numbers, 'Unit Number': unit_numbers, 'Floor Number': floor_numbers, 'Room Number': room_numbers}
df = pd.DataFrame(data)
df.to_excel('data.xlsx', index=False)