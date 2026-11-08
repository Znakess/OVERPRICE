import tkinter as tk
from tkinter import ttk
import webbrowser
import os, json, math, time, zlib, itertools, statistics, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote_plus, urlparse, parse_qs, urlencode
from urllib.request import Request, urlopen
import urllib.error
import re, hashlib, hmac, secrets, sqlite3

# ============================================================
# OverPrice – Astana | Native desktop version (v5: with cybersecurity)
#
# SECURITY FEATURES (each one answers a risk from our Security Risk Table):
#  1. Location privacy  - location stays in memory, is rounded to ~100 m, is never saved
#                         or sent anywhere; GPS bridge uses a secret token, localhost only,
#                         Host check and a 60 s expiry; geocoding sends only branch addresses.
#  2. SQL injection     - product search runs through SQLite with PARAMETERIZED queries;
#                         input is cleaned and limited to 40 characters.
#  3. Fake prices       - price reports are range-checked, rate-limited, never change the
#                         ranking (pending review) and go to a tamper-evident audit log.
#  Extra: local files are validated on load and written with private permissions.
#  See the "Security" tab: status + a Security Lab with safe simulations (fake data only).
# Standard library only (Tkinter).
#
# IMPORTANT:
# Prices below are DEMO / estimated comparison values, not live
# prices. Store names and some Astana branches were expanded
# using publicly available listings/catalogues.
# ============================================================

BG = "#0E1914"
SURFACE = "#17251E"
INK = "#E8F1EC"
MUTED = "#9DB0A5"
LINE = "#2A3B33"
DARK = "#082A20"
BRAND = "#3FCB9B"
MINT = "#173A2B"
YELLOW = "#FFD84D"
WARN = "#FF9C93"
BRAND_INK = "#04241A"      # dark text on green buttons
BAR = "#3A4F45"
HOVER_G = "#1F6B50"        # hover colour of normal buttons (green)
HOVER_LIGHT = "#7CEBC4"    # hover colour of green buttons

STORES = [
    {
        "id": "magnum", "name": "Magnum",
        "branches": [
            "ул. Шокана Уалиханова, 20",
            "пр. Туран, 55Д",
            "шоссе Алаш, 23/1",
            "ул. Сыганак, 17Б",
        ],
    },
    {
        "id": "small", "name": "Small",
        "branches": [
            "пр. Кабанбай Батыра, 6/2",
            "пр. Кабанбай Батыра, 21 (Asia Park)",
            "пр. Туран, 65",
        ],
    },
    {
        "id": "galmart", "name": "Galmart",
        "branches": [
            "ул. Достык, 9 (Keruen)",
            "Коргалжинское шоссе, 1 (Keruen City)",
            "ул. Сыганак, 60/5 (Abu Dhabi Plaza)",
            "пр. Кабанбай Батыра, 62 (MEGA Silk Way)",
            "пр. Кабанбай Батыра, 119 (аэропорт)",
            "ул. Калдаякова, 6",
            "ул. Амман, 21",
            "ул. Акмешит, 1, блок 3",
        ],
    },
    {
        "id": "anvar", "name": "Анвар",
        "branches": [
            "ул. Алматы, 5",
            "пр. Б. Момышулы, 8",
            "пр. Туран, 45",
            "шоссе Алаш, 37",
        ],
    },
    {
        "id": "ayan", "name": "Ayan",
        "branches": [
            "ул. Каныша Сатпаева, 14",
            "ул. Сарыарка, 31",
            "ул. Косшыгулулы, 24",
            "ул. Кажымукана, 14",
        ],
    },
    {
        "id": "toimart", "name": "Toimart",
        "branches": [
            "Астана — филиалы сети Toimart",
        ],
    },
    {
        "id": "metro", "name": "METRO",
        "branches": [
            "Трасса Астана–Караганда, 4/1",
        ],
    },
    {
        "id": "eurospar", "name": "Eurospar",
        "branches": [
            "ул. Кенесары, 38",
        ],
    },
    {
        "id": "fermag", "name": "ФерМаг",
        "branches": [
            "ул. Жангельдина, 7",
            "ул. Алматы, 11",
            "ул. Иманова, 41",
            "ул. Улы Дала, 23",
            "ул. Иманбаевой, 7А",
            "пр. Кабанбай Батыра, 58А корпус I",
            "ул. Сыганак, 2",
            "ул. Бейбітшілік, 32",
            "ул. Конституции, 22",
            "ул. И. Есенберлина, 18",
            "пр. Кабанбай Батыра, 9/2",
            "пр. Мангилик Ел, 53",
            "пр. Абая, 98В",
        ],
    },
    {
        "id": "gastro", "name": "Гастроном",
        "branches": ["ул. Сарайшык, 7А"],
    },
]

# id, emoji, RU, EN, base price, groups, store factors
# Group = (RU label, EN label, [(RU, EN, factor), ...])
P = [
("milk","🥛","Молоко","Milk",650,
 [("Бренд","Brand",[("Lactel","Lactel",1),("Простоквашино","Prostokvashino",.97),("Adal","Adal",.92),("Домик в деревне","House in the Village",1.03),("Родина","Rodina",.9)]),
  ("Объём / вес","Size",[("1 л","1 L",1),("0,5 л","0.5 L",.56)])]),
("kefir","🥛","Кефир","Kefir",620,
 [("Бренд","Brand",[("Молочный бидончик","Molochnyy Bidonchik",1),("Домик в деревне","House in the Village",1.04),("Простоквашино","Prostokvashino",1.02),("Родина","Rodina",.92)]),
  ("Объём","Size",[("1 л","1 L",1),("0,5 л","0.5 L",.56)])]),
("smetana","🍶","Сметана","Sour cream",780,
 [("Бренд","Brand",[("Родина","Rodina",1),("Простоквашино","Prostokvashino",1.1),("Домик в деревне","House in the Village",1.12)]),
  ("Вес","Weight",[("400 г","400 g",1),("200 г","200 g",.55)])]),
("tvorog","🥄","Творог","Cottage cheese",650,
 [("Бренд","Brand",[("Родина","Rodina",1),("Простоквашино","Prostokvashino",1.12),("Домик в деревне","House in the Village",1.15)]),
  ("Вес","Weight",[("200 г","200 g",1),("350 г","350 g",1.7)])]),
("bread","🍞","Хлеб","Bread",230,
 [("Вид","Type",[("Белый батон","White loaf",1),("Ржаной","Rye bread",1.15),("Цельнозерновой","Wholegrain",1.3)]),
  ("Вес","Weight",[("600 г","600 g",1),("400 г","400 g",.75),("1 кг","1 kg",1.6)])]),
("eggs","🥚","Яйца","Eggs",600,
 [("Категория","Category",[("С1","C1",1),("С0 (отборные)","C0",1.12)]),
  ("Упаковка","Pack",[("10 шт","10 pcs",1),("20 шт","20 pcs",1.95),("30 шт","30 pcs",2.85)])]),
("rice","🍚","Рис","Rice",540,
 [("Вид","Type",[("Кызылординский","Kyzylorda rice",1),("Басмати","Basmati",2.5),("Пропаренный","Parboiled",1.25)]),
  ("Вес","Weight",[("1 кг","1 kg",1),("0,5 кг","0.5 kg",.55),("5 кг","5 kg",4.6)])]),
("water","💧","Вода","Water",220,
 [("Бренд","Brand",[("BonAqua","BonAqua",1),("Tassay","Tassay",.9),("Aseu","Aseu",.94)]),
  ("Объём","Size",[("1,5 л","1.5 L",1),("0,5 л","0.5 L",.55),("5 л","5 L",2.7)])]),
("sugar","🧂","Сахар","Sugar",430,
 [("Вес","Weight",[("1 кг","1 kg",1),("2 кг","2 kg",1.95),("5 кг","5 kg",4.7)])]),
("flour","🌾","Мука","Flour",540,
 [("Бренд","Brand",[("Макфа","Makfa",1),("Пионер","Pioner",.95),("Цесна","Tsesna",.98)]),
  ("Вес","Weight",[("1 кг","1 kg",1),("2 кг","2 kg",1.9),("5 кг","5 kg",4.5)])]),
("pasta","🍝","Макароны","Pasta",380,
 [("Бренд","Brand",[("Макфа","Makfa",1),("Barilla","Barilla",1.55),("Зерновая культура","Zernovaya kultura",.94)]),
  ("Форма","Shape",[("Спагетти","Spaghetti",1),("Спирали","Fusilli",1.05)])]),
("buckwheat","🌾","Гречка","Buckwheat",410,
 [("Бренд","Brand",[("Мистраль","Mistral",1.2),("Пассим","Passim",.95),("Цесна","Tsesna",.98)]),
  ("Вес","Weight",[("1 кг","1 kg",1),("0,5 кг","0.5 kg",.55),("5 кг","5 kg",4.8)])]),
("tea","🍵","Чёрный чай","Black tea",1100,
 [("Бренд","Brand",[("Lipton","Lipton",1),("Greenfield","Greenfield",1.05),("Ahmad Tea","Ahmad Tea",1.15)]),
  ("Упаковка","Pack",[("25 пакетиков","25 bags",1),("100 пакетиков","100 bags",3.6)])]),
("coffee","☕","Кофе","Coffee",2500,
 [("Бренд","Brand",[("Jacobs","Jacobs",1),("Nescafé","Nescafé",.95),("MacCoffee","MacCoffee",.78),("Carte Noire","Carte Noire",1.2)]),
  ("Вес","Weight",[("95 г","95 g",1),("200 г","200 g",1.9)])]),
("bananas","🍌","Бананы","Bananas",1160,
 [("Вес","Weight",[("1 кг","1 kg",1),("0,5 кг","0.5 kg",.52),("2 кг","2 kg",1.95)])]),
("apples","🍎","Яблоки","Apples",800,
 [("Сорт","Variety",[("Гала","Gala",1),("Голден","Golden",1.05),("Гренни Смит","Granny Smith",1.1)]),
  ("Вес","Weight",[("1 кг","1 kg",1),("0,5 кг","0.5 kg",.52),("2 кг","2 kg",1.95)])]),
("potatoes","🥔","Картофель","Potatoes",222,
 [("Вес","Weight",[("1 кг","1 kg",1),("2 кг","2 kg",1.95),("5 кг","5 kg",4.6)])]),
("tomatoes","🍅","Помидоры","Tomatoes",950,
 [("Вид","Type",[("Обычные","Regular",1),("Черри","Cherry",1.8)]),
  ("Вес","Weight",[("1 кг","1 kg",1),("0,5 кг","0.5 kg",.52)])]),
("cucumber","🥒","Огурцы","Cucumbers",850,
 [("Вид","Type",[("Обычные","Regular",1),("Мини","Mini",1.25)]),
  ("Вес","Weight",[("1 кг","1 kg",1),("0,5 кг","0.5 kg",.52)])]),
("chicken","🍗","Курица","Chicken",1730,
 [("Часть","Cut",[("Тушка","Whole",1),("Филе","Fillet",1.7),("Голень","Drumsticks",1.15)]),
  ("Вес","Weight",[("1 кг","1 kg",1),("0,5 кг","0.5 kg",.52),("2 кг","2 kg",1.95)])]),
("sausages","🌭","Сосиски","Sausages",1900,
 [("Бренд","Brand",[("Индилайт","Indilight",1),("Пава-Пава","Pava-Pava",.95),("Ремит","Remit",1.08)]),
  ("Вес","Weight",[("440 г","440 g",1),("600 г","600 g",1.32)])]),
("cheese","🧀","Сыр","Cheese",2800,
 [("Бренд","Brand",[("Hochland","Hochland",1),("President","President",1.08),("Сваля","Svalya",1.12)]),
  ("Вес","Weight",[("200 г","200 g",1),("400 г","400 g",1.9)])]),
("butter","🧈","Сливочное масло","Butter",1200,
 [("Бренд","Brand",[("Петропавловское","Petropavlovsk",1),("Маслозавод","Maslozavod",.96),("President","President",1.1),("Родина","Rodina",.98)]),
  ("Вес","Weight",[("180 г","180 g",1),("200 г","200 g",1.1),("500 г","500 g",2.65)])]),
("yogurt","🥣","Йогурт","Yogurt",430,
 [("Бренд","Brand",[("Activia","Activia",1),("Данон","Danone",1.02),("Растишка","Rastishka",.95)]),
  ("Объём","Size",[("120 г","120 g",1),("260 г","260 g",2.05)])]),
("juice","🧃","Сок","Juice",850,
 [("Бренд","Brand",[("Добрый","Dobry",1),("J7","J7",1.25),("DaDa","DaDa",.88)]),
  ("Объём","Size",[("1 л","1 L",1),("2 л","2 L",1.85)])]),
("cola","🥤","Coca-Cola","Coca-Cola",650,
 [("Объём","Size",[("0,5 л","0.5 L",1),("1 л","1 L",1.65),("2 л","2 L",2.6)])]),
("chocolate","🍫","Шоколад","Chocolate",550,
 [("Бренд","Brand",[("Roshen","Roshen",1),("Alpen Gold","Alpen Gold",1.08),("Milka","Milka",1.35)]),
  ("Вес","Weight",[("80 г","80 g",1),("90 г","90 g",1.12),("100 г","100 g",1.25)])]),
("cookies","🍪","Печенье","Cookies",650,
 [("Бренд","Brand",[("Юбилейное","Yubileynoye",1),("OREO","OREO",1.35),("Любятово","Lyubyatovo",.94)]),
  ("Вес","Weight",[("126 г","126 g",1),("228 г","228 g",1.75)])]),
("cereal","🥣","Хлопья","Cereal",1050,
 [("Бренд","Brand",[("Nestlé","Nestlé",1),("Kellogg's","Kellogg's",1.25),("Любятово","Lyubyatovo",.9)]),
  ("Вес","Weight",[("300 г","300 g",1),("500 г","500 g",1.55)])]),
("oil","🫗","Подсолнечное масло","Sunflower oil",900,
 [("Бренд","Brand",[("Злато","Zlato",1),("Аведовъ","Avedov",.96),("ARO","ARO",.88)]),
  ("Объём","Size",[("1 л","1 L",1),("2 л","2 L",1.9)])]),
("ketchup","🍅","Кетчуп","Ketchup",650,
 [("Бренд","Brand",[("Heinz","Heinz",1),("Calve","Calve",.92),("Махеевъ","Makheev",.85)]),
  ("Вес","Weight",[("350 г","350 g",1),("500 г","500 g",1.4)])]),
("mayonnaise","🥫","Майонез","Mayonnaise",750,
 [("Бренд","Brand",[("Махеевъ","Makheev",1),("Calve","Calve",1.08),("Sloboda","Sloboda",.98)]),
  ("Вес","Weight",[("400 мл","400 ml",1),("800 мл","800 ml",1.9)])]),
("detergent","🧺","Стиральный порошок","Laundry detergent",3100,
 [("Бренд","Brand",[("Ariel","Ariel",1),("Tide","Tide",.92),("Persil","Persil",1.1)]),
  ("Вес","Weight",[("3 кг","3 kg",1),("6 кг","6 kg",1.9)])]),
("shampoo","🧴","Шампунь","Shampoo",1700,
 [("Бренд","Brand",[("Pantene","Pantene",1),("Head & Shoulders","Head & Shoulders",1.08),("Elseve","Elseve",1.05)]),
  ("Объём","Size",[("400 мл","400 ml",1),("650 мл","650 ml",1.55)])]),
("petfood","🐱","Корм для животных","Pet food",550,
 [("Бренд","Brand",[("ARO","ARO",1),("Whiskas","Whiskas",1.3),("Purina","Purina",1.25)]),
  ("Вес","Weight",[("400 г","400 g",1),("800 г","800 g",1.9)])]),
]

# Store-specific demo coefficients. They create variation so the app can compare
# stores even though it does not have a live price API.
STORE_FACTOR = [0.96, 1.00, 1.08, 0.98, 1.02, 0.94, 0.97, 1.06, 1.01, 0.99]

PRODUCTS = {
    x[0]: {
        "id":x[0], "emoji":x[1], "ru":x[2], "en":x[3], "base":x[4],
        "groups":x[5]
    } for x in P
}

TEXT = {
"ru": {
"tag":"АСТАНА","hero":"Не переплачивайте в Астане",
"sub":"Сравнивайте цены, выбирайте магазин и собирайте список покупок.",
"search":"Найти продукт, например молоко","all":"Все продукты","found":"Найденные продукты",
"back":"Назад","choose":"Выберите вариант","cheapest":"ДЕШЕВЛЕ ВСЕГО",
"add":"В список","move":"Перенести в этот магазин","inlist":"✓ В списке",
"list":"Мой список","view":"Открыть список","empty":"Список пуст",
"find":"Найти продукты","total":"Итого","clear":"Очистить список",
"branches":"Филиалы","save":"Покупайте в {shop} и сэкономьте до {money}",
"note":"Цены в приложении демонстрационные и не являются актуальными ценами магазинов. Перед покупкой проверяйте цену в магазине.",
"shops":"Магазины Астаны","copy":"Скопировать список","copied":"Список скопирован",
"removed":"Удалить","items":"шт.","increase":"Больше","decrease":"Меньше",
},
"en": {
"tag":"ASTANA","hero":"Stop overpaying in Astana",
"sub":"Compare prices, choose a store and build your shopping list.",
"search":"Search a product, e.g. milk","all":"All products","found":"Matching products",
"back":"Back","choose":"Choose an option","cheapest":"CHEAPEST",
"add":"Add to list","move":"Move to this shop","inlist":"✓ On your list",
"list":"My list","view":"View list","empty":"Your list is empty",
"find":"Find products","total":"Total","clear":"Clear list",
"branches":"Branches","save":"Buy at {shop} and save up to {money}",
"note":"Prices in this app are demonstration values, not live shop prices. Check the shelf price before buying.",
"shops":"Astana stores","copy":"Copy list","copied":"List copied",
"removed":"Remove","items":"items","increase":"Increase","decrease":"Decrease",
}}


# ============================================================
# v4: categories, favourites, value rating, student mode, GPS
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(BASE_DIR, "overprice_settings.json")   # favourites, budget, language
GEO_FILE = os.path.join(BASE_DIR, "overprice_geo_cache.json")       # coordinates of store branches
AUDIT_FILE = os.path.join(BASE_DIR, "overprice_audit.log")          # tamper-evident security log

# --- categories: id, emoji, RU, EN, product ids ---
CATEGORIES = [
    ("dairy",  "🥛", "Молочное и яйца", "Dairy & eggs",
     ["milk", "kefir", "smetana", "tvorog", "yogurt", "cheese", "butter", "eggs"]),
    ("grains", "🍞", "Хлеб и крупы", "Bread & grains",
     ["bread", "flour", "rice", "pasta", "buckwheat", "cereal"]),
    ("meat",   "🍗", "Мясо и колбасы", "Meat",
     ["chicken", "sausages"]),
    ("fruit",  "🍎", "Овощи и фрукты", "Fruit & veg",
     ["bananas", "apples", "potatoes", "tomatoes", "cucumber"]),
    ("drinks", "🥤", "Напитки", "Drinks",
     ["water", "juice", "cola", "tea", "coffee"]),
    ("pantry", "🧂", "Бакалея", "Pantry",
     ["sugar", "oil", "ketchup", "mayonnaise"]),
    ("sweets", "🍫", "Сладости", "Sweets",
     ["chocolate", "cookies"]),
    ("home",   "🧺", "Дом и питомцы", "Home & pets",
     ["detergent", "shampoo", "petfood"]),
]

# --- places for "choose where I am" (approximate coordinates of well-known Astana places) ---
LANDMARKS = [
    ("Байтерек", "Baiterek", 51.1283, 71.4305),
    ("Хан Шатыр", "Khan Shatyr", 51.1328, 71.4038),
    ("Mega Silk Way", "Mega Silk Way", 51.1318, 71.4090),
    ("Астана Арена", "Astana Arena", 51.1082, 71.4025),
    ("ЭКСПО", "EXPO", 51.0904, 71.4166),
    ("Назарбаев Университет", "Nazarbayev University", 51.0905, 71.3980),
    ("Аэропорт Астана", "Astana Airport", 51.0222, 71.4669),
]

# --- value rating settings (assumptions, change them if you like) ---
TRAVEL_COST_PER_KM = 60     # ₸ per km one way (bus/taxi/time). A round trip is counted twice.
ROAD_FACTOR = 1.25          # straight line -> real road distance
WALK_MIN_PER_KM = 12        # walking speed 5 km/h
ANALOG_GROUPS = {"Бренд", "Сорт", "Категория", "Форма"}   # groups where another option is an equal replacement

NOMINATIM = "https://nominatim.openstreetmap.org/search"
ASTANA_BOX = "71.20,51.25,71.75,50.95"

TEXT["ru"].update({
"tab_products": "Продукты", "tab_fav": "Избранное", "tab_student": "Студент",
"all_cat": "Все", "fav_empty": "В избранном пока пусто", "fav_hint": "Нажмите ♡ на карточке продукта, чтобы добавить его сюда.",
"fav_add": "♡ В избранное", "fav_on": "♥ В избранном",
"branches_hint": "Магазины и филиалы (нажмите на адрес, чтобы открыть карту)", "more": "ещё {n}", "less": "свернуть",
"whole": "Весь список в одном магазине", "list_title": "Список покупок",
"empty_hint": "Выберите продукт, бренд и объём и добавьте его из нужного магазина.",
"added": "{p}: добавлено из {s}", "moved": "{p}: перенесено в {s}", "gone": "{p}: удалено",
"undo": "Отменить", "cleared": "Список очищен", "from": "от", "rice_unit": "Рис, 1 кг",
"loc_unknown": "Местоположение не определено — расстояния не учитываются",
"loc_waiting": "Жду разрешение на доступ к местоположению в браузере…",
"loc_set": "Я здесь: {name}", "loc_err": "Не удалось получить GPS. Выберите место вручную.",
"gps_btn": "📡 GPS", "place_btn": "🗺 Выбрать место", "loc_clear": "Сбросить",
"geo_progress": "Считаю расстояния: {done}/{total}", "geo_fail": "Не найдены адреса: {n}",
"place_title": "Где вы находитесь?", "cancel": "Отмена",
"sort_value": "Выгодность", "sort_price": "Цена", "sort_dist": "Расстояние",
"score": "Выгодность {n}/100", "best_tag": "ЛУЧШИЙ ВЫБОР",
"dist_line": "📏 {km} · ≈{min} мин пешком",
"adv_same": "Лучший вариант для вас: {best}. Самая низкая цена, и магазин находится близко: {km}.",
"adv_same_far": "Лучший вариант для вас: {best}. Самая низкая цена — она выгоднее, даже с учётом дороги ({km}).",
"adv_diff": "Лучший вариант для вас: {best}. Цена на {diff} выше, чем в {cheap}, зато магазин ближе: {km_best} вместо {km_cheap}.",
"adv_nogps": "Определите местоположение (GPS), чтобы учитывать расстояние до магазинов.",
"stu_desc": "Задайте бюджет — OverPrice предупредит о перерасходе и предложит более дешёвые аналоги.",
"budget_label": "💰 Мой бюджет: {m}", "budget_ph": "Сумма в тенге", "apply": "Применить",
"mode_on": "Режим студента: ВКЛ", "mode_off": "Режим студента: ВЫКЛ",
"spent": "Потрачено {a} из {b}", "left": "Осталось {m}", "over": "⚠️ Вы превысили бюджет на {m}",
"save_tip": "Можно сэкономить {m}, заменив {n} {w} на более дешёвые аналоги.",
"show_swaps": "Показать замены", "hide_swaps": "Скрыть замены", "swap": "Заменить", "swap_all": "Заменить все",
"enough": "Этого хватит, чтобы уложиться в бюджет.", "notenough": "Этого пока недостаточно — уберите ещё что-нибудь.",
"budget_bad": "Введите сумму больше 0", "no_budget": "Бюджет не задан.", "no_swaps": "Более дешёвых аналогов не нашлось.",
"dock_left": "осталось {m}", "dock_over": "перерасход {m}",
})
TEXT["en"].update({
"tab_products": "Products", "tab_fav": "Favorites", "tab_student": "Student",
"all_cat": "All", "fav_empty": "No favorites yet", "fav_hint": "Tap ♡ on a product card to add it here.",
"fav_add": "♡ Add to favorites", "fav_on": "♥ In favorites",
"branches_hint": "Stores and branches (click an address to open the map)", "more": "{n} more", "less": "show less",
"whole": "Your whole list in one shop", "list_title": "Shopping list",
"empty_hint": "Pick a product, choose brand and size, and add it from the shop you like.",
"added": "{p} added from {s}", "moved": "{p} moved to {s}", "gone": "{p} removed",
"undo": "Undo", "cleared": "List cleared", "from": "from", "rice_unit": "Rice, 1 kg",
"loc_unknown": "Location not set — distances are not used",
"loc_waiting": "Waiting for location permission in your browser…",
"loc_set": "I am here: {name}", "loc_err": "Could not get GPS. Choose a place manually.",
"gps_btn": "📡 GPS", "place_btn": "🗺 Choose place", "loc_clear": "Reset",
"geo_progress": "Measuring distances: {done}/{total}", "geo_fail": "Addresses not found: {n}",
"place_title": "Where are you?", "cancel": "Cancel",
"sort_value": "Best value", "sort_price": "Price", "sort_dist": "Distance",
"score": "Value {n}/100", "best_tag": "BEST CHOICE",
"dist_line": "📏 {km} · ≈{min} min on foot",
"adv_same": "Best option for you: {best}. Lowest price and the store is close: {km}.",
"adv_same_far": "Best option for you: {best}. Lowest price — worth it even after the trip ({km}).",
"adv_diff": "Best option for you: {best}. The price is {diff} higher than at {cheap}, but the store is closer: {km_best} instead of {km_cheap}.",
"adv_nogps": "Set your location (GPS) so distances to the stores are taken into account.",
"stu_desc": "Set a budget — OverPrice warns you when you go over it and suggests cheaper alternatives.",
"budget_label": "💰 My budget: {m}", "budget_ph": "Amount in tenge", "apply": "Apply",
"mode_on": "Student mode: ON", "mode_off": "Student mode: OFF",
"spent": "Spent {a} of {b}", "left": "{m} left", "over": "⚠️ You are over budget by {m}",
"save_tip": "You can save {m} by swapping {n} {w} for cheaper alternatives.",
"show_swaps": "Show swaps", "hide_swaps": "Hide swaps", "swap": "Swap", "swap_all": "Swap all",
"enough": "That is enough to get back within budget.", "notenough": "That is not enough yet — remove something else.",
"budget_bad": "Enter an amount above 0", "no_budget": "No budget set.", "no_swaps": "No cheaper alternatives found.",
"dock_left": "{m} left", "dock_over": "over by {m}",
})

HEAD = "Trebuchet MS"      # headings (same as the web version)
BODY = "Segoe UI"          # body text
EMOJI = "Segoe UI Emoji"   # if emoji crash Tk on your Linux, set USE_EMOJI = False
USE_EMOJI = True
TAG_INK = "#3A2E00"
MAX_W = 520                # width of the content column
MAX_BRANCHES = 2           # branches shown before "+N more"
HEART_ON = "#FF8FA3"


def ru_plural(n, forms):
    n = abs(int(n)) % 100
    if 11 <= n <= 14:
        return forms[2]
    n %= 10
    return forms[0] if n == 1 else forms[1] if 2 <= n <= 4 else forms[2]


def haversine_km(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def recolor(widget, color):
    """Change the background of a widget and all its children (used for hover)."""
    if isinstance(widget, (tk.Frame, tk.Label)):
        try:
            widget.configure(bg=color)
        except tk.TclError:
            pass
    for child in widget.winfo_children():
        recolor(child, color)


def click_all(widget, command):
    """Make a widget and everything inside it clickable."""
    widget.bind("<Button-1>", lambda e: command())
    try:
        widget.configure(cursor="hand2")
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        click_all(child, command)


def hover_card(card):
    """Green highlight while the mouse is over a card."""
    def enter(e):
        recolor(card, MINT)
        card.configure(highlightbackground=BRAND)

    def leave(e):
        try:
            x, y = card.winfo_pointerxy()
            under = card.winfo_containing(x, y)
            if under is not None and str(under).startswith(str(card)):
                return
        except tk.TclError:
            pass
        recolor(card, SURFACE)
        card.configure(highlightbackground=LINE)

    def bind_tree(w):
        w.bind("<Enter>", enter, add="+")
        w.bind("<Leave>", leave, add="+")
        for c in w.winfo_children():
            bind_tree(c)
    bind_tree(card)


def hover_label(label, normal_bg, normal_fg, over_bg=HOVER_G, over_fg="#FFFFFF"):
    label.bind("<Enter>", lambda e: label.configure(bg=over_bg, fg=over_fg))
    label.bind("<Leave>", lambda e: label.configure(bg=normal_bg, fg=normal_fg))


class Btn(tk.Frame):
    """Label-based button. Same look on Windows, macOS and Linux. Turns green on hover."""

    def __init__(self, parent, text, command, bg=BRAND, fg=None, border=None,
                 font=(BODY, 10, "bold"), padx=14, pady=7, bw=1):
        primary = bg == BRAND
        fg = fg or (BRAND_INK if primary else INK)
        border = border or bg
        super().__init__(parent, bg=border, bd=0, highlightthickness=0)
        self.label = tk.Label(self, text=text, bg=bg, fg=fg, font=font, padx=padx, pady=pady,
                              cursor="hand2")
        self.label.pack(padx=bw, pady=bw)
        over_bg, over_fg, over_border = ((HOVER_LIGHT, BRAND_INK, HOVER_LIGHT) if primary
                                         else (HOVER_G, "#FFFFFF", BRAND))

        def enter(e):
            self.label.configure(bg=over_bg, fg=over_fg)
            self.configure(bg=over_border)

        def leave(e):
            self.label.configure(bg=bg, fg=fg)
            self.configure(bg=border)
        self.label.bind("<Enter>", enter)
        self.label.bind("<Leave>", leave)
        self.label.bind("<Button-1>", lambda e: command())
        self.bind("<Button-1>", lambda e: command())


class ScrollArea(tk.Frame):
    """Scrollable page with a column that is always centred."""

    def __init__(self, parent):
        super().__init__(parent, bg=BG)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.bar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview,
                                bg=LINE, troughcolor=BG, activebackground=BRAND, bd=0, width=12)
        self.canvas.configure(yscrollcommand=self.bar.set)
        self.bar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=BG)
        self.win = self.canvas.create_window((0, 0), window=self.inner, anchor="n")
        self.inner.bind("<Configure>", self._sync)
        self.canvas.bind("<Configure>", self._sync)
        self.canvas.bind_all("<MouseWheel>", self._wheel)                                   # Windows / macOS
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))  # Linux
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

    def _sync(self, event=None):
        # The scroll region starts at x=0 and is exactly as wide as the window,
        # so the column is centred (no shift to the left/right).
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.inner.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.itemconfigure(self.win, width=min(w, MAX_W))
        self.canvas.coords(self.win, w // 2, 0)
        self.canvas.configure(scrollregion=(0, 0, w, h))

    def _wheel(self, e):
        step = -int(e.delta / 120) if abs(e.delta) >= 120 else -e.delta
        self.canvas.yview_scroll(step, "units")

    def to_top(self):
        self.canvas.yview_moveto(0)


# ------------------------------------------------------------
# Security layer
# ------------------------------------------------------------
MAX_QUERY_LEN = 40
MAX_BUDGET = 10_000_000
ASTANA_BBOX = (50.95, 51.25, 71.20, 71.75)      # lat_min, lat_max, lon_min, lon_max
PRICE_TOLERANCE = 0.5                           # a price report must be within +-50% of the verified price
REPORT_LIMIT = (3, 60)                          # at most 3 price reports per 60 seconds
GPS_TIMEOUT_S = 60


def in_astana(lat, lon):
    return ASTANA_BBOX[0] <= lat <= ASTANA_BBOX[1] and ASTANA_BBOX[2] <= lon <= ASTANA_BBOX[3]


def clean_text(text, limit=MAX_QUERY_LEN):
    """Drop control characters and limit the length of any text typed by the user."""
    return "".join(ch for ch in str(text) if ch.isprintable())[:limit]


def like_escape(text):
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def write_private(path, text):
    """Write a file that only the current user can read (0600) and replace it atomically."""
    tmp = path + ".tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


class SearchIndex:
    """Product search through SQLite using PARAMETERIZED queries.
    The text typed by the user is passed as a parameter and is never part of the SQL string."""

    def __init__(self, products):
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.execute("CREATE TABLE item (id TEXT PRIMARY KEY, hay TEXT NOT NULL)")
        rows = []
        for p in products.values():
            hay = " ".join([p["ru"].lower(), p["en"].lower(), p["id"].lower(),
                            *[o[0].lower() for g in p["groups"] for o in g[2]],
                            *[o[1].lower() for g in p["groups"] for o in g[2]]])
            rows.append((p["id"], hay))
        self.db.executemany("INSERT INTO item (id, hay) VALUES (?, ?)", rows)

    def search(self, text):
        text = clean_text(text).lower().strip()
        if not text:
            return {r[0] for r in self.db.execute("SELECT id FROM item")}
        cur = self.db.execute("SELECT id FROM item WHERE hay LIKE ? ESCAPE '\\'",
                              ("%" + like_escape(text) + "%",))
        return {r[0] for r in cur}


class InjectionLab:
    """Controlled simulation on a throw-away in-memory database with FAKE data.
    It shows why gluing user text into SQL is dangerous. Nothing real is touched."""

    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.execute("CREATE TABLE demo_users (name TEXT, email TEXT)")
        self.db.executemany("INSERT INTO demo_users VALUES (?, ?)", [
            ("aigerim", "aigerim@example.test"), ("daulet", "daulet@example.test"),
            ("madina", "madina@example.test")])

    def unsafe(self, text):                      # BAD: the text becomes part of the SQL
        sql = "SELECT name, email FROM demo_users WHERE name = '" + text + "'"
        try:
            return self.db.execute(sql).fetchall(), sql
        except sqlite3.Error as e:
            return [], sql + "   -> " + str(e)

    def safe(self, text):                        # GOOD: the text is only a parameter
        return self.db.execute("SELECT name, email FROM demo_users WHERE name = ?", (text,)).fetchall()


class AuditLog:
    """Tamper-evident security log: every entry contains the SHA-256 hash of the previous one,
    so changing or deleting an old entry breaks the chain and is detected."""
    GENESIS = "0" * 64

    def __init__(self, path=None):
        self.path = path
        self.entries = []
        if path and os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    for line in f.readlines()[-500:]:
                        e = json.loads(line)
                        if isinstance(e, dict):
                            self.entries.append(e)
            except Exception:
                pass
        self.broken_at = self.verify(self.entries)

    @staticmethod
    def _hash(body):
        return hashlib.sha256(json.dumps(body, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

    @staticmethod
    def verify(entries):
        """Index of the first damaged entry, or None if the chain is intact."""
        prev = entries[0].get("prev") if entries else AuditLog.GENESIS
        for i, e in enumerate(entries):
            try:
                body = {k: e[k] for k in ("t", "event", "data", "prev")}
                if e["prev"] != prev or AuditLog._hash(body) != e["hash"]:
                    return i
                prev = e["hash"]
            except (KeyError, TypeError):
                return i
        return None

    def add(self, event, data):
        prev = self.entries[-1]["hash"] if self.entries else self.GENESIS
        body = {"t": int(time.time()), "event": event, "data": data, "prev": prev}
        entry = dict(body, hash=self._hash(body))
        self.entries.append(entry)
        if self.path:
            try:
                fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                with os.fdopen(fd, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError:
                pass
        return entry


class PriceGuard:
    """Checks every price report. A report NEVER changes a displayed price or the ranking:
    at best it becomes 'pending review'. Every attempt is written to the audit log."""

    def __init__(self, audit):
        self.audit = audit
        self.times = []

    def check(self, raw_value, trusted_price, ctx):
        now = time.time()
        self.times = [t for t in self.times if now - t < REPORT_LIMIT[1]]
        status, reason, value = "pending", "ok", None
        try:
            value = float(clean_text(raw_value, 20).replace(",", ".").replace(" ", "").replace("₸", ""))
            if not math.isfinite(value):
                raise ValueError
        except ValueError:
            status, reason = "rejected", "not_a_number"
        if status == "pending":
            low, high = trusted_price * (1 - PRICE_TOLERANCE), trusted_price * (1 + PRICE_TOLERANCE)
            if value <= 0 or value < low or value > high:
                status, reason = "rejected", "out_of_range"
        if status == "pending" and len(self.times) >= REPORT_LIMIT[0]:
            status, reason = "rejected", "rate_limit"
        self.times.append(now)
        self.audit.add("price_report", dict(ctx, value=value if value is not None else clean_text(raw_value, 20),
                                            trusted=trusted_price, status=status, reason=reason))
        return status, reason, value


class LocationBridge:
    """Gets the real location from the browser (GPS / Wi-Fi / network) via a tiny local web page.

    Desktop Python cannot read GPS directly, but every browser can (navigator.geolocation).
    Protection: listens on 127.0.0.1 only, secret random token in the URL, Host header check
    (against DNS rebinding), strict security headers, only the first valid answer is accepted
    and the bridge expires after 60 seconds. Nothing leaves the computer.
    """
    PAGE = """<!doctype html><meta charset="utf-8"><title>OverPrice GPS</title>
<body style="font-family:Arial,sans-serif;background:#0E1914;color:#E8F1EC;text-align:center;padding:48px">
<h2 id="m">OverPrice: please allow location access in your browser...</h2>
<script nonce="__NONCE__">
function send(p){return fetch(p).catch(function(){})}
navigator.geolocation.getCurrentPosition(function(p){
  send('/__TOKEN__/loc?lat='+p.coords.latitude+'&lon='+p.coords.longitude+'&acc='+p.coords.accuracy).then(function(){
    document.getElementById('m').textContent='Location sent to OverPrice. You can close this tab.'})
},function(e){
  send('/__TOKEN__/err?code='+e.code);
  document.getElementById('m').textContent='Location is not available ('+e.message+'). Go back to OverPrice and choose a place manually.'
},{enableHighAccuracy:true,timeout:20000,maximumAge:0});
</script></body>"""

    def __init__(self):
        self.result = None          # (lat, lon, accuracy_m)
        self.error = None
        self.denied = 0             # rejected requests (wrong token / host / expired)
        self.token = secrets.token_urlsafe(16)
        self.expires = time.time() + GPS_TIMEOUT_S
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, body, ctype="text/plain", status=200, nonce=None):
                data = body.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", ctype + "; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Referrer-Policy", "no-referrer")
                csp = "default-src 'none'; connect-src 'self'"
                if nonce:
                    csp += f"; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'"
                self.send_header("Content-Security-Policy", csp)
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                host_ok = self.headers.get("Host", "") in (f"127.0.0.1:{bridge.port}", f"localhost:{bridge.port}")
                parts = urlparse(self.path)
                segs = [s for s in parts.path.split("/") if s]
                token_ok = bool(segs) and hmac.compare_digest(segs[0], bridge.token)
                if not (host_ok and token_ok) or time.time() > bridge.expires:
                    bridge.denied += 1
                    self._send("forbidden", status=403)
                    return
                action = segs[1] if len(segs) > 1 else ""
                q = parse_qs(parts.query)
                if action == "loc":
                    if bridge.result is None:                 # only the first valid answer counts
                        try:
                            lat, lon = float(q["lat"][0]), float(q["lon"][0])
                            acc = float(q.get("acc", ["0"])[0])
                            if -90 <= lat <= 90 and -180 <= lon <= 180:
                                bridge.result = (lat, lon, acc)
                            else:
                                bridge.error = "range"
                        except (KeyError, ValueError):
                            bridge.error = "bad"
                    self._send("ok")
                elif action == "err":
                    bridge.error = q.get("code", ["?"])[0][:10]
                    self._send("ok")
                else:
                    nonce = secrets.token_urlsafe(12)
                    page = LocationBridge.PAGE.replace("__NONCE__", nonce).replace("__TOKEN__", bridge.token)
                    self._send(page, "text/html", nonce=nonce)

        self.server = HTTPServer(("127.0.0.1", 0), Handler)      # localhost only, random free port
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def url(self):
        return f"http://127.0.0.1:{self.port}/{self.token}/"

    def close(self):
        try:
            self.server.shutdown()
            self.server.server_close()
        except Exception:
            pass


class Geocoder(threading.Thread):
    """Finds coordinates of store branches (OpenStreetMap Nominatim, max 1 request/second, cached)."""

    def __init__(self, items, cache):
        super().__init__(daemon=True)
        self.items = items          # [(key, query)]
        self.cache = cache          # key -> (lat, lon)
        self.total = len(items)
        self.done = 0
        self.failed = 0
        self.changed = False

    def run(self):
        for key, query in self.items:
            if key not in self.cache:
                try:
                    url = NOMINATIM + "?" + urlencode({
                        "q": query, "format": "json", "limit": 1,
                        "viewbox": ASTANA_BOX, "bounded": 1, "accept-language": "ru"})
                    req = Request(url, headers={"User-Agent": "OverPrice-Astana-student-project/1.0"})
                    # Privacy: only the BRANCH ADDRESS is sent (never the user's location), over HTTPS.
                    with urlopen(req, timeout=10) as r:
                        data = json.loads(r.read(200_000).decode("utf-8"))      # size limit
                    lat, lon = (float(data[0]["lat"]), float(data[0]["lon"])) if data else (None, None)
                    if lat is not None and in_astana(lat, lon):                # reject results outside Astana
                        self.cache[key] = (lat, lon)
                        self.changed = True
                    else:
                        self.failed += 1
                except Exception:
                    self.failed += 1
                time.sleep(1.1)       # Nominatim usage policy
            self.done += 1


def geocode_query(branch):
    """Street + house number of a branch, without the mall name in brackets."""
    if "филиалы" in branch:
        return None
    text = branch.split("(")[0].strip().rstrip(",")
    return f"{text}, Астана"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("OverPrice – Astana")
        self.geometry("580x900")
        self.minsize(480, 640)
        self.configure(bg=BG)

        self.lang = "ru"
        self.page = "home"
        self.tab = "products"           # products | favorites | student
        self.category = "all"
        self.stack = []
        self.query = tk.StringVar()
        self.budget_var = tk.StringVar()
        self.product_id = None
        self.selected = {}
        self.cart = []
        self.fav = set()
        self.expanded = set()
        self.sort_mode = "value"        # value | price | dist
        self.student = False
        self.budget = None
        self.show_swaps = False
        self.last_removed = None
        self.toast_frame = None
        self.toast_job = None

        # location
        self.user_loc = None            # (lat, lon)
        self.loc_name = ""
        self.loc_acc = None
        self.loc_status = ""            # "", "waiting", "error"
        self.bridge = None
        self.gps_ticks = 0
        self.geo = {}                   # "store|branch" -> (lat, lon)
        self.geocoder = None

        self.audit = AuditLog(AUDIT_FILE)
        self.guard = PriceGuard(self.audit)
        self.index = SearchIndex(PRODUCTS)
        self.reports = []               # price reports waiting for review (never used in the ranking)
        self.denied_total = 0           # rejected requests to the GPS bridge
        self.lab = {}                   # results of the Security Lab
        self.lab_sql_var = tk.StringVar(value="' OR '1'='1")
        self.lab_price_var = tk.StringVar(value="1")
        self.load_state()
        self.dock_frame = tk.Frame(self, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
        self.scroll = ScrollArea(self)
        self.scroll.pack(fill="both", expand=True)
        self.pf = self.scroll.inner
        self.render(top=True)
        if self.audit.broken_at is not None:
            self.after(800, lambda: self.show_toast(self.t2("⚠ Журнал безопасности был изменён!",
                                                           "⚠ The security log was modified!"), warn=True))

    # ---------- storage ----------
    def load_state(self):
        """Local files are treated as untrusted input: every value is validated."""
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as f:
                s = json.load(f)
            if not isinstance(s, dict):
                raise ValueError
            if s.get("lang") in ("ru", "en"):
                self.lang = s["lang"]
            fav = s.get("fav", [])
            if isinstance(fav, list):
                self.fav = {x for x in fav if isinstance(x, str) and x in PRODUCTS}
            b = s.get("budget")
            if isinstance(b, int) and not isinstance(b, bool) and 0 < b <= MAX_BUDGET:
                self.budget = b
                self.budget_var.set(str(b))
            self.student = s.get("student") is True
        except Exception:
            pass
        self.geo = {}
        try:
            with open(GEO_FILE, encoding="utf-8") as f:
                raw = json.load(f)
            for k, v in raw.items():
                if (isinstance(k, str) and isinstance(v, list) and len(v) == 2
                        and all(isinstance(n, (int, float)) and not isinstance(n, bool) for n in v)
                        and in_astana(v[0], v[1])):
                    self.geo[k] = (float(v[0]), float(v[1]))
        except Exception:
            self.geo = {}

    def save_state(self):
        # The user's location is deliberately NOT saved.
        try:
            write_private(SETTINGS_FILE, json.dumps({"lang": self.lang, "fav": sorted(self.fav),
                                                     "budget": self.budget, "student": self.student},
                                                    ensure_ascii=False))
        except Exception:
            pass

    def save_geo(self):
        try:
            write_private(GEO_FILE, json.dumps({k: list(v) for k, v in self.geo.items()}, ensure_ascii=False))
        except Exception:
            pass

    # ---------- basics ----------
    def tr(self, key, **kw):
        return TEXT[self.lang][key].format(**kw) if kw else TEXT[self.lang][key]

    def money(self, n):
        return f"{int(n):,}".replace(",", "\u00a0") + " ₸"

    def fmt_km(self, km):
        if km is None:
            return "—"
        if km < 1:
            m = int(round(km * 1000 / 10.0) * 10)
            return f"{m} м" if self.lang == "ru" else f"{m} m"
        s = f"{km:.1f}"
        return (s.replace(".", ",") + " км") if self.lang == "ru" else (s + " km")

    def price(self, p, selection, store):
        factor = 1
        for i, group in enumerate(p["groups"]):
            factor *= group[2][selection[i]][2]
        # deterministic +-3% difference per product and store, so the cheapest shop changes between products
        jitter = 0.97 + (zlib.crc32(f'{p["id"]}:{store}'.encode()) % 7) / 100
        return round(p["base"] * factor * STORE_FACTOR[store] * jitter / 10) * 10

    def variant_preview(self, p, sel):
        k = 0 if self.lang == "ru" else 1
        return " · ".join(g[2][sel[i]][k] for i, g in enumerate(p["groups"]))

    def L(self, parent, text, size=10, bold=False, fg=INK, bg=BG, family=BODY, **kw):
        return tk.Label(parent, text=text, bg=bg, fg=fg,
                        font=(family, size, "bold" if bold else "normal"), **kw)

    def emoji(self, parent, text, size, bg):
        if not USE_EMOJI:
            text = ""
        return tk.Label(parent, text=text, bg=bg, fg=INK, font=(EMOJI, size))

    def card(self, parent, border=LINE, bw=1, padx=18, pady=5):
        c = tk.Frame(parent, bg=SURFACE, highlightbackground=border, highlightthickness=bw)
        c.pack(fill="x", padx=padx, pady=pady)
        return c

    def badge(self, parent, text, bg=YELLOW, fg=TAG_INK):
        return tk.Label(parent, text=text, bg=bg, fg=fg, font=(HEAD, 8, "bold"), padx=7, pady=2)

    def price_bar(self, parent, share, best, bg=SURFACE, color=None):
        c = tk.Canvas(parent, height=12, bg=bg, highlightthickness=0, bd=0)

        def draw(e):
            c.delete("all")
            c.create_rectangle(0, 0, e.width, 12, fill=LINE, outline="")
            c.create_rectangle(0, 0, e.width * share, 12, fill=color or (BRAND if best else BAR), outline="")
        c.bind("<Configure>", draw)
        return c

    def segmented(self, parent, options, current, callback):
        seg = tk.Frame(parent, bg=LINE)
        for key, text in options:
            on = key == current
            lab = tk.Label(seg, text=text, bg=BRAND if on else SURFACE, fg=BRAND_INK if on else MUTED,
                           font=(BODY, 9, "bold"), padx=12, pady=7, cursor="hand2")
            lab.pack(side="left", padx=1, pady=1)
            lab.bind("<Button-1>", lambda e, k=key: callback(k))
            if not on:
                hover_label(lab, SURFACE, MUTED)
        return seg

    # ---------- navigation ----------
    def go(self, page):
        self.stack.append(self.page)
        self.page = page
        self.render(top=True)

    def back(self):
        if self.stack:
            self.page = self.stack.pop()
            self.render(top=True)

    def go_home(self):
        self.stack = []
        self.page = "home"
        self.render(top=True)

    def set_tab(self, tab):
        self.tab = tab
        self.render(top=True)

    def set_lang(self, lang):
        self.lang = lang
        self.save_state()
        self.render()

    def render(self, top=False):
        for w in self.pf.winfo_children():
            w.destroy()
        {"home": self.page_home, "compare": self.page_compare, "list": self.page_list}[self.page]()
        self.update_dock()
        if top:
            self.scroll.to_top()

    # ---------- top pieces ----------
    def topbar(self, back=False):
        top = tk.Frame(self.pf, bg=BG)
        top.pack(fill="x", padx=18, pady=(14, 10))
        if back:
            Btn(top, "← " + self.tr("back"), self.back, bg=BG, fg=BRAND, border=BG,
                font=(HEAD, 12, "bold"), padx=8, pady=5).pack(side="left")
        else:
            tk.Label(top, text=f'{self.tr("tag")} • OVERPRICE', bg=YELLOW, fg=TAG_INK,
                     font=(HEAD, 9, "bold"), padx=10, pady=5).pack(side="left")
        seg = tk.Frame(top, bg=LINE)
        seg.pack(side="right")
        for code in ("en", "ru"):
            on = self.lang == code
            lab = tk.Label(seg, text=code.upper(), bg=BRAND if on else SURFACE,
                           fg=BRAND_INK if on else MUTED, font=(BODY, 9, "bold"),
                           padx=12, pady=6, cursor="hand2")
            lab.pack(side="left", padx=(1, 0) if code == "en" else (0, 1), pady=1)
            lab.bind("<Button-1>", lambda e, c=code: self.set_lang(c))
            if not on:
                hover_label(lab, SURFACE, MUTED)

    def hero(self):
        hero = tk.Frame(self.pf, bg=DARK)
        hero.pack(fill="x", padx=18, pady=(0, 12))
        left = tk.Frame(hero, bg=DARK)
        left.pack(side="left", fill="both", expand=True)
        self.L(left, self.tr("hero"), 21, True, "white", DARK, HEAD, wraplength=280,
               justify="left").pack(anchor="w", padx=18, pady=(16, 3))
        self.L(left, self.tr("sub"), 10, False, "#CADCD2", DARK, wraplength=280,
               justify="left").pack(anchor="w", padx=18, pady=(0, 16))
        rice = PRODUCTS["rice"]
        sel = [0] * len(rice["groups"])
        low = min(self.price(rice, sel, i) for i in range(len(STORES)))
        box = tk.Frame(hero, bg="#12503D", highlightbackground="#2C7A5F", highlightthickness=1)
        box.pack(side="right", padx=(0, 14), pady=14)
        self.L(box, self.tr("rice_unit"), 9, False, "#CADCD2", "#12503D").pack(padx=12, pady=(8, 0))
        self.L(box, self.money(low), 18, True, "white", "#12503D", HEAD).pack(padx=12)
        self.badge(box, self.tr("cheapest")).pack(pady=(3, 9))

    def location_card(self):
        c = self.card(self.pf, pady=(0, 10))
        row = tk.Frame(c, bg=SURFACE)
        row.pack(fill="x", padx=12, pady=10)
        if self.user_loc:
            text = "📍 " + self.tr("loc_set", name=self.loc_name or "GPS")
            if self.loc_acc:
                text += f" (±{int(self.loc_acc)} м)" if self.lang == "ru" else f" (±{int(self.loc_acc)} m)"
        elif self.loc_status == "waiting":
            text = "📡 " + self.tr("loc_waiting")
        elif self.loc_status == "error":
            text = "⚠️ " + self.tr("loc_err")
        else:
            text = "📍 " + self.tr("loc_unknown")
        info = tk.Frame(row, bg=SURFACE)
        info.pack(side="left", fill="x", expand=True)
        self.L(info, text, 10, True, INK, SURFACE, wraplength=300, justify="left").pack(anchor="w")
        g = self.geocoder
        if self.user_loc and g is not None and g.is_alive():
            self.L(info, self.tr("geo_progress", done=g.done, total=g.total), 9, False, MUTED,
                   SURFACE).pack(anchor="w")
        elif self.user_loc and g is not None and g.failed:
            self.L(info, self.tr("geo_fail", n=g.failed), 9, False, MUTED, SURFACE).pack(anchor="w")
        btns = tk.Frame(row, bg=SURFACE)
        btns.pack(side="right")
        Btn(btns, self.tr("gps_btn"), self.use_gps, padx=10, pady=5).pack(side="left", padx=(0, 6))
        Btn(btns, self.tr("place_btn"), self.choose_place, bg=SURFACE, border=LINE,
            padx=10, pady=5).pack(side="left")
        if self.user_loc:
            clr = tk.Label(btns, text="✕", bg=SURFACE, fg=MUTED, font=(BODY, 11, "bold"),
                           padx=8, cursor="hand2")
            clr.pack(side="left")
            clr.bind("<Button-1>", lambda e: self.clear_location())
            hover_label(clr, SURFACE, MUTED, over_bg=SURFACE, over_fg=BRAND)

    def tabbar(self):
        bar = tk.Frame(self.pf, bg=BG)
        bar.pack(fill="x", padx=18, pady=(0, 10))
        tabs = [("products", self.tr("tab_products")),
                ("favorites", f'♥ {self.tr("tab_fav")}' + (f" ({len(self.fav)})" if self.fav else "")),
                ("student", "🎓 " + self.tr("tab_student")),
                ("security", "🔒 " + self.t2("Защита", "Security"))]
        for i, (key, text) in enumerate(tabs):
            on = self.tab == key
            lab = tk.Label(bar, text=text, bg=BRAND if on else SURFACE,
                           fg=BRAND_INK if on else INK, font=(HEAD, 10, "bold"),
                           padx=8, pady=9, cursor="hand2")
            lab.pack(side="left", fill="x", expand=True, padx=(0 if i == 0 else 4, 0))
            lab.bind("<Button-1>", lambda e, k=key: self.set_tab(k))
            if not on:
                hover_label(lab, SURFACE, INK)

    def update_dock(self):
        for w in self.dock_frame.winfo_children():
            w.destroy()
        if not self.cart or self.page == "list":
            self.dock_frame.pack_forget()
            return
        self.dock_frame.pack(side="bottom", fill="x", before=self.scroll)
        info = tk.Frame(self.dock_frame, bg=SURFACE)
        info.pack(side="left", padx=16, pady=8)
        self.L(info, self.money(self.cart_total()), 14, True, INK, SURFACE, HEAD).pack(anchor="w")
        count = sum(x["qty"] for x in self.cart)
        line = f'{count} {self.tr("items")}'
        color = MUTED
        if self.student and self.budget:
            diff = self.budget - self.cart_total()
            line += " · 💰 " + (self.tr("dock_left", m=self.money(diff)) if diff >= 0
                                 else self.tr("dock_over", m=self.money(-diff)))
            color = MUTED if diff >= 0 else WARN
        self.L(info, line, 9, False, color, SURFACE).pack(anchor="w")
        Btn(self.dock_frame, self.tr("view"), lambda: self.go("list"),
            font=(BODY, 11, "bold"), padx=16, pady=9).pack(side="right", padx=14, pady=8)

    def show_toast(self, text, undo=False, warn=False):
        if self.toast_job:
            self.after_cancel(self.toast_job)
        if self.toast_frame:
            self.toast_frame.destroy()
        t = tk.Frame(self, bg=INK)
        self.L(t, text, 10, True, WARN if warn else BG, INK).pack(side="left", padx=14, pady=11)
        if undo:
            u = tk.Label(t, text=self.tr("undo"), bg=INK, fg=HOVER_G, font=(BODY, 10, "bold"),
                         padx=12, cursor="hand2")
            u.pack(side="right", pady=6)
            u.bind("<Button-1>", lambda e: self.undo())
        t.place(relx=0.5, rely=1.0, y=-82 if self.cart and self.page != "list" else -20, anchor="s")
        t.lift()
        self.toast_frame = t
        self.toast_job = self.after(6000 if undo else 3200, self.hide_toast)

    def hide_toast(self):
        if self.toast_frame:
            self.toast_frame.destroy()
            self.toast_frame = None
        self.toast_job = None

    # ---------- home ----------
    def page_home(self):
        self.topbar()
        self.hero()
        self.location_card()
        self.tabbar()
        if self.tab == "favorites":
            self.tab_favorites()
        elif self.tab == "student":
            self.tab_student()
        elif self.tab == "security":
            self.tab_security()
        else:
            self.tab_products()
        self.L(self.pf, self.tr("note"), 9, False, MUTED, BG, wraplength=MAX_W - 40,
               justify="left").pack(anchor="w", padx=18, pady=(14, 24))

    def tab_products(self):
        box = tk.Frame(self.pf, bg=LINE)
        box.pack(fill="x", padx=18, pady=(0, 10))
        entry = tk.Entry(box, textvariable=self.query, bg=SURFACE, fg=INK, insertbackground=INK,
                         relief="flat", bd=0, font=(BODY, 13))
        entry.pack(fill="x", padx=2, pady=2, ipady=10)
        entry.bind("<KeyRelease>", lambda e: self.populate())
        entry.bind("<FocusIn>", lambda e: box.configure(bg=BRAND))
        entry.bind("<FocusOut>", lambda e: box.configure(bg=LINE))
        ph = tk.Label(entry, text=self.tr("search"), bg=SURFACE, fg=MUTED, font=(BODY, 12), cursor="xterm")
        ph.bind("<Button-1>", lambda e: entry.focus_set())
        self.placeholder = ph

        # category switcher
        cats = tk.Frame(self.pf, bg=BG)
        cats.pack(fill="x", padx=14, pady=(0, 8))
        items = [("all", "", self.tr("all_cat"))] + [
            (c[0], c[1], c[2] if self.lang == "ru" else c[3]) for c in CATEGORIES]
        for i in range(3):
            cats.columnconfigure(i, weight=1, uniform="cat")
        for i, (cid, em, name) in enumerate(items):
            on = self.category == cid
            text = (em + " " if em and USE_EMOJI else "") + name
            Btn(cats, text, lambda c=cid: self.set_category(c),
                bg=MINT if on else SURFACE, fg=INK, border=BRAND if on else LINE,
                bw=2 if on else 1, font=(BODY, 9, "bold"), padx=6, pady=7).grid(
                row=i // 3, column=i % 3, sticky="ew", padx=4, pady=3)

        self.title_label = self.L(self.pf, "", 10, True, BRAND, BG, HEAD)
        self.title_label.pack(anchor="w", padx=18, pady=(2, 5))
        self.products_area = tk.Frame(self.pf, bg=BG)
        self.products_area.pack(fill="x", padx=13)
        self.populate()

    def set_category(self, cid):
        self.category = cid
        self.render()

    def populate(self):
        if not self.products_area.winfo_exists():
            return
        for w in self.products_area.winfo_children():
            w.destroy()
        raw = self.query.get()
        cleaned = clean_text(raw)                      # input validation: printable characters, max 40
        if cleaned != raw:
            self.query.set(cleaned)
        q = cleaned.lower().strip()
        if self.query.get():
            self.placeholder.place_forget()
        else:
            self.placeholder.place(x=8, rely=0.5, anchor="w")
        allowed = None
        if self.category != "all":
            allowed = next(c[4] for c in CATEGORIES if c[0] == self.category)
        title = self.tr("found") if q else self.tr("all")
        if self.category != "all":
            cat = next(c for c in CATEGORIES if c[0] == self.category)
            title = cat[2] if self.lang == "ru" else cat[3]
        self.title_label.configure(text=title.upper())

        found = self.index.search(q)                   # parameterized SQL query (see SearchIndex)
        result = [p["id"] for p in PRODUCTS.values()
                  if p["id"] in found and (allowed is None or p["id"] in allowed)]
        if not result:
            msg = ("Нет продукта «%s»" if self.lang == "ru" else "No product called “%s”") % q
            self.L(self.products_area, msg, 12, True, INK, BG, HEAD).pack(pady=(24, 2))
            self.L(self.products_area,
                   "Проверьте написание или очистите поиск." if self.lang == "ru"
                   else "Check the spelling or clear the search.", 10, False, MUTED).pack()
            return
        self.tiles(self.products_area, result)

    def tiles(self, parent, pids):
        parent.columnconfigure(0, weight=1, uniform="c")
        parent.columnconfigure(1, weight=1, uniform="c")
        for i, pid in enumerate(pids):
            p = PRODUCTS[pid]
            sel = [0] * len(p["groups"])
            low = min(self.price(p, sel, s) for s in range(len(STORES)))
            card = tk.Frame(parent, bg=SURFACE, highlightbackground=LINE, highlightthickness=1)
            card.grid(row=i // 2, column=i % 2, sticky="nsew", padx=5, pady=5)
            top = tk.Frame(card, bg=SURFACE)
            top.pack(fill="x", padx=12, pady=(10, 0))
            self.emoji(top, p["emoji"], 24, SURFACE).pack(side="left")
            heart = tk.Label(top, text="♥" if pid in self.fav else "♡", bg=SURFACE,
                             fg=HEART_ON if pid in self.fav else MUTED, font=(BODY, 16), cursor="hand2")
            heart.pack(side="right")
            self.L(card, p[self.lang], 12, True, INK, SURFACE, HEAD).pack(anchor="w", padx=12)
            self.L(card, self.variant_preview(p, sel), 9, False, MUTED, SURFACE, wraplength=190,
                   justify="left").pack(anchor="w", padx=12)
            self.L(card, f'{self.tr("from")} {self.money(low)}', 12, True, BRAND, SURFACE,
                   HEAD).pack(anchor="w", padx=12, pady=(4, 12))
            click_all(card, lambda pid=pid: self.open(pid))
            heart.bind("<Button-1>", lambda e, pid=pid: self.toggle_fav(pid))   # overrides the card click
            hover_card(card)

    def toggle_fav(self, pid):
        self.fav ^= {pid}
        self.save_state()
        self.render()

    def open(self, pid):
        self.product_id = pid
        self.selected.setdefault(pid, [0] * len(PRODUCTS[pid]["groups"]))
        self.expanded = set()
        self.go("compare")

    # ---------- favourites tab ----------
    def tab_favorites(self):
        pids = [p for p in PRODUCTS if p in self.fav]
        if not pids:
            c = self.card(self.pf)
            self.L(c, "♡", 26, False, MUTED, SURFACE).pack(pady=(18, 0))
            self.L(c, self.tr("fav_empty"), 13, True, INK, SURFACE, HEAD).pack(pady=(4, 2))
            self.L(c, self.tr("fav_hint"), 10, False, MUTED, SURFACE, wraplength=MAX_W - 100,
                   justify="center").pack(padx=16, pady=(0, 18))
            return
        area = tk.Frame(self.pf, bg=BG)
        area.pack(fill="x", padx=13)
        self.tiles(area, pids)

    # ---------- student mode ----------
    def tab_student(self):
        c = self.card(self.pf)
        self.L(c, "🎓 " + self.tr("tab_student"), 15, True, INK, SURFACE, HEAD).pack(anchor="w", padx=14, pady=(12, 2))
        self.L(c, self.tr("stu_desc"), 10, False, MUTED, SURFACE, wraplength=MAX_W - 90,
               justify="left").pack(anchor="w", padx=14)
        Btn(c, self.tr("mode_on") if self.student else self.tr("mode_off"), self.toggle_student,
            bg=BRAND if self.student else SURFACE, border=BRAND if self.student else LINE,
            font=(BODY, 10, "bold"), padx=14, pady=8).pack(anchor="w", padx=14, pady=(10, 6))

        row = tk.Frame(c, bg=SURFACE)
        row.pack(fill="x", padx=14, pady=(4, 6))
        box = tk.Frame(row, bg=LINE)
        box.pack(side="left", fill="x", expand=True)
        entry = tk.Entry(box, textvariable=self.budget_var, bg=SURFACE, fg=INK, insertbackground=INK,
                         relief="flat", bd=0, font=(BODY, 13))
        entry.pack(fill="x", padx=2, pady=2, ipady=8)
        entry.bind("<Return>", lambda e: self.apply_budget())
        entry.bind("<FocusIn>", lambda e: box.configure(bg=BRAND))
        entry.bind("<FocusOut>", lambda e: box.configure(bg=LINE))
        Btn(row, self.tr("apply"), self.apply_budget, padx=14, pady=9).pack(side="left", padx=(8, 0))
        chips = tk.Frame(c, bg=SURFACE)
        chips.pack(fill="x", padx=14, pady=(0, 12))
        for v in (5000, 10000, 15000, 20000):
            Btn(chips, self.money(v), lambda v=v: self.set_budget(v), bg=SURFACE, border=LINE,
                padx=10, pady=5).pack(side="left", padx=(0, 6))
        self.budget_panel(self.pf)

    def toggle_student(self):
        self.student = not self.student
        self.save_state()
        self.render()

    def apply_budget(self):
        raw = self.budget_var.get().replace(" ", "").replace("\u00a0", "").replace("₸", "")
        try:
            value = int(float(raw.replace(",", ".")))
        except ValueError:
            value = 0
        if value <= 0 or value > MAX_BUDGET:
            self.show_toast(self.tr("budget_bad"), warn=True)
            return
        self.set_budget(value)

    def set_budget(self, value):
        self.budget = int(value)
        self.budget_var.set(str(self.budget))
        self.student = True
        self.save_state()
        self.render()

    def swap_suggestions(self):
        """Cheaper equal alternatives (another brand / variety / category, same size) in the same store."""
        result = []
        for idx, x in enumerate(self.cart):
            p = PRODUCTS[x["pid"]]
            groups = [i for i, g in enumerate(p["groups"]) if g[0] in ANALOG_GROUPS]
            if not groups:
                continue
            current = self.price(p, x["sel"], x["store"])
            best = None
            for combo in itertools.product(*[range(len(p["groups"][i][2])) for i in groups]):
                cand = x["sel"][:]
                for i, o in zip(groups, combo):
                    cand[i] = o
                pr = self.price(p, cand, x["store"])
                if pr < current and (best is None or pr < best[0]):
                    best = (pr, cand)
            if best:
                result.append({"idx": idx, "sel": best[1], "saving": (current - best[0]) * x["qty"]})
        result.sort(key=lambda s: -s["saving"])
        return result

    def apply_swap(self, idx):
        x = self.cart[idx]
        suggestion = next((s for s in self.swap_suggestions() if s["idx"] == idx), None)
        if suggestion:
            self._swap(x, suggestion["sel"])
        self.render()

    def _swap(self, x, new_sel):
        x["sel"] = new_sel[:]
        for other in self.cart:      # merge if the same item is already in the list
            if other is not x and other["pid"] == x["pid"] and other["sel"] == x["sel"] \
                    and other["store"] == x["store"]:
                other["qty"] = min(9, other["qty"] + x["qty"])
                self.cart.remove(x)
                break

    def apply_all_swaps(self):
        items = [(self.cart[s["idx"]], s["sel"]) for s in self.swap_suggestions()]
        for x, sel in items:
            if x in self.cart:
                self._swap(x, sel)
        self.show_swaps = False
        self.render()

    def budget_panel(self, parent):
        """💰 budget, warning and the offer to swap items for cheaper analogues."""
        if not (self.student and self.budget):
            if self.page == "list" and self.student:
                self.L(parent, self.tr("no_budget"), 10, False, MUTED).pack(anchor="w", padx=18)
            return
        total = self.cart_total()
        diff = self.budget - total
        c = self.card(parent, border=BRAND if diff >= 0 else WARN, bw=2)
        self.L(c, self.tr("budget_label", m=self.money(self.budget)), 14, True, INK, SURFACE,
               HEAD).pack(anchor="w", padx=14, pady=(12, 2))
        share = min(1.0, total / self.budget) if self.budget else 0
        self.price_bar(c, share, diff >= 0, color=BRAND if diff >= 0 else WARN).pack(fill="x", padx=14, pady=(6, 4))
        self.L(c, self.tr("spent", a=self.money(total), b=self.money(self.budget)), 10, False, MUTED,
               SURFACE).pack(anchor="w", padx=14)
        if diff < 0:
            self.L(c, self.tr("over", m=self.money(-diff)), 12, True, WARN, SURFACE,
                   HEAD).pack(anchor="w", padx=14, pady=(6, 0))
        else:
            self.L(c, self.tr("left", m=self.money(diff)), 11, True, BRAND, SURFACE,
                   HEAD).pack(anchor="w", padx=14, pady=(6, 0))

        swaps = self.swap_suggestions()
        if swaps:
            save = sum(s["saving"] for s in swaps)
            n = len(swaps)
            words = ru_plural(n, ("товар", "товара", "товаров")) if self.lang == "ru" \
                else ("item" if n == 1 else "items")
            tip = self.tr("save_tip", m=self.money(save), n=n, w=words)
            self.L(c, tip, 10, True, INK, SURFACE, wraplength=MAX_W - 90, justify="left").pack(
                anchor="w", padx=14, pady=(8, 0))
            if diff < 0:
                self.L(c, self.tr("enough") if save >= -diff else self.tr("notenough"), 9, False,
                       MUTED, SURFACE, wraplength=MAX_W - 90, justify="left").pack(anchor="w", padx=14)
            Btn(c, self.tr("hide_swaps") if self.show_swaps else self.tr("show_swaps"),
                self.toggle_swaps, bg=SURFACE, border=LINE, padx=12, pady=6).pack(
                anchor="w", padx=14, pady=(8, 12 if not self.show_swaps else 4))
            if self.show_swaps:
                k = 0 if self.lang == "ru" else 1
                for s in swaps:
                    x = self.cart[s["idx"]]
                    p = PRODUCTS[x["pid"]]
                    row = tk.Frame(c, bg=SURFACE)
                    row.pack(fill="x", padx=14, pady=4)
                    text = (f'{p[self.lang]}: {self.variant_preview(p, x["sel"])} → '
                            f'{self.variant_preview(p, s["sel"])}  (−{self.money(s["saving"])})')
                    self.L(row, text, 9, False, INK, SURFACE, wraplength=MAX_W - 190,
                           justify="left").pack(side="left", fill="x", expand=True)
                    Btn(row, self.tr("swap"), lambda i=s["idx"]: self.apply_swap(i), padx=10, pady=4).pack(side="right")
                Btn(c, self.tr("swap_all"), self.apply_all_swaps, padx=14, pady=8).pack(
                    anchor="w", padx=14, pady=(6, 12))
        elif self.cart:
            self.L(c, self.tr("no_swaps"), 9, False, MUTED, SURFACE).pack(anchor="w", padx=14, pady=(6, 12))
        else:
            tk.Frame(c, bg=SURFACE, height=10).pack()

    def toggle_swaps(self):
        self.show_swaps = not self.show_swaps
        self.render()

    # ---------- location (GPS) ----------
    def use_gps(self):
        """Ask for consent first (privacy), then start the protected GPS bridge."""
        win = tk.Toplevel(self, bg=BG)
        win.title(self.t2("Доступ к местоположению", "Location access"))
        win.geometry(f"400x300+{self.winfo_rootx() + 60}+{self.winfo_rooty() + 100}")
        win.resizable(False, False)
        self.L(win, "📡 " + self.t2("Определить местоположение?", "Use your location?"), 14, True, INK, BG,
               HEAD).pack(pady=(18, 8))
        self.L(win, self.t2(
            "• Браузер попросит у вас разрешение.\n• Местоположение остаётся на этом компьютере.\n"
            "• Оно округляется до ~100 м, нигде не сохраняется и никуда не отправляется.\n"
            "• Нужно только для расчёта расстояний до магазинов.",
            "• Your browser will ask for permission.\n• The location stays on this computer.\n"
            "• It is rounded to ~100 m, never saved and never sent anywhere.\n"
            "• It is only used to calculate distances to stores."),
            10, False, MUTED, BG, wraplength=350, justify="left").pack(padx=24)
        Btn(win, self.t2("Разрешить", "Allow"), lambda: (win.destroy(), self._start_gps()),
            font=(BODY, 11, "bold"), padx=18, pady=9).pack(pady=(16, 4))
        Btn(win, self.tr("cancel"), win.destroy, bg=BG, border=BG, fg=MUTED, padx=10, pady=5).pack()

    def _start_gps(self):
        if self.bridge:
            self.denied_total += self.bridge.denied
            self.bridge.close()
        try:
            self.bridge = LocationBridge()
        except OSError:
            self.loc_status = "error"
            self.render()
            return
        self.loc_status = "waiting"
        self.gps_ticks = 0
        webbrowser.open(self.bridge.url())
        self.render()
        self.after(500, self.poll_gps)

    def poll_gps(self):
        b = self.bridge
        if not b:
            return
        self.gps_ticks += 1
        if b.result:
            lat, lon, acc = b.result
            self.denied_total += b.denied
            b.close()
            self.bridge = None
            self.set_location(lat, lon, "GPS", acc)
        elif b.error or time.time() > b.expires:        # error or expired
            self.denied_total += b.denied
            b.close()
            self.bridge = None
            self.loc_status = "error"
            self.render()
        else:
            self.after(500, self.poll_gps)

    def choose_place(self):
        win = tk.Toplevel(self, bg=BG)
        win.title(self.tr("place_title"))
        win.geometry(f"340x{120 + 46 * len(LANDMARKS)}+{self.winfo_rootx() + 60}+{self.winfo_rooty() + 80}")
        win.resizable(False, False)
        self.L(win, self.tr("place_title"), 14, True, INK, BG, HEAD).pack(pady=(16, 8))
        for ru, en, lat, lon in LANDMARKS:
            name = ru if self.lang == "ru" else en
            Btn(win, name, lambda n=name, a=lat, b=lon, w=win: (w.destroy(), self.set_location(a, b, n, None)),
                bg=SURFACE, border=LINE, font=(BODY, 11, "bold"), padx=10, pady=8).pack(fill="x", padx=24, pady=3)
        Btn(win, self.tr("cancel"), win.destroy, bg=BG, border=BG, fg=MUTED,
            padx=10, pady=6).pack(pady=(8, 10))

    def set_location(self, lat, lon, name, acc):
        self.user_loc = (round(lat, 3), round(lon, 3))     # data minimisation: ~100 m is enough for distances
        self.loc_name = name
        self.loc_acc = acc
        self.loc_status = ""
        self.start_geocoding()
        self.render()

    def clear_location(self):
        self.user_loc = None
        self.loc_name = ""
        self.loc_acc = None
        self.loc_status = ""
        self.render()

    def start_geocoding(self):
        """Find coordinates of all branches in the background (once, then cached in a file)."""
        if self.geocoder is not None and self.geocoder.is_alive():
            return
        items = []
        for s in STORES:
            for b in s["branches"]:
                q = geocode_query(b)
                if q:
                    items.append((f'{s["id"]}|{b}', q))
        if all(k in self.geo for k, _ in items):
            return
        self.geocoder = Geocoder(items, self.geo)
        self.geocoder.start()
        self.after(1500, self.poll_geo)

    def poll_geo(self):
        g = self.geocoder
        if g is None:
            return
        if g.changed:
            g.changed = False
            self.save_geo()
        if self.page in ("compare", "list") or (self.page == "home" and self.tab != "products"):
            self.render()
        elif self.page == "home":
            pass        # do not rebuild the page while the user may be typing in the search field
        if g.is_alive():
            self.after(2500, self.poll_geo)
        else:
            self.save_geo()
            if not (self.page == "home" and self.tab == "products"):
                self.render()

    def branch_km(self, store, branch):
        """Road distance from the user to a branch in km, or None."""
        if not self.user_loc:
            return None
        pos = self.geo.get(f'{store["id"]}|{branch}')
        if not pos:
            return None
        return haversine_km(self.user_loc, pos) * ROAD_FACTOR

    def store_dist(self, si):
        """(km, branch) of the nearest branch with a known position, or None."""
        best = None
        for b in STORES[si]["branches"]:
            km = self.branch_km(STORES[si], b)
            if km is not None and (best is None or km < best[0]):
                best = (km, b)
        return best

    # ---------- value rating ----------
    def rank(self, prices):
        """Value rating 0-100 of every store: price + cost of the trip (distance)."""
        dists = [self.store_dist(i) for i in range(len(STORES))]
        known = [d[0] for d in dists if d]
        have = bool(known)
        fill = statistics.median(known) if known else 0
        info = []
        for i in range(len(STORES)):
            km = dists[i][0] if dists[i] else None
            travel = (km if km is not None else fill) * 2 * TRAVEL_COST_PER_KM if have else 0
            info.append({"i": i, "price": prices[i], "km": km, "travel": travel,
                         "eff": prices[i] + travel})
        best = min(x["eff"] for x in info)
        for x in info:
            x["score"] = round(100 * best / x["eff"]) if x["eff"] else 100
        return info, have

    def advice(self, info, have):
        """'Best option for you' text, e.g. a cheaper store that is too far away."""
        if not have:
            return None
        cheap = min(info, key=lambda x: (x["price"], x["eff"]))
        best = min(info, key=lambda x: x["eff"])
        names = lambda x: STORES[x["i"]]["name"]
        if best["i"] == cheap["i"] or best["price"] == cheap["price"]:
            key = "adv_same" if (best["km"] is not None and best["km"] <= 3) else "adv_same_far"
            return self.tr(key, best=names(best), km=self.fmt_km(best["km"]))
        return self.tr("adv_diff", best=names(best), diff=self.money(best["price"] - cheap["price"]),
                       cheap=names(cheap), km_best=self.fmt_km(best["km"]), km_cheap=self.fmt_km(cheap["km"]))

    def score_color(self, score):
        return BRAND if score >= 90 else YELLOW if score >= 70 else WARN

    # ---------- compare ----------
    def page_compare(self):
        p = PRODUCTS[self.product_id]
        sel = self.selected[self.product_id]
        self.topbar(back=True)

        title = tk.Frame(self.pf, bg=BG)
        title.pack(fill="x", padx=18, pady=(2, 4))
        self.emoji(title, p["emoji"], 30, BG).pack(side="left")
        col = tk.Frame(title, bg=BG)
        col.pack(side="left", padx=12)
        self.L(col, p[self.lang], 22, True, INK, BG, HEAD).pack(anchor="w")
        self.L(col, self.variant_preview(p, sel), 10, False, MUTED).pack(anchor="w")
        is_fav = self.product_id in self.fav
        Btn(title, self.tr("fav_on") if is_fav else self.tr("fav_add"),
            lambda: self.toggle_fav(self.product_id), bg=MINT if is_fav else SURFACE,
            border=BRAND if is_fav else LINE, padx=10, pady=6).pack(side="right")

        for gi, g in enumerate(p["groups"]):
            self.L(self.pf, (g[0] if self.lang == "ru" else g[1]).upper(), 9, True, BRAND, BG,
                   HEAD).pack(anchor="w", padx=18, pady=(10, 4))
            row = tk.Frame(self.pf, bg=BG)
            row.pack(fill="x", padx=18)
            for oi, opt in enumerate(g[2]):
                on = sel[gi] == oi
                Btn(row, opt[0] if self.lang == "ru" else opt[1],
                    lambda a=gi, b=oi: self.option(a, b),
                    bg=MINT if on else SURFACE, fg=INK, border=BRAND if on else LINE,
                    bw=2 if on else 1, padx=14, pady=7).pack(side="left", padx=(0, 6), pady=2)

        prices = [self.price(p, sel, i) for i in range(len(STORES))]
        info, have = self.rank(prices)
        lowest, highest = min(prices), max(prices)
        mode = self.sort_mode if have or self.sort_mode == "price" else "price"
        if mode == "value":
            order = [x["i"] for x in sorted(info, key=lambda x: (-x["score"], x["price"]))]
        elif mode == "dist":
            order = [x["i"] for x in sorted(info, key=lambda x: (x["km"] is None, x["km"] or 0))]
        else:
            order = sorted(range(len(STORES)), key=lambda x: prices[x])
        best_value = min(info, key=lambda x: x["eff"])["i"] if have else None
        item = self.cart_item()

        # advice banner
        tip = self.advice(info, have)
        banner = tk.Label(self.pf, text=("⭐ " + tip) if tip else ("📍 " + self.tr("adv_nogps")),
                          bg=BRAND if tip else MINT, fg=BRAND_INK if tip else INK,
                          font=(HEAD, 11, "bold") if tip else (BODY, 10),
                          wraplength=MAX_W - 70, justify="left", anchor="w", padx=16, pady=12)
        banner.pack(fill="x", padx=18, pady=(14, 6))

        head = tk.Frame(self.pf, bg=BG)
        head.pack(fill="x", padx=18, pady=(6, 2))
        opts = [("value", self.tr("sort_value")), ("price", self.tr("sort_price"))]
        if have:
            opts.append(("dist", self.tr("sort_dist")))
        else:
            opts = [("price", self.tr("sort_price"))]
        self.segmented(head, opts, mode, self.set_sort).pack(side="right")
        self.L(head, self.tr("branches_hint").split(" (")[0].upper(), 9, True, BRAND, BG, HEAD).pack(side="left")

        for si in order:
            store = STORES[si]
            x = info[si]
            is_cheapest = prices[si] == lowest
            is_best = have and si == best_value
            shop = self.card(self.pf, BRAND if (is_best or (not have and is_cheapest)) else LINE,
                             2 if (is_best or (not have and is_cheapest)) else 1, pady=6)

            top = tk.Frame(shop, bg=SURFACE)
            top.pack(fill="x", padx=14, pady=(10, 0))
            self.L(top, store["name"], 14, True, INK, SURFACE, HEAD).pack(side="left")
            if is_cheapest:
                self.badge(top, self.tr("cheapest")).pack(side="left", padx=(8, 0))
            if is_best:
                self.badge(top, "★ " + self.tr("best_tag"), BRAND, BRAND_INK).pack(side="left", padx=(6, 0))
            self.L(top, self.money(prices[si]), 16, True, INK, SURFACE, HEAD).pack(side="right")

            self.price_bar(shop, prices[si] / highest, is_cheapest).pack(fill="x", padx=14, pady=(8, 4))

            if have:
                meta = tk.Frame(shop, bg=SURFACE)
                meta.pack(fill="x", padx=14, pady=(0, 2))
                if x["km"] is not None:
                    self.L(meta, self.tr("dist_line", km=self.fmt_km(x["km"]),
                                         min=max(1, int(round(x["km"] * WALK_MIN_PER_KM)))),
                           9, False, MUTED, SURFACE).pack(side="left")
                self.L(meta, self.tr("score", n=x["score"]), 9, True, self.score_color(x["score"]),
                       SURFACE).pack(side="right")

            branches = list(store["branches"])
            if have:
                branches.sort(key=lambda b: (self.branch_km(store, b) is None, self.branch_km(store, b) or 0))
            open_all = store["id"] in self.expanded
            shown = branches if open_all else branches[:MAX_BRANCHES]
            for b in shown:
                km = self.branch_km(store, b)
                label = "📍 " + b + (f"  ·  {self.fmt_km(km)}" if km is not None else "") + " ↗"
                lab = tk.Label(shop, text=label, bg=SURFACE, fg=BRAND, font=(BODY, 9, "underline"),
                               anchor="w", cursor="hand2", wraplength=MAX_W - 80, justify="left")
                lab.pack(fill="x", padx=14, pady=1)
                lab.bind("<Button-1>", lambda e, s=store["name"], br=b: self.open_map(s, br))
                hover_label(lab, SURFACE, BRAND, over_bg=SURFACE, over_fg=HOVER_LIGHT)
            if len(branches) > MAX_BRANCHES:
                txt = self.tr("less") if open_all else "+ " + self.tr("more", n=len(branches) - MAX_BRANCHES)
                more = tk.Label(shop, text=txt, bg=SURFACE, fg=MUTED, font=(BODY, 9, "bold"),
                                anchor="w", cursor="hand2")
                more.pack(fill="x", padx=14, pady=(2, 0))
                more.bind("<Button-1>", lambda e, sid=store["id"]: self.toggle_branches(sid))
                hover_label(more, SURFACE, MUTED, over_bg=SURFACE, over_fg=BRAND)

            actions = tk.Frame(shop, bg=SURFACE)
            actions.pack(fill="x", padx=14, pady=(8, 11))
            if item and item["store"] == si:
                self.L(actions, self.tr("inlist"), 10, True, BRAND, SURFACE).pack(side="left")
                Btn(actions, self.tr("removed"), self.remove_current, bg=SURFACE, fg=BRAND,
                    border=BRAND).pack(side="left", padx=10)
            else:
                Btn(actions, self.tr("move") if item else self.tr("add"),
                    lambda s=si: self.add(s)).pack(side="left")
            rep_link = tk.Label(actions, text=self.t2("⚑ Сообщить цену", "⚑ Report a price"), bg=SURFACE,
                                fg=MUTED, font=(BODY, 9, "bold"), cursor="hand2")
            rep_link.pack(side="right")
            rep_link.bind("<Button-1>", lambda e, s=si: self.report_price_dialog(s))
            hover_label(rep_link, SURFACE, MUTED, over_bg=SURFACE, over_fg=BRAND)

        self.L(self.pf, self.tr("save", shop=STORES[prices.index(lowest)]["name"],
                                money=self.money(highest - lowest)),
               10, True, MUTED, BG, wraplength=MAX_W - 40, justify="left").pack(anchor="w", padx=18, pady=(8, 0))

    def set_sort(self, mode):
        self.sort_mode = mode
        self.render()

    def option(self, g, o):
        self.selected[self.product_id][g] = o
        self.render()

    def toggle_branches(self, sid):
        self.expanded ^= {sid}
        self.render()

    # ---------- cart ----------
    def cart_item(self):
        pid, sel = self.product_id, self.selected[self.product_id]
        for x in self.cart:
            if x["pid"] == pid and x["sel"] == sel:
                return x
        return None

    def cart_total(self):
        return sum(self.price(PRODUCTS[x["pid"]], x["sel"], x["store"]) * x["qty"] for x in self.cart)

    def add(self, store):
        p = PRODUCTS[self.product_id]
        x = self.cart_item()
        shop = STORES[store]["name"]
        if x:
            x["store"] = store
            msg = self.tr("moved", p=p[self.lang], s=shop)
        else:
            self.cart.append({"pid": self.product_id, "sel": self.selected[self.product_id][:],
                              "store": store, "qty": 1})
            msg = self.tr("added", p=p[self.lang], s=shop)
        self.render()
        if self.student and self.budget and self.cart_total() > self.budget:
            self.show_toast(self.tr("over", m=self.money(self.cart_total() - self.budget)), warn=True)
        else:
            self.show_toast(msg)

    def remove_current(self):
        x = self.cart_item()
        if x:
            self.remove(self.cart.index(x))

    def remove(self, i):
        item = self.cart.pop(i)
        self.last_removed = (i, item)
        self.render()
        self.show_toast(self.tr("gone", p=PRODUCTS[item["pid"]][self.lang]), undo=True)

    def undo(self):
        if self.last_removed:
            i, item = self.last_removed
            self.cart.insert(min(i, len(self.cart)), item)
            self.last_removed = None
            self.hide_toast()
            self.render()

    def qty(self, i, d):
        self.cart[i]["qty"] = max(1, min(9, self.cart[i]["qty"] + d))
        self.render()

    def clear_cart(self):
        self.cart.clear()
        self.render()
        self.show_toast(self.tr("cleared"))

    def copy_list(self):
        lines = []
        for x in self.cart:
            p = PRODUCTS[x["pid"]]
            lines.append(f'{p[self.lang]} · {self.variant_preview(p, x["sel"])} ×{x["qty"]} — '
                         f'{STORES[x["store"]]["name"]} — '
                         f'{self.money(self.price(p, x["sel"], x["store"]) * x["qty"])}')
        lines.append(f'{self.tr("total")}: {self.money(self.cart_total())}')
        self.clipboard_clear()
        self.clipboard_append("\n".join(lines))
        self.show_toast(self.tr("copied"))

    # ---------- list ----------
    def page_list(self):
        self.topbar(back=True)
        self.L(self.pf, self.tr("list_title"), 24, True, INK, BG, HEAD).pack(anchor="w", padx=18, pady=(2, 8))
        self.budget_panel(self.pf)

        if not self.cart:
            c = self.card(self.pf)
            self.L(c, self.tr("empty"), 13, True, INK, SURFACE, HEAD).pack(pady=(22, 4))
            self.L(c, self.tr("empty_hint"), 10, False, MUTED, SURFACE, wraplength=MAX_W - 100,
                   justify="center").pack(padx=16)
            Btn(c, self.tr("find"), self.go_home, font=(BODY, 11, "bold"), padx=18, pady=9).pack(pady=(12, 22))
            return

        for si, store in enumerate(STORES):
            items = [(i, x) for i, x in enumerate(self.cart) if x["store"] == si]
            if not items:
                continue
            sub = sum(self.price(PRODUCTS[x["pid"]], x["sel"], si) * x["qty"] for _, x in items)
            grp = self.card(self.pf)
            head = tk.Frame(grp, bg=SURFACE)
            head.pack(fill="x", padx=14, pady=(10, 2))
            self.L(head, store["name"], 13, True, INK, SURFACE, HEAD).pack(side="left")
            self.L(head, self.money(sub), 12, True, INK, SURFACE, HEAD).pack(side="right")
            for n, (i, x) in enumerate(items):
                p = PRODUCTS[x["pid"]]
                if n:
                    tk.Frame(grp, bg=LINE, height=1).pack(fill="x", padx=14, pady=4)
                line = tk.Frame(grp, bg=SURFACE)
                line.pack(fill="x", padx=14, pady=(6, 6))
                left = tk.Frame(line, bg=SURFACE)
                left.pack(side="left")
                self.L(left, f'{p["emoji"] if USE_EMOJI else ""} {p[self.lang]}'.strip(), 12, True, INK,
                       SURFACE, HEAD).pack(anchor="w")
                self.L(left, self.variant_preview(p, x["sel"]), 9, False, MUTED, SURFACE).pack(anchor="w")
                stepper = tk.Frame(left, bg=SURFACE)
                stepper.pack(anchor="w", pady=(6, 0))
                Btn(stepper, "−", lambda j=i: self.qty(j, -1), bg=SURFACE, border=LINE,
                    font=(BODY, 12, "bold"), padx=10, pady=2).pack(side="left")
                self.L(stepper, str(x["qty"]), 11, True, INK, SURFACE, width=3).pack(side="left")
                Btn(stepper, "+", lambda j=i: self.qty(j, 1), bg=SURFACE, border=LINE,
                    font=(BODY, 12, "bold"), padx=10, pady=2).pack(side="left")
                right = tk.Frame(line, bg=SURFACE)
                right.pack(side="right")
                self.L(right, self.money(self.price(p, x["sel"], si) * x["qty"]), 14, True, INK,
                       SURFACE, HEAD).pack(anchor="e")
                rm = tk.Label(right, text=self.tr("removed"), bg=SURFACE, fg=WARN,
                              font=(BODY, 10, "bold"), cursor="hand2")
                rm.pack(anchor="e", pady=(10, 0))
                rm.bind("<Button-1>", lambda e, j=i: self.remove(j))
                hover_label(rm, SURFACE, WARN, over_bg=SURFACE, over_fg="#FFC2BC")

        total = tk.Frame(self.pf, bg=BG)
        total.pack(fill="x", padx=18, pady=(6, 10))
        self.L(total, self.tr("total"), 15, True, INK, BG, HEAD).pack(side="left")
        self.L(total, self.money(self.cart_total()), 17, True, INK, BG, HEAD).pack(side="right")

        # whole list in one shop (price + trip cost)
        totals = [sum(self.price(PRODUCTS[x["pid"]], x["sel"], s) * x["qty"] for x in self.cart)
                  for s in range(len(STORES))]
        info, have = self.rank(totals)
        order = sorted(info, key=lambda x: (x["eff"], x["price"]))[:5]
        top_total = max(x["eff"] for x in info)
        box = self.card(self.pf)
        self.L(box, self.tr("whole"), 12, True, INK, SURFACE, HEAD).pack(anchor="w", padx=14, pady=(10, 2))
        tip = self.advice(info, have)
        if tip:
            self.L(box, "⭐ " + tip, 10, True, BRAND, SURFACE, wraplength=MAX_W - 90,
                   justify="left").pack(anchor="w", padx=14, pady=(2, 4))
        for rank, x in enumerate(order):
            s = x["i"]
            r = tk.Frame(box, bg=SURFACE)
            r.pack(fill="x", padx=14, pady=(8, 0))
            self.L(r, STORES[s]["name"], 11, True, INK, SURFACE, HEAD).pack(side="left")
            if x["price"] == min(totals):
                self.badge(r, self.tr("cheapest")).pack(side="left", padx=8)
            self.L(r, self.money(totals[s]), 11, True, INK, SURFACE, HEAD).pack(side="right")
            self.price_bar(box, x["eff"] / top_total, rank == 0).pack(fill="x", padx=14, pady=(4, 0))
            if have and x["km"] is not None:
                self.L(box, self.tr("dist_line", km=self.fmt_km(x["km"]),
                                    min=max(1, int(round(x["km"] * WALK_MIN_PER_KM)))) + "   " +
                       self.tr("score", n=x["score"]), 9, False, MUTED, SURFACE).pack(anchor="w", padx=14)
        tk.Frame(box, bg=SURFACE, height=10).pack()

        actions = tk.Frame(self.pf, bg=BG)
        actions.pack(fill="x", padx=18, pady=(4, 8))
        Btn(actions, self.tr("copy"), self.copy_list, bg=BG, fg=BRAND, border=BRAND,
            font=(BODY, 11, "bold"), padx=16, pady=9, bw=2).pack(side="left")
        clr = tk.Label(actions, text=self.tr("clear"), bg=BG, fg=WARN, font=(BODY, 10, "bold"),
                       cursor="hand2", padx=14)
        clr.pack(side="left")
        clr.bind("<Button-1>", lambda e: self.clear_cart())
        hover_label(clr, BG, WARN, over_bg=BG, over_fg="#FFC2BC")
        self.L(self.pf, self.tr("note"), 9, False, MUTED, BG, wraplength=MAX_W - 40,
               justify="left").pack(anchor="w", padx=18, pady=(8, 24))

    # ---------- security: helpers ----------
    def t2(self, ru, en):
        return ru if self.lang == "ru" else en

    def report_msg(self, status, reason, trusted):
        low, high = int(trusted * (1 - PRICE_TOLERANCE)), int(trusted * (1 + PRICE_TOLERANCE))
        if status == "pending":
            return self.t2("Спасибо! Цена отправлена на проверку и пока не влияет на рейтинг.",
                           "Thanks! The price is sent for review and does not affect the ranking yet.")
        if reason == "out_of_range":
            return self.t2(f"Цена отклонена: сильно отличается от проверенной ({self.money(trusted)}). "
                           f"Допустимо: {self.money(low)} – {self.money(high)}.",
                           f"Price rejected: too far from the verified price ({self.money(trusted)}). "
                           f"Allowed: {self.money(low)} – {self.money(high)}.")
        if reason == "rate_limit":
            return self.t2("Слишком много отчётов. Подождите минуту.", "Too many reports. Please wait a minute.")
        return self.t2("Введите число, например 640.", "Enter a number, for example 640.")

    def report_price_dialog(self, si):
        p = PRODUCTS[self.product_id]
        sel = self.selected[self.product_id]
        trusted = self.price(p, sel, si)
        win = tk.Toplevel(self, bg=BG)
        win.title(self.t2("Сообщить цену", "Report a price"))
        win.geometry(f"400x300+{self.winfo_rootx() + 60}+{self.winfo_rooty() + 120}")
        win.resizable(False, False)
        self.L(win, "⚑ " + self.t2("Сообщить цену", "Report a price"), 14, True, INK, BG, HEAD).pack(pady=(16, 4))
        self.L(win, f'{p[self.lang]} · {self.variant_preview(p, sel)}\n{STORES[si]["name"]}: '
                    f'{self.t2("в приложении", "in the app")} {self.money(trusted)}',
               10, False, MUTED, BG, justify="center").pack()
        var = tk.StringVar()
        box = tk.Frame(win, bg=BRAND)
        box.pack(fill="x", padx=40, pady=(14, 6))
        entry = tk.Entry(box, textvariable=var, bg=SURFACE, fg=INK, insertbackground=INK, relief="flat",
                         bd=0, font=(BODY, 13))
        entry.pack(fill="x", padx=2, pady=2, ipady=8)
        entry.focus_set()

        def send():
            status, reason, value = self.guard.check(var.get(), trusted,
                                                     {"product": self.product_id, "store": STORES[si]["id"]})
            win.destroy()
            if status == "pending":
                self.reports.append({"pid": self.product_id, "store": si, "value": value})
            self.render()
            self.show_toast(self.report_msg(status, reason, trusted), warn=status != "pending")
        entry.bind("<Return>", lambda e: send())
        Btn(win, self.t2("Отправить", "Send"), send, font=(BODY, 11, "bold"), padx=18, pady=9).pack(pady=8)
        self.L(win, self.t2("Отчёты проверяются и не меняют рейтинг.", "Reports are reviewed and never change the ranking."),
               9, False, MUTED, BG).pack()

    # ---------- security: tab ----------
    def tab_security(self):
        log_ok = self.audit.broken_at is None
        c = self.card(self.pf)
        self.L(c, "🔒 " + self.t2("Защита данных", "Data protection"), 15, True, INK, SURFACE,
               HEAD).pack(anchor="w", padx=14, pady=(12, 2))
        self.L(c, self.t2("Что приложение защищает прямо сейчас:", "What the app protects right now:"),
               10, False, MUTED, SURFACE).pack(anchor="w", padx=14, pady=(0, 6))
        n_log = len(self.audit.entries)
        items = [
            (True, self.t2("Геолокация: только в памяти, округлена до ~100 м, не сохраняется и не отправляется на сервер.",
                           "Location: memory only, rounded to ~100 m, never saved or sent to a server.")),
            (True, self.t2(f"GPS-мост: секретный токен, только localhost, закрывается через {GPS_TIMEOUT_S} с. Отклонено запросов: {self.denied_total}.",
                           f"GPS bridge: secret token, localhost only, closes after {GPS_TIMEOUT_S} s. Requests rejected: {self.denied_total}.")),
            (True, self.t2(f"Поиск: параметризованные SQL-запросы, ввод очищается и ограничен {MAX_QUERY_LEN} символами.",
                           f"Search: parameterized SQL queries, input cleaned and limited to {MAX_QUERY_LEN} characters.")),
            (True, self.t2(f"Отчёты о ценах: проверка диапазона (±{int(PRICE_TOLERANCE * 100)}%), лимит {REPORT_LIMIT[0]} в минуту, в рейтинге не участвуют. На проверке: {len(self.reports)}.",
                           f"Price reports: range check (±{int(PRICE_TOLERANCE * 100)}%), {REPORT_LIMIT[0]} per minute, never used in the ranking. Pending: {len(self.reports)}.")),
            (log_ok, self.t2(f"Журнал безопасности ({n_log} записей): цепочка хэшей SHA-256 — " + ("целостность подтверждена." if log_ok else f"ИЗМЕНЕНИЕ в записи №{self.audit.broken_at + 1}!"),
                             f"Security log ({n_log} entries): SHA-256 hash chain — " + ("integrity verified." if log_ok else f"TAMPERING at entry #{self.audit.broken_at + 1}!"))),
            (True, self.t2("Локальные файлы: данные проверяются при загрузке, файлы пишутся с правами только для вас.",
                           "Local files: data is validated on load, files are written readable only by you.")),
        ]
        for ok, text in items:
            row = tk.Frame(c, bg=SURFACE)
            row.pack(fill="x", padx=14, pady=2)
            self.L(row, "✓" if ok else "⚠", 11, True, BRAND if ok else WARN, SURFACE).pack(side="left", anchor="n")
            self.L(row, text, 9, False, INK, SURFACE, wraplength=MAX_W - 100, justify="left").pack(
                side="left", padx=(6, 0))
        tk.Frame(c, bg=SURFACE, height=10).pack()

        self.L(self.pf, self.t2("ЛАБОРАТОРИЯ БЕЗОПАСНОСТИ", "SECURITY LAB"), 10, True, BRAND, BG,
               HEAD).pack(anchor="w", padx=18, pady=(8, 2))
        self.L(self.pf, self.t2("Безопасные симуляции: только ваш компьютер и вымышленные данные. Ничего реального не атакуется.",
                                "Safe simulations: only your computer and fake data. Nothing real is attacked."),
               9, False, MUTED, BG, wraplength=MAX_W - 40, justify="left").pack(anchor="w", padx=18, pady=(0, 4))

        def entry_in(row, var, width=18):
            box = tk.Frame(row, bg=LINE)
            box.pack(side="left", padx=(0, 8))
            tk.Entry(box, textvariable=var, bg=SURFACE, fg=INK, insertbackground=INK, relief="flat", bd=0,
                     font=(BODY, 11), width=width).pack(padx=2, pady=2, ipady=6)

        self.lab_card(self.t2("1. Атака через поле поиска (SQL-инъекция)", "1. Attack through the search box (SQL injection)"),
                      self.t2("Угроза: текст пользователя вставляют прямо в SQL. Защита: параметризованный запрос.",
                              "Threat: user text is glued into the SQL. Protection: a parameterized query."),
                      "sql", lambda row: (entry_in(row, self.lab_sql_var),
                                          Btn(row, self.t2("Запустить", "Run"), lambda: self.run_lab("sql", self.lab_sql),
                                              padx=12, pady=7).pack(side="left")))
        self.lab_card(self.t2("2. Поддельная цена", "2. Fake price"),
                      self.t2("Угроза: кто-то присылает цену молока 1 ₸. Защита: проверка диапазона, лимит, журнал.",
                              "Threat: someone sends a milk price of 1 ₸. Protection: range check, rate limit, log."),
                      "price", lambda row: (entry_in(row, self.lab_price_var, 8),
                                            Btn(row, self.t2("Отправить", "Send"), lambda: self.run_lab("price", self.lab_price),
                                                padx=12, pady=7).pack(side="left", padx=(0, 6)),
                                            Btn(row, self.t2("Реальная цена", "Realistic price"),
                                                lambda: self.run_lab("price", lambda: self.lab_price(real=True)),
                                                bg=SURFACE, border=LINE, padx=12, pady=7).pack(side="left")))
        self.lab_card(self.t2("3. Подделка запроса к GPS-мосту", "3. Forged request to the GPS bridge"),
                      self.t2("Угроза: чужая программа или сайт шлёт фальшивые координаты. Защита: секретный токен.",
                              "Threat: another program or website sends fake coordinates. Protection: secret token."),
                      "gps", lambda row: Btn(row, self.t2("Запустить симуляцию", "Run simulation"),
                                             lambda: self.run_lab("gps", self.lab_gps), padx=12, pady=7).pack(side="left"))
        self.lab_card(self.t2("4. Подмена записи в журнале", "4. Tampering with the log"),
                      self.t2("Угроза: кто-то правит старую запись. Защита: цепочка хэшей SHA-256 выдаёт изменение.",
                              "Threat: someone edits an old entry. Protection: the SHA-256 hash chain exposes it."),
                      "log", lambda row: (Btn(row, self.t2("Проверить журнал", "Verify log"),
                                              lambda: self.run_lab("log", lambda: self.lab_log(False)),
                                              padx=12, pady=7).pack(side="left", padx=(0, 6)),
                                          Btn(row, self.t2("Подменить запись (копия)", "Tamper (copy)"),
                                              lambda: self.run_lab("log", lambda: self.lab_log(True)),
                                              bg=SURFACE, border=LINE, padx=12, pady=7).pack(side="left")))

    def lab_card(self, title, desc, key, controls):
        c = self.card(self.pf)
        self.L(c, title, 12, True, INK, SURFACE, HEAD).pack(anchor="w", padx=14, pady=(12, 2))
        self.L(c, desc, 9, False, MUTED, SURFACE, wraplength=MAX_W - 90, justify="left").pack(anchor="w", padx=14)
        row = tk.Frame(c, bg=SURFACE)
        row.pack(fill="x", padx=14, pady=(8, 4))
        controls(row)
        colors = {"threat": WARN, "prot": BRAND, "ok": BRAND, "info": MUTED}
        for kind, text in self.lab.get(key, []):
            self.L(c, text, 9, kind in ("threat", "prot"), colors.get(kind, INK), SURFACE,
                   wraplength=MAX_W - 90, justify="left").pack(anchor="w", padx=14, pady=1)
        tk.Frame(c, bg=SURFACE, height=10).pack()

    def run_lab(self, key, fn):
        self.lab[key] = fn()
        self.render()

    def lab_sql(self):
        text = self.lab_sql_var.get()[:60]
        lab = InjectionLab()
        rows_u, sql = lab.unsafe(text)
        rows_s = lab.safe(text)
        lines = [("info", self.t2("Небезопасный запрос: ", "Unsafe query: ") + sql),
                 ("threat", self.t2(f"⚠ Небезопасный код вернул {len(rows_u)} строк(и) — утечка данных (вымышленных).",
                                    f"⚠ Unsafe code returned {len(rows_u)} row(s) — a data leak (fake data)."))]
        if rows_u:
            lines.append(("info", self.t2("Пример: ", "Example: ") + rows_u[0][1]))
        lines += [("prot", self.t2(f"✓ Защищённый код (параметр) вернул {len(rows_s)} строк — ввод воспринят как обычный текст.",
                                   f"✓ Protected code (parameter) returned {len(rows_s)} rows — the input is plain text.")),
                  ("ok", self.t2("Поиск в OverPrice работает защищённым способом (SearchIndex).",
                                 "Search in OverPrice uses the protected way (SearchIndex)."))]
        return lines

    def lab_price(self, real=False):
        p = PRODUCTS["milk"]
        sel = [0] * len(p["groups"])
        trusted = self.price(p, sel, 0)
        raw = str(round(trusted * 1.03)) if real else self.lab_price_var.get()
        status, reason, value = self.guard.check(raw, trusted, {"product": "milk", "store": STORES[0]["id"],
                                                                "source": "lab"})
        lines = [("threat", self.t2(f"Угроза: {p['ru']} • {STORES[0]['name']} • {clean_text(raw, 12)} ₸ (проверенная цена: {self.money(trusted)})",
                                    f"Threat: {p['en']} • {STORES[0]['name']} • {clean_text(raw, 12)} ₸ (verified price: {self.money(trusted)})"))]
        if status == "pending":
            lines.append(("prot", self.t2("✓ Цена правдоподобна → статус «на проверке».", "✓ Price looks plausible → status “pending review”.")))
        else:
            lines.append(("prot", "✓ " + self.report_msg(status, reason, trusted)))
        lines.append(("ok", self.t2("Рейтинг по-прежнему использует проверенные цены. Событие записано в журнал.",
                                    "The ranking still uses verified prices. The event is written to the log.")))
        return lines

    def lab_gps(self):
        b = LocationBridge()
        codes = []
        try:
            for path in ("/loc?lat=51.1&lon=71.4", "/wrong-token/loc?lat=51.1&lon=71.4"):
                try:
                    urlopen(Request(f"http://127.0.0.1:{b.port}{path}"), timeout=3)
                    codes.append(200)
                except urllib.error.HTTPError as e:
                    codes.append(e.code)
            unchanged = b.result is None
            denied = b.denied
        finally:
            b.close()
        self.denied_total += denied
        return [("threat", self.t2("Угроза: запросы к мосту без секретного токена и с неверным токеном.",
                                   "Threat: requests to the bridge without the secret token and with a wrong one.")),
                ("prot", self.t2(f"✓ Ответы сервера: {codes} (403 = запрещено). Отклонено: {denied}.",
                                 f"✓ Server answers: {codes} (403 = forbidden). Rejected: {denied}.")),
                ("ok", self.t2("Местоположение не изменилось." if unchanged else "ВНИМАНИЕ: местоположение изменилось!",
                               "Location unchanged." if unchanged else "WARNING: location changed!"))]

    def lab_log(self, tamper):
        log = AuditLog(None)                                  # throw-away copy in memory
        for i in range(4):
            log.add("price_report", {"product": "milk", "value": 640 + i, "status": "pending"})
        if tamper:
            log.entries[1]["data"]["value"] = 1               # the attacker edits an old entry
        bad = AuditLog.verify(log.entries)
        lines = [("info", self.t2("Тестовый журнал из 4 записей (копия в памяти).", "Test log with 4 entries (in-memory copy)."))]
        if tamper:
            lines.append(("threat", self.t2("Угроза: запись №2 изменена (цена 641 → 1).", "Threat: entry #2 was edited (price 641 → 1).")))
        if bad is None:
            lines.append(("ok", self.t2("✓ Цепочка хэшей цела — журнал не менялся.", "✓ The hash chain is intact — the log was not changed.")))
        else:
            lines.append(("prot", self.t2(f"✓ Защита сработала: изменение найдено в записи №{bad + 1}.",
                                          f"✓ Protection worked: tampering detected at entry #{bad + 1}.")))
        real = self.audit.broken_at
        lines.append(("info", self.t2("Настоящий журнал: ", "Real log: ") + (self.t2("цел", "intact") if real is None
                                                                      else self.t2(f"повреждён в записи №{real + 1}", f"damaged at entry #{real + 1}"))))
        return lines

    # ---------- map ----------
    def open_map(self, store, branch):
        url = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{store} {branch} Астана")
        webbrowser.open(url)


if __name__ == "__main__":
    App().mainloop()