# encoding= utf-8
# __author__= gary
import requests


# 定义一个函数用于处理 HTTP 请求，减少代码重复
def send_request(method, url, headers=None, json=None, cookies=None):
    try:
        if method.lower() == 'post':
            response = requests.post(url, headers=headers, json=json, cookies=cookies)
        else:
            raise ValueError(f"不支持的请求方法: {method}")
        response.raise_for_status()  # 检查响应状态码，如果不是 200 则抛出异常
        return response
    except requests.RequestException as e:
        print(f"请求发生异常: {e}")
        return None
    except ValueError as e:
        print(f"方法错误: {e}")
        return None


def hotel_login(url, params):
    headers = {
        "Content-Type": "application/json"
    }
    response = send_request('post', url, headers=headers, json=params)
    if response:
        return response.cookies.get_dict()
    else:
        print("登录失败")
        return None


def get_hotel_list(url, page, params, cookies):
    request_url = f"{url}/hotel/hotel-list?page={page['page']}&size={page['size']}"
    print(request_url)
    response = send_request('post', request_url, headers={"Cookie": "; ".join([f"{key}={value}" for key, value in cookies.items()])}, json=params, cookies=cookies)
    if response:
        try:
            return response.json()
        except ValueError:
            print("响应不是有效的 JSON 格式:", response.text)
            return None
    return None


def fetch_hotel_list(username, password):
    # 假设的酒店系统登录接口 URL
    login_url = "https://hotel.gemvary.cn/hotelcloud/sysprojectUser/login"
    # 登录参数
    login_params = {
        "username": username,
        "password": password
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
    cookies = hotel_login(login_url, login_params)
    if cookies:
        print("登录成功，cookies:", cookies)
        hotel_list = get_hotel_list("https://hotel.gemvary.cn/hotelcloud", page, request_data, cookies)
        if hotel_list:
            return hotel_list
    print("获取酒店列表失败")
    return None


def fetch_hotel_rooms_no(username, password, hotel_code):
    # 假设的酒店系统登录接口 URL
    login_url = "https://hotel.gemvary.cn/hotelcloud/sysprojectUser/login"
    # 登录参数
    login_params = {
        "username": username,
        "password": password
    }
    # 调用 hotel_login 函数获取 cookies
    cookies = hotel_login(login_url, login_params)
    if cookies:
        print("登录成功，cookies:", cookies)
        # 将 cookies 字典转换为字符串
        cookies_str = "; ".join([f"{key}={value}" for key, value in cookies.items()])
        # 房间信息请求的 URL
        request_url = f"http://hotel.gemvary.cn:8090/hotelcloud/panel/roomDeviceStatus?hotelCode={hotel_code}"
        print(request_url)
        headers = {
            "Cookie": cookies_str
        }
        print(headers)
        # 假设的请求参数
        params = {
            "unitno": "",
            "floorNo": "",
            "roomno": "",
            "spaceId": "",
            "status": 10,
            "hotelPlatformType": 0
        }
        response = requests.post(url=request_url, headers=headers, json=params)
        try:
            room_list = response.json()
            # 提取 roomNo 列表
            room_no_list = [room.get('roomNo') for room in room_list.get('data', [])]
            return room_no_list
        except ValueError:
            print("响应不是有效的 JSON 格式:", response.text)
            return None
    print("登录失败，无法获取房间信息")
    return None


# 示例调用
if __name__ == "__main__":
    username = "13925716872"
    password = "21218cca77804d2ba1922c33e0151105"
    hotel_code = "10086"
    room_list1 = fetch_hotel_rooms_no(username, password, hotel_code)
    print(room_list1)
