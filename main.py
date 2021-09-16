import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import random
import re
import csv
import json


"""
собираю информацию с сайта chelrestoran.ru (рестораны Челябинска), 
1. Соберу ссылки на каждую карточку, 
2. Пройду по каждой карточке выдерну: *имя кафе, *количество просмотров, *средний чек, *тип заведения, *тип кухни, *ссылку
3. Запишу в json & CSV
"""
 

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
}

# это текущая дата, позже я буду подписывать ей файлы
cur_date = datetime.now().strftime("%Y.%m.%d")

url = 'https://chelrestoran.ru/catalog/?PAGEN_2=1&SIZEN_2=20'

def data_index():
    
    response = requests.get(url=url, headers=headers)
    
    # with open('index.html', 'w') as file:
    #     src = file.write(response.text)
    #     print(src)
    
    # собираю ссылки на карточку каждого ресторана
    
    # создаю обьект BeautifulSoup
    soup = BeautifulSoup(response.text, 'lxml')
    
    # нахожу последнюю страницу
    last_page = int(soup.find('ul', class_='justify-content-center').find_all('li', class_='page-item')[-2].text)
    # print(last_page)
    
    #  для хранения ссылок
    list_link = []
    
    # блок пагинации меняет страницы
    for pagination_page in range(1, 3): #(1, last_page + 1)
        pagination_page_url = f"https://chelrestoran.ru/catalog/?PAGEN_2={pagination_page}&SIZEN_2=20"   
        
        # к каждой странице делаю запрос
        r = requests.get(url=pagination_page_url, headers=headers)
        
        # передаю в soup мой r
        soup = BeautifulSoup(r.text, 'lxml')
        
        # собираю ссылки
        link = soup.find('div', class_='whiteWithBorder').find_all('div', class_='col-12 col-md-8 col-xl-4 text-center text-md-right')
        for i in link:
            list_link.append(f"https://chelrestoran.ru{i.find('a').get('href')}")
        

        # пауза между реквестами к новой странице
        time.sleep(random.randrange(2, 5))
        
        print(f'\n--> Собираю ссылки со страницы: {pagination_page} из {last_page}\n')
        
    # запишу переменную с сылками
    with open(f"{cur_date}_list_link.txt", 'a') as file:
        
        # запишу строчками, что бы можно было количество посмотреть
        for line in list_link:
            file.write(f'{line}\n')
    
    # print(list_link)        
    print(f"\n\n --->Сбор ссылок закончен!\n")
    
    return list_link
    

def collect_data_cafe(list_link, *args):
    
    # для мониторинга процесса сбора инфы
    urls_count = len(list_link)
    print(f"Теперь обработаем {urls_count} ссылок")
    
    # шаблон для записи в csv
    with open(f'{cur_date}_all_data_cafe.csv', 'w') as file:
        writer = csv.writer(file)
        writer.writerow(
            (
                'Имя кафе',
                'Просмотры',
                'Средний чек',
                'Тип заведения',
                'Тип кухни',
                'Ссылка'
            )
        )
        
    # создаю переменную для записи в json
    all_data_cafe = []
    
    # подсчет обработанных ссылок
    count = 1
    
    # делаем запрос к каждой карточке и вытаскиваем данные
    for url in list_link: #[0:1]
       
        response = requests.get(url=url, headers=headers)
        
        soup = BeautifulSoup(response.text, 'lxml')
        
        try:
            # Имя кафе
            card_name_cafe = soup.find('div', id='saloonHeader').find('h1').text
        
        except Exception as ex:
            card_name_cafe = 'None'
        
        try:
            # Количество просмотров НЕ СМОГ!
            card_views = soup.find('i', class_='icon-view').next_element.text
            print(card_views)
            # test 
        
        except Exception as ex:
            card_views = None
            
        try:
            # Средний чек
            card_average_check = soup.find('div', text=re.compile('Средний чек:')).find_next().text.replace('руб.', '')
        
        except Exception as ex:
            card_average_check = None
            
        try:
            # Тип заведения
            card_type_cafe = soup.find('div', text=re.compile('Тип заведения:')).find_next().find_next().text
        
        except Exception as ex:
            card_type_cafe = 'None'
            
        try:
            # Тип кухни
            card_type_cuisine = soup.find('div', text=re.compile('Кухни:')).find_next().find_next().text
        
        except Exception as ex:
            card_type_cuisine = 'None'
            
        # Ссылка на карточку кафе
        card_link = url
        
        # упаковываю данные в csv
        with open(f'{cur_date}_all_data_cafe.csv', 'a') as file:
            writer = csv.writer(file)
            writer.writerow(
                (
                    card_name_cafe,
                    card_views,
                    card_average_check,
                    card_type_cafe,
                    card_type_cuisine,
                    card_link
                )
            )
            
        # упаковываю данные в json
        all_data_cafe.append(
            {
                'card_name_cafe': card_name_cafe,
                'card_views': card_views,
                'card_average_check': card_average_check,
                'card_type_cafe': card_type_cafe,
                'card_type_cuisine': card_type_cuisine,
                'card_link': card_link
            }
        )
        
        # print(f"Имя кафе: {card_name_cafe}\nКоличество просмотров: {card_views}\nСредний чек: {card_average_check}\nТип заведения: {card_type_cafe}\nТип кухни: {card_type_cuisine}\nСсылка на карточку кафе: {card_link}\n\n")
    
        # монитор работы прохождения по ссылкам
        print(f"--> Обработана {count} из {urls_count} ссылок")
        
        count += 1
        
        # после прохождения по каждой ссылке-пауза
        time.sleep(random.randrange(2, 4))
        
    # запишу json
    with open(f'{cur_date}_all_data_cafe.json', 'w') as file:
        json.dump(all_data_cafe, file, indent=4, ensure_ascii=False)
      
    
    # нужно передать из первой функции время старта и высчитать разницу
    # print(f"Время старта кода: {start_time}\n")
    
  
        
    return 'Сбор данных завершен'


def main():
    
    # фиксирую время старта работы кода
    start_time = time.time()
    print(f"\nВремя старта кода: {datetime.fromtimestamp(start_time)}")
    
    print(collect_data_cafe(list_link=data_index())) 
    
    # фиксирую время окончания работы кода
    working_time = time.time() - start_time
    print(f"Working time: {working_time}")
    print(f"Время окончания работы кода: {datetime.fromtimestamp(time.time())}")   
    

if __name__ == '__main__':
    main()
