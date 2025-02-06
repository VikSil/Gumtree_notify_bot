from bs4 import BeautifulSoup
from environ import Env
from pathlib import Path
from twilio.rest import Client

import polars as pl
import requests

BASE_DIR = Path(__file__).resolve().parent
env = Env()
env.read_env(BASE_DIR / 'variables.env')
SMS_ACCOUNT_ID = env('TWILIO_SID')
SMS_API_KEY = env('TWILIO_API_KEY')
FROM_PHONE = env('TWILIO_PHONE_NUMBER')
TO_PHONE = env('MY_PHONE_NUMBER')


def main():

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
        try:
            result = send_sms_alert(row['title'], row['url'], row['image'])
            print(type(result))
            print(result)
        except Exception as e:
            print(e)
        else:
            with open(filename, 'a') as f:
                f.write(row['title'] + '\n')


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


def send_sms_alert(title: str, url: str, image: str):
    '''
    Function sends sms notifications about new ads
    '''
    msg = f'New freebie: {title}, image: {image} ad: {url}'
    sms_client = Client(SMS_ACCOUNT_ID, SMS_API_KEY)
    message = sms_client.messages.create(body=msg, from_=FROM_PHONE, to=TO_PHONE)

    return message.status


if __name__ == "__main__":
    main()
