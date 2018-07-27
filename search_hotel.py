from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import smtplib
from email.mime.text import MIMEText
from email.utils import formatdate
import logging


_BASE_URL = "https://www.booking.com/"
_CITY = '札幌市'
_FROM_YEAR = '2018'
_FROM_MONTH = '11'
_FROM_DAY = '16'
_TO_YEAR = '2018'
_TO_MONTH = '11'
_TO_DAY = '19'
_GUEST = '2'
_PRICE = 70000
_MAIL_ADDRESS = ''
_PASSWORD = ''

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def booking():
    logging.info('Start search')
    driver = webdriver.Chrome(executable_path=r'C:\Users\A541811\Documents\projects\selenium\chromedriver.exe')
    driver.get(url=_BASE_URL)

    # city
    city = driver.find_element_by_id('ss')
    city.clear()
    city.send_keys('札幌市')
    city.send_keys(Keys.TAB)

    try:
        # select-box
        driver.find_element_by_xpath('//div[@data-mode="checkin"]/div/span')
        # check-in date
        in_month = driver.find_element_by_xpath('//div[@data-mode="checkin"]/div/div/div[@data-type="month-year"]/select')
        in_month_select = Select(in_month)
        in_month_select.select_by_value('{}-{}'.format(str(int(_FROM_MONTH) - 1), _FROM_YEAR))
        in_date = driver.find_element_by_xpath('//div[@data-mode="checkin"]/div/div/div[@data-type="date"]/select')
        in_date_select = Select(in_date)
        in_date_select.select_by_value(_FROM_DAY)

        # check-out date
        out_month = driver.find_element_by_xpath('//div[@data-mode="checkout"]/div/div/div[@data-type="month-year"]/select')
        out_month_select = Select(out_month)
        out_month_select.select_by_value('{}-{}'.format(str(int(_TO_MONTH) - 1), _TO_YEAR))
        out_date = driver.find_element_by_xpath('//div[@data-mode="checkout"]/div/div/div[@data-type="date"]/select')
        out_date_select = Select(out_date)
        out_date_select.select_by_value(_TO_DAY)
    except NoSuchElementException:
        # input
        city.send_keys(Keys.TAB)
        driver.find_element_by_name('checkin_year').send_keys(_FROM_YEAR)
        driver.find_element_by_name('checkin_month').send_keys(_FROM_MONTH)
        in_day = driver.find_element_by_name('checkin_monthday')
        in_day.send_keys(_FROM_DAY)
        driver.find_element_by_name('checkout_year').send_keys(_TO_YEAR)
        driver.find_element_by_name('checkout_month').send_keys(_TO_MONTH)
        out_day = driver.find_element_by_name('checkout_monthday')
        out_day.clear()
        out_day.send_keys(_TO_DAY)

    # guests
    driver.find_element_by_id('xp__guests__toggle').click()
    people = driver.find_element_by_id('group_adults')
    people_select = Select(people)
    people_select.select_by_value(_GUEST)

    driver.find_element_by_xpath('//button[@data-sb-id="main"]').click()

    # sort
    wait = WebDriverWait(driver, 10)
    price_sort = wait.until(expected_conditions.visibility_of_element_located((By.XPATH, '//li[contains(@class, "sort_price")]/a')))
    price_sort.click()
    wait.until(expected_conditions.visibility_of_element_located((By.CLASS_NAME, 'sr_warnings__content')))
    notice = driver.find_element_by_xpath('//div[@class="sr_warnings__content"]/div/a')
    if notice.text == '個室のみを表示する':
        notice.click()
    # wait for display
    # wait.until_not(expected_conditions.visibility_of_element_located((By.TAG_NAME, 'iframe')))

    # sleep(3)
    # # get lowest price
    # hotels = driver.find_elements_by_xpath('//div[@data-hotelid]/div[contains(@class, "sr_item_content")]')
    # result = []
    # for hotel in hotels:
    #     price = hotel.find_element_by_xpath('//td[contains(@class, "roomPrice")]/div/strong/b').text
    #     result.append(price)
    # return result
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    result = []
    for hotel in soup.find_all('div', 'sr_item_content'):
        if hotel.find('b') and hotel.find('b').string:
            price = hotel.find('b').string
            if int(price.replace('￥', '').replace(',', '')) < _PRICE:
                price = price.strip()
                title = hotel.find('span', 'sr-hotel__name').string.strip()
                url = urljoin(_BASE_URL, hotel.find('a', 'hotel_name_link').get('href').strip().split('\n')[0])
                result.append({'title': title, 'url': url, 'price': price})
    driver.close()
    logging.info('End search')
    return result


def send_mail(hotels):
    body = []
    body.append('{} {}/{}/{}～{}/{}/{} {}人'.format(_CITY, _FROM_YEAR, _FROM_MONTH, _FROM_DAY, _TO_YEAR, _TO_MONTH, _TO_DAY, _GUEST))
    for hotel in hotels:
        body.append('ホテル：{}\n金額：{}\nURL：{}'.format(hotel['title'], hotel['price'], hotel['url']))
    body = '\n'.join(body)
    msg = MIMEText(body)
    msg['Subject'] = '条件にヒットしたホテルがありました'
    msg['From'] = _MAIL_ADDRESS
    msg['To'] = _MAIL_ADDRESS
    msg['Date'] = formatdate()
    logging.info('Start send mail')
    smtpobj = smtplib.SMTP('smtp.gmail.com', 587)
    smtpobj.ehlo()
    smtpobj.starttls()
    smtpobj.ehlo()
    smtpobj.login(_MAIL_ADDRESS, _PASSWORD)
    smtpobj.sendmail(_MAIL_ADDRESS, _MAIL_ADDRESS, msg.as_string())
    logging.info('Sent mail')
    smtpobj.close()


if __name__ == '__main__':
    hotels = booking()
    if len(hotels) != 0:
        send_mail(hotels)



