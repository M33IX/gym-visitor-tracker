import requests 
import json
from bs4 import BeautifulSoup as Soup
import re
import sqlite3
from datetime import datetime
import time
import sched

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://vrn.alexfitness.ru',
    'DNT': '1',
    'Sec-GPC': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://vrn.alexfitness.ru/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'cross-site',
    'Priority': 'u=0',
    'TE': 'trailers'
}
REQUEST_BODY = "method=getFitCalendar&params%5BsalonId%5D=&params%5BcalendarType%5D=&params%5BgetAll%5D=Y&params%5Bwindow_width%5D=2225&params%5BgetUser%5D=false&params%5Btoken_master%5D=&params%5Btoken%5D=&params%5Butm%5D%5Breferrer%5D=&params%5Butm%5D%5Bsource%5D=https%3A%2F%2Fvrn.alexfitness.ru%2Fmoskovskiy%2Fkabinet&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Bid%5D=3cc97910-ab5e-11ec-876a-005056834a83&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Btitle%5D=Alex+Fitness+%D0%9C%D0%BE%D1%81%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%B8%D0%B9&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Bcountries%5D%5B%5D=&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Bcurrent%5D=true&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Bauth_message_to_user%5D=&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Bfree_registration%5D=false&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Btime_zone%5D=Europe%2FMoscow&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Btimestamp%5D=1727783215&clubs%5B3cc97910-ab5e-11ec-876a-005056834a83%5D%5Bphoto%5D=&api_key=acbe059c-640e-416d-8bdf-f33515809628&lang=ru&lang_cookie=&host_type="
URL = "https://reservi.ru/api-fit1c/json/v2/"
DIGITS_PATTERN = re.compile(r'\d+')

def get_online_people() -> int:
    r = requests.post(URL, headers=REQUEST_HEADERS, data=REQUEST_BODY)
    if "Error" in r.json(): return -1
    page_data: str = r.json().get('SLIDER').get('ALL_BLOCK')
    soup = Soup(page_data, 'html5lib')
    online_people_text: str = soup.findAll('div', {"class": "online-people_rz"})[0].get_text()
    try:
        online_people = int(re.findall(DIGITS_PATTERN, online_people_text)[0])
    except ValueError:
        online_people = -1
    return online_people

def create_db(name: str) -> None:
    connection = sqlite3.connect(name)
    cursor = connection.cursor()
    cursor.execute("""
CREATE TABLE IF NOT EXISTS test (
time TEXT NOT NULL,
online INTEGER
)
""")
    connection.commit()
    connection.close()

def push_data(name: str, time: str, online_people: int) -> None:
    connection = sqlite3.connect(name)
    cursor = connection.cursor()
    cursor.execute("""INSERT INTO test (time, online) VALUES (?,?)""", (time, online_people))
    connection.commit()
    connection.close()

def get_time_in_format() -> str:
    now = datetime.now()
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted

def loop(scheduler: sched.scheduler, name: str) -> None:
    scheduler.enter(60, 1, loop, (scheduler, name,))
    online_people = get_online_people()
    current_time = get_time_in_format()
    print(f"{current_time} - {online_people}")
    push_data(name, current_time, online_people)

if __name__ == "__main__":
    db_name = "test.db"
    create_db(db_name)
    t_scheduler = sched.scheduler(time.time, time.sleep)
    t_scheduler.enter(60, 1, loop, (t_scheduler, db_name,))
    t_scheduler.run()