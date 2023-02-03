# @cigvincev
import os
import json
import requests
import pandas as pd
import time
from matplotlib import pyplot as plt
# from collections import Counter #не использую
import seaborn as sns
import numpy as np
import io
# import csv #не использую

import asyncio
import logging
from aiogram import Bot, Dispatcher, types

from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils.markdown import text, bold, italic, code, pre #для оформления 

from contextlib import suppress #для обработчика ошибок 

from aiogram.utils.exceptions import (MessageToEditNotFound, MessageCantBeEdited, MessageCantBeDeleted,
                                      MessageToDeleteNotFound) #для обработчика ошибок
from PIL import Image
# from datetime import datetime #не использую

from wordcloud import WordCloud

"""
Бот-парсер HeadHunter 
Контакты @cigvincev
"""

# Запускаем логгирование
log = logging.getLogger(__name__)
log.setLevel(os.environ.get('LOGGING_LEVEL', 'INFO').upper())
storage = MemoryStorage() #для работы FSM

# Хендлеры
# Стартовое сообщение /start
async def start(message: types.Message, state: FSMContext):
    
    await message.reply(
        'Привет, {}!  Это бот для поиска и анализа вакансий на HeadHunter. Просто отправь боту сообщение с названием вакансии (без кавычек), например, "продавец-консультант". Можешь отправить уточняющий запрос, например, "продавец-консультант москва" или "junior тестировшик самара". Подробнее о боте /help '.format(
            message.from_user.first_name))
    await message.reply('Внимание! Обработка запроса занимает до 20 секунд. \nПожалуйста, подожди, бот обязательно ответит 😉')

# Загрузка CSV /csv
async def csv_download(message: types.Message, state: FSMContext):
    message_text = 'Чтобы сформировать csv файл, отправьте название вакансии. \nПосле поиска на HH и анализа, можно будет выгрузить CSV. \nПодробнее - наберите команду /help'
    data = await state.get_data() #получаем словарь из FSM
    test_control=data.get('test_control') #получаем данные их словаря по ключам
        # функция для обрезки названия вакансии           
    def vac_len_control(vac_name, k=60):
        if len(vac_name)>k:
            return vac_name[:k]+'...'
        else: 
            return vac_name

    

    if test_control==0:
        await message.reply('Ошибка')
    elif test_control=='test':
        z=data.get('z') #получаем данные их словаря по ключам
        vac_name=data.get('vac_name') #получаем данные их словаря по ключам
        t_date=data.get('t_date') #получаем данные их словаря по ключам
        f_date=data.get('f_date') #получаем данные их словаря по ключам
        def df_to_csv2(z):
            buf = io.BytesIO()
            z.to_csv(buf)
            buf.seek(0)
            # задаем имя
            buf.name = f'{vac_name[:30]}_{f_date}-{t_date}.csv'
            return buf
        
        await types.ChatActions.upload_document() # делаем вид что грузим док
        await asyncio.sleep(3)  # ждем 3 сек
        await message.answer_document(document=types.InputFile(df_to_csv2(z)), caption=f'датасет объявлений по вакансии {vac_len_control(vac_name, 70)}')
        await state.finish()
    else:
        await message.reply(message_text)
        # await state.finish()
    # await message.reply(some_info)

# Помощь   /help 
async def helpcommand(message: types.Message, state: FSMContext):
    s = '''🔎 Для поиска и анализа вакансий отправь боту сообщение с названием вакансии (без кавычек), например, 
"продавец-консультант".
Можешь отправить уточняющий запрос, например, 
"продавец-консультант москва" 
или "junior тестировшик самара".
Особенности бота: 
☑️ бот сам разберется, где грейд а где локация (хотя бывают исключения);
☑️ бот исправляет ошибки раскладки (но в заголовках будет абракадабра);
☑️ бот понимает язык запросов HH (например: "(аналитик OR Data analyst) not "1C", not "бизнес-аналитик" not "системный аналитик" DESCRIPTION:SQL, Excel, Python");
☑️ бот приводит зарплаты в NET (ставка НДФЛ для РФ), в рублях по курсу ЦБ РФ на дату обращения;
☑️ бот позволяет выгрузить результаты выдачи в CSV (нужно нажать на команду сразу после выдачи запроса).
Ограничения бота: 
❗️ максимальный размер выдачи не более 2000 вакансий (ограничение hh);
❗️ скорость запросов к API HH ограничена. Поэтому, после запроса бот может думать до ~20 сек.

Бот написан на Python, работает через API HH, "хостится" на Yandex Cloud (serverless).

Отзывы, пожелания, предложения пишите на @cigvincev 


'''
# ps 
    s1 = text('Для поиска и анализа вакансий отправь боту сообщение с названием вакансии (без кавычек), например, ',
        code('продавец-консультант'),
         '\nМожешь отправить уточняющий запрос, например, ',
        code('продавец-консультант москва'),
        ' или ',
        code('junior тестировшик самара'),
        ' (дальше бот сам разберется, где грейд а где локация).\n',
        'Зарплаты приведены NET, в рублях по курсу ЦБ РФ на дату обращения.\n',
        'Бот написан на Python, работает через API HH, "хостится" на Yandex Cloud (serverless).\n',
        '(!) Ограничения бота: макимальный размер выдачи не более 2000 вакансий (ограничение hh).\n',
        italic('\n ps тут ваша реклама'))

    await message.reply(s)


async def echo(message: types.Message, state: FSMContext):
    # await message.answer(message.text)
    vac_name = message.text
    def vac_len_control(vac_name, k=60):
        if len(vac_name)>k:
            return vac_name[:k]+'...'
        else: 
            return vac_name
    first_message = await message.answer(f'Ищу вакансии по запросу "{vac_len_control(vac_name, 150)}", пожалуйста, подождите...')
    await types.ChatActions.upload_photo()
    # await types.ChatActions.TYPING
    # блок номер один
    # sent = await bot.send_message(...)
    # Или 
    # sent = await msg.answer(...)
    
    # await asyncio.sleep(10)
    # await message.delete()
    # vac_name = message.text
    # var_message_answer = message.answer() 
    # var_msg_id = var_message_answer.message_id
     
    url = 'https://api.hh.ru/vacancies'
    vac_input = 'NAME:' + vac_name[:300]
    parametrs = {
        'text': vac_input,  # Текст фильтра по названию
        #           'area': 1, # Поиск ощуществляется по вакансиям города Москва
        'per_page': 100,  # Кол-во вакансий на 1 странице
        'responses_count_enabled': True,  # если нужен счетчик откликов
        'only_with_salary': True  # только вакансии с зп
        #         ,'date_from': 2022-08-02  #фильтр по дате бубликациии(от)
    }
    # конец блока номер один
    # начало блока номер два
    page, k, vacancy = 0, 0, pd.DataFrame()
    for page_number in range(0, 20):  # с 0 до 20 - все равно HH больше 2000 (20*100) вакансий не отдаст
        parametrs['page'] = page_number
        req = requests.get(url=url,
                           params=parametrs)
        res = req.json()
        k = len(vacancy) + len(res['items'])
        vacancy = pd.concat([vacancy, pd.DataFrame(res['items'])])
        if len(res['items']) < 100:  # Проверяем, может вакансии кончились
            # print('Уже скачано',len(res['items']),'вакансий')
            break
            # print('Уже скачано',k,'вакансий')
        time.sleep(0.5)  # Делаем задержку
    if len(vacancy) != 0:
        # await message.answer(len(vacancy)) #маркер
        # получаем курсы валют ЦБРФ
        data = requests.get('https://www.cbr-xml-daily.ru/daily_json.js').json()  # получаем курсы валют ЦБРФ

# начало блока аналитики===================================================================================
        vacancy['type'] = vacancy['area'].apply(lambda x: x['name'])  # вытаскиваем статус вакансии
        # vacancy['city_id'] = vacancy['area'].apply(lambda x: x['id']) #вытаскиваем ID города
        vacancy['city'] = vacancy['area'].apply(lambda x: x['name'])  # вытаскиваем ГОРОД
        # vacancy['city_url'] = vacancy['area'].apply(lambda x: x['url'])
        # vacancy['employers_name'] = vacancy['schedule'].apply(lambda x: x['name'])
        # vacancy['text'] = map(lambda x: x.get('text', ''), vacancy['salary'])
        vacancy['employers_name'] = vacancy['employer'].apply(lambda x: str(x['name']))  # вытаскиваем работадателя
        vacancy['requirements'] = vacancy['snippet'].apply(
            lambda x: str(x['requirement']))  # вытаскиваем требования к соискателю
        vacancy['requirements']=vacancy['requirements'].replace({'<highlighttext>':'',
                                                   '</highlighttext>':''}, regex=True) # удаляем символы разметки
        vacancy['responsibility'] = vacancy['snippet'].apply(
            lambda x: str(x['responsibility']))  # вытаскиваем требования к соискателю
        vacancy['responsibility']=vacancy['responsibility'].replace({'<highlighttext>':'',
                                                   '</highlighttext>':''}, regex=True) # удаляем символы разметки
        vacancy['schedule_type'] = vacancy['schedule'].apply(lambda x: str(x['name']))  # вытаскиваем формат работы
        vacancy['lat'] = vacancy['address'].apply(lambda x: '' if x==None else str(x['lat'])) #вытаскиваем щироту
        vacancy['lng'] = vacancy['address'].apply(lambda x: '' if x==None else str(x['lng'])) #вытаскиваем долготу
        # работа с зарплатными данными
        dict=data['Valute'] #даем название переменной словарю с курсами цб
        def cbrf_salary(x,dict):    #функция для перевода валют
            if x in dict.keys():
                salary_change_k=dict[x]['Value']/dict[x]['Nominal']
            elif x=='BYR':
                salary_change_k=dict['BYN']['Value']/dict['BYN']['Nominal']
            elif x=='RUR':
                salary_change_k=1
            elif x=='GEL':
                salary_change_k=35 # палка, но что поделать))
            else:
                salary_change_k=1
            return salary_change_k 
        #определяем гросс или нет
        vacancy['gross_coef'] = vacancy['salary'].apply(lambda x: 0.87 if x['gross']==True else 1)
        #вытаскиваем валюту ЗП
        vacancy['salary_currency'] = vacancy['salary'].apply(lambda x: x['currency']) #вытаскиваем валюту ЗП
        # создаем временный столбец с коэф.перевода валют
        vacancy['salary_change_k'] = vacancy.apply(lambda x: cbrf_salary(x['salary_currency'], data['Valute']), axis =  1)
        # считаем от
        vacancy['salary_from'] = vacancy['salary'].apply(lambda x: x['from'])*vacancy['salary_change_k']
        # считаем до
        vacancy['salary_to'] = vacancy['salary'].apply(lambda x: x['to'])*vacancy['salary_change_k']
        # применяем gross
        vacancy['salary_from']=vacancy['salary_from']*vacancy['gross_coef'] 
        vacancy['salary_to']=vacancy['salary_to']*vacancy['gross_coef']


        # вытаскиваем счетчик откликов
        vacancy['responses_count'] = vacancy['counters'].apply(lambda x: x['responses'])
        vacancy['created_at']=pd.to_datetime(vacancy['created_at'])
        vacancy['published_at'] =pd.to_datetime(vacancy['published_at'])
        # vacancy.head()
        # vacancy['id'].nunique()
        # await message.answer('Проанализированно!') #тестовое
        z = vacancy[
            ['id', 'name', 'city', 'employers_name', 'schedule_type', 'salary_from', 'salary_to', 'responses_count',
             'published_at', 'created_at', 'requirements', 'responsibility','lat','lng','salary_currency']]

        if np.isnan(z['salary_from'].quantile(0.5))==True:
            f_median='-'
            f_min='-'
        else:
            f_median=round(z['salary_from'].quantile(0.5))
            f_min=round(z['salary_from'].min())
        if np.isnan(z['salary_to'].quantile(0.5))==True:
            t_median='-'
            t_max='-'
        else:
            t_median=round(z['salary_to'].quantile(0.5))
            t_max=round(z['salary_to'].max())
        #     даты бубликаций
        f_date=str(z['published_at'].min())[0:10] #минимальная дата публикации
        # f_date=z['published_at'].min().to_pydatetime().strftime('%d.%m.%y') хз че не работает
        t_date=str(z['published_at'].max())[0:10] #максимальная дата публикации
        

        def sklonenie(i): #функция для правильного сколонения слова ваканси(и,я,й)
            d,h=i%10,i%100
            if d==1 and h!=11:
                s="я"
            elif 1<d<5 and not 11<h<15:
                s="и"
            else:
                s="й"
            return(s)
        l = ('ВСЕГО ' + str(len(vacancy)) + ' ваканси'+sklonenie(len(vacancy))+'. \nЗарплата (медианная, net) от ' + str(f_median) + ' до ' + str(
            t_median) + ' руб. \nДля загрузки CSV-файла наберите команду /csv' )
        # await message.answer(l)
        
        # функция конвертирующая график
        def fig2img(fig):
            buf = io.BytesIO()
            fig.savefig(buf)                
            buf.seek(0)
            img = Image.open(buf)
            return img
        # функция для обрезки названия вакансии           
        def vac_len_control(vac_name, k=60):
            if len(vac_name)>k:
                return vac_name[:k]+'...'
            else: 
                return vac_name

#=============================================================================================================
#Топ наиболее популярных работодателей по зап=== график (бар) популярности 10 зарплатодателей по сумме откликов
        def bar_with_popular_employers(z,vac_name):
            z2=z.groupby('employers_name')['responses_count'].sum().reset_index().sort_values(
                by="responses_count",
                ascending=False
                ).reset_index().head(10).copy()
            y,z99=z2['responses_count'],0
            figure, ax = plt.subplots(figsize=(12, 7))
            
            plt.title(label=f'Топ наиболее популярных работодателей по запросу \n{vac_len_control(vac_name, 70)}', loc='center', size=12, pad=10) # заголовок
            plt.barh(z2['employers_name'], 
                    z2['responses_count'],
                    tick_label=z2['employers_name'].astype(str).str[:50]
            #         textposition = 'outside', cliponaxis = False
                    )
            # plt.tight_layout()
            plt.gca().invert_yaxis()
            if z2['responses_count'].max()!=0:
                for i, v in enumerate(z2['responses_count']):
                    plt.text(v , i + 0.1, ' '+str(v), color='black',horizontalalignment='left',fontstyle='italic')
                    z99+=1
            # z99=0    v+1
            # for i, v in enumerate(z2['responses_count']):
            #     plt.text(v+1, i + 0.1,'от '+str(k[z99])+' ₽', color='black',horizontalalignment='left')
            #     z99+=1
            plt.xlabel(f'сумма числа откликов на вакансии \n @hh_analytics_bot')
            if z2['responses_count'].max()!=0:
                ax.set_xlim([-1*(z2['responses_count'].max()/15), z2['responses_count'].max()+(z2['responses_count'].max()/5)])
                plt.tight_layout() #обрезаем как надо
            # рисуем график и применяем функцию
            fig = plt.gcf()
            img = fig2img(fig)
            # конвертириуем PIL в байтовые
            buf7 = io.BytesIO()
            img.save(buf7, 'PNG')
            buf7.seek(0)
            return buf7
        
# Рейтинг работодателей по количеству опубликованных объявлений == график (бар) 10 зарплатодателей по количеству опубликованных объявлений
        def bar_with_count_employers(z,vac_name):
            z2=z.groupby('employers_name')['responses_count'].count().reset_index().sort_values(
                by="responses_count",
                ascending=False
                ).reset_index().head(10).copy()
            
            y,z99=z2['responses_count'],0
            figure, ax = plt.subplots(figsize=(12, 7))
            
            plt.title(label=f'Рейтинг работодателей по количеству опубликованных объявлений по вакансии \n{vac_len_control(vac_name, 70)}', loc='center', size=12, pad=10) # заголовок
            plt.barh(z2['employers_name'], 
                    z2['responses_count'],
                    tick_label=z2['employers_name'].astype(str).str[:50]
            #         textposition = 'outside', cliponaxis = False
                    )
            # plt.tight_layout()
            plt.gca().invert_yaxis()
            for i, v in enumerate(z2['responses_count']):
                plt.text(v , i + 0.1, ' '+str(v), color='black',horizontalalignment='left',fontstyle='italic')
                z99+=1
            # z99=0     v+0.01
            # for i, v in enumerate(z2['responses_count']):
            #     plt.text(v+1, i + 0.1,'от '+str(k[z99])+' ₽', color='black',horizontalalignment='left')
            #     z99+=1
            if z2['responses_count'].max()!=0:
                ax.set_xlim([-1*(z2['responses_count'].max()/15), z2['responses_count'].max()+(z2['responses_count'].max()/5)])
            plt.xlabel(f'количество размещенных объявлений \n @hh_analytics_bot')
            plt.tight_layout() #обрезаем как надо
            # рисуем график и применяем функцию
            fig = plt.gcf()
            img = fig2img(fig)
            # конвертириуем PIL в байтовые
            buf7 = io.BytesIO()
            img.save(buf7, 'PNG')
            buf7.seek(0)
            return buf7
                

# основной боксплот с зп от и до
        def boxpot_vacancy_from_to(z,vac_name,f_median,t_median,f_min,t_max,f_date,t_date):
            # графики
            plt.figure(figsize=(5, 9))  # Зададим размер фигуры
            plt.title(label=f'Распределение зарплат по вакансии \n{vac_len_control(vac_name, 35)}', loc='center', size=14, pad=15)  # заголовок
            plt.grid()  # Добавим сетку

            # отрисовываем график
            # box_plot = sns.boxplot(data=f.loc[(f['salary_from']<f['salary_from'].quantile(0.99))&(f['salary_to']<f['salary_to'].quantile(0.99))],
            #             palette='Set3')
            box_plot = sns.boxplot(data=z[['salary_from', 'salary_to']],
                                palette='coolwarm')
            # ax = sns.swarmplot(data=f.loc[(f['salary_from']<100000)&(f['salary_to']<100000)],
            #                    color='lightgrey')
            plt.ylabel('Размер зарплаты (net), руб.')  # Подпишем ось Y
            # medians = f['salary_from'].median()
            # vertical_offset = f['salary_from'].median() * 0.05 # offset from median for display
            # for xtick in box_plot.get_xticks():
            #     box_plot.text(xtick,medians[xtick] + vertical_offset,medians[xtick],
            #             horizontalalignment='center',size='x-small',color='w',weight='semibold')
            # plt.xlabel(round(f['salary_from'].quantile(0.5),1)) # Подпишем ось Y

            plt.xlabel(
                f'медиана: {f_median} руб.  медиана: {t_median} руб. \n min: {f_min} руб. max: {t_max} руб. \n (c {f_date} по {t_date})\n @hh_analytics_bot')

            # рисуем график и применяем функцию
            fig = plt.gcf() #обрезаем правильно
            img = fig2img(fig)
            # конвертириуем PIL в байтовые
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            buf.seek(0)
            return buf
        # bio_image=buf.getvalue()

# график публикации вакансий в течении времени
        def grafik_vac_in_time(z):
            z4=z.copy()
            z4['published_at2']=z4['published_at'].dt.floor("D")
            z4=z4.groupby(z4['published_at2'])['id'].count().reset_index()
            # import matplotlib.dates as mdates
            fig, ax = plt.subplots(figsize=(15, 7))
            published_at2_min=z4['published_at2'].min().strftime('%d.%m.%Y')
            published_at2_max=z4['published_at2'].max().strftime('%d.%m.%Y')
            plt.title(label=f'График публикации объявлений по вакансии \n{vac_len_control(vac_name, 120)} \n(с {published_at2_min} по {published_at2_max})', loc='center', size=12, pad=10) # заголовок

            #####
            # import matplotlib.ticker as mticker
            ######
            plt.plot(z4['published_at2'],z4['id'],'-o')
            ax.set_xticks(z4['published_at2']) #назначим свои тики
            ax.set_xlabel('@hh_analytics_bot')
            ax.set_ylabel('Количество опубликованных объявлений')
            
            fig.autofmt_xdate(rotation=45) 
            plt.grid(True) #сеточка
            plt.tight_layout() #обрезаем правильно
            # plt.figure(figsize=(12, 7))
            # рисуем график и применяем функцию
            fig = plt.gcf() 
            img = fig2img(fig)
            # конвертириуем PIL в байтовые
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            buf.seek(0)
            return buf

        # еще одна картинка
        
#Основные требования к соискателю индийский код, осторожно, чистим DF
        def popular_word_requirements(z):
            df2=z['requirements'].reset_index()
            df2['requirements']=df2['requirements'].str.lower()
            df2['requirements']=df2['requirements'].replace({'!':'',
                                                            ',':'',
                                                            '<':'',
                                                            '>':'',
                                                            ' на ':' ',
                                                            ' с ':' ',
                                                            ' и ':' ',
                                                            ' или ':' ',
                                                            ' либо ':' ',
                                                            ' всех ':' ',
                                                            'навык.':' ',
                                                            'понимание':' ',
                                                            ' к ':' ',
                                                            ' от ':' ',
                                                            ' из ':' ',
                                                            'умение':'',
                                                            'работы':' ',
                                                            'работать':' ',
                                                            'знание':' ',
                                                            'знания':' ',
                                                            'опыт ':' ',
                                                            'highlighttext':' ',
                                                            'index':' ',
                                                            'пользователь':' ',
                                                            'желательно':' ',
                                                            'рассматриваем':' ',
                                                            'образование':' ',
                                                            'приветствуется':' ',
                                                            'requirements':' ',
                                                            'index':' ',
                                                            'requirements0':' ',
                                                            ' в ':' '}, regex=True)
            text = df2.to_string()
            text = text.replace('\n', '') # удаляем знаки разделения на абзацы
            text = text.replace('requirements', '') # удаляем 
            text = text.replace('index', '') # удаляем 
            text = text.replace(')', ' ') # удаляем 
            text = text.replace('(', ' ') # удаляем 
            text = text.replace('.', ' ') # удаляем 
            # Функция для визуализации облака слов
            def plot_cloud(wordcloud):
                # Устанавливаем размер картинки
                plt.figure(figsize=(20, 30))
                # Показать изображение
                plt.imshow(wordcloud) 
                # Без подписей на осях
                plt.axis("off")
                plt.title(label=f'Требования к соискателю', loc='center', size=14, pad=15)
            # Генерируем облако слов
            plt.figure(figsize=(7, 11))  # Зададим размер фигуры
            plt.title(label=f'Основные требования к соискателю по вакансии\n{vac_len_control(vac_name, 60)}', loc='center', size=14, pad=15)  # заголовок
            wordcloud = WordCloud(width = 600, 
                                height = 1200, 
                                random_state=1, 
                                background_color='white', 
                                margin=10, 
                                colormap='coolwarm', 
                                collocations=False, 
            #                       stopwords = STOPWORDS_RU
                                ).generate(text)

            plt.axis("off")
            plt.text(400, 1220, '@hh_analytics_bot',fontsize=12, color='coral'); # добавляем подпись к графику 
            plt.imshow(wordcloud)
            plt.tight_layout()
            # рисуем график и применяем функцию
            fig = plt.gcf()
            img = fig2img(fig)
            # конвертириуем PIL в байтовые
            buf2 = io.BytesIO()
            img.save(buf2, 'PNG')
            buf2.seek(0)
            return buf2
        
#Топ наиболее популярных объявлений по вакансии бар с популярными вакансиями=================================================================
        def bar_with_popular_vac(z):
            z_df=z.sort_values(
                by="responses_count",
                ascending=False
                ).reset_index().head(10)
            k=list(z_df['salary_from'])
            k2=list(z_df['salary_to'])
            for i in range(len(k)):
                if np.isnan(k[i])==True:
                    if np.isnan(k2[i])==True:
                        k[i]='- '
                    else:
                        k[i]=('до '+str(round(k2[i]))+' ₽ ')    
                else: 
                    k[i]=('от '+str(round(k[i]))+' ₽ ')
            # ff=z_df['salary_from']+z_df['employers_name']
            y,z=z_df['responses_count'],0
            plt.figure(figsize=(12, 7))
            plt.title(label=f'Топ наиболее популярных объявлений по вакансии \n{vac_len_control(vac_name, 55)}', loc='center', size=12, pad=10) # заголовок
            plt.barh(z_df['id'], z_df['responses_count'],tick_label=z_df['name'].astype(str).str[:40]+'... ('+z_df['employers_name'].astype(str).str[:30]+')')
            plt.xlabel(f'число откликов на вакансию \n @hh_analytics_bot')
            
            plt.gca().invert_yaxis()
            #добавить условие с изменением цвета (тест)
            for i, v in enumerate(z_df['responses_count']):
                if z_df['responses_count'].max()/(v+1)>2.2:
                    plt.text(v, i + 0.1,(len(str(v))*' ')+'     '+k[z], color='black',horizontalalignment='left',fontstyle='italic')
                else:
                    plt.text(v, i + 0.1,k[z]+' ', color='white',horizontalalignment='right',fontstyle='italic')
                z+=1
            for i, v in enumerate(z_df['responses_count']):
                plt.text(v, i + 0.1,' '+str(v), color='red',horizontalalignment='left')
                z+=1


            #добавить условие - первоначальный вариант
            # for i, v in enumerate(z_df['responses_count']):
            #     plt.text(v - 0, i + 0.1,k[z], color='white',horizontalalignment='right',fontstyle='italic')
            #     z+=1
            # for i, v in enumerate(z_df['responses_count']):
            #     plt.text(v, i + 0.1,' '+str(v), color='red',horizontalalignment='left')
            #     z+=1
            plt.tight_layout() #обрезаем как надо
            # рисуем график и применяем функцию
            fig = plt.gcf()
            img = fig2img(fig)
            # конвертириуем PIL в байтовые
            buf3 = io.BytesIO()
            img.save(buf3, 'PNG')
            buf3.seek(0)
            return buf3

#сообщения ===============================================================================
        await types.ChatActions.upload_photo()
        # await types.ChatActions.typing()
        
        # Create media group
        media = types.MediaGroup()
        # Attach local file
        
        media.attach_photo(types.InputFile(boxpot_vacancy_from_to(z,vac_name,f_median,t_median,f_min,t_max,f_date,t_date)), l)
        media.attach_photo(types.InputFile(popular_word_requirements(z)))
        media.attach_photo(types.InputFile(bar_with_popular_vac(z)))
        media.attach_photo(types.InputFile(bar_with_popular_employers(z,vac_name)))
        media.attach_photo(types.InputFile(bar_with_count_employers(z,vac_name)))
        media.attach_photo(types.InputFile(grafik_vac_in_time(z)))
        
        


        
        # отправляем медиагруппу
        await message.reply_media_group(media=media)
        
        #удаляем первое сообщение
        with suppress(MessageCantBeDeleted, MessageToDeleteNotFound):
            await first_message.delete()
        # старое комментим
        # await message.answer_photo(photo=types.InputFile(bar_with_popular_vac(z)), caption='Наиболее популярные вакансии по отзывам')
        # await message.answer_photo(photo=types.InputFile(boxpot_vacancy_from_to(z,vac_name,f_median,t_median,f_min,t_max,f_date,t_date)), caption=l)
        # await message.answer_photo(photo=types.InputFile(popular_word_requirements(z)), caption='Облако слов-требований из описания вакансий')
        # тестовое сообщение номер 2
        # def df_to_csv(z,vac_name):
        #     test_data=z.to_csv()
        #     s = io.StringIO()
        #     csv.writer(s).writerows(test_data)
        #     s.seek(0)
        #     # python-telegram-bot library can send files only from io.BytesIO buffer
        #     # we need to convert StringIO to BytesIO
        #     buf = io.BytesIO()
        #     # extract csv-string, convert it to bytes and write to buffer
        #     buf.write(s.getvalue().encode())
        #     buf.seek(0)
        #     # set a filename with file's extension
        #     buf.name = f'vacancy.csv'
        #     return buf
        
        # def df_to_csv_BIO(z): #плохой код
        #     buf5 = io.BytesIO()
        #     ## compression_opts = dict(method='zip', archive_name='out.csv')  # doctest: +SKIP
        #     ## df.to_csv('out.zip', index=False, compression=compression_opts)  # doctest: +SKIP
        #     z.to_csv(buf5)
        #     return buf5.seek(0)


        # await message.answer('Конец блока с картинками')

        # await bot.send_photo(message.from_user.id, img,
        #                  caption='Подпись к фото',
        #                  reply_to_message_id=message.message_id)
        # await bot.send_photo(chat_id=message.from_user.id, photo=img)

#блок с записью переменных из функции в FSM - для возможности вызова и использования их в другом хендлере
        test_control='test'
        
        await state.update_data(test_control=test_control)
        await state.update_data(z=z)
        await state.update_data(vac_name=vac_name)
        await state.update_data(t_date=t_date)
        await state.update_data(f_date=f_date)

#=====================================================

#  ====================================      
        # data = await state.get_data()
        # some_info2=data.get('some_info')
        
        # if some_info2==0:
        #     await message.reply('Равно 0')
        # elif some_info2=='test':
        #     await message.reply('Все нашлось')
        # else:
        #     await message.reply('Ничего не нашлось')
# # очищаем стейты ==================================== 
        # await state.finish()



    else:
        await message.answer('Вакансии не найдены. Попробуйте переформулировать запрос или воспользуйтесь командой /help')
        
        #удаляем первое сообщение
        await first_message.delete()
    # конец блока номер два

    # if message.text == 'аналитик':
    #     await message.answer('Привет аналитикам ;) ')
    # else:
    # await message.answer('простое второе сообщения для проверки else')


async def unknown_message(message: types.Message, state: FSMContext):
    message_text = 'Ой, наверное, вы ошиблись чатом - бот понимает только текстовые сообщения. \nЕсли вы не знаете, что делать, наберите команду /help'

    await message.reply(message_text)


# Функции Yandex.Cloud
async def register_handlers(dp: Dispatcher):
    """Registration all handlers before processing update."""

    dp.register_message_handler(start, commands=['start'], state='*')
    dp.register_message_handler(helpcommand, commands=['help'], state='*')
    dp.register_message_handler(csv_download, commands=['csv'], state='*')
    
    dp.register_message_handler(echo, state='*')
    dp.register_message_handler(unknown_message, content_types=types.ContentTypes.ANY)

    log.debug('Handlers are registered.')


async def process_event(event, dp: Dispatcher):
    """
    Converting an Yandex.Cloud functions event to an update and
    handling tha update.
    """

    update = json.loads(event['body'])
    log.debug('Update: ' + str(update))

    Bot.set_current(dp.bot)
    update = types.Update.to_object(update)
    await dp.process_update(update)


async def handler(event, context):
    """Yandex.Cloud хендлер """

    if event['httpMethod'] == 'POST':
        # инициализируем бот и диспатчер
        bot = Bot(os.environ.get('TOKEN'))
        
        dp = Dispatcher(bot, storage=storage) #storage=storage для работы FSM


        await register_handlers(dp)
        await process_event(event, dp)

        return {'statusCode': 200, 'body': 'ok'}
    return {'statusCode': 405}
