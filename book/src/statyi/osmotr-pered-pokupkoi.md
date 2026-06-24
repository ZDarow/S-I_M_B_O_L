# Осмотр Renault Symbol перед покупкой: чеклист

```mermaid
flowchart TD
    subgraph Inspection[Осмотр]
        A1[Кузов / коррозия<br/>арки, пороги, днище]
        A2[Двигатель<br/>масло, стуки, течи]
        A3[КПП / сцепление<br/>шумы, включения]
        A4[Подвеска<br/>стуки, люфты]
        A5[Электрика<br/>лампы, ЭСП, ЦЗ]
        A6[Салон<br/>износ, запах, вода]
    end

    subgraph Doc[Документы]
        B1[ПТС / СТС<br/>совпадение VIN]
        B2[Сервисная книжка<br/>отметки ТО]
        B3[Диагностика OBD2<br/>ошибки ЭБУ]
    end

    Inspection --> Doc

    style Inspection fill:#1565c0,color:#fff
    style Doc fill:#e65100,color:#fff
```

Интерактивный чеклист для осмотра Renault Symbol перед покупкой.

<script>
(function() {
  if (document.getElementById('inspection-checklist')) return;
  var container = document.createElement('div');
  container.id = 'inspection-checklist';
  container.style.cssText = 'margin:16px 0;border:1px solid var(--searchbar-border-color);border-radius:8px;overflow:hidden;';

  var categories = [
    {
      name: 'Кузов и ЛКП',
      items: [
        { id: 'c1', label: 'Осмотр порогов и арок — типичная ржавчина Symbol', bad: 'Сквозная коррозия', cost: '5000–15000 ₽ на сварку' },
        { id: 'c2', label: 'Крышка багажника — ржавчина под уплотнителем', bad: 'Вздутия, пузыри', cost: '3000–8000 ₽' },
        { id: 'c3', label: 'Лонжероны передние — геометрия после ДТП', bad: 'Гармошка, сварные швы', cost: 'Ремонт геометрии >20000 ₽' },
        { id: 'c4', label: 'Передние крылья — зазоры с дверями', bad: 'Зазор >5 мм, разный с двух сторон', cost: 'Покраска 5000–12000 ₽' },
        { id: 'c5', label: 'Толщина ЛКП (если есть толщиномер)', bad: '>200 мкм — шпаклёвка', cost: 'Зависит от объёма' },
      ]
    },
    {
      name: 'Двигатель',
      items: [
        { id: 'e1', label: 'Запуск на холодную — без посторонних звуков', bad: 'Стук гидрокомпенсаторов >5 сек', cost: 'Гидрокомпенсаторы 3000–6000 ₽' },
        { id: 'e2', label: 'Шум ГРМ — без свиста и цоканья', bad: 'Свист натяжителя, стук помпы', cost: 'Комплект ГРМ 5000–10000 ₽' },
        { id: 'e3', label: 'Масло — уровень, цвет, запах', bad: 'Густая чёрная эмульсия (вода)', cost: 'Пробита прокладка ГБЦ >10000 ₽' },
        { id: 'e4', label: 'Антифриз — уровень, цвет', bad: 'Масляная плёнка / ржавчина', cost: 'Прокладка ГБЦ / радиатор от 5000 ₽' },
        { id: 'e5', label: 'Выхлоп на прогретом — цвет дыма', bad: 'Синий (масло) / белый (антифриз)', cost: 'Маслосъёмные колпачки 5000 ₽ / ГБЦ 15000 ₽' },
        { id: 'e6', label: 'Обороты ХХ — 750–850, без плавания', bad: 'Плавают >100 об/мин', cost: 'Чистка дросселя 500 ₽' },
        { id: 'e7', label: 'Проверка утечек — подтёки на двигателе', bad: 'Масло с сальника коленвала / клапанной крышки', cost: 'Сальники 2000–5000 ₽' },
      ]
    },
    {
      name: 'Трансмиссия',
      items: [
        { id: 't1', label: 'Сцепление — схватывание в середине хода педали', bad: 'Схватывает в самом верху (износ)', cost: 'Замена сцепления 6000–15000 ₽' },
        { id: 't2', label: 'КПП — передачи включаются чётко, без хруста', bad: 'Хруст 2-й / 3-й передачи', cost: 'Синхронизаторы от 10000 ₽' },
        { id: 't3', label: 'ШРУСы — хруст при полном вывороте колёс', bad: 'Отчётливый хруст с одной стороны', cost: 'Замена ШРУСа 2000–5000 ₽' },
        { id: 't4', label: 'Масло в КПП — уровень, цвет', bad: 'Чёрное, запах гари', cost: 'Замена масла 800–1500 ₽' },
      ]
    },
    {
      name: 'Подвеска и рулевое',
      items: [
        { id: 's1', label: 'Стук спереди на неровностях (<20 км/ч)', bad: 'Глухой стук (стабилизатор / сайлентблоки)', cost: 'Стабилизатор 1000–3000 ₽' },
        { id: 's2', label: 'Стук сзади на «лежачих»', bad: 'Амортизаторы / сайлентблоки балки', cost: 'Амортизаторы 3000–6000 ₽' },
        { id: 's3', label: 'Люфт руля — не более 10°', bad: 'Люфт >15° (наконечники / рейка)', cost: 'Наконечники 1500–3000 ₽ / рейка 5000–12000 ₽' },
        { id: 's4', label: 'Руль не уводит при разгоне/торможении', bad: 'Увод (развал/схождение / сайлентблоки)', cost: 'Развал 800–1500 ₽' },
        { id: 's5', label: 'Амортизаторы — без потёков масла', bad: 'Подтёки, отбой на отрыв (проверка качком)', cost: 'Замена амортизаторов 5000–12000 ₽' },
      ]
    },
    {
      name: 'Электрика',
      items: [
        { id: 'l1', label: 'Фары — ближний, дальний, ПТФ', bad: 'Не горит одна сторона / ПТФ', cost: 'Лампа H4 300 ₽' },
        { id: 'l2', label: 'Стеклоподъёмники — все 4 или 2 передних', bad: 'Не работают, заедают', cost: 'Моторчик 1500–3000 ₽' },
        { id: 'l3', label: 'Центральный замок — открытие/закрытие', bad: 'Не реагирует на пульт', cost: 'Блок ЦЗ 2000–5000 ₽' },
        { id: 'l4', label: 'Печка — все скорости вентилятора', bad: 'Работает только на 4-й (сопротивление печки)', cost: 'Резистор печки 500–1500 ₽' },
        { id: 'l5', label: 'Check Engine — отсутствие на панели', bad: 'Горит постоянно', cost: 'Диагностика OBD2 500 ₽' },
        { id: 'l6', label: 'Заряд АКБ — напряжение 14,0–14,5 В на работающем двигателе', bad: '<13,5 В (генератор)', cost: 'Щётки 500 ₽ / регулятор 800–2000 ₽' },
      ]
    },
    {
      name: 'Тормозная система',
      items: [
        { id: 'b1', label: 'Педаль тормоза — упругая, без провалов', bad: 'Мягкая / проваливается (воздух / утечка)', cost: 'Прокачка 500–1500 ₽ / ГТЦ 2000–5000 ₽' },
        { id: 'b2', label: 'Скрип / визг при торможении', bad: 'Износ колодок до индикатора', cost: 'Колодки 1000–2000 ₽' },
        { id: 'b3', label: 'Ручник — держит на 3–5 щелчке', bad: 'Не держит', cost: 'Трос 1000–2500 ₽' },
        { id: 'b4', label: 'ABS — лампа гаснет после запуска', bad: 'Горит постоянно', cost: 'Датчик 800–2000 ₽' },
      ]
    },
    {
      name: 'Салон',
      items: [
        { id: 'i1', label: 'Сиденья — без протирания боковой поддержки', bad: 'Протёрто до основы (частый дефект Symbol)', cost: 'Перетяжка 3000–5000 ₽ / сиденье' },
        { id: 'i2', label: 'Потолок — не провисает', bad: 'Отклеился (частая проблема после 10 лет)', cost: 'Переклейка потолка 3000–5000 ₽' },
        { id: 'i3', label: 'Печка — дует во все дефлекторы', bad: 'Забит салонный фильтр / заслонка', cost: 'Фильтр 300–800 ₽' },
        { id: 'i4', label: 'Кнопки стеклоподъёмников — не провалились', bad: 'Износ пластиковых направляющих', cost: 'Кнопка 200–500 ₽' },
      ]
    },
  ];

  categories.forEach(function(cat, ci) {
    var catDiv = document.createElement('div');
    catDiv.style.cssText = 'border-bottom:1px solid var(--searchbar-border-color);';

    var header = document.createElement('div');
    header.style.cssText = 'padding:10px 16px;font-weight:bold;cursor:pointer;display:flex;justify-content:space-between;align-items:center;';
    header.innerHTML = '<span>' + cat.name + '</span><span class="cat-progress" id="cp-' + ci + '">0/' + cat.items.length + '</span>';
    header.onclick = function(e) {
      if (e.target.tagName === 'BUTTON') return;
      var body = catDiv.querySelector('.cat-body');
      body.style.display = body.style.display === 'none' ? '' : 'none';
    };

    var body = document.createElement('div');
    body.className = 'cat-body';
    body.style.cssText = 'padding:0 16px 12px;';

    cat.items.forEach(function(item) {
      var row = document.createElement('div');
      row.style.cssText = 'display:flex;align-items:flex-start;gap:8px;margin:6px 0;';

      var cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.id = item.id;
      cb.style.cssText = 'margin-top:4px;flex-shrink:0;';

      var labelDiv = document.createElement('div');
      labelDiv.style.cssText = 'flex:1;font-size:0.9em;';

      var strong = document.createElement('strong');
      strong.textContent = item.label;
      labelDiv.appendChild(strong);

      var badP = document.createElement('div');
      badP.style.cssText = 'opacity:0.8;font-size:0.85em;color:#f44336;';
      badP.innerHTML = '⚠️ На что обратить внимание: ' + item.bad;
      labelDiv.appendChild(badP);

      var costP = document.createElement('div');
      costP.style.cssText = 'opacity:0.7;font-size:0.8em;';
      costP.innerHTML = '💰 Стоимость ремонта: ' + item.cost;
      labelDiv.appendChild(costP);

      cb.addEventListener('change', function() {
        var items = catDiv.querySelectorAll('input[type="checkbox"]');
        var checked = 0;
        items.forEach(function(c) { if (c.checked) checked++; });
        catDiv.querySelector('.cat-progress').textContent = checked + '/' + items.length;
        updateSummary();
      });

      row.appendChild(cb);
      row.appendChild(labelDiv);
      body.appendChild(row);
    });

    catDiv.appendChild(header);
    catDiv.appendChild(body);
    container.appendChild(catDiv);
  });

  var summary = document.createElement('div');
  summary.id = 'inspection-summary';
  summary.style.cssText = 'margin:16px;padding:12px 16px;border-radius:8px;background:rgba(76,175,80,0.08);text-align:center;';
  summary.innerHTML = '<strong>Итого:</strong> проверено 0/' + countTotal() + ' пунктов';
  container.appendChild(summary);

  function countTotal() {
    var n = 0;
    categories.forEach(function(c) { n += c.items.length; });
    return n;
  }

  function updateSummary() {
    var all = document.querySelectorAll('#inspection-checklist input[type="checkbox"]');
    var total = all.length;
    var checked = 0;
    all.forEach(function(c) { if (c.checked) checked++; });
    summary.innerHTML = '<strong>Итого:</strong> проверено ' + checked + '/' + total + ' пунктов (' + Math.round(checked/total*100) + '%)';
    var pct = Math.round(checked/total*100);
    if (pct >= 80) summary.innerHTML += ' ✅ Состояние авто выше среднего';
    else if (pct >= 50) summary.innerHTML += ' ⚠️ Требуется торг и осмотр специалиста';
    else summary.innerHTML += ' 🔴 Рекомендуется поискать другой экземпляр';
  }

  var heading = document.querySelector('.content h1');
  if (heading) heading.parentNode.insertBefore(container, heading.nextSibling);
})();
</script>

## Как пользоваться

При осмотре автомобиля отмечайте пункты, которые проверили и не нашли дефектов. Чеклист показывает прогресс и итоговую оценку состояния.

- **>80%** — хороший экземпляр, можно рассматривать к покупке
- **50–80%** — требует детального осмотра специалистом и торга
- **<50%** — рекомендуем поискать другой автомобиль

Перед осмотром возьмите: фонарик, зеркальце для днища, магнит (немаркий, для скрытого шпаклёва), толщиномер (если есть), OBD2-сканер.

## Дополнительные советы

| Что проверить | Как проверить | На что смотреть |
|--------------|---------------|-----------------|
| Документы | ПТС, СТС, сервисная книжка | Количество владельцев, даты ТО, залог |
| Вин-номер | Сверить по кузову и документам | Совпадение, коррозия таблички |
| Пробег | Сверка: одометр, тормозной диск, педали, руль (износ) | Занижение пробега — бич Symbol |
| Тест-драйв | Прогрев до 90 °C, трасса, город | Шумы, вибрации, работа КПП |

## Типичные болезни Symbol по пробегу

| Пробег | Характерные проблемы |
|--------|----------------------|
| 50 000–80 000 км | Ремень ГРМ + помпа (если не менялись), передние стойки стабилизатора |
| 100 000–150 000 км | Замена сцепления, лямбда-зонд, амортизаторы, гидрокомпенсаторы |
| 150 000–200 000 км | ШРУСы, генератор (щётки/регулятор), КПП (синхронизаторы), рулевая рейка |
| >200 000 км | Двигатель — маслосъёмные колпачки, поршневые кольца, капитальный ремонт |

> **Совет:** Самые дорогие проблемы на Symbol — ГРМ (обрыв гнёт клапаны), автоматическая КПП (выход из строя, ремонт 30 000–60 000 ₽), коррозия порогов и арок.
