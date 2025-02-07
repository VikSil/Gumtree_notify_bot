from bs4 import BeautifulSoup
from environ import Env
from pathlib import Path

import datetime
import polars as pl
import requests
import sys

BASE_DIR = Path(__file__).resolve().parent
env = Env()
env.read_env(BASE_DIR / 'variables.env')
NUMBER = env('PHONE_NUMBER')
IPADDRESS = env('ROUTER_IP')
USERNAME = env('ROUTER_USER')
PASSWORD = env('ROUTER_PASSWORD')


def main():

    now = datetime.datetime.now()
    hour = now.hour
    minute = now.minute

    if (7 <= hour <= 8) and (0 <= minute <= 10):
        send_sms_alert('Heartbeat from Gumtree script')
        sys.exit()

    filename = 'ads.txt'
    URLs = ['http://www.gumtree.com/for-sale/freebies/uk/oxford']

    for url in URLs:
        page_html = get_html(url)
        ads = get_nearby_results(page_html)
        titles = ads['title'].to_list()

    with open(filename, 'r+') as f:
        for line in f:
            if line.rstrip() in titles:
                ads = ads.filter(pl.col('title') != line.rstrip())

    for row in ads.rows(named=True):
        if send_sms_alert(f"New freebie: { row['title']}, image: {row['image']} ad: {row['url']}"):
            with open(filename, 'a') as f:
                f.write(row['title'] + '\n')

    truncate_file(filename)


def get_html(url: str) -> BeautifulSoup:
    '''
    Function retrieves and returns the HTML from a URL
    '''

    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    response = requests.get(url, headers=HEADERS)
    # works with html parser as well as lxml - slightly different outputs, but the span tag is the same
    soup = BeautifulSoup(response.content.decode('utf-8', 'ignore'), 'html.parser')

    return soup


def get_nearby_results(soup: BeautifulSoup) -> pl.DataFrame:
    '''
    Function parses HTML and returns a dataframe of recent nearby ad data
    '''

    middle_div = soup.find(name='div', class_='css-zfj6vx')
    ads = middle_div.find_all(name='div', class_='css-in27v8')

    data = {"title": [], "url": [], "image": []}
    results = pl.DataFrame(data, schema={"title": pl.String, "url": pl.String, "image": pl.String})

    for ad in ads:
        title = ad.find(name='div', class_='e25keea13').getText().rstrip()
        url = ad.find(name='a', class_='e25keea16', href=True)
        image = ad.find(name='img')
        if image != None:
            image = str(image)
            pos = image.index('https')
            image = image[pos:-3]
        else:
            image = 'None'

        new_row = pl.DataFrame([{"title": title, "url": 'https://www.gumtree.com/' + url['href'], "image": image}])
        results = pl.concat([results, new_row])

    return results


def send_sms_alert(msg: str) -> bool:
    '''
    Function logs into a D-Link DWR-921 B3 router and sends sms notifications
    '''

    try:

        with requests.session() as c:
            # Log in
            response = c.get(
                'http://'
                + IPADDRESS
                + '/log/in?un='
                + USERNAME
                + '&pw='
                + PASSWORD
                + '&rd=%2Fuir%2Fdwrhome.htm&rd2=%2Fuir%2Floginpage.htm&Nrd=1&Nlmb='
            )

            # Get next sms token
            response = c.get('http://' + IPADDRESS + '/csrf.xml')
            token_pos = response.text.index('<token>')
            token = response.text[token_pos + 7 : token_pos + 13]

            # Send sms
            response = c.get(
                'http://'
                + IPADDRESS
                + '/sys_smsmsg.htm?csrftok='
                + token
                + '&Nsend=1&Nmsgindex=0&S801E2701='
                + NUMBER
                + '&S801E2801='
                + msg
            )

            response.text.index('Enter Message...')  # will raise exception if authorisation error occured
            response = c.get('http://' + IPADDRESS + '/sms2.htm?Ncmd=2')
    except:
        return False

    return True


def truncate_file(filename: str) -> None:
    '''
    Function removes lines from file, leaving 50 last/newest lines
    '''
    lines = []
    with open(filename, 'r+') as f:
        lines = f.readlines()

    with open(filename, 'w') as f:
        f.writelines(lines[-50:])


if __name__ == "__main__":
    main()
