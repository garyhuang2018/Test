
# encoding= utf-8
# __author__= gary
import requests


def hotel_login(url, params):
    try:
        # 设置请求头
        headers = {
            "Content-Type": "application/json"
        }
        # 发送 POST 请求
        response = requests.post(url, headers=headers, json=params)
        # 检查响应状态码
        if response.status_code == 200:
            # 登录成功，返回响应的 cookies
            return response.cookies.get_dict()
        else:
            # 登录失败，打印错误信息
            print(f"登录失败，状态码: {response.status_code}，错误信息: {response.text}")
            return None
    except requests.RequestException as e:
        # 处理请求异常
        print(f"请求发生异常: {e}")
        return None


def get_hotel_list(url, page, params, cookies):
    request_url = f"{url}/hotel/hotel-list?page={page['page']}&size={page['size']}"
    print(request_url)
    # 将 cookies 字典转换为正确的 Cookie 字符串格式
    cookie_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])
    headers = { "Cookie": cookie_str }
    response = requests.post(url=request_url, headers=headers, json=params)
    return response.json()


# 示例调用
if __name__ == "__main__":
    # 假设的酒店系统登录接口 URL
    login_url = "https://hotel.gemvary.cn/hotelcloud/sysprojectUser/login"
    # 登录参数
    login_params = {
        "username": "13925716872",
        "password": "21218cca77804d2ba1922c33e0151105"
    }
    request_data = {
        "address": "",
        "hotelId": "",
        "hotelLabel": "",
        "hotelName": "",
        "hotelType": None
    }
    page = {
        "page": 0,
        "size": 11
    }
    # 调用 hotel_login 函数
    result = hotel_login(login_url, login_params)
    if result:
        print("登录成功，cookies:", result)
        # 将 cookies 字典转换为正确的 Cookie 字符串格式
        cookie_str = "; ".join([f"{key}={value}" for key, value in result.items()])
        headers = {"Cookie": cookie_str }
        # 重新构造请求 URL
        re_url = f"https://hotel.gemvary.cn/hotelcloud/hotel/hotel-list?page={page['page']}&size={page['size']}"
        response = requests.post(url=re_url, headers=headers, json=request_data)
        print(response.status_code)
        try:
            print(response.json())
        except ValueError:
            print("响应不是有效的 JSON 格式:", response.text)
    else:
        print("登录失败")