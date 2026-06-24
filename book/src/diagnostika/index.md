# Диагностика по симптомам

<script>
// Interactive symptom filter + cost filter
document.addEventListener('DOMContentLoaded', function() {
  const textFilter = document.getElementById('symptom-filter');
  const costButtons = document.querySelectorAll('.cost-filter-btn');
  const counter = document.getElementById('filter-count');
  if (!textFilter) return;

  let activeCost = 'all';
  let activeQuery = '';

  function applyFilters() {
    const items = document.querySelectorAll('.symptom-item');
    let visible = 0;

    items.forEach(function(item) {
      const text = item.textContent.toLowerCase();
      const passText = !activeQuery || text.includes(activeQuery);
      
      let passCost = true;
      if (activeCost !== 'all') {
        const costTags = item.querySelectorAll('.cost-tag.' + activeCost);
        passCost = costTags.length > 0;
      }
      
      if (passText && passCost) {
        item.style.display = '';
        visible++;
      } else {
        item.style.display = 'none';
      }
    });

    if (counter) {
      const total = items.length;
      const suffix = activeCost !== 'all' ? ' (фильтр по цене)' : '';
      counter.textContent = visible + ' из ' + total + ' симптомов' + suffix;
    }
  }

  // Text filter
  textFilter.addEventListener('input', function() {
    activeQuery = this.value.toLowerCase().trim();
    applyFilters();
  });

  // Cost filter buttons
  costButtons.forEach(function(btn) {
    btn.addEventListener('click', function() {
      const cost = this.dataset.cost;
      activeCost = cost;
      costButtons.forEach(function(b) {
        b.style.background = (b.dataset.cost === cost) ? 'var(--searchbar-bg)' : 'var(--bg)';
        b.style.fontWeight = (b.dataset.cost === cost) ? 'bold' : 'normal';
        b.style.borderWidth = (b.dataset.cost === cost) ? '2px' : '1px';
      });
      applyFilters();
    });
  });
});
</script>

<style>
    .symptom-filter-input {
        width: 100%;
        padding: 12px 16px;
        font-size: 16px;
        border: 2px solid var(--searchbar-border-color);
        border-radius: 8px;
        background: var(--searchbar-bg);
        color: var(--fg);
        margin: 16px 0;
        box-sizing: border-box;
    }
    .symptom-filter-input:focus {
        outline: none;
        border-color: var(--links);
    }
    .filter-count {
        font-size: 0.9em;
        color: var(--fg);
        opacity: 0.7;
        margin: 0 0 20px 0;
    }
    .symptom-category {
        margin: 0 0 24px 0;
    }
    .symptom-item {
        padding: 12px 16px;
        margin: 8px 0;
        border: 1px solid var(--searchbar-border-color);
        border-radius: 6px;
        background: var(--bg);
        transition: opacity 0.2s, display 0.2s;
    }
    .symptom-item strong {
        color: var(--links);
        font-size: 1.05em;
    }
    .symptom-item .cause {
        margin: 6px 0;
        font-size: 0.95em;
        opacity: 0.85;
    }
    .symptom-item .action {
        margin: 6px 0 0 0;
        font-size: 0.9em;
    }
    .symptom-item .action a {
        text-decoration: underline;
        text-underline-offset: 2px;
    }
    .symptom-item .cost-tag {
        display: inline-block;
        font-size: 0.8em;
        padding: 2px 8px;
        border-radius: 10px;
        margin-right: 6px;
    }
    .symptom-item .cost-tag.low {
        background: #4caf50;
        color: #fff;
    }
    .symptom-item .cost-tag.medium {
        background: #ff9800;
        color: #fff;
    }
    .symptom-item .cost-tag.high {
        background: #f44336;
        color: #fff;
    }
    .symptom-item .cost-tag.variable {
        background: #78909c;
        color: #fff;
    }
    .symptom-item.hidden {
        display: none;
    }
    .symptom-category h3 {
        margin-top: 20px;
        padding-bottom: 6px;
        border-bottom: 1px solid var(--searchbar-border-color);
    }
</style>

<input type="text" id="symptom-filter" class="symptom-filter-input" placeholder="Введите симптом: стук, дым, не заводится, течь масла, плавают обороты..." autofocus>
<div class="filter-count" id="filter-count">Все симптомы</div>

<div class="cost-filter-bar" style="margin:0 0 16px 0;display:flex;gap:8px;flex-wrap:wrap;">
    <button class="cost-filter-btn active" data-cost="all" style="padding:6px 14px;border:1px solid var(--searchbar-border-color);border-radius:16px;background:var(--bg);cursor:pointer;font-size:0.85em;">Все цены</button>
    <button class="cost-filter-btn" data-cost="low" style="padding:6px 14px;border:1px solid #4caf50;border-radius:16px;background:var(--bg);cursor:pointer;font-size:0.85em;color:#4caf50;">🟢 до 1500 ₽</button>
    <button class="cost-filter-btn" data-cost="medium" style="padding:6px 14px;border:1px solid #ff9800;border-radius:16px;background:var(--bg);cursor:pointer;font-size:0.85em;color:#ff9800;">🟠 1500–5000 ₽</button>
    <button class="cost-filter-btn" data-cost="high" style="padding:6px 14px;border:1px solid #f44336;border-radius:16px;background:var(--bg);cursor:pointer;font-size:0.85em;color:#f44336;">🔴 от 5000 ₽</button>
</div>

```mermaid
flowchart TD
    A[Симптом] --> B{Двигатель заводится?}
    B -->|Нет| C{Стартер крутит?}
    C -->|Да| D[Нет искры / нет топлива]
    C -->|Нет| E[АКБ / стартер / масса]
    D --> F{Есть ошибки OBD2?}
    F -->|Да| G[Читать DTC-коды]
    F -->|Нет| H[ДПКВ / иммо / предохранители]
    B -->|Да| I{Посторонние звуки?}
    I -->|Стук сверху| J[Гидрокомпенсаторы / ГРМ]
    I -->|Стук снизу| K[Коленвал / поршневая]
    I -->|Нет| L{Дымит?}
    L -->|Чёрный| M[Богатая смесь]
    L -->|Синий| N[Масло в цилиндрах]
    L -->|Белый| O[Антифриз в цилиндрах]
    L -->|Нет| P[Проверить свечи / форсунки]
    
    style A fill:#1565c0,color:#fff
    style G fill:#e65100,color:#fff
    style O fill:#c62828,color:#fff
```

## Двигатель

<div class="symptom-category">

### Система зажигания и запуск

<div class="symptom-item">
<strong>Двигатель не заводится (стартер крутит)</strong>
<div class="cause">Причины: нет искры, нет топлива, неисправен ДПКВ, иммобилайзер</div>
<div class="action">→ <a href="../dvigatel/3-1.md">Диагностика двигателя</a> · <a href="../elektrika/8-3.md">Система пуска</a></div>
<div><span class="cost-tag low">Бесплатно</span> <span class="cost-tag variable">диагностика ОБД2</span></div>
</div>

<div class="symptom-item">
<strong>Двигатель не заводится (стартер молчит)</strong>
<div class="cause">Причины: разряжена АКБ, окислены клеммы, неисправен стартер или втягивающее реле</div>
<div class="action">→ <a href="../elektrika/8-1.md">АКБ</a> · <a href="../elektrika/8-3.md">Стартер</a></div>
<div><span class="cost-tag low">от 0 ₽</span> <span class="cost-tag medium">до 5000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Двигатель заводится и сразу глохнет</strong>
<div class="cause">Причины: иммобилайзер (ключ не распознан), подсос воздуха, загрязнён РХХ</div>
<div class="action">→ <a href="../dvigatel/3-2.md#%D0%A0%D0%B5%D0%B3%D1%83%D0%BB%D0%B8%D1%80%D0%BE%D0%B2%D0%BA%D0%B0-%D0%BE%D0%B1%D0%BE%D1%80%D0%BE%D1%82%D0%BE%D0%B2-%D1%85%D0%BE%D0%BB%D0%BE%D1%81%D1%82%D0%BE%D0%B3%D0%BE-%D1%85%D0%BE%D0%B4%D0%B0">Регулировка ХХ</a></div>
<div><span class="cost-tag low">чистка дросселя: 500 ₽</span> <span class="cost-tag variable">иммо: от 2000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Провалы при резком нажатии педали газа</strong>
<div class="cause">Причины: загрязнение форсунок, подсос воздуха, забит топливный фильтр</div>
<div class="action">→ <a href="../dvigatel/3-2.md#%D0%A4%D0%BE%D1%80%D1%81%D1%83%D0%BD%D0%BA%D0%B8-%D0%B4%D0%B8%D0%B0%D0%B3%D0%BD%D0%BE%D1%81%D1%82%D0%B8%D0%BA%D0%B0-%D0%B8-%D0%B7%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0">Форсунки</a></div>
<div><span class="cost-tag low">фильтр: 500–800 ₽</span> <span class="cost-tag medium">форсунки: 4000–8000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Плавают обороты холостого хода</strong>
<div class="cause">Причины: загрязнён дроссель, неисправен РХХ, подсос воздуха</div>
<div class="action">→ <a href="../dvigatel/3-2.md#%D0%94%D1%80%D0%BE%D1%81%D1%81%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9-%D1%83%D0%B7%D0%B5%D0%BB">Чистка дросселя</a></div>
<div><span class="cost-tag low">чистка: 300–500 ₽</span> <span class="cost-tag medium">РХХ: 800–1500 ₽</span></div>
</div>

</div>

<div class="symptom-category">

### Выхлоп и цвета дыма

<div class="symptom-item">
<strong>Белый дым из выхлопной трубы</strong>
<div class="cause">Причины: пробита прокладка ГБЦ (охлаждающая жидкость в камере сгорания), трещина в ГБЦ</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A2%D0%B8%D0%BF%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BD%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%B4%D0%B2%D0%B8%D0%B3%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9">Неисправности двигателя</a></div>
<div><span class="cost-tag high">прокладка ГБЦ: 5000–12000 ₽</span> <span class="cost-tag high">ГБЦ: от 15000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Синий дым (при запуске после стоянки)</strong>
<div class="cause">Причины: износ маслосъёмных колпачков</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A2%D0%B8%D0%BF%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BD%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%B4%D0%B2%D0%B8%D0%B3%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9">Замена колпачков</a></div>
<div><span class="cost-tag medium">колпачки: 3000–5000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Чёрный дым</strong>
<div class="cause">Причины: богатая смесь (неисправны форсунки, лямбда-зонд, MAP-датчик)</div>
<div class="action">→ <a href="../dvigatel/3-2.md">Система питания</a> · <a href="../dtc.md">Коды ошибок OBD2</a></div>
<div><span class="cost-tag low">лямбда: 1500–3000 ₽</span> <span class="cost-tag medium">форсунки: 4000–8000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Двигатель троит / пропуски зажигания</strong>
<div class="cause">Причины: неисправна свеча/катушка зажигания, подсос воздуха, низкая компрессия</div>
<div class="action">→ <a href="../statyi/svechi.md">Свечи зажигания</a> · <a href="../dvigatel/3-1.md">Диагностика</a></div>
<div><span class="cost-tag low">свечи: 600–1200 ₽</span> <span class="cost-tag medium">катушка: 1500–3000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Двигатель набирает обороты, но не едет</strong>
<div class="cause">Причины: пробуксовка сцепления, износ диска</div>
<div class="action">→ <a href="../transmissiya/4-1.md">Замена сцепления</a></div>
<div><span class="cost-tag high">комплект сцепления: 5000–15000 ₽</span></div>
</div>

</div>

<div class="symptom-category">

### Стуки и шумы

<div class="symptom-item">
<strong>Стук гидрокомпенсаторов (цоканье на холодную)</strong>
<div class="cause">Причины: воздух в масле, загрязнение масляных каналов, износ</div>
<div class="action">→ <a href="../dvigatel/3-3.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D0%BC%D0%B0%D1%81%D0%BB%D0%B0-%D0%B8-%D0%BC%D0%B0%D1%81%D0%BB%D1%8F%D0%BD%D0%BE%D0%B3%D0%BE-%D1%84%D0%B8%D0%BB%D1%8C%D1%82%D1%80%D0%B0">Замена масла</a></div>
<div><span class="cost-tag low">замена масла: 1500–2500 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Перегрев двигателя (температура выше 105 °C)</strong>
<div class="cause">Причины: низкий уровень антифриза, термостат закрыт, воздушная пробка, неисправен вентилятор</div>
<div class="action">→ <a href="../dvigatel/3-4.md">Система охлаждения</a> · <a href="../dvigatel/3-4.md#%D0%92%D0%B5%D0%BD%D1%82%D0%B8%D0%BB%D1%8F%D1%82%D0%BE%D1%80-%D0%BE%D1%85%D0%BB%D0%B0%D0%B6%D0%B4%D0%B5%D0%BD%D0%B8%D1%8F-%D1%80%D0%B0%D0%B4%D0%B8%D0%B0%D1%82%D0%BE%D1%80%D0%B0">Вентилятор</a></div>
<div><span class="cost-tag low">термостат: 600–1200 ₽</span> <span class="cost-tag medium">вентилятор: 3000–6000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Плохо заводится на горячую</strong>
<div class="cause">Причины: неисправен ДПКВ (датчик коленвала) при нагреве, падает давление топлива (обратный клапан)</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A2%D0%B8%D0%BF%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BD%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%B4%D0%B2%D0%B8%D0%B3%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9">Диагностика</a></div>
<div><span class="cost-tag medium">ДПКВ: 800–2000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Стук поршневого пальца</strong>
<div class="cause">Причины: износ втулки верхней головки шатуна</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A2%D0%B8%D0%BF%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BD%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%B4%D0%B2%D0%B8%D0%B3%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9">Диагностика</a></div>
<div><span class="cost-tag high">ремонт двигателя: от 15000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Посторонний шум в районе ГРМ</strong>
<div class="cause">Причины: износ натяжителя или ремня ГРМ, помпы</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A0%D0%B0%D1%81%D0%BF%D1%80%D0%B5%D0%B4%D0%B5%D0%BB%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9-%D0%B2%D0%B0%D0%BB-%D0%B8-%D0%93%D0%A0%D0%9C">Замена ремня ГРМ</a> · <a href="../dvigatel/3-4.md#%D0%AD%D0%BB%D0%B5%D0%BC%D0%B5%D0%BD%D1%82%D1%8B-%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D1%8B">Помпа</a></div>
<div><span class="cost-tag medium">комплект ГРМ: 4000–8000 ₽</span> <span class="cost-tag high">с заменой: 8000–15000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Металлический стук при проезде лежачих полицейских</strong>
<div class="cause">Причины: износ стабилизатора, сайлентблоков, амортизаторов</div>
<div class="action">→ <a href="../hodovaya/5-1.md#%D0%A1%D0%B0%D0%B9%D0%BB%D0%B5%D0%BD%D1%82-%D0%B1%D0%BB%D0%BE%D0%BA%D0%B8-%D1%80%D1%8B%D1%87%D0%B0%D0%B3%D0%B0">Сайлент-блоки</a> · <a href="../hodovaya/5-1.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%81%D1%82%D0%BE%D0%B9%D0%BA%D0%B8-%D0%B2-%D1%81%D0%B1%D0%BE%D1%80%D0%B5">Амортизаторы</a></div>
<div><span class="cost-tag medium">сайлентблоки: 2000–4000 ₽</span> <span class="cost-tag high">амортизаторы: 5000–12000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Запах бензина в салоне</strong>
<div class="cause">Причины: трещина в топливной магистрали, неплотная крышка бензобака, подсос через адсорбер</div>
<div class="action">→ <a href="../dvigatel/3-2.md">Система питания</a></div>
<div><span class="cost-tag low">крышка бензобака: 200–500 ₽</span> <span class="cost-tag medium">адсорбер: 2000–4000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Повышенный расход топлива</strong>
<div class="cause">Причины: неисправен лямбда-зонд, загрязнение форсунок, неправильная работа термостата, износ свечей</div>
<div class="action">→ <a href="../dvigatel/3-2.md">Система питания</a> · <a href="../dtc.md">Чтение ошибок OBD2</a></div>
<div><span class="cost-tag low">свечи: 600–1200 ₽</span> <span class="cost-tag medium">лямбда: 1500–3000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Свист при нажатии на сцепление</strong>
<div class="cause">Причины: износ выжимного подшипника</div>
<div class="action">→ <a href="../transmissiya/4-1.md">Сцепление — замена</a></div>
<div><span class="cost-tag high">замена сцепления: 6000–15000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Дизелит / масло на свечах</strong>
<div class="cause">Причины: износ маслосъёмных колпачков, залегли поршневые кольца</div>
<div class="action">→ <a href="../dvigatel/3-3.md#%D0%A1%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%B0-%D0%B2%D0%B5%D0%BD%D1%82%D0%B8%D0%BB%D1%8F%D1%86%D0%B8%D0%B8-%D0%BA%D0%B0%D1%80%D1%82%D0%B5%D1%80%D0%BD%D1%8B%D1%85-%D0%B3%D0%B0%D0%B7%D0%BE%D0%B2">Система смазки</a></div>
<div><span class="cost-tag medium">декарбонизация: 1500–3000 ₽</span> <span class="cost-tag high">кольца: от 12000 ₽</span></div>
</div>

</div>

## Трансмиссия

<div class="symptom-category">

<div class="symptom-item">
<strong>Задняя передача не включается</strong>
<div class="cause">Причины: неисправен электромагнит reverse lockout</div>
<div class="action">→ <a href="../transmissiya/4-2.md#%D0%9D%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-reverse-lockout">Reverse lockout</a></div>
<div><span class="cost-tag low">reverse lockout: 1000–2500 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Хруст при переключении передач</strong>
<div class="cause">Причины: низкий уровень масла в КПП, износ синхронизаторов</div>
<div class="action">→ <a href="../transmissiya/4-2.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D0%BC%D0%B0%D1%81%D0%BB%D0%B0">Замена масла КПП</a></div>
<div><span class="cost-tag low">масло КПП: 800–1500 ₽</span> <span class="cost-tag high">синхронизатор: от 10000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Дёргается при трогании (сцепление)</strong>
<div class="cause">Причины: износ диска сцепления, масло на диске, износ корзины</div>
<div class="action">→ <a href="../transmissiya/4-1.md">Замена сцепления</a></div>
<div><span class="cost-tag high">замена сцепления: 6000–15000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Вибрирует на скорости 80–100 км/ч</strong>
<div class="cause">Причины: износ ШРУС, разбалансировка колёс, износ стоек стабилизатора</div>
<div class="action">→ <a href="../transmissiya/4-3.md">Приводные валы</a> · <a href="../hodovaya/5-3.md#%D0%9F%D0%BE%D1%80%D1%8F%D0%B4%D0%BE%D0%BA-%D0%B7%D0%B0%D0%BC%D0%B5%D0%BD%D1%8B-%D0%BA%D0%BE%D0%BB%D0%B5%D1%81%D0%B0">Колёса</a></div>
<div><span class="cost-tag low">балансировка: 400–800 ₽</span> <span class="cost-tag medium">ШРУС: 2000–5000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Хруст при поворотах</strong>
<div class="cause">Причины: износ наружного ШРУСа, порван пыльник</div>
<div class="action">→ <a href="../transmissiya/4-3.md#%D0%9F%D0%BE%D1%80%D1%8F%D0%B4%D0%BE%D0%BA-%D1%80%D0%B0%D0%B1%D0%BE%D1%82-%D0%BD%D0%B0%D1%80%D1%83%D0%B6%D0%BD%D1%8B%D0%B9-%D0%A8%D0%A0%D0%A3%D0%A1">Замена наружного ШРУС</a></div>
<div><span class="cost-tag medium">ШРУС: 2000–5000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Выбивает передачи на ходу</strong>
<div class="cause">Причины: износ вилок КПП, износ синхронизаторов, ослабление крепления КПП</div>
<div class="action">→ <a href="../transmissiya/4-2.md#%D0%9D%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8">Неисправности КПП</a></div>
<div><span class="cost-tag high">ремонт КПП: от 15000 ₽</span></div>
</div>

</div>

## Ходовая часть и рулевое

<div class="symptom-category">

<div class="symptom-item">
<strong>Стук в рулевой колонке</strong>
<div class="cause">Причины: износ рулевой рейки, затяжка упора</div>
<div class="action">→ <a href="../rulevoe/6-1.md#%D0%A0%D0%B5%D0%BC%D0%BE%D0%BD%D1%82-%D0%BD%D0%B0-%D0%BC%D0%B5%D1%81%D1%82%D0%B5">Регулировка рейки</a></div>
<div><span class="cost-tag low">регулировка: 500–1500 ₽</span> <span class="cost-tag high">рейка: 5000–12000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Руль тугой / тяжело вращается</strong>
<div class="cause">Причины: низкий уровень жидкости ГУР, износ насоса ГУР, завоздушивание</div>
<div class="action">→ <a href="../rulevoe/6-2.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D0%B6%D0%B8%D0%B4%D0%BA%D0%BE%D1%81%D1%82%D0%B8-%D0%93%D0%A3%D0%A0">Замена жидкости ГУР</a></div>
<div><span class="cost-tag medium">насос ГУР: 3000–8000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Биение руля при торможении</strong>
<div class="cause">Причины: деформация тормозных дисков, неравномерный износ</div>
<div class="action">→ <a href="../tormoza/7-1.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%82%D0%BE%D1%80%D0%BC%D0%BE%D0%B7%D0%BD%D1%8B%D1%85-%D0%B4%D0%B8%D1%81%D0%BA%D0%BE%D0%B2">Замена дисков</a></div>
<div><span class="cost-tag medium">диски: 3000–6000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Увод в сторону при движении</strong>
<div class="cause">Причины: нарушен развал-схождение, неравномерное давление в шинах, износ сайлентблоков</div>
<div class="action">→ <a href="../hodovaya/5-3.md">Колёса и шины</a> · <a href="../hodovaya/5-1.md">Передняя подвеска</a></div>
<div><span class="cost-tag low">развал: 800–1500 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Стук сзади на неровностях</strong>
<div class="cause">Причины: износ амортизаторов, износ сайлентблоков балки</div>
<div class="action">→ <a href="../hodovaya/5-2.md#%D0%9F%D1%80%D0%B8%D0%B7%D0%BD%D0%B0%D0%BA%D0%B8-%D0%B8%D0%B7%D0%BD%D0%BE%D1%81%D0%B0-%D0%B0%D0%BC%D0%BE%D1%80%D1%82%D0%B8%D0%B7%D0%B0%D1%82%D0%BE%D1%80%D0%BE%D0%B2">Амортизаторы задние</a></div>
<div><span class="cost-tag medium">амортизаторы: 3000–6000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Люфт руля / бьёт руль на скорости</strong>
<div class="cause">Причины: износ рулевых наконечников, износ рейки</div>
<div class="action">→ <a href="../rulevoe/6-1.md">Рулевой механизм</a> · <a href="../spravochnaya/oem.md#%D0%A0%D1%83%D0%BB%D0%B5%D0%B2%D0%BE%D0%B9-%D0%BD%D0%B0%D0%BA%D0%BE%D0%BD%D0%B5%D1%87%D0%BD%D0%B8%D0%BA">Наконечники</a></div>
<div><span class="cost-tag medium">наконечники: 1500–3000 ₽</span></div>
</div>

</div>

## Электрооборудование

<div class="symptom-category">

<div class="symptom-item">
<strong>АКБ разряжается за 1–2 дня</strong>
<div class="cause">Причины: утечка тока, неисправен генератор (диодный мост), старость АКБ</div>
<div class="action">→ <a href="../elektrika/8-1.md">АКБ</a> · <a href="../elektrika/8-2.md">Генератор</a></div>
<div><span class="cost-tag low">АКБ: 2500–5000 ₽</span> <span class="cost-tag medium">генератор: 5000–10000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Горит лампа зарядки АКБ</strong>
<div class="cause">Причины: обрыв ремня генератора, износ щёток, неисправен регулятор напряжения</div>
<div class="action">→ <a href="../elektrika/8-2.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%80%D0%B5%D0%B3%D1%83%D0%BB%D1%8F%D1%82%D0%BE%D1%80%D0%B0-%D0%BD%D0%B0%D0%BF%D1%80%D1%8F%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F">Замена регулятора</a></div>
<div><span class="cost-tag medium">регулятор: 800–2000 ₽</span> <span class="cost-tag low">щётки: 300–500 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Не работают стеклоподъёмники</strong>
<div class="cause">Причины: сгорел предохранитель, неисправен моторчик, обрыв проводки в гофре двери</div>
<div class="action">→ <a href="../elektrika/8-5.md">Предохранители</a> · <a href="../shemy/index.md">Схемы</a></div>
<div><span class="cost-tag low">предохранитель: 20 ₽</span> <span class="cost-tag medium">моторчик: 1500–3000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Не работают дворники</strong>
<div class="cause">Причины: сгорел предохранитель, износ моторедуктора, закисла трапеция</div>
<div class="action">→ <a href="../elektrika/8-5.md">Предохранители</a> · <a href="../statyi/dvorniki.md">Ремонт дворников</a></div>
<div><span class="cost-tag low">пред: 20 ₽</span> <span class="cost-tag medium">трапеция: 2000–4000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Не работают наружные световые приборы</strong>
<div class="cause">Причины: перегорела лампа, сгорел предохранитель, окисление контактов, неисправен подрулевой переключатель</div>
<div class="action">→ <a href="../elektrika/8-4.md">Освещение и сигнализация</a> · <a href="../elektrika/8-5.md">Предохранители</a></div>
<div><span class="cost-tag low">лампа: 100–300 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Печка дует холодным / не включается кондиционер</strong>
<div class="cause">Причины: низкий уровень или утечка хладагента, неисправен компрессор, забит салонный фильтр, обрыв вентилятора отопителя</div>
<div class="action">→ <a href="../expluataciya/1-2.md">Климатическая установка</a></div>
<div><span class="cost-tag low">салонный фильтр: 300–800 ₽</span> <span class="cost-tag medium">заправка: 1500–2500 ₽</span> <span class="cost-tag high">компрессор: от 15000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Не работает прикуриватель / аудиосистема</strong>
<div class="cause">Причины: сгорел предохранитель S1, окисление контактов</div>
<div class="action">→ <a href="../elektrika/8-5.md#%D0%9F%D1%80%D0%B5%D0%B4%D0%BE%D1%85%D1%80%D0%B0%D0%BD%D0%B8%D1%82%D0%B5%D0%BB%D0%B8-%D1%81%D0%B0%D0%BB%D0%BE%D0%BD%D0%B0">Блок предохранителей салона</a></div>
<div><span class="cost-tag low">предохранитель: 20 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Не работают центральный замок / ключ не поворачивается</strong>
<div class="cause">Причины: износ личинки замка, неисправен блок ЦЗ</div>
<div class="action">→ <a href="../elektrika/8-5.md#%D0%9F%D1%80%D0%B5%D0%B4%D0%BE%D1%85%D1%80%D0%B0%D0%BD%D0%B8%D1%82%D0%B5%D0%BB%D0%B8-%D1%81%D0%B0%D0%BB%D0%BE%D0%BD%D0%B0">Предохранители ЦЗ</a></div>
<div><span class="cost-tag medium">замок: 1500–4000 ₽</span></div>
</div>

</div>

## Тормозная система

<div class="symptom-category">

<div class="symptom-item">
<strong>Скрип тормозов</strong>
<div class="cause">Причины: износ колодок до индикатора, загрязнение, дешёвые колодки</div>
<div class="action">→ <a href="../tormoza/7-1.md">Передние тормоза</a> · <a href="../tormoza/7-2.md">Задние тормоза</a></div>
<div><span class="cost-tag low">колодки: 1000–2000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Мягкая педаль тормоза / проваливается</strong>
<div class="cause">Причины: воздух в системе, утечка тормозной жидкости, износ главного цилиндра</div>
<div class="action">→ <a href="../tormoza/7-1.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%82%D0%BE%D1%80%D0%BC%D0%BE%D0%B7%D0%BD%D1%8B%D1%85-%D0%BA%D0%BE%D0%BB%D0%BE%D0%B4%D0%BE%D0%BA">Прокачка тормозов</a></div>
<div><span class="cost-tag low">прокачка: 500–1500 ₽</span> <span class="cost-tag medium">ГТЦ: 2000–5000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Горит лампа ABS</strong>
<div class="cause">Причины: загрязнение датчика ABS, неисправен гидроблок, обрыв проводки</div>
<div class="action">→ <a href="../tormoza/7-3.md">ABS</a> · <a href="../dtc.md">Коды ABS</a></div>
<div><span class="cost-tag low">датчик: 800–2000 ₽</span> <span class="cost-tag high">гидроблок: 10000–20000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Торможение рывками / пульсация педали</strong>
<div class="cause">Причины: деформация тормозных дисков, неравномерная выработка</div>
<div class="action">→ <a href="../tormoza/7-1.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%82%D0%BE%D1%80%D0%BC%D0%BE%D0%B7%D0%BD%D1%8B%D1%85-%D0%B4%D0%B8%D1%81%D0%BA%D0%BE%D0%B2">Замена дисков</a></div>
<div><span class="cost-tag medium">диски + колодки: 5000–10000 ₽</span></div>
</div>

<div class="symptom-item">
<strong>Ручник не держит / слабый</strong>
<div class="cause">Причины: износ троса, износ задних колодок, неотрегулирован</div>
<div class="action">→ <a href="../tormoza/7-2.md#%D0%A0%D0%B5%D0%B3%D1%83%D0%BB%D0%B8%D1%80%D0%BE%D0%B2%D0%BA%D0%B0-%D1%81%D1%82%D0%BE%D1%8F%D0%BD%D0%BE%D1%87%D0%BD%D0%BE%D0%B3%D0%BE-%D1%82%D0%BE%D1%80%D0%BC%D0%BE%D0%B7%D0%B0">Регулировка ручника</a></div>
<div><span class="cost-tag low">регулировка: 300–500 ₽</span> <span class="cost-tag medium">трос: 1000–2500 ₽</span></div>
</div>

</div>

---

> 🔧 **Не нашли свой симптом?** Используйте поиск сверху — фильтр работает по всему тексту страницы. Также смотрите <a href="../dtc.md">коды неисправностей OBD2</a>.
