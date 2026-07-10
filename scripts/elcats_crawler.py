#!/usr/bin/env python3
"""
Полный краулер каталога запчастей Renault с elcats.ru.

Pipeline:
  1. Group.aspx?Model=GUID — 3-колоночное дерево (67 групп, 186 подгрупп)
  2. Unit.aspx?Model=GUID&Subgroup=GUID — список Unit'ов (диаграмм)
  3. Parts.aspx?Model=GUID&Unit=GUID — страница с позициями
  4. ASP.NET callback (WebForm_DoCallback) с номером позиции → HTML с ключами кода
  5. Codes.ashx?Key=... — PNG-изображение номера → OCR → OEM-номер

Использование:
  python3 scripts/elcats_crawler.py                    # полный запуск
  python3 scripts/elcats_crawler.py --resume           # продолжить
  python3 scripts/elcats_crawler.py --output cat.json  # кастомный путь
  python3 scripts/elcats_crawler.py --test             # только 1 подгруппа
"""

import argparse
import json
import logging
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Конфигурация ────────────────────────────────────────────────
BASE_URL = "http://www.elcats.ru/renault"
MODEL_GUID = "1792b579-3be7-4ec0-ad76-f70e952158f1"
DELAY = 0.25  # секунд между запросами (анти-бан)
MAX_POSITIONS = 20  # макс номер позиции на Parts.aspx
RESUME_FILE = Path(tempfile.gettempdir()) / "elcats_progress.json"

# ─── Структура каталога ──────────────────────────────────────────
CATALOG_TREE: dict[str, Any] = {
    "modelGuid": MODEL_GUID,
    "columns": [
        {
            "name": "Кузов",
            "groups": [
                {
                    "index": 0, "label": "Крупные части кузова",
                    "subgroups": [
                        {"guid": "34e0ef60-6410-4a1e-8b40-a424d2a190c7", "label": "Передняя и задняя части"},
                        {"guid": "25d5f20d-38aa-4b18-9413-dd9afab15a58", "label": "Кузов"},
                    ],
                },
                {
                    "index": 1, "label": "Нижние части",
                    "subgroups": [
                        {"guid": "cd83bb94-1f4e-475a-b04f-05547fa4499d", "label": "Средняя часть пола"},
                        {"guid": "06e2fa25-b328-448b-8f96-4c0ccb2efb08", "label": "Передняя часть пола"},
                        {"guid": "3da5a113-210b-4816-8247-7e14e9fff9bb", "label": "Пол"},
                        {"guid": "511b443f-79ed-400f-9165-acda9b488719", "label": "Задняя часть пола"},
                    ],
                },
                {
                    "index": 2, "label": "Передние нижние части",
                    "subgroups": [
                        {"guid": "46d3d356-7b34-4d27-b44b-2b7f2ee19149", "label": "Передняя сторона"},
                        {"guid": "6d3dd407-1a60-46d2-b8cc-a7ceddd88761", "label": "Щиток передка"},
                    ],
                },
                {
                    "index": 3, "label": "Боковые неподвижные части",
                    "subgroups": [
                        {"guid": "ec1d39cd-a365-4f8f-a502-243b7acd17bb", "label": "Боковины кузова и задние крылья"},
                    ],
                },
                {
                    "index": 4, "label": "Задние нижние части",
                    "subgroups": [
                        {"guid": "b8cc0c6f-2ad9-4957-b1f7-3380e0a439f2", "label": "Задняя часть кузова"},
                        {"guid": "cc79492e-c318-442b-8535-450ce767db67", "label": "Задняя юбка"},
                    ],
                },
                {
                    "index": 5, "label": "Верхние части",
                    "subgroups": [
                        {"guid": "ba01fd6b-ebbe-4175-b3e8-a65502919ddc", "label": "Стандартная крыша"},
                    ],
                },
                {
                    "index": 6, "label": "Крылья и защитные кожухи",
                    "subgroups": [
                        {"guid": "1b0cd4bd-c94a-4ac8-aa79-69586532eb80", "label": "Передние крылья"},
                        {"guid": "28dba826-124b-4873-b360-9698662cd8f4", "label": "Защитный кожух"},
                    ],
                },
                {
                    "index": 7, "label": "Боковые открывающиеся элементы кузова",
                    "subgroups": [
                        {"guid": "441aeb2f-9b26-4a67-90ff-9f267db21771", "label": "Боковые открывающиеся элементы кузова"},
                    ],
                },
                {
                    "index": 8, "label": "Небоковые открывающиеся элементы кузова",
                    "subgroups": [
                        {"guid": "7049dad8-8bf5-4827-aba9-23042e419b1d", "label": "Небоковые открывающиеся элементы кузова"},
                    ],
                },
                {
                    "index": 9, "label": "Механизмы",
                    "subgroups": [
                        {"guid": "848d619a-a18a-4cdd-8925-054ef261cb08", "label": "Петли дверей"},
                        {"guid": "140fe61f-c178-4965-89c2-0bd0ccca33eb", "label": "Наружные рукоятки дверей"},
                        {"guid": "83011fb5-55af-409c-bbbf-2122aaf227d7", "label": "Механические стеклоподъемники"},
                        {"guid": "bcac513f-aafd-4824-ae1a-b212fd4c36bb", "label": "Электрические стеклоподъемники"},
                        {"guid": "f3bef7b6-823b-41a3-b17f-c2b2f585bb59", "label": "Внутренние рукоятки дверей"},
                        {"guid": "d5f44057-8d47-4502-883f-ea8f06fe9b04", "label": "Все замки"},
                    ],
                },
                {
                    "index": 10, "label": "Противовесы двери задка или крышки багажника",
                    "subgroups": [
                        {"guid": "f7b881c4-f5fa-41ff-8fa3-4bbd0f30d145", "label": "Все замки"},
                    ],
                },
                {
                    "index": 11, "label": "Цилиндр замка",
                    "subgroups": [
                        {"guid": "811888c3-c5a8-4ef2-960e-23be15d47959", "label": "Цилиндр замка"},
                    ],
                },
                {
                    "index": 12, "label": "Стекла",
                    "subgroups": [
                        {"guid": "86f95693-a160-48cc-8789-999fa32683e0", "label": "Стекла"},
                    ],
                },
                {
                    "index": 13, "label": "Наружные защитные и декоративные элементы",
                    "subgroups": [
                        {"guid": "cf0731a7-dc33-4001-a24d-311dd9051eb1", "label": "Декоративные колпаки"},
                        {"guid": "2c2c6a63-70db-44b9-acde-57ed04486dc2", "label": "Боковые защитные накладки"},
                        {"guid": "e7208ba0-c96e-4a63-a643-5a1323ecebea", "label": "Задний бампер"},
                        {"guid": "23bfe0b3-17ca-4035-a4ba-697456b97428", "label": "Решетка радиатора"},
                        {"guid": "6678dd8d-b9ff-43eb-9273-dda8a53359b8", "label": "Защитное покрытие порога двери"},
                        {"guid": "eec83de5-6864-4f7d-86c5-e24c75580b94", "label": "Аэродинамический элемент"},
                        {"guid": "91309cae-5213-441f-b892-fb7ad6ef7249", "label": "Передний бампер"},
                    ],
                },
                {
                    "index": 14, "label": "Различные наружные аксессуары",
                    "subgroups": [
                        {"guid": "d60bd9db-3879-4dce-b623-1e5168b5c4ad", "label": "Защитные элементы колесных арок"},
                        {"guid": "e3e7d938-643f-4bc4-a767-26b9c33819f7", "label": "Зеркала заднего вида"},
                        {"guid": "75e12d29-95d6-46a1-aaf7-69684bb9c173", "label": "Номерной знак"},
                        {"guid": "6574e5a7-76d8-41c4-88c2-9c8e466016ac", "label": "Внутренние/наружные зеркала заднего вида"},
                        {"guid": "5aba8e00-259f-4dc9-969e-ef6a1bfa2ca5", "label": "Монограммы"},
                        {"guid": "1d905cd5-90f3-483f-a632-f98c19d4f03a", "label": "Фартук и дефлектор"},
                    ],
                },
            ],
        },
        {
            "name": "Механические узлы",
            "groups": [
                {
                    "index": 15, "label": "Двигатель",
                    "subgroups": [
                        {"guid": "06f5aea1-21d5-4bdd-9a58-0aa7621d69c5", "label": "Двигатель в сборе"},
                        {"guid": "c913b4d8-1f71-4d91-b820-6670c9fd6b80", "label": "Масляный насос"},
                        {"guid": "6ef548a5-2114-4c71-85ac-714f3b08beb9", "label": "Коленчатый вал"},
                        {"guid": "94abf417-933c-4f3c-8fbd-789dade6d30d", "label": "Масляный фильтр"},
                        {"guid": "b0e77c71-2847-4f79-b800-869b3618e260", "label": "Блок цилиндров"},
                        {"guid": "e0e98fac-2ea1-443e-be25-a2c4280cc1e2", "label": "Вкладыши - Подшипники"},
                        {"guid": "12b65af5-fd30-4aef-8cc2-c4260e18861c", "label": "Масляный картер"},
                        {"guid": "1df73e60-b56a-4936-9be4-d354b31d1a8d", "label": "Гильзы цилиндров"},
                        {"guid": "93f6ff50-f45b-4032-858c-f3a8c62aba18", "label": "Уплотнения двигателя"},
                    ],
                },
                {
                    "index": 16, "label": "Верхняя часть двигателя",
                    "subgroups": [
                        {"guid": "87868da5-c8dc-490d-b900-ab20cf2cbbf8", "label": "Водяной насос"},
                        {"guid": "b6b10c31-5020-4a02-9088-b534eb654cec", "label": "Газораспределительный механизм"},
                        {"guid": "c8281f68-fcba-4936-88c3-da26bb9b8f5b", "label": "Крышка клапанного механизма / ГБЦ"},
                    ],
                },
                {
                    "index": 17, "label": "Смесеобразование",
                    "subgroups": [
                        {"guid": "5ff92c9c-8f41-4981-b2ec-3b3d2bbfb4d7", "label": "Турбокомпрессор"},
                        {"guid": "734df122-0fe5-4226-81e3-6f6367255827", "label": "Коллектор"},
                        {"guid": "f3e5dccb-5b3e-42ec-b6d2-74cfba9e0b34", "label": "Масляный насос"},
                        {"guid": "3c085a5a-162d-411f-b8cc-b34c01f6a316", "label": "Система впрыска бензинового двигателя"},
                        {"guid": "a5ee4f53-14df-4f8c-81c8-d156d027126c", "label": "Нагрев / Охлаждение масла или топлива"},
                    ],
                },
                {
                    "index": 18, "label": "Питание",
                    "subgroups": [
                        {"guid": "df956734-1eea-48b2-b183-14a19e015ba9", "label": "Инжектор"},
                        {"guid": "156ff8f1-db15-482b-b5af-3351f538d468", "label": "Механический тормозной насос"},
                        {"guid": "73ee179d-d37e-4fe9-be43-441c9b8ff732", "label": "Предварительный подогрев"},
                        {"guid": "2d20b244-f707-4392-a5c0-5f5190e24643", "label": "Система впрыска дизельного двигателя"},
                        {"guid": "026389e9-ec34-4da5-8247-736441c64c85", "label": "Патрубок воздушного фильтра"},
                        {"guid": "bec8512b-7a37-4322-8798-99fd5018dcd5", "label": "Нагнетательный насос"},
                        {"guid": "c9dd8623-0ba5-4f61-8e27-9c8904de5fcc", "label": "Воздушный фильтр"},
                    ],
                },
                {
                    "index": 19, "label": "Система снижения токсичности / Впрыск",
                    "subgroups": [
                        {"guid": "0b5a256a-5756-4f92-9cdd-0a4bdefc4843", "label": "Система снижения токсичности"},
                        {"guid": "e1a5424c-4af3-4c23-92a2-5e945242c26e", "label": "Оборудование системы питания сжиженным газом"},
                    ],
                },
                {
                    "index": 20, "label": "Кронштейн / Привод доп. оборудования",
                    "subgroups": [
                        {"guid": "1c8d9735-4250-4db1-b1e7-09d52206cf7c", "label": "Натяжитель / Ремень"},
                        {"guid": "ea1ef65b-8345-4358-8bc8-5c6510c0c4a5", "label": "Оборудование системы питания сжиженным газом"},
                        {"guid": "15cc0548-cff4-42c7-b8df-8251d9238b30", "label": "Крепление вспомогательных устройств двигателя"},
                    ],
                },
                {
                    "index": 21, "label": "Запуск двигателя / Заряд АКБ",
                    "subgroups": [
                        {"guid": "57d89f9a-5183-4e84-9e8a-107ca13a9dd6", "label": "Подробное описание генератора"},
                        {"guid": "44816b31-0d86-4f0f-9687-31b105edd83e", "label": "Подробное описание стартера"},
                        {"guid": "4cd47bdf-e5eb-45fa-9dbf-e7645207a42f", "label": "Генератор / Стартер"},
                    ],
                },
                {
                    "index": 22, "label": "Зажигание / Впрыск",
                    "subgroups": [
                        {"guid": "6a53c7cf-ccb3-4bbe-bd1e-027588af13a0", "label": "Свечи"},
                        {"guid": "02cb2f70-1295-45bf-b58b-46f55ca545b0", "label": "Высоковольтные провода"},
                        {"guid": "209b6283-4d53-4872-9f51-491263f645bc", "label": "Катушка зажигания"},
                        {"guid": "8a734da9-e925-4e32-afdc-60da8c406723", "label": "Система впрыска дизельного двигателя"},
                        {"guid": "10e194e1-794d-4e3b-844c-aa0c92aaf5c9", "label": "Система впрыска бензинового двигателя"},
                    ],
                },
                {
                    "index": 23, "label": "Чистота в моторном отсеке",
                    "subgroups": [
                        {"guid": "6f789047-a935-4540-9513-4c2feb56cedf", "label": "Капот двигателя"},
                    ],
                },
                {
                    "index": 24, "label": "Охлаждение / Емкости / Выпуск",
                    "subgroups": [
                        {"guid": "729964bd-dd8e-4db7-8ddc-05ba443192d7", "label": "Кронштейн двигателя"},
                        {"guid": "b1805aa9-67ea-40b8-8512-45c62e18b130", "label": "Оборудование системы питания сжиженным газом"},
                        {"guid": "6ee8ba7e-e867-48ee-ac3f-64ab83566e2a", "label": "Система выпуска отработавших газов"},
                        {"guid": "4f1fa372-b93e-4851-ba14-6b212474097f", "label": "Трубопровод радиатора"},
                        {"guid": "6aa0e2a6-3852-4879-82c8-a15f0cfaba10", "label": "Водяной радиатор"},
                        {"guid": "c9fc3ca8-ef95-4065-9844-a2928b5b7c65", "label": "Тяговая батарея"},
                        {"guid": "b12c766a-f629-4c76-8d98-ede62d561522", "label": "Топливный бак"},
                    ],
                },
                {
                    "index": 25, "label": "Сцепление",
                    "subgroups": [
                        {"guid": "b6efd712-fe43-45d8-899c-a56e37feb3b5", "label": "Сцепление"},
                    ],
                },
                {
                    "index": 26, "label": "Механическая коробка передач",
                    "subgroups": [
                        {"guid": "5fb64961-0536-46f4-9d43-088fb8cba7ea", "label": "Шестерни коробки передач"},
                        {"guid": "b5ef0609-f601-4c5f-8635-2efded6fd43c", "label": "Вилка коробки передач"},
                        {"guid": "a6400719-a78c-4ce8-a103-3234cffac26d", "label": "Управление полуавтоматической коробкой"},
                        {"guid": "c49e6f36-b633-4d5d-a499-9a6fa5446a13", "label": "Набор для ремонта коробки передач"},
                        {"guid": "acb59c9a-69a2-4dab-bc40-a1a73e4d4ceb", "label": "Дифференциал"},
                        {"guid": "f76e8717-ec87-456c-89c3-d3537a8599f4", "label": "Механическая коробка передач"},
                        {"guid": "c562788a-b85a-4187-9e08-ef03e51cb299", "label": "Картеры коробки передач"},
                    ],
                },
                {
                    "index": 27, "label": "Раздаточная коробка",
                    "subgroups": [
                        {"guid": "08d786b4-c1ae-4a45-beed-157c7661eef6", "label": "Гнездо привода вспомогательного оборудования"},
                    ],
                },
                {
                    "index": 28, "label": "Автоматическая коробка передач",
                    "subgroups": [
                        {"guid": "3ebe8f64-ac8f-4227-99f6-35563fd0cbbb", "label": "Картеры автоматической коробки"},
                        {"guid": "f161d0c4-d355-4d09-81ac-768728dc52b0", "label": "Дифференциал"},
                        {"guid": "a668eb53-a7ba-49c1-bf95-7e945dee87a3", "label": "Комплект для ремонта коробки"},
                        {"guid": "f3c9fc29-e899-499b-a10b-910e93c76d10", "label": "Управление автоматической коробкой"},
                        {"guid": "361aeb48-e38b-4767-9924-92cfaa8f6e09", "label": "Шестерни автоматической коробки"},
                        {"guid": "fc5874d6-ba88-4170-a8d9-a9b62f21f724", "label": "Автоматическая коробка передач"},
                    ],
                },
                {
                    "index": 29, "label": "Трансмиссия",
                    "subgroups": [
                        {"guid": "de842956-f12d-4d2e-b574-45b2f8c09da7", "label": "Боковая трансмиссия"},
                    ],
                },
                {
                    "index": 30, "label": "Передние несущие элементы",
                    "subgroups": [
                        {"guid": "e435287d-c4e7-47ff-a18a-b831e2259a3d", "label": "Хвостовик / Тормозной диск"},
                        {"guid": "5db95561-6c7a-4eef-b0de-c1968fa8e495", "label": "Передняя подвеска"},
                    ],
                },
                {
                    "index": 31, "label": "Передние ненесущие элементы",
                    "subgroups": [
                        {"guid": "889a0f64-c125-4105-bee1-22a475e7a612", "label": "Плавающая скоба тормозного механизма"},
                        {"guid": "faf40b9a-0b4f-4310-80bb-5fa0db625d50", "label": "Стабилизатор поперечной устойчивости"},
                        {"guid": "892e703d-c86d-4e9c-87f2-b8f7121c9372", "label": "Амортизатор"},
                    ],
                },
                {
                    "index": 32, "label": "Задние несущие элементы",
                    "subgroups": [
                        {"guid": "0b0137f9-9bc1-4eff-b5d8-413410059e97", "label": "Задняя подвеска"},
                        {"guid": "2f5bbc37-398e-4445-af5c-ef9380f3f3d6", "label": "Хвостовик / Ступицы (Тормозной барабан)"},
                    ],
                },
                {
                    "index": 33, "label": "Задние ненесущие элементы",
                    "subgroups": [
                        {"guid": "5b185e34-2a87-4dda-a6a5-383aff41ebec", "label": "Барабанные тормозные механизмы"},
                        {"guid": "390361af-1bbf-46c2-9ea4-576c6e4c40d8", "label": "Амортизатор"},
                    ],
                },
                {
                    "index": 34, "label": "Колеса / Шины",
                    "subgroups": [
                        {"guid": "f21f16fd-3e2c-4b2c-b8eb-0996be601e3f", "label": "Алюминиевый колесный диск"},
                        {"guid": "b8a50d50-f9c5-4393-bb87-878e4c5b40f6", "label": "Колеса"},
                    ],
                },
                {
                    "index": 35, "label": "Рулевое управление",
                    "subgroups": [
                        {"guid": "eddc7216-e243-4d2c-8bf7-2bbe16606f71", "label": "Насос усилителя рулевого управления"},
                        {"guid": "4bcc580d-fbd2-466f-a584-394cfd4eb332", "label": "Рулевое колесо"},
                        {"guid": "3ab9bef1-1e80-40f4-8a8b-58e8450bb6b9", "label": "Рулевое управление"},
                    ],
                },
                {
                    "index": 36, "label": "Педали",
                    "subgroups": [
                        {"guid": "ec45dd93-a601-4901-830c-24c5b9900412", "label": "Педальный механизм"},
                        {"guid": "7006f46f-8123-4675-9fd3-394a190a5618", "label": "Крепления"},
                        {"guid": "14627c22-c8d0-4819-99b2-4f2d9ac7b209", "label": "АБС"},
                        {"guid": "f8863096-b125-4331-ab48-55fdd03f0335", "label": "Система распределения тормозных усилий"},
                        {"guid": "fb865a9c-24ff-4ad2-a4bd-8f0cfcb0a1e0", "label": "Усилитель тормозов"},
                        {"guid": "13c4bf50-2262-4fa5-b6f0-8fa983cb29ae", "label": "Главный тормозной цилиндр"},
                        {"guid": "ccd93f92-f4bc-4743-af2d-a425ffc6af2c", "label": "Трубопроводы тормозной системы"},
                    ],
                },
                {
                    "index": 37, "label": "Органы ручного управления",
                    "subgroups": [
                        {"guid": "3faabd81-30b7-4160-b0b9-6a026615ee1d", "label": "Автоматическая коробка передач"},
                        {"guid": "03be9420-122a-446f-ba38-c18e641e00f1", "label": "Стояночный тормоз"},
                        {"guid": "bcbe9454-34a7-46db-981b-e62b6b4c048d", "label": "Механическая коробка передач"},
                    ],
                },
                {
                    "index": 38, "label": "Домкрат / Мелкие принадлежности",
                    "subgroups": [
                        {"guid": "2e4b8983-b302-4f4d-bb40-a36b65dec470", "label": "Домкрат"},
                    ],
                },
            ],
        },
        {
            "name": "Элементы из кожи / Электрика",
            "groups": [
                {
                    "index": 39, "label": "Приборная панель",
                    "subgroups": [
                        {"guid": "8b01454c-14ea-4a70-b33c-3a700d1f76d6", "label": "Приборная панель"},
                        {"guid": "4e719008-5412-41f0-9cea-8158b8e3d146", "label": "Пепельница"},
                        {"guid": "2ff403b3-6441-447e-b44a-834520a088a3", "label": "Дополнительное оборудование приборной панели"},
                    ],
                },
                {
                    "index": 40, "label": "Аксессуары для салона",
                    "subgroups": [
                        {"guid": "231690ab-a636-4b77-b917-0946055899df", "label": "Внутренние/наружные зеркала заднего вида"},
                        {"guid": "2e8ff831-0e4e-4d35-b5eb-18a11ed9bcbd", "label": "Крепление для автомагнитолы / Консоль"},
                        {"guid": "e3f4e2a7-e2db-4c46-a652-5478b7da3f3e", "label": "Солнцезащитный козырек"},
                        {"guid": "09cfb661-f2e7-4cf0-989f-bb1720085aa1", "label": "Комплект безопасности при аварии"},
                        {"guid": "97f29fdd-604b-4d2d-bb7f-edfd3a3971a0", "label": "Аптечка"},
                    ],
                },
                {
                    "index": 41, "label": "Крепежные ремни багажника",
                    "subgroups": [
                        {"guid": "982d803e-30b2-4012-b6a4-06fec473f713", "label": "Поперечины багажника крыши"},
                        {"guid": "74ed4908-b6ee-45ae-a7f1-4f351d5c81aa", "label": "Подушки безопасности"},
                        {"guid": "5134258a-a70a-4e40-9f43-6021cbdf17c4", "label": "Ремни безопасности"},
                        {"guid": "dd4e40a2-5c5a-4bcd-8e39-fcad69ceada8", "label": "Тягово-сцепное устройство"},
                    ],
                },
                {
                    "index": 42, "label": "Управление кондиционированием и отоплением",
                    "subgroups": [
                        {"guid": "16adaeea-5499-43a9-89ce-a0cf07e54ba2", "label": "Вентилятор"},
                        {"guid": "865b76f9-18e5-4c61-86d9-e57ffa3a1b01", "label": "Радиатор отопителя"},
                    ],
                },
                {
                    "index": 43, "label": "Отопление и управление кондиционером",
                    "subgroups": [
                        {"guid": "a46b0110-b11b-42a4-9597-55b2f0db8e29", "label": "Управление кондиционированием"},
                        {"guid": "a420047a-d929-4b85-8bff-84480e953263", "label": "Радиатор отопителя"},
                    ],
                },
                {
                    "index": 44, "label": "Система кондиционирования",
                    "subgroups": [
                        {"guid": "13a84d8b-b7f4-49bc-b9f7-71ace44d646a", "label": "Насос кондиционера"},
                    ],
                },
                {
                    "index": 45, "label": "Уплотнительные прокладки (заглушек)",
                    "subgroups": [
                        {"guid": "4e96affe-eaba-47c4-b233-1db42b063e18", "label": "Уплотнительные прокладки"},
                    ],
                },
                {
                    "index": 46, "label": "Уплотнительные прокладки (дверей)",
                    "subgroups": [
                        {"guid": "c5802a8a-ca23-4024-95a2-704baf1621f7", "label": "Уплотнительные прокладки"},
                    ],
                },
                {
                    "index": 47, "label": "Уплотнительные прокладки (стекол)",
                    "subgroups": [
                        {"guid": "741bb97a-15b6-4db2-b2a8-cd5b0d79755b", "label": "Уплотнительные прокладки"},
                    ],
                },
                {
                    "index": 48, "label": "Внутренние защитные элементы",
                    "subgroups": [
                        {"guid": "bf6581f0-24c3-4725-83bc-25dd3610f5dd", "label": "Коврик"},
                    ],
                },
                {
                    "index": 49, "label": "Коврик",
                    "subgroups": [
                        {"guid": "ed6f0dec-d89a-4c3c-a92e-17036f706f79", "label": "Коврик"},
                        {"guid": "8620c8c6-cc85-42c2-89ef-33862ec9b032", "label": "Напольный коврик"},
                        {"guid": "4689af9d-1dce-4220-a72f-6ad68f20bb04", "label": "Вещевой ящик"},
                    ],
                },
                {
                    "index": 50, "label": "Обивка крыши",
                    "subgroups": [
                        {"guid": "44e25aa2-d511-4594-b704-16e16378316b", "label": "Система крепления багажа"},
                        {"guid": "38625080-945f-4a73-a0e5-8a2208ccf66a", "label": "Обивка крыши"},
                        {"guid": "f6b26070-ef0d-4097-bd3c-b1aff5a0d2ad", "label": "Внутренняя обивка кузова"},
                    ],
                },
                {
                    "index": 51, "label": "Обивка дверей",
                    "subgroups": [
                        {"guid": "e8190284-12be-4ddf-8776-5f56574c92bb", "label": "Обивка дверей"},
                    ],
                },
                {
                    "index": 52, "label": "Задняя полка",
                    "subgroups": [
                        {"guid": "bfe34912-0e51-4c9a-aa2c-42746f88a486", "label": "Задняя полка"},
                    ],
                },
                {
                    "index": 53, "label": "Механизм сиденья",
                    "subgroups": [
                        {"guid": "4178b309-8980-4259-a307-a1394f9d536b", "label": "Салазки сиденья"},
                        {"guid": "7f354a7e-4b00-4ecc-8816-ecfed33e4296", "label": "Каркас сиденья"},
                    ],
                },
                {
                    "index": 54, "label": "Каркас сиденья",
                    "subgroups": [
                        {"guid": "d2c5f36a-661c-46f4-a195-042caf7ec70f", "label": "Каркас сиденья"},
                    ],
                },
                {
                    "index": 55, "label": "Обивка передних сидений",
                    "subgroups": [
                        {"guid": "44ebfa69-6052-4687-915d-acd381389d84", "label": "Обивка сиденья"},
                    ],
                },
                {
                    "index": 56, "label": "Обивка задних сидений",
                    "subgroups": [
                        {"guid": "f1fb0953-9837-4388-8781-4e45d1c5073b", "label": "Обивка сиденья"},
                    ],
                },
                {
                    "index": 57, "label": "Подголовник",
                    "subgroups": [
                        {"guid": "833fd170-d548-4ab5-9ad5-7d4c308af8c4", "label": "Обивка сиденья"},
                    ],
                },
                {
                    "index": 58, "label": "АКБ / Наружные световые приборы",
                    "subgroups": [
                        {"guid": "42322819-cd0b-4849-801e-3de5ef2c126b", "label": "Аккумуляторная батарея"},
                        {"guid": "52f16ea3-ecbd-4718-9e55-5af7d2810a72", "label": "Фара"},
                        {"guid": "16350e5f-84b9-414a-92d6-7d59f2323680", "label": "Противотуманная фара"},
                        {"guid": "70b48ad2-5bd1-477e-a6fa-c17207cd782d", "label": "Боковой габаритный огонь"},
                    ],
                },
                {
                    "index": 59, "label": "Задние фонари / Внутреннее освещение",
                    "subgroups": [
                        {"guid": "ad2eb4e3-d6dc-4a76-abc0-374962d2c658", "label": "Фонарь освещения номерного знака"},
                        {"guid": "fd2e61b3-ab67-4726-a892-44380ecbfee8", "label": "Плафон освещения в салоне"},
                        {"guid": "85b42d3b-c4ea-4424-a9fd-66b8c2d6c3d5", "label": "Габаритный огонь"},
                    ],
                },
                {
                    "index": 60, "label": "Звуковой сигнал / Электронная блокировка",
                    "subgroups": [
                        {"guid": "65d42061-cd5e-48a8-8b70-8ec5f341e557", "label": "Звуковой сигнал"},
                        {"guid": "cf29f505-397c-4a7d-a274-ad6227058728", "label": "Программная блокировка"},
                        {"guid": "ed0e562d-a239-4e77-8e4b-de9835a4cc5a", "label": "Сигнализация"},
                    ],
                },
                {
                    "index": 61, "label": "Контрольно-измерительные приборы",
                    "subgroups": [
                        {"guid": "3adeafe5-9dda-418d-947d-303a447a7372", "label": "Щиток приборов"},
                        {"guid": "d5974fa6-a663-4784-ac28-984f71919ed2", "label": "Парковочный радар"},
                        {"guid": "ac118de4-ae5c-4b43-b1fd-bcb42261e7ca", "label": "Кабель счетчика / Маслоизмерительный щуп"},
                        {"guid": "47912cb1-ecfe-44f0-a6a1-f56b0caa5760", "label": "Радар системы помощи при парковке"},
                    ],
                },
                {
                    "index": 62, "label": "Управление / Сигнализация",
                    "subgroups": [
                        {"guid": "3f4450bb-6d2f-445e-9049-3e2f801ac7b2", "label": "Подрулевой переключатель"},
                        {"guid": "ed31e0d2-15ab-40a4-850c-50c26076edef", "label": "Прикуриватель / Часы"},
                        {"guid": "c0ef3077-5eb8-4ead-877c-71078ca2023a", "label": "Замок зажигания"},
                        {"guid": "62c4d625-eb5b-43a5-8fbf-a06c13185291", "label": "Замок зажигания / Выключатель"},
                    ],
                },
                {
                    "index": 63, "label": "Стеклоочистители",
                    "subgroups": [
                        {"guid": "fa49f588-afed-4e24-a020-ce419898933f", "label": "Стеклоочиститель"},
                    ],
                },
                {
                    "index": 64, "label": "Выключатель / Под автомагнитолу",
                    "subgroups": [
                        {"guid": "817d589a-6634-47b9-b306-0ecc522c64b4", "label": "Замок зажигания / Выключатель"},
                        {"guid": "87ec31c3-d3d7-4ace-a5c3-2108b98ceb93", "label": "Автомагнитола"},
                        {"guid": "a1bdf78e-3d24-4994-bbbd-d68ab35acde8", "label": "Бачок стеклоомывателя"},
                        {"guid": "00c099b2-a67a-4291-b2a6-e01b1e946a53", "label": "Монтажное пространство под автомагнитолу"},
                    ],
                },
                {
                    "index": 65, "label": "Вспомогательное электрооборудование",
                    "subgroups": [
                        {"guid": "9341f3f5-affd-46e6-ad7c-182a3b910476", "label": "Электрические реле"},
                        {"guid": "fdac6609-1caa-484c-b80e-b67990a9b880", "label": "Вентилятор"},
                    ],
                },
                {
                    "index": 66, "label": "Электропроводка",
                    "subgroups": [
                        {"guid": "c664e256-2817-4c2f-9ad4-941a71172b48", "label": "Электропроводка"},
                    ],
                },
            ],
        },
    ],
}

# ─── HTTP-сессия ─────────────────────────────────────────────────
_session: requests.Session | None = None


def get_session() -> requests.Session:
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        })
    return _session


# ─── Вспомогательные функции ─────────────────────────────────────

def fetch_unit_page(subgroup_guid: str) -> str | None:
    """Загрузить Unit.aspx для подгруппы — получить список Unit'ов (диаграмм)."""
    url = f"{BASE_URL}/Unit.aspx?Model={MODEL_GUID}&Subgroup={subgroup_guid}"
    try:
        resp = get_session().get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return resp.text
    except requests.RequestException as exc:
        logger.warning("  Ошибка Unit.aspx: %s", exc)
        return None


def parse_units(html: str) -> list[dict[str, str]]:
    """Извлечь Unit GUID'ы и их заголовки из Unit.aspx."""
    units: list[dict[str, str]] = []
    # Ищем submit('model', 'unit_guid') - для Parts.aspx
    for m in re.finditer(
        r"submit\('([a-f0-9\-]+)','([a-f0-9\-]+)'\)",
        html,
    ):
        unit_guid = m.group(2)
        if unit_guid not in {u["guid"] for u in units}:
            # Ищем title рядом
            title_m = re.search(rf'{re.escape(unit_guid)}[^"]*title="([^"]+)"', html)
            title = title_m.group(1) if title_m else ""
            units.append({"guid": unit_guid, "title": title})

    # Резерв: ищем ImageUnitHandler ссылки
    if not units:
        for m in re.finditer(
            r'ImageUnitHandler\.ashx\?Unit=([a-f0-9\-]+)',
            html,
        ):
            unit_guid = m.group(1)
            if unit_guid not in {u["guid"] for u in units}:
                units.append({"guid": unit_guid, "title": ""})

    return units


def fetch_parts_page(unit_guid: str) -> tuple[str, str, str]:
    """Загрузить Parts.aspx и извлечь ViewState, ViewStateGenerator, EventValidation."""
    url = f"{BASE_URL}/Parts.aspx?Model={MODEL_GUID}&Unit={unit_guid}"
    resp = get_session().get(url, timeout=15)
    resp.encoding = "utf-8"
    html = resp.text

    vs = re.search(r'id="__VIEWSTATE" value="([^"]+)"', html)
    vsg = re.search(r'id="__VIEWSTATEGENERATOR" value="([^"]+)"', html)
    ve = re.search(r'id="__EVENTVALIDATION" value="([^"]+)"', html)

    return (
        vs.group(1) if vs else "",
        vsg.group(1) if vsg else "",
        ve.group(1) if ve else "",
    )


def callback_parts(viewstate: str, vsg: str, ve: str, unit_guid: str, pos: str) -> str | None:
    """ASP.NET WebForm_DoCallback для получения данных по позиции."""
    url = f"{BASE_URL}/Parts.aspx?Model={MODEL_GUID}&Unit={unit_guid}"
    data = {
        "__CALLBACKID": "__Page",
        "__CALLBACKPARAM": pos,
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": vsg,
        "__EVENTVALIDATION": ve,
    }
    try:
        resp = get_session().post(url, data=data, timeout=15)
        resp.encoding = "utf-8"
        return resp.text
    except requests.RequestException as exc:
        logger.warning("    Callback pos %s error: %s", pos, exc)
        return None


def parse_callback_response(response: str) -> list[dict[str, Any]]:
    """Извлечь коды деталей из ответа callback'а.

    Ответ: 0|<table>...</table>
    Код детали — изображение Codes.ashx?Key=...
    Описание — текст в <td style="text-align:left">
    """
    parts = []

    # Удаляем префикс "0|"
    if response.startswith("0|"):
        response = response[2:]

    # Извлекаем строки таблицы
    rows = re.findall(r"<tr>(.*?)</tr>", response, re.DOTALL | re.IGNORECASE)
    for row_html in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL | re.IGNORECASE)
        if len(cells) < 2:
            continue

        # Код детали — изображение (src может быть без кавычек)
        code_img = re.search(r'Codes\.ashx\?Key=([^\s>"\'&]+)', row_html)
        code_key = code_img.group(1) if code_img else ""

        # Описание (обычно второй td)
        description = ""
        for cell in cells:
            clean = re.sub(r"<[^>]+>", "", cell).strip()
            clean = clean.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
            # Пропускаем позиционный номер (чисто цифровой)
            if clean.isdigit():
                continue
            if clean and clean != "Цена" and not clean.startswith("Альтернативное"):
                description = clean
                break

        # Проверка на "нет информации"
        if "Нет информации" in row_html or "нет информации" in row_html:
            continue

        # Альтернативное предложение
        is_alternative = "Альтернативное" in row_html

        if code_key:
            parts.append({
                "code_key": code_key,  # оставляем URL-encoded для Codes.ashx
                "description": description,
                "is_alternative": is_alternative,
            })

    return parts


def ocr_code_image(code_key: str) -> str:
    """Скачать изображение кода и распознать через Tesseract."""
    url = f"http://www.elcats.ru/Codes.ashx?Key={code_key}"
    try:
        resp = get_session().get(url, timeout=10)
        if resp.status_code != 200 or len(resp.content) < 50:
            return ""
    except requests.RequestException:
        return ""

    # Сохраняем во временный файл
    tmp = Path(tempfile.gettempdir()) / f"elcats_code_{hash(code_key)}.png"
    tmp.write_bytes(resp.content)

    try:
        result = subprocess.run(
            ["tesseract", str(tmp), "stdout", "--psm", "7", "-l", "rus+eng"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = result.stdout.strip()
        # Очищаем: оставляем только цифры и пробелы
        oem = re.sub(r"[^\d\s]", "", raw).strip()
        # Удаляем лишние пробелы, нормализуем формат
        oem = re.sub(r"\s+", " ", oem)
        return oem
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.debug("  OCR error: %s", exc)
        return ""
    finally:
        if tmp.exists():
            tmp.unlink()


# ─── Основной краулер ────────────────────────────────────────────

def crawl_catalog(output_path: Path, test_mode: bool = False, resume: bool = False) -> int:
    """Полный обход каталога.

    Возвращает количество найденных OEM-номеров.
    """
    # Загружаем прогресс, если нужен
    processed = set()
    if resume and RESUME_FILE.exists():
        try:
            processed = set(json.loads(RESUME_FILE.read_text()))
            logger.info("Возобновление: уже обработано %d подгрупп", len(processed))
        except (json.JSONDecodeError, KeyError):
            processed = set()

    results: list[dict[str, Any]] = []
    total_oems = 0
    subgroup_count = 0
    test_limit = 3 if test_mode else 9999

    for column in CATALOG_TREE["columns"]:
        col_name = column["name"]
        for group in column["groups"]:
            group_label = group["label"]
            for sg in group["subgroups"]:
                guid = sg["guid"]
                sub_label = sg["label"]
                subgroup_count += 1

                if guid in processed:
                    logger.debug(
                        "[%s/%s] %s — пропущено (уже обработано)",
                        subgroup_count, 186, sub_label[:40],
                    )
                    continue

                if subgroup_count > test_limit:
                    logger.info("Достигнут лимит, завершаем")
                    # Сохраняем результат и выходим
                    _save_results(output_path, results, processed)
                    return total_oems

                logger.info(
                    "[%s/%s] %s → %s → %s",
                    subgroup_count, 186,
                    col_name[:20], group_label[:30], sub_label[:40],
                )

                time.sleep(DELAY)

                # Шаг 1: Unit.aspx — получить список диаграмм
                unit_html = fetch_unit_page(guid)
                if not unit_html:
                    processed.add(guid)
                    RESUME_FILE.write_text(json.dumps(list(processed)))
                    continue

                units = parse_units(unit_html)
                if not units:
                    logger.info("  Нет Unit'ов для этой подгруппы")
                    processed.add(guid)
                    RESUME_FILE.write_text(json.dumps(list(processed)))
                    continue

                # Шаг 2: Для каждого Unit'а
                for unit in units:
                    unit_guid = unit["guid"]
                    unit_title = unit.get("title", "")
                    logger.info("  Unit: %s (%s)", unit_guid[:8], unit_title or "без названия")

                    time.sleep(DELAY)

                    # Parts.aspx
                    vs, vsg, ve = fetch_parts_page(unit_guid)
                    if not vs:
                        logger.warning("    Нет ViewState, пропускаем")
                        continue

                    # Шаг 3: Обход позиций (Поз № 1–20)
                    for pos_num in range(1, MAX_POSITIONS + 1):
                        time.sleep(DELAY * 0.5)

                        cb_response = callback_parts(vs, vsg, ve, unit_guid, str(pos_num))
                        if not cb_response:
                            break  # возможно, закончились позиции

                        parts_data = parse_callback_response(cb_response)
                        if not parts_data:
                            continue  # нет данных для этой позиции

                        # Шаг 4: OCR для каждой детали
                        for part in parts_data:
                            code_key = part["code_key"]
                            time.sleep(DELAY * 0.3)

                            oem = ocr_code_image(code_key)
                            if oem:
                                # Нормализация OEM
                                oem_clean = oem.replace(" ", "")
                                results.append({
                                    "category": f"{col_name} / {group_label} / {sub_label}",
                                    "group": group_label,
                                    "subgroup": sub_label,
                                    "unit_title": unit_title,
                                    "position": pos_num,
                                    "oem": oem_clean,
                                    "oem_formatted": oem,
                                    "description": part.get("description", ""),
                                    "is_alternative": part.get("is_alternative", False),
                                })
                                total_oems += 1
                                logger.info(
                                    "    Поз %s: OEM %s  %s",
                                    pos_num, oem, part.get("description", "")[:40],
                                )
                            else:
                                logger.debug("    Поз %s: код не распознан", pos_num)

                # Сохраняем прогресс
                processed.add(guid)
                RESUME_FILE.write_text(json.dumps(list(processed)))

    # Сохраняем результат
    _save_results(output_path, results, processed, total_oems)
    return total_oems


def _save_results(
    output_path: Path,
    results: list[dict[str, Any]],
    processed: set,
    total_oems: int = 0,
) -> None:
    """Сохранить JSON-каталог."""
    total = total_oems if total_oems else sum(1 for r in results if r.get("oem"))
    catalog = {
        "modelGuid": MODEL_GUID,
        "name": "Renault Symbol / Thalia",
        "source": "http://www.elcats.ru/renault/",
        "elcats_model_url": f"{BASE_URL}/Group.aspx?Model={MODEL_GUID}",
        "parts": results,
        "statistics": {
            "total_oems": total,
            "total_subgroups_processed": len(processed),
            "total_subgroups_total": 186,
        },
    }

    output_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("")
    logger.info("═" * 50)
    logger.info("Скачивание завершено!")
    logger.info("Файл: %s", output_path)
    logger.info("OEM-номеров: %d", total)
    logger.info("Обработано подгрупп: %d / 186", len(processed))
    logger.info("═" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Краулер каталога запчастей Renault с elcats.ru",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("renault_elcats_catalog.json"),
        help="Путь для сохранения JSON",
    )
    parser.add_argument("--test", action="store_true", help="Тест на 3 подгруппах")
    parser.add_argument("--resume", action="store_true", help="Продолжить прерванный запуск")
    parser.add_argument(
        "--delay", type=float, default=None,
        help="Задержка между запросами (сек)",
    )
    args = parser.parse_args()

    global DELAY
    if args.delay is not None:
        DELAY = args.delay

    # Проверка tesseract
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.error("Tesseract не найден. Установи: sudo apt install tesseract-ocr tesseract-ocr-rus")
        return 1

    total = crawl_catalog(args.output, test_mode=args.test, resume=args.resume)
    return 0 if total > 0 else 0


if __name__ == "__main__":
    exit(main())
