/**
 * Интерактивный поиск и фильтрация DTC-кодов для Renault Symbol
 * Полностью автономный виджет, не требует внешних зависимостей
 */
(function() {
  'use strict';

  // ─── База данных DTC-кодов ─────────────────────────────────────
  const DTC_DB = [
    // Двигатель — P01xx
    { code: 'P0105', system: 'engine', cat: 'Топливо/воздух',
      desc: 'MAP-датчик — неисправность цепи',
      cause: 'Засорение вакуумной трубки, обрыв проводки, окисление контактов',
      fix: 'Продувка вакуумной трубки MAP, проверка целостности проводов, замена датчика' },
    { code: 'P0110', system: 'engine', cat: 'Топливо/воздух',
      desc: 'Датчик температуры впускного воздуха (IAT) — неисправность',
      cause: 'Обрыв, короткое замыкание, окисление контактов',
      fix: 'Замена датчика IAT' },
    { code: 'P0115', system: 'engine', cat: 'Топливо/воздух',
      desc: 'Датчик температуры ОЖ (ECT) — неисправность',
      cause: 'Обрыв цепи, неверный сигнал, окисление разъёма',
      fix: 'Проверка разъёма, замена датчика ECT' },
    { code: 'P0120', system: 'engine', cat: 'Топливо/воздух',
      desc: 'Датчик положения дроссельной заслонки (ДПДЗ) — неисправность',
      cause: 'Износ потенциометра, обрыв цепи, загрязнение',
      fix: 'Замена ДПДЗ (в сборе с дроссельным узлом)' },
    { code: 'P0130', system: 'engine', cat: 'Топливо/воздух',
      desc: 'Датчик кислорода (лямбда-зонд 1) — неисправность',
      cause: 'Старение, загрязнение, топливо низкого качества, подсос воздуха',
      fix: 'Диагностика, замена лямбда-зонда' },
    { code: 'P0135', system: 'engine', cat: 'Топливо/воздух',
      desc: 'Подогрев лямбда-зонда — неисправность цепи',
      cause: 'Обрыв цепи подогрева, перегоревший предохранитель',
      fix: 'Проверка предохранителя, замена лямбда-зонда' },
    { code: 'P0170', system: 'engine', cat: 'Топливо/воздух',
      desc: 'Коррекция смеси — выход за пределы',
      cause: 'Подсос воздуха после MAF, неисправность лямбда-зонда, низкое давление топлива',
      fix: 'Поиск трещин в патрубках, проверка уплотнений, диагностика топливной системы' },

    // Двигатель — P02xx
    { code: 'P0201', system: 'engine', cat: 'Форсунки',
      desc: 'Форсунка цилиндр 1 — обрыв цепи',
      cause: 'Обрыв обмотки форсунки, короткое замыкание, обрыв проводки',
      fix: 'Замер сопротивления (норма 11–15 Ом), замена форсунки' },
    { code: 'P0202', system: 'engine', cat: 'Форсунки',
      desc: 'Форсунка цилиндр 2 — обрыв цепи',
      cause: 'Обрыв обмотки форсунки, короткое замыкание',
      fix: 'Замер сопротивления (норма 11–15 Ом), замена форсунки' },
    { code: 'P0203', system: 'engine', cat: 'Форсунки',
      desc: 'Форсунка цилиндр 3 — обрыв цепи',
      cause: 'Обрыв обмотки форсунки, короткое замыкание',
      fix: 'Замер сопротивления (норма 11–15 Ом), замена форсунки' },
    { code: 'P0204', system: 'engine', cat: 'Форсунки',
      desc: 'Форсунка цилиндр 4 — обрыв цепи',
      cause: 'Обрыв обмотки форсунки, короткое замыкание',
      fix: 'Замер сопротивления (норма 11–15 Ом), замена форсунки' },
    { code: 'P0230', system: 'engine', cat: 'Форсунки',
      desc: 'Реле топливного насоса — неисправность',
      cause: 'Сгоревшее реле, обрыв цепи питания насоса',
      fix: 'Замена реле в блоке предохранителей моторного отсека' },

    // Двигатель — P03xx
    { code: 'P0300', system: 'engine', cat: 'Зажигание',
      desc: 'Случайные / множественные пропуски зажигания',
      cause: 'Бедная смесь, свечи, катушка, компрессия, вакуумные утечки',
      fix: 'Комплексная диагностика: свечи → катушки → компрессия → топливная смесь' },
    { code: 'P0301', system: 'engine', cat: 'Зажигание',
      desc: 'Пропуски зажигания — цилиндр 1',
      cause: 'Свеча, катушка, форсунка, низкая компрессия',
      fix: 'Перестановка катушки/свечи с другим цилиндром для локализации' },
    { code: 'P0302', system: 'engine', cat: 'Зажигание',
      desc: 'Пропуски зажигания — цилиндр 2',
      cause: 'Свеча, катушка, форсунка, низкая компрессия',
      fix: 'Перестановка катушки/свечи для локализации' },
    { code: 'P0303', system: 'engine', cat: 'Зажигание',
      desc: 'Пропуски зажигания — цилиндр 3',
      cause: 'Свеча, катушка, форсунка, низкая компрессия',
      fix: 'Перестановка катушки/свечи для локализации' },
    { code: 'P0304', system: 'engine', cat: 'Зажигание',
      desc: 'Пропуски зажигания — цилиндр 4',
      cause: 'Свеча, катушка, форсунка, низкая компрессия',
      fix: 'Перестановка катушки/свечи для локализации' },
    { code: 'P0325', system: 'engine', cat: 'Зажигание',
      desc: 'Датчик детонации — неисправность цепи',
      cause: 'Обрыв проводки, ослабление крепления датчика',
      fix: 'Затяжка датчика (20 Н·м), проверка цепи, замена датчика' },
    { code: 'P0335', system: 'engine', cat: 'Зажигание',
      desc: 'Датчик положения коленвала (ДПКВ) — неисправность',
      cause: 'Обрыв, загрязнение датчика, неверный зазор',
      fix: 'Проверка зазора (0,5–1,5 мм), замена датчика' },
    { code: 'P0340', system: 'engine', cat: 'Зажигание',
      desc: 'Датчик фаз (распредвала) — неисправность',
      cause: 'Обрыв проводки, неверный сигнал, загрязнение',
      fix: 'Замена датчика распредвала' },
    { code: 'P0350', system: 'engine', cat: 'Зажигание',
      desc: 'Катушка зажигания — первичная/вторичная цепь',
      cause: 'Обрыв в первичной цепи катушки, неисправность ЭБУ',
      fix: 'Проверка катушки, замена при необходимости' },

    // Двигатель — P04xx
    { code: 'P0400', system: 'engine', cat: 'Выпуск',
      desc: 'EGR — недостаточный расход',
      cause: 'Засорение клапана EGR нагаром, залипание',
      fix: 'Чистка или замена клапана EGR' },
    { code: 'P0403', system: 'engine', cat: 'Выпуск',
      desc: 'EGR — неисправность цепи управления',
      cause: 'Обрыв электроклапана EGR, короткое замыкание',
      fix: 'Проверка цепи, замена клапана EGR' },
    { code: 'P0420', system: 'engine', cat: 'Выпуск',
      desc: 'Катализатор — эффективность ниже порога',
      cause: 'Разрушенный или забитый катализатор, неисправность лямбда-зонда',
      fix: 'Замена катализатора или установка обманки' },
    { code: 'P0441', system: 'engine', cat: 'Выпуск',
      desc: 'Система улавливания паров — неверный расход',
      cause: 'Трещина в адсорбере, неисправность клапана продувки',
      fix: 'Замена клапана продувки адсорбера' },
    { code: 'P0450', system: 'engine', cat: 'Выпуск',
      desc: 'Датчик давления в системе EVAP — неисправность',
      cause: 'Засорение, обрыв цепи',
      fix: 'Проверка цепей, замена датчика' },

    // Двигатель — P05xx
    { code: 'P0505', system: 'engine', cat: 'ХХ/скорость',
      desc: 'Регулятор холостого хода — неисправность',
      cause: 'Загрязнение РХХ, обрыв цепи, износ',
      fix: 'Чистка или замена РХХ' },
    { code: 'P0560', system: 'engine', cat: 'ХХ/скорость',
      desc: 'Напряжение бортовой сети — неверное',
      cause: 'Неисправность генератора, разряд АКБ, окисление клемм',
      fix: 'Проверка зарядки генератора, чистка клемм АКБ' },

    // Двигатель — P06xx
    { code: 'P0605', system: 'engine', cat: 'ЭБУ',
      desc: 'ПЗУ ЭБУ — внутренняя неисправность',
      cause: 'Отказ энергонезависимой памяти, сбой прошивки',
      fix: 'Перепрошивка или замена ЭБУ' },
    { code: 'P0625', system: 'engine', cat: 'ЭБУ',
      desc: 'Цепь питания генератора (L-вывод) — неисправность',
      cause: 'Обрыв проводки, неисправность генератора',
      fix: 'Диагностика генератора, проверка цепи L-вывода' },
    { code: 'P0650', system: 'engine', cat: 'ЭБУ',
      desc: 'Цепь индикатора MIL (Check Engine) — неисправность',
      cause: 'Перегоревшая лампа, обрыв цепи на панели приборов',
      fix: 'Замена лампы, проверка панели приборов' },
    { code: 'P0685', system: 'engine', cat: 'ЭБУ',
      desc: 'Главное реле — обрыв цепи',
      cause: 'Сгоревшее реле впрыска, обрыв цепи управления',
      fix: 'Замена реле в блоке BSM' },

    // Двигатель — P0Axx
    { code: 'P0A08', system: 'engine', cat: 'Охлаждение',
      desc: 'Цепь вентилятора охлаждения — неисправность',
      cause: 'Залипшее реле, неисправность двигателя вентилятора, обрыв',
      fix: 'Замена реле или мотора вентилятора' },

    // ─── Renault-specific P1xxx ──────────────────────────────────
    { code: 'P1105', system: 'engine', cat: 'Renault',
      desc: 'MAP-датчик — неверный сигнал',
      cause: 'Засор вакуумной трубки, неисправность датчика',
      fix: 'Продувка трубки, замена датчика MAP' },
    { code: 'P1113', system: 'engine', cat: 'Renault',
      desc: 'Датчик IAT — вход высокий/низкий',
      cause: 'Обрыв, короткое замыкание',
      fix: 'Замена датчика IAT' },
    { code: 'P1121', system: 'engine', cat: 'Renault',
      desc: 'Потенциометр дросселя — сигнал вне диапазона',
      cause: 'Износ потенциометра, загрязнение',
      fix: 'Замена ДПДЗ (в сборе с дросселем)' },
    { code: 'P1122', system: 'engine', cat: 'Renault',
      desc: 'Потенциометр дросселя — залипание',
      cause: 'Механический износ, загрязнение',
      fix: 'Замена дроссельного узла в сборе' },
    { code: 'P1130', system: 'engine', cat: 'Renault',
      desc: 'Лямбда-зонд — медленный отклик',
      cause: 'Старение датчика кислорода',
      fix: 'Замена лямбда-зонда' },
    { code: 'P1141', system: 'engine', cat: 'Renault',
      desc: 'Лямбда-зонд №2 — подогрев',
      cause: 'Обрыв цепи подогрева',
      fix: 'Замена лямбда-зонда' },
    { code: 'P1161', system: 'engine', cat: 'Renault',
      desc: 'Топливная коррекция на пределе',
      cause: 'Подсос воздуха, износ лямбда-зонда',
      fix: 'Поиск подсоса, замена лямбда-зонда' },
    { code: 'P1170', system: 'engine', cat: 'Renault',
      desc: 'Лямбда-зонд — сигнал за пределами диапазона',
      cause: 'Неисправность датчика, обрыв',
      fix: 'Замена лямбда-зонда' },
    { code: 'P1300', system: 'engine', cat: 'Renault',
      desc: 'Катушка зажигания — обрыв первичной цепи',
      cause: 'Неисправность катушки, обрыв проводки',
      fix: 'Проверка катушки, замена' },
    { code: 'P1301', system: 'engine', cat: 'Renault',
      desc: 'Катушка — обрыв цилиндр 1',
      cause: 'Неисправность катушки или свечи',
      fix: 'Замена катушки/свечи' },
    { code: 'P1302', system: 'engine', cat: 'Renault',
      desc: 'Катушка — обрыв цилиндр 2',
      cause: 'Неисправность катушки или свечи',
      fix: 'Замена катушки/свечи' },
    { code: 'P1303', system: 'engine', cat: 'Renault',
      desc: 'Катушка — обрыв цилиндр 3',
      cause: 'Неисправность катушки или свечи',
      fix: 'Замена катушки/свечи' },
    { code: 'P1304', system: 'engine', cat: 'Renault',
      desc: 'Катушка — обрыв цилиндр 4',
      cause: 'Неисправность катушки или свечи',
      fix: 'Замена катушки/свечи' },
    { code: 'P1336', system: 'engine', cat: 'Renault',
      desc: 'Датчик детонации — сигнал вне диапазона',
      cause: 'Ослабление крепления, обрыв проводки',
      fix: 'Затяжка датчика (20 Н·м), замена при необходимости' },
    { code: 'P1340', system: 'engine', cat: 'Renault',
      desc: 'Датчик распредвала — неверный сигнал',
      cause: 'Обрыв, загрязнение датчика',
      fix: 'Замена датчика распредвала' },
    { code: 'P1360', system: 'engine', cat: 'Renault',
      desc: 'ДПКВ — прерывистый сигнал',
      cause: 'Неверный зазор, загрязнение, ослабление крепления',
      fix: 'Проверка зазора 0,5–1,5 мм' },
    { code: 'P1390', system: 'engine', cat: 'Renault',
      desc: 'Пропуски зажигания — катализатор повреждён',
      cause: 'Многократные пропуски зажигания',
      fix: 'Устранение причины пропусков, стирание кода после ремонта' },
    { code: 'P1500', system: 'engine', cat: 'Renault',
      desc: 'Иммобилайзер — нет связи с ключом',
      cause: 'Неисправность чипа ключа, антенны иммо',
      fix: 'Адаптация нового ключа, диагностика антенны' },
    { code: 'P1501', system: 'engine', cat: 'Renault',
      desc: 'Иммобилайзер — запрет пуска',
      cause: 'Несовпадение кода чипа и ЭБУ',
      fix: 'Диагностика иммобилайзера, переадаптация ключей' },
    { code: 'P1510', system: 'engine', cat: 'Renault',
      desc: 'РХХ — неисправность цепи',
      cause: 'Обрыв, загрязнение регулятора холостого хода',
      fix: 'Чистка или замена РХХ' },
    { code: 'P1515', system: 'engine', cat: 'Renault',
      desc: 'Электромагнитный клапан адсорбера (EVAP)',
      cause: 'Обрыв обмотки клапана, замыкание',
      fix: 'Замена клапана адсорбера' },
    { code: 'P1525', system: 'engine', cat: 'Renault',
      desc: 'Реле вентилятора — неисправность',
      cause: 'Сгоревшее реле вентилятора охлаждения',
      fix: 'Замена реле' },
    { code: 'P1550', system: 'engine', cat: 'Renault',
      desc: 'Напряжение АКБ — ниже порога',
      cause: 'Разряд АКБ, неисправность генератора',
      fix: 'Зарядка АКБ, проверка генератора' },
    { code: 'P1600', system: 'engine', cat: 'Renault',
      desc: 'ЭБУ — EEPROM ошибка',
      cause: 'Отказ энергонезависимой памяти ЭБУ',
      fix: 'Перепрошивка или замена ЭБУ' },
    { code: 'P1610', system: 'engine', cat: 'Renault',
      desc: 'ЭБУ — ошибка контрольной суммы',
      cause: 'Сбой прошивки, отказ ЭБУ',
      fix: 'Замена или перепрошивка ЭБУ' },
    { code: 'P1625', system: 'engine', cat: 'Renault',
      desc: 'ЭБУ — внутреннее реле',
      cause: 'Отказ реле внутри блока ЭБУ',
      fix: 'Замена блока ЭБУ' },

    // ─── Дизельные коды K9K ──────────────────────────────────────
    { code: 'P0380', system: 'engine', cat: 'Дизель K9K',
      desc: 'Свеча накаливания — обрыв цепи',
      cause: 'Перегоревшая свеча, неисправность реле накала',
      fix: 'Замена свечей накаливания, проверка реле' },
    { code: 'P0381', system: 'engine', cat: 'Дизель K9K',
      desc: 'Свеча накаливания — цепь индикатора',
      cause: 'Перегоревшая лампа, обрыв проводки',
      fix: 'Проверка индикатора на панели' },
    { code: 'P0470', system: 'engine', cat: 'Дизель K9K',
      desc: 'Датчик давления выхлопных газов',
      cause: 'Обрыв, засорение датчика',
      fix: 'Замена датчика давления' },
    { code: 'P2002', system: 'engine', cat: 'Дизель K9K',
      desc: 'Сажевый фильтр — эффективность ниже порога',
      cause: 'Забит DPF, недостаточная регенерация',
      fix: 'Принудительная регенерация или замена DPF' },
    { code: 'P2146', system: 'engine', cat: 'Дизель K9K',
      desc: 'Форсунки Common Rail — общая цепь',
      cause: 'Неисправность ТНВД, общая проводка форсунок',
      fix: 'Диагностика системы Common Rail' },
    { code: 'P2147', system: 'engine', cat: 'Дизель K9K',
      desc: 'Форсунка 1 — обрыв цепи',
      cause: 'Неисправность форсунки, обрыв',
      fix: 'Замена форсунки' },
    { code: 'P2148', system: 'engine', cat: 'Дизель K9K',
      desc: 'Форсунка 2 — обрыв цепи',
      cause: 'Неисправность форсунки, обрыв',
      fix: 'Замена форсунки' },
    { code: 'P2149', system: 'engine', cat: 'Дизель K9K',
      desc: 'Форсунка 3 — обрыв цепи',
      cause: 'Неисправность форсунки, обрыв',
      fix: 'Замена форсунки' },

    // ─── ABS ──────────────────────────────────────────────────────
    { code: 'C0001', system: 'abs', cat: 'ABS',
      desc: 'Датчик скорости левый передний — неисправность',
      cause: 'Загрязнение датчика, неверный зазор, обрыв проводки',
      fix: 'Чистка датчика, проверка зазора (норма 0,3–1,2 мм)' },
    { code: 'C0002', system: 'abs', cat: 'ABS',
      desc: 'Датчик скорости правый передний — неисправность',
      cause: 'Загрязнение датчика, неверный зазор, обрыв проводки',
      fix: 'Чистка датчика, проверка зазора' },
    { code: 'C0003', system: 'abs', cat: 'ABS',
      desc: 'Датчик скорости левый задний — неисправность',
      cause: 'Загрязнение датчика, неверный зазор, обрыв проводки',
      fix: 'Чистка датчика, проверка зазора' },
    { code: 'C0004', system: 'abs', cat: 'ABS',
      desc: 'Датчик скорости правый задний — неисправность',
      cause: 'Загрязнение датчика, неверный зазор, обрыв проводки',
      fix: 'Чистка датчика, проверка зазора' },
    { code: 'C0031', system: 'abs', cat: 'ABS',
      desc: 'Гидроагрегат ABS — неисправность левый передний',
      cause: 'Отказ гидроблока, засорение канала',
      fix: 'Диагностика гидроагрегата, замена при необходимости' },
    { code: 'C0032', system: 'abs', cat: 'ABS',
      desc: 'Гидроагрегат ABS — неисправность правый передний',
      cause: 'Отказ гидроблока',
      fix: 'Диагностика гидроагрегата' },
    { code: 'C0033', system: 'abs', cat: 'ABS',
      desc: 'Гидроагрегат ABS — неисправность левый задний',
      cause: 'Отказ гидроблока',
      fix: 'Диагностика гидроагрегата' },
    { code: 'C0034', system: 'abs', cat: 'ABS',
      desc: 'Гидроагрегат ABS — неисправность правый задний',
      cause: 'Отказ гидроблока',
      fix: 'Диагностика гидроагрегата' },
    { code: 'C0035', system: 'abs', cat: 'ABS',
      desc: 'Гидроагрегат ABS — общая неисправность',
      cause: 'Отказ блока ABS',
      fix: 'Замена гидроагрегата ABS' },
    { code: 'C0040', system: 'abs', cat: 'ABS',
      desc: 'Насос ABS — неисправность цепи',
      cause: 'Обрыв или короткое замыкание мотора насоса',
      fix: 'Проверка реле насоса ABS, замена насоса' },
    { code: 'C0050', system: 'abs', cat: 'ABS',
      desc: 'ESP/ASR — неисправность блока',
      cause: 'Отказ блока ESP, потеря связи',
      fix: 'Диагностика блока ESP' },
    { code: 'C0060', system: 'abs', cat: 'ABS',
      desc: 'Реле насоса ABS — неисправность',
      cause: 'Сгоревшее реле, обрыв цепи',
      fix: 'Замена реле в блоке BSM' },
    { code: 'C0070', system: 'abs', cat: 'ABS',
      desc: 'Напряжение питания ABS — ниже нормы',
      cause: 'Напряжение ниже 9 В на блоке ABS',
      fix: 'Проверка АКБ и генератора' },

    // ─── SRS (Airbag) ────────────────────────────────────────────
    { code: 'B1000', system: 'srs', cat: 'SRS',
      desc: 'Подушка водителя — высокое сопротивление',
      cause: 'Окисление контактов контактного кольца (clock spring)',
      fix: 'Чистка контактного кольца под рулём, замена при необходимости' },
    { code: 'B1003', system: 'srs', cat: 'SRS',
      desc: 'Подушка пассажира — высокое сопротивление',
      cause: 'Обрыв в жгуте проводки под передним сиденьем',
      fix: 'Проверка проводки под сиденьем пассажира' },
    { code: 'B1015', system: 'srs', cat: 'SRS',
      desc: 'Блок SRS — внутренняя неисправность',
      cause: 'Отказ электроники блока SRS',
      fix: 'Замена блока SRS (требуется адаптация у дилера)' },
    { code: 'B1020', system: 'srs', cat: 'SRS',
      desc: 'Подушка водителя — низкое сопротивление',
      cause: 'Короткое замыкание в цепи подушки',
      fix: 'Замена подушки безопасности водителя' },
    { code: 'B1025', system: 'srs', cat: 'SRS',
      desc: 'Датчик удара — неисправность',
      cause: 'Обрыв проводки, неисправность датчика',
      fix: 'Диагностика, замена датчика удара' },
    { code: 'B1030', system: 'srs', cat: 'SRS',
      desc: 'Ремень безопасности — преднатяжитель',
      cause: 'Обрыв цепи преднатяжителя',
      fix: 'Замена преднатяжителя в сборе с ремнём' },
    { code: 'B1050', system: 'srs', cat: 'SRS',
      desc: 'ESP/ASR — нет связи по CAN',
      cause: 'Обрыв CAN-шины, неисправность блока',
      fix: 'Диагностика CAN-шины' },

    // ─── Трансмиссия ─────────────────────────────────────────────
    { code: 'P0705', system: 'trans', cat: 'АКПП',
      desc: 'Датчик положения селектора АКПП — неисправность',
      cause: 'Износ датчика, обрыв проводки',
      fix: 'Замена датчика положения селектора' },
    { code: 'P0710', system: 'trans', cat: 'АКПП',
      desc: 'Датчик температуры масла АКПП — неисправность',
      cause: 'Обрыв цепи датчика',
      fix: 'Замена датчика температуры' },
    { code: 'P0715', system: 'trans', cat: 'АКПП',
      desc: 'Датчик скорости входного вала АКПП',
      cause: 'Загрязнение, износ датчика',
      fix: 'Диагностика, замена датчика' },
    { code: 'P0720', system: 'trans', cat: 'АКПП',
      desc: 'Датчик скорости выходного вала АКПП',
      cause: 'Загрязнение, износ',
      fix: 'Замена датчика' },
    { code: 'P0730', system: 'trans', cat: 'АКПП',
      desc: 'Передаточное отношение — неверное',
      cause: 'Износ фрикционов, гидроблока',
      fix: 'Дефектовка АКПП, капитальный ремонт' },
    { code: 'P0740', system: 'trans', cat: 'АКПП',
      desc: 'Муфта блокировки гидротрансформатора',
      cause: 'Износ муфты, загрязнение масла',
      fix: 'Замена масла АКПП, ремонт гидротрансформатора' },
    { code: 'P0745', system: 'trans', cat: 'АКПП',
      desc: 'Клапан давления гидроблока — неисправность',
      cause: 'Засорение гидроблока, износ соленоида',
      fix: 'Промывка или замена гидроблока' },
    { code: 'P0750', system: 'trans', cat: 'АКПП',
      desc: 'Соленоид переключения A — неисправность',
      cause: 'Обрыв обмотки соленоида',
      fix: 'Замена соленоида' },
    { code: 'P0753', system: 'trans', cat: 'АКПП',
      desc: 'Соленоид переключения B — неисправность',
      cause: 'Обрыв обмотки соленоида',
      fix: 'Замена соленоида' },
    { code: 'P0758', system: 'trans', cat: 'АКПП',
      desc: 'Соленоид переключения C — неисправность',
      cause: 'Обрыв обмотки соленоида',
      fix: 'Замена соленоида' },
    { code: 'P0805', system: 'trans', cat: 'МКПП',
      desc: 'Датчик положения сцепления (МКПП) — неисправность',
      cause: 'Износ датчика, обрыв проводки',
      fix: 'Замена датчика сцепления' },
  ];

  // ─── Системные метки ──────────────────────────────────────────
  const SYSTEM_LABELS = {
    engine: 'Двигатель',
    abs: 'ABS',
    srs: 'SRS (Airbag)',
    trans: 'Трансмиссия',
  };

  const SYSTEM_ICONS = {
    engine: '⚙️',
    abs: '🛞',
    srs: '🛡️',
    trans: '🔧',
  };

  // ─── Построение DOM ────────────────────────────────────────────
  function buildWidget(container) {
    // Контейнер
    const wrapper = document.createElement('div');
    wrapper.className = 'dtc-widget';
    wrapper.innerHTML = `
      <style>
        .dtc-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 1.5em 0; }
        .dtc-widget * { box-sizing: border-box; }
        .dtc-widget .dtc-header { background: #ff6b00; color: #fff; padding: 1em 1.2em; border-radius: 8px 8px 0 0; }
        .dtc-widget .dtc-header h3 { margin: 0 0 0.3em; font-size: 1.2em; color: #fff; }
        .dtc-widget .dtc-header p { margin: 0; opacity: 0.9; font-size: 0.9em; }
        .dtc-widget .dtc-search-wrap { display: flex; gap: 0.5em; padding: 0.8em; background: #f5f5f5; }
        .dtc-widget .dtc-input { flex: 1; padding: 0.7em 1em; border: 2px solid #ddd; border-radius: 6px; font-size: 1em; transition: border-color 0.2s; }
        .dtc-widget .dtc-input:focus { border-color: #ff6b00; outline: none; }
        .dtc-widget .dtc-input.small { font-size: 0.85em; }
        .dtc-widget .dtc-clear { padding: 0.7em 1em; background: #aaa; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 1em; }
        .dtc-widget .dtc-clear:hover { background: #888; }
        .dtc-widget .dtc-tabs { display: flex; flex-wrap: wrap; gap: 0.3em; padding: 0.5em 0.8em; background: #eee; border-bottom: 1px solid #ddd; }
        .dtc-widget .dtc-tab { padding: 0.4em 0.8em; border: 1px solid #ccc; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.85em; transition: all 0.2s; }
        .dtc-widget .dtc-tab:hover { background: #ffe0b2; }
        .dtc-widget .dtc-tab.active { background: #ff6b00; color: #fff; border-color: #ff6b00; }
        .dtc-widget .dtc-count { margin-left: 0.3em; opacity: 0.7; font-size: 0.8em; }
        .dtc-widget .dtc-results { max-height: 600px; overflow-y: auto; border: 1px solid #ddd; border-top: 0; border-radius: 0 0 8px 8px; }
        .dtc-widget .dtc-item { padding: 0.8em 1em; border-bottom: 1px solid #eee; cursor: pointer; transition: background 0.15s; }
        .dtc-widget .dtc-item:last-child { border-bottom: 0; }
        .dtc-widget .dtc-item:hover { background: #fff3e0; }
        .dtc-widget .dtc-item.hidden { display: none; }
        .dtc-widget .dtc-item-code { font-weight: 700; color: #d32f2f; font-size: 1.1em; }
        .dtc-widget .dtc-item-code .sys-badge { display: inline-block; font-size: 0.65em; padding: 0.15em 0.5em; border-radius: 3px; color: #fff; margin-left: 0.5em; vertical-align: middle; }
        .dtc-widget .dtc-item-code .sys-badge.engine { background: #d32f2f; }
        .dtc-widget .dtc-item-code .sys-badge.abs { background: #1565c0; }
        .dtc-widget .dtc-item-code .sys-badge.srs { background: #6a1b9a; }
        .dtc-widget .dtc-item-code .sys-badge.trans { background: #2e7d32; }
        .dtc-widget .dtc-item-cat { font-size: 0.8em; color: #888; margin-top: 0.2em; }
        .dtc-widget .dtc-item-desc { margin-top: 0.3em; color: #333; }
        .dtc-widget .dtc-item-detail { margin-top: 0.5em; padding: 0.5em 0.7em; background: #fafafa; border-left: 3px solid #ff6b00; border-radius: 0 4px 4px 0; display: none; font-size: 0.9em; }
        .dtc-widget .dtc-item-detail.open { display: block; }
        .dtc-widget .dtc-item-detail dt { font-weight: 600; color: #e65100; margin-top: 0.4em; }
        .dtc-widget .dtc-item-detail dt:first-child { margin-top: 0; }
        .dtc-widget .dtc-item-detail dd { margin: 0.2em 0 0 0.5em; }
        .dtc-widget .dtc-empty { padding: 2em; text-align: center; color: #888; font-style: italic; }
        @media (prefers-color-scheme: dark) {
          .dtc-widget .dtc-search-wrap { background: #333; }
          .dtc-widget .dtc-input { background: #444; color: #eee; border-color: #555; }
          .dtc-widget .dtc-tabs { background: #2a2a2a; border-bottom-color: #444; }
          .dtc-widget .dtc-tab { background: #444; color: #ddd; border-color: #555; }
          .dtc-widget .dtc-tab:hover { background: #664; }
          .dtc-widget .dtc-results { border-color: #444; }
          .dtc-widget .dtc-item { border-bottom-color: #333; }
          .dtc-widget .dtc-item:hover { background: #3a3020; }
          .dtc-widget .dtc-item-desc { color: #ccc; }
          .dtc-widget .dtc-item-detail { background: #2a2a2a; }
          .dtc-widget .dtc-empty { color: #aaa; }
        }
      </style>
      <div class="dtc-header">
        <h3>🔍 Поиск DTC-кодов</h3>
        <p>Введите код неисправности (P0170) или ключевое слово (лямбда, ABS, пропуски)</p>
      </div>
      <div class="dtc-search-wrap">
        <input class="dtc-input" type="text" id="dtc-query" placeholder="Поиск по коду или описанию..." autocomplete="off">
        <button class="dtc-clear" id="dtc-clear-btn">✕</button>
      </div>
      <div class="dtc-tabs" id="dtc-tabs"></div>
      <div class="dtc-results" id="dtc-results"></div>
    `;
    container.appendChild(wrapper);

    const queryInput = wrapper.querySelector('#dtc-query');
    const clearBtn = wrapper.querySelector('#dtc-clear-btn');
    const tabsEl = wrapper.querySelector('#dtc-tabs');
    const resultsEl = wrapper.querySelector('#dtc-results');

    let activeSystem = 'all';
    let searchQuery = '';

    // ─── Фильтрация ────────────────────────────────────────────────
    function getFiltered() {
      let items = DTC_DB;
      if (activeSystem !== 'all') {
        items = items.filter(d => d.system === activeSystem);
      }
      if (searchQuery.trim()) {
        const q = searchQuery.trim().toLowerCase();
        items = items.filter(d =>
          d.code.toLowerCase().includes(q) ||
          d.desc.toLowerCase().includes(q) ||
          d.cause.toLowerCase().includes(q) ||
          d.fix.toLowerCase().includes(q) ||
          d.cat.toLowerCase().includes(q)
        );
      }
      return items;
    }

    // ─── Подсчёт по системам ────────────────────────────────────────
    function countBySystem() {
      const counts = { all: DTC_DB.length };
      for (const key in SYSTEM_LABELS) {
        counts[key] = DTC_DB.filter(d => d.system === key).length;
      }
      return counts;
    }

    // ─── Рендер вкладок ─────────────────────────────────────────────
    function renderTabs() {
      const counts = countBySystem();
      const html = ['<button class="dtc-tab' + (activeSystem === 'all' ? ' active' : '') + '" data-system="all">Все <span class="dtc-count">' + counts.all + '</span></button>'];
      for (const [key, label] of Object.entries(SYSTEM_LABELS)) {
        const icon = SYSTEM_ICONS[key] || '';
        html.push('<button class="dtc-tab' + (activeSystem === key ? ' active' : '') + '" data-system="' + key + '">' + icon + ' ' + label + ' <span class="dtc-count">' + (counts[key] || 0) + '</span></button>');
      }
      tabsEl.innerHTML = html.join('');

      tabsEl.querySelectorAll('.dtc-tab').forEach(btn => {
        btn.addEventListener('click', function() {
          activeSystem = this.dataset.system;
          renderTabs();
          renderResults();
        });
      });
    }

    // ─── Рендер результатов ─────────────────────────────────────────
    function renderResults() {
      const items = getFiltered();
      if (items.length === 0) {
        resultsEl.innerHTML = '<div class="dtc-empty">По вашему запросу ничего не найдено. Попробуйте другой код или ключевое слово.</div>';
        return;
      }

      let html = '';
      for (const d of items) {
        const sysLabel = SYSTEM_LABELS[d.system] || d.system;
        html += '<div class="dtc-item" data-code="' + d.code + '">';
        html += '  <div class="dtc-item-code">' + d.code + ' <span class="sys-badge ' + d.system + '">' + sysLabel + '</span></div>';
        html += '  <div class="dtc-item-cat">' + d.cat + '</div>';
        html += '  <div class="dtc-item-desc">' + d.desc + '</div>';
        html += '  <div class="dtc-item-detail">';
        html += '    <dl>';
        html += '      <dt>🔍 Причина</dt><dd>' + d.cause + '</dd>';
        html += '      <dt>✅ Решение</dt><dd>' + d.fix + '</dd>';
        html += '    </dl>';
        html += '  </div>';
        html += '</div>';
      }
      resultsEl.innerHTML = html;

      // Клик по элементу — разворачиваем детали
      resultsEl.querySelectorAll('.dtc-item').forEach(el => {
        el.addEventListener('click', function(e) {
          // Не переключать, если клик внутри уже открытого detail
          const detail = this.querySelector('.dtc-item-detail');
          if (detail) {
            const wasOpen = detail.classList.contains('open');
            // Закрыть все
            resultsEl.querySelectorAll('.dtc-item-detail.open').forEach(d => d.classList.remove('open'));
            if (!wasOpen) {
              detail.classList.add('open');
            }
          }
        });
      });
    }

    // ─── Обработчики поиска ─────────────────────────────────────────
    queryInput.addEventListener('input', function() {
      searchQuery = this.value;
      renderResults();
    });

    clearBtn.addEventListener('click', function() {
      queryInput.value = '';
      searchQuery = '';
      renderResults();
      queryInput.focus();
    });

    // ─── Инициализация ──────────────────────────────────────────────
    renderTabs();
    renderResults();
  }

  // ─── Автоматический запуск ──────────────────────────────────────
  // Ищем контейнер #dtc-widget или создаём его после content
  function init() {
    let container = document.getElementById('dtc-widget');
    if (!container) {
      // Ищем первый <h2> после заголовка с "Коды" или конец статьи
      const content = document.querySelector('.content, article, main');
      if (content) {
        container = document.createElement('div');
        container.id = 'dtc-widget';
        // Вставить после h1 или в начало content
        const firstH = content.querySelector('h1, h2');
        if (firstH && firstH.parentNode === content) {
          firstH.insertAdjacentElement('afterend', container);
        } else {
          content.insertBefore(container, content.firstChild);
        }
      } else {
        container = document.createElement('div');
        container.id = 'dtc-widget';
        document.body.insertBefore(container, document.body.firstChild);
      }
    }
    buildWidget(container);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
