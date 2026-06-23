# Диагностика по симптомам

<script>
// Interactive symptom filter
document.addEventListener('DOMContentLoaded', function() {
  const filter = document.getElementById('symptom-filter');
  if (!filter) return;
  
  filter.addEventListener('input', function() {
    const query = this.value.toLowerCase().trim();
    const items = document.querySelectorAll('.symptom-item');
    let visible = 0;

    items.forEach(function(item) {
      const text = item.textContent.toLowerCase();
      if (!query || text.includes(query)) {
        item.style.display = '';
        visible++;
      } else {
        item.style.display = 'none';
      }
    });

    const counter = document.getElementById('filter-count');
    if (counter) counter.textContent = visible + ' из ' + items.length + ' симптомов';
  });
});
</script>

<style>
.symptom-filter-input {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  border: 2px solid #ddd;
  border-radius: 8px;
  margin: 16px 0;
  box-sizing: border-box;
}
.symptom-filter-input:focus {
  border-color: #1565c0;
  outline: none;
}
.symptom-category {
  margin: 24px 0;
  padding: 16px;
  background: #f5f5f5;
  border-radius: 8px;
}
.symptom-category h3 {
  margin-top: 0;
  color: #1565c0;
}
.symptom-item {
  margin: 8px 0;
  padding: 12px;
  background: white;
  border-left: 4px solid #e65100;
  border-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.symptom-item .cause {
  color: #666;
  font-size: 0.9em;
  margin-top: 4px;
}
.symptom-item .action {
  color: #1565c0;
  font-size: 0.9em;
  margin-top: 2px;
}
.symptom-item .action a {
  text-decoration: none;
}
.symptom-item .action a:hover {
  text-decoration: underline;
}
.filter-count {
  text-align: right;
  color: #888;
  font-size: 0.9em;
  margin-top: -8px;
}
@media (prefers-color-scheme: dark) {
  .symptom-category { background: #1e1e1e; }
  .symptom-item { background: #2d2d2d; border-left-color: #ff8a65; }
  .symptom-item .cause { color: #aaa; }
  .symptom-filter-input { background: #2d2d2d; color: #eee; border-color: #444; }
}
</style>

<input type="text" id="symptom-filter" class="symptom-filter-input" placeholder="Введите симптом: стук, дым, не заводится, течь масла, плавают обороты..." autofocus>
<div class="filter-count" id="filter-count">Все симптомы</div>

## Двигатель

<div class="symptom-category">

### Система зажигания и запуск

<div class="symptom-item">
<strong>Двигатель не заводится (стартер крутит)</strong>
<div class="cause">Причины: нет искры, нет топлива, неисправен ДПКВ, иммобилайзер</div>
<div class="action">→ <a href="../dvigatel/3-1.md">Диагностика двигателя</a> · <a href="../elektrika/8-3.md">Система пуска</a></div>
</div>

<div class="symptom-item">
<strong>Двигатель не заводится (стартер молчит)</strong>
<div class="cause">Причины: разряжена АКБ, окислены клеммы, неисправен стартер или втягивающее реле</div>
<div class="action">→ <a href="../elektrika/8-1.md">АКБ</a> · <a href="../elektrika/8-3.md">Стартер</a></div>
</div>

<div class="symptom-item">
<strong>Двигатель заводится и сразу глохнет</strong>
<div class="cause">Причины: иммобилайзер (ключ не распознан), подсос воздуха, загрязнён РХХ</div>
<div class="action">→ <a href="../dvigatel/3-2.md#%D0%A0%D0%B5%D0%B3%D1%83%D0%BB%D0%B8%D1%80%D0%BE%D0%B2%D0%BA%D0%B0-%D0%BE%D0%B1%D0%BE%D1%80%D0%BE%D1%82%D0%BE%D0%B2-%D1%85%D0%BE%D0%BB%D0%BE%D1%81%D1%82%D0%BE%D0%B3%D0%BE-%D1%85%D0%BE%D0%B4%D0%B0">Регулировка ХХ</a></div>
</div>

<div class="symptom-item">
<strong>Провалы при резком нажатии педали газа</strong>
<div class="cause">Причины: загрязнение форсунок, подсос воздуха, забит топливный фильтр</div>
<div class="action">→ <a href="../dvigatel/3-2.md#%D0%A4%D0%BE%D1%80%D1%81%D1%83%D0%BD%D0%BA%D0%B8-%D0%B4%D0%B8%D0%B0%D0%B3%D0%BD%D0%BE%D1%81%D1%82%D0%B8%D0%BA%D0%B0-%D0%B8-%D0%B7%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0">Форсунки</a></div>
</div>

<div class="symptom-item">
<strong>Плавают обороты холостого хода</strong>
<div class="cause">Причины: загрязнён дроссель, неисправен РХХ, подсос воздуха</div>
<div class="action">→ <a href="../dvigatel/3-2.md#%D0%94%D1%80%D0%BE%D1%81%D1%81%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9-%D1%83%D0%B7%D0%B5%D0%BB">Чистка дросселя</a></div>
</div>

</div>

<div class="symptom-category">

### Выхлоп и цвета дыма

<div class="symptom-item">
<strong>Белый дым из выхлопной трубы</strong>
<div class="cause">Причины: пробита прокладка ГБЦ (охлаждающая жидкость в камере сгорания), трещина в ГБЦ</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A2%D0%B8%D0%BF%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BD%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%B4%D0%B2%D0%B8%D0%B3%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9">Неисправности двигателя</a></div>
</div>

<div class="symptom-item">
<strong>Синий дым (при запуске после стоянки)</strong>
<div class="cause">Причины: износ маслосъёмных колпачков</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A2%D0%B8%D0%BF%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BD%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%B4%D0%B2%D0%B8%D0%B3%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9">Замена колпачков</a></div>
</div>

<div class="symptom-item">
<strong>Чёрный дым</strong>
<div class="cause">Причины: богатая смесь (неисправны форсунки, лямбда-зонд, MAP-датчик)</div>
<div class="action">→ <a href="../dvigatel/3-2.md">Система питания</a> · <a href="../dtc.md">Коды ошибок OBD2</a></div>
</div>

</div>

<div class="symptom-category">

### Стуки и шумы

<div class="symptom-item">
<strong>Стук гидрокомпенсаторов (цоканье на холодную)</strong>
<div class="cause">Причины: воздух в масле, загрязнение масляных каналов, износ</div>
<div class="action">→ <a href="../dvigatel/3-3.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D0%BC%D0%B0%D1%81%D0%BB%D0%B0-%D0%B8-%D0%BC%D0%B0%D1%81%D0%BB%D1%8F%D0%BD%D0%BE%D0%B3%D0%BE-%D1%84%D0%B8%D0%BB%D1%8C%D1%82%D1%80%D0%B0">Замена масла</a></div>
</div>

<div class="symptom-item">
<strong>Стук поршневого пальца</strong>
<div class="cause">Причины: износ втулки верхней головки шатуна</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A2%D0%B8%D0%BF%D0%BE%D0%B2%D1%8B%D0%B5-%D0%BD%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-%D0%B4%D0%B2%D0%B8%D0%B3%D0%B0%D1%82%D0%B5%D0%BB%D0%B5%D0%B9">Диагностика</a></div>
</div>

<div class="symptom-item">
<strong>Посторонний шум в районе ГРМ</strong>
<div class="cause">Причины: износ натяжителя или ремня ГРМ, помпы</div>
<div class="action">→ <a href="../dvigatel/3-1.md#%D0%A0%D0%B0%D1%81%D0%BF%D1%80%D0%B5%D0%B4%D0%B5%D0%BB%D0%B8%D1%82%D0%B5%D0%BB%D1%8C%D0%BD%D1%8B%D0%B9-%D0%B2%D0%B0%D0%BB-%D0%B8-%D0%93%D0%A0%D0%9C">Замена ремня ГРМ</a> · <a href="../dvigatel/3-4.md#%D0%AD%D0%BB%D0%B5%D0%BC%D0%B5%D0%BD%D1%82%D1%8B-%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D1%8B">Помпа</a></div>
</div>

<div class="symptom-item">
<strong>Металлический стук при проезде лежачих полицейских</strong>
<div class="cause">Причины: износ стабилизатора, сайлентблоков, амортизаторов</div>
<div class="action">→ <a href="../hodovaya/5-1.md#%D0%A1%D0%B0%D0%B9%D0%BB%D0%B5%D0%BD%D1%82-%D0%B1%D0%BB%D0%BE%D0%BA%D0%B8-%D1%80%D1%8B%D1%87%D0%B0%D0%B3%D0%B0">Сайлент-блоки</a> · <a href="../hodovaya/5-1.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%81%D1%82%D0%BE%D0%B9%D0%BA%D0%B8-%D0%B2-%D1%81%D0%B1%D0%BE%D1%80%D0%B5">Амортизаторы</a></div>
</div>

<div class="symptom-item">
<strong>Свист при нажатии на сцепление</strong>
<div class="cause">Причины: износ выжимного подшипника</div>
<div class="action">→ <a href="../transmissiya/4-1.md">Сцепление — замена</a></div>
</div>

</div>

## Трансмиссия

<div class="symptom-category">

<div class="symptom-item">
<strong>Задняя передача не включается</strong>
<div class="cause">Причины: неисправен электромагнит reverse lockout</div>
<div class="action">→ <a href="../transmissiya/4-2.md#%D0%9D%D0%B5%D0%B8%D1%81%D0%BF%D1%80%D0%B0%D0%B2%D0%BD%D0%BE%D1%81%D1%82%D0%B8-reverse-lockout">Reverse lockout</a></div>
</div>

<div class="symptom-item">
<strong>Хруст при переключении передач</strong>
<div class="cause">Причины: низкий уровень масла в КПП, износ синхронизаторов</div>
<div class="action">→ <a href="../transmissiya/4-2.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D0%BC%D0%B0%D1%81%D0%BB%D0%B0">Замена масла КПП</a></div>
</div>

<div class="symptom-item">
<strong>Дёргается при трогании (сцепление)</strong>
<div class="cause">Причины: износ диска сцепления, масло на диске, износ корзины</div>
<div class="action">→ <a href="../transmissiya/4-1.md">Замена сцепления</a></div>
</div>

<div class="symptom-item">
<strong>Вибрирует на скорости 80–100 км/ч</strong>
<div class="cause">Причины: износ ШРУС, разбалансировка колёс, износ стоек стабилизатора</div>
<div class="action">→ <a href="../transmissiya/4-3.md">Приводные валы</a> · <a href="../hodovaya/5-3.md#%D0%9F%D0%BE%D1%80%D1%8F%D0%B4%D0%BE%D0%BA-%D0%B7%D0%B0%D0%BC%D0%B5%D0%BD%D1%8B-%D0%BA%D0%BE%D0%BB%D0%B5%D1%81%D0%B0">Колёса</a></div>
</div>

<div class="symptom-item">
<strong>Хруст при поворотах</strong>
<div class="cause">Причины: износ наружного ШРУСа, порван пыльник</div>
<div class="action">→ <a href="../transmissiya/4-3.md#%D0%9F%D0%BE%D1%80%D1%8F%D0%B4%D0%BE%D0%BA-%D1%80%D0%B0%D0%B1%D0%BE%D1%82-%D0%BD%D0%B0%D1%80%D1%83%D0%B6%D0%BD%D1%8B%D0%B9-%D0%A8%D0%A0%D0%A3%D0%A1">Замена наружного ШРУС</a></div>
</div>

</div>

## Ходовая часть и рулевое

<div class="symptom-category">

<div class="symptom-item">
<strong>Стук в рулевой колонке</strong>
<div class="cause">Причины: износ рулевой рейки, затяжка упора</div>
<div class="action">→ <a href="../rulevoe/6-1.md#%D0%A0%D0%B5%D0%BC%D0%BE%D0%BD%D1%82-%D0%BD%D0%B0-%D0%BC%D0%B5%D1%81%D1%82%D0%B5">Регулировка рейки</a></div>
</div>

<div class="symptom-item">
<strong>Руль тугой / тяжело вращается</strong>
<div class="cause">Причины: низкий уровень жидкости ГУР, износ насоса ГУР, завоздушивание</div>
<div class="action">→ <a href="../rulevoe/6-2.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D0%B6%D0%B8%D0%B4%D0%BA%D0%BE%D1%81%D1%82%D0%B8-%D0%93%D0%A3%D0%A0">Замена жидкости ГУР</a></div>
</div>

<div class="symptom-item">
<strong>Биение руля при торможении</strong>
<div class="cause">Причины: деформация тормозных дисков, неравномерный износ</div>
<div class="action">→ <a href="../tormoza/7-1.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%82%D0%BE%D1%80%D0%BC%D0%BE%D0%B7%D0%BD%D1%8B%D1%85-%D0%B4%D0%B8%D1%81%D0%BA%D0%BE%D0%B2">Замена дисков</a></div>
</div>

<div class="symptom-item">
<strong>Увод в сторону при движении</strong>
<div class="cause">Причины: нарушен развал-схождение, неравномерное давление в шинах, износ сайлентблоков</div>
<div class="action">→ <a href="../hodovaya/5-3.md">Колёса и шины</a> · <a href="../hodovaya/5-1.md">Передняя подвеска</a></div>
</div>

<div class="symptom-item">
<strong>Стук сзади на неровностях</strong>
<div class="cause">Причины: износ амортизаторов, износ сайлентблоков балки</div>
<div class="action">→ <a href="../hodovaya/5-2.md#%D0%9F%D1%80%D0%B8%D0%B7%D0%BD%D0%B0%D0%BA%D0%B8-%D0%B8%D0%B7%D0%BD%D0%BE%D1%81%D0%B0-%D0%B0%D0%BC%D0%BE%D1%80%D1%82%D0%B8%D0%B7%D0%B0%D1%82%D0%BE%D1%80%D0%BE%D0%B2">Амортизаторы задние</a></div>
</div>

</div>

## Электрооборудование

<div class="symptom-category">

<div class="symptom-item">
<strong>АКБ разряжается за 1–2 дня</strong>
<div class="cause">Причины: утечка тока, неисправен генератор (диодный мост), старость АКБ</div>
<div class="action">→ <a href="../elektrika/8-1.md">АКБ</a> · <a href="../elektrika/8-2.md">Генератор</a></div>
</div>

<div class="symptom-item">
<strong>Горит лампа зарядки АКБ</strong>
<div class="cause">Причины: обрыв ремня генератора, износ щёток, неисправен регулятор напряжения</div>
<div class="action">→ <a href="../elektrika/8-2.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%80%D0%B5%D0%B3%D1%83%D0%BB%D1%8F%D1%82%D0%BE%D1%80%D0%B0-%D0%BD%D0%B0%D0%BF%D1%80%D1%8F%D0%B6%D0%B5%D0%BD%D0%B8%D1%8F">Замена регулятора</a></div>
</div>

<div class="symptom-item">
<strong>Не работают стеклоподъёмники</strong>
<div class="cause">Причины: сгорел предохранитель, неисправен моторчик, обрыв проводки в гофре двери</div>
<div class="action">→ <a href="../shemy/index.md">Схемы</a></div>
</div>

<div class="symptom-item">
<strong>Не работают дворники</strong>
<div class="cause">Причины: сгорел предохранитель, износ моторедуктора, закисла трапеция</div>
<div class="action">→ <a href="../statyi/dvorniki.md">Ремонт дворников</a></div>
</div>

<div class="symptom-item">
<strong>Не работают наружные световые приборы</strong>
<div class="cause">Причины: перегорела лампа, сгорел предохранитель, окисление контактов, неисправен подрулевой переключатель</div>
<div class="action">→ <a href="../elektrika/8-4.md">Освещение и сигнализация</a> · <a href="../shemy/index.md">Схемы</a></div>
</div>

</div>

## Тормозная система

<div class="symptom-category">

<div class="symptom-item">
<strong>Скрип тормозов</strong>
<div class="cause">Причины: износ колодок до индикатора, загрязнение, дешёвые колодки</div>
<div class="action">→ <a href="../tormoza/7-1.md">Передние тормоза</a> · <a href="../tormoza/7-2.md">Задние тормоза</a></div>
</div>

<div class="symptom-item">
<strong>Мягкая педаль тормоза / проваливается</strong>
<div class="cause">Причины: воздух в системе, утечка тормозной жидкости, износ главного цилиндра</div>
<div class="action">→ <a href="../tormoza/7-1.md#%D0%97%D0%B0%D0%BC%D0%B5%D0%BD%D0%B0-%D1%82%D0%BE%D1%80%D0%BC%D0%BE%D0%B7%D0%BD%D1%8B%D1%85-%D0%BA%D0%BE%D0%BB%D0%BE%D0%B4%D0%BE%D0%BA">Прокачка тормозов</a></div>
</div>

<div class="symptom-item">
<strong>Горит лампа ABS</strong>
<div class="cause">Причины: загрязнение датчика ABS, неисправен гидроблок, обрыв проводки</div>
<div class="action">→ <a href="../tormoza/7-3.md">ABS</a> · <a href="../dtc.md">Коды ABS</a></div>
</div>

</div>

---

> 🔧 **Не нашли свой симптом?** Используйте поиск сверху — фильтр работает по всему тексту страницы. Также смотрите <a href="../dtc.md">коды неисправностей OBD2</a>.
