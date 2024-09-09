import browser_cookie3
import json
import os

chrome_cookies = browser_cookie3.chrome(domain_name='i.mooc.ucas.edu.cn')
cookie_dict = {cookie.name: cookie.value for cookie in chrome_cookies}
print(cookie_dict)
with open(os.path.join('config', 'cookies.json'), 'w') as f:
    json.dump(cookie_dict, f, indent=2)