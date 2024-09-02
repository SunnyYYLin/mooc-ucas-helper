import browser_cookie3
import json

# 获取Chrome浏览器的Cookie
chrome_cookies = browser_cookie3.chrome(domain_name='i.mooc.ucas.edu.cn')

# 转换为字典
cookie_dict = {cookie.name: cookie.value for cookie in chrome_cookies}

# 输出结果
print(cookie_dict)

# 如果需要保存到文件
with open('cookies.json', 'w') as f:
    json.dump(cookie_dict, f, indent=2)