import json
import requests
from bs4 import BeautifulSoup as bs

myspace_url = "https://i.mooc.ucas.edu.cn"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
}

def get_notice_link(session):
    myspace_html = session.get(myspace_url, headers=headers)
    myspace_soup = bs(myspace_html.text, 'lxml')
    notice_a = myspace_soup.find('a', id='zne_tz_icon')
    if notice_a:
        notice_link = notice_a['href'].split('\'')[-2]
    else:
        raise Exception('未找到notice链接')
    return notice_link

def get_notice_bs(session, notice_link):
    notice_response = session.get(notice_link, headers=headers)
    if notice_response.status_code == 200:
        print("notice请求成功！")
    else:
        print(f"请求失败，状态码：{notice_response.status_code}")
    notice_bs = bs(notice_response.text, 'lxml')
    return notice_bs

def sparse_notice(notice_bs: bs):
    notice_div = notice_bs.select_one('#datas')
    print(notice_div.text)
    li_lst = notice_div.find_all('li', class_='dataBody_td dataBody_item')
    print(li_lst)
    for li in li_lst:
        print(li.text)
    
    
if __name__ == '__main__':
    with open('cookies.json', 'r') as f:
        cookies = json.load(f)
    
    session = requests.Session()
    session.cookies.update(cookies)
    
    notice_link = get_notice_link(session)
    notice_bs = get_notice_bs(session, notice_link)
    with open('notice.html', 'w', encoding='utf-8') as f:
        f.write(notice_bs.prettify())
    sparse_notice(notice_bs)