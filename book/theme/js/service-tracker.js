/**
 * Интерактивный планировщик ТО для Renault Symbol
 * Рассчитывает предстоящие обслуживания, отслеживает выполненные
 */
(function() {
  'use strict';

  // ─── Регламент ТО для Renault Symbol ──────────────────────────
  // Вложенный массив: [пробег, единица, операции...]
  const serviceSchedule = [
    { km: 0, years: 0, label: '0 км — Подготовка к эксплуатации',
      items: ['Проверка уровней всех жидкостей', 'Регулировка давления в шинах', 'Проверка световых приборов'],
      critical: false },
    { km: 15000, years: 1, label: '15 000 км / 1 год — ТО-1',
      items: ['Моторное масло + масляный фильтр', 'Проверка ремня ГРМ', 'Проверка тормозных колодок', 'Проверка ШРУСов', 'Проверка выхлопной системы'],
      critical: true },
    { km: 30000, years: 2, label: '30 000 км / 2 года — ТО-2',
      items: ['Всё из ТО-1', 'Свечи зажигания (замена)', 'Салонный фильтр', 'Воздушный фильтр', 'Смазка замков и петель', 'Проверка рулевых наконечников'],
      critical: true },
    { km: 40000, years: 2, label: '40 000 км / 2 года',
      items: ['Тормозная жидкость DOT 4 (замена)', 'Проверка амортизаторов', 'Проверка сайлент-блоков'],
      critical: true },
    { km: 60000, years: 4, label: '60 000 км / 4 года — ТО-3',
      items: ['Всё из ТО-2', 'Ремень ГРМ + натяжной ролик + помпа', 'Антифриз (замена)', 'Масло в МКПП', 'Топливный фильтр (дизель)', 'Проверка ремня генератора', 'Проверка тормозных дисков'],
      critical: true },
    { km: 90000, years: 6, label: '90 000 км / 6 лет',
      items: ['Ремень ГРМ (дизель K9K)', 'Проверка турбины (дизель)'],
      critical: true },
    { km: 120000, years: 8, label: '120 000 км — ТО-4',
      items: ['Ремень ГРМ повторно + помпа', 'Топливный фильтр (бензин)', 'Передние амортизаторы', 'Сайлент-блоки рычагов', 'Рулевые наконечники', 'Проверка глушителя'],
      critical: true },
    { km: 150000, years: 10, label: '150 000+ км',
      items: ['Сцепление (комплект)', 'Задние амортизаторы', 'Ступичные подшипники'],
      critical: false },
  ];

  const STORAGE_KEY = 'renault_symbol_service_history';

  // ─── Работа с localStorage ─────────────────────────────────────
  function loadHistory() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch { return []; }
  }

  function saveHistory(history) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(history));
    } catch {}
  }

  // ─── Построение DOM ────────────────────────────────────────────
  function buildWidget(container) {
    // Стили
    const style = document.createElement('style');
    style.textContent = `
      .service-widget { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 1.5em 0; }
      .service-widget * { box-sizing: border-box; }
      .service-widget .sw-header { background: linear-gradient(135deg, #ff6b00, #e65100); color: #fff; padding: 1em 1.2em; border-radius: 8px 8px 0 0; }
      .service-widget .sw-header h3 { margin: 0 0 0.3em; font-size: 1.2em; color: #fff; }
      .service-widget .sw-header p { margin: 0; opacity: 0.9; font-size: 0.9em; }
      .service-widget .sw-body { padding: 1em; border: 1px solid #ddd; border-top: 0; border-radius: 0 0 8px 8px; }
      .service-widget .sw-row { display: flex; flex-wrap: wrap; gap: 1em; margin-bottom: 1em; }
      .service-widget .sw-field { flex: 1; min-width: 140px; }
      .service-widget .sw-field label { display: block; font-size: 0.85em; font-weight: 600; margin-bottom: 0.3em; color: #666; }
      .service-widget .sw-field input { width: 100%; padding: 0.6em 0.8em; border: 2px solid #ddd; border-radius: 6px; font-size: 1em; }
      .service-widget .sw-field input:focus { border-color: #ff6b00; outline: none; }
      .service-widget .sw-submit { padding: 0.7em 1.5em; background: #ff6b00; color: #fff; border: none; border-radius: 6px; font-size: 1em; cursor: pointer; font-weight: 600; }
      .service-widget .sw-submit:hover { background: #e65100; }
      .service-widget .sw-reset { padding: 0.7em 1em; background: #888; color: #fff; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85em; }
      .service-widget .sw-reset:hover { background: #666; }
      .service-widget .sw-upcoming { margin-top: 1em; }
      .service-widget .sw-upcoming h4 { margin: 0 0 0.5em; font-size: 1em; color: #333; }
      .service-widget .sw-card { border: 1px solid #ddd; border-radius: 6px; margin-bottom: 0.5em; overflow: hidden; }
      .service-widget .sw-card.overdue { border-color: #d32f2f; }
      .service-widget .sw-card.due-soon { border-color: #ff6b00; }
      .service-widget .sw-card.done { border-color: #4caf50; opacity: 0.85; }
      .service-widget .sw-card-header { display: flex; justify-content: space-between; align-items: center; padding: 0.6em 1em; cursor: pointer; }
      .service-widget .sw-card-header.overdue { background: #ffebee; }
      .service-widget .sw-card-header.due-soon { background: #fff3e0; }
      .service-widget .sw-card-header.done { background: #e8f5e9; }
      .service-widget .sw-card-km { font-weight: 700; color: #1565c0; }
      .service-widget .sw-card-label { flex: 1; margin-left: 0.8em; font-weight: 600; }
      .service-widget .sw-card-status { font-size: 0.8em; padding: 0.2em 0.5em; border-radius: 3px; }
      .service-widget .sw-card-status.pending { background: #e3f2fd; color: #1565c0; }
      .service-widget .sw-card-status.overdue { background: #d32f2f; color: #fff; }
      .service-widget .sw-card-status.done { background: #4caf50; color: #fff; }
      .service-widget .sw-card-body { padding: 0.5em 1em 1em; border-top: 1px solid #eee; display: none; }
      .service-widget .sw-card-body.open { display: block; }
      .service-widget .sw-card-body ul { margin: 0; padding-left: 1.5em; }
      .service-widget .sw-card-body li { margin: 0.2em 0; font-size: 0.9em; }
      .service-widget .sw-card-body .sw-mark-btn { margin-top: 0.5em; padding: 0.3em 0.8em; border: 1px solid #4caf50; background: #fff; color: #4caf50; border-radius: 4px; cursor: pointer; font-size: 0.85em; }
      .service-widget .sw-card-body .sw-mark-btn:hover { background: #4caf50; color: #fff; }
      .service-widget .sw-card-body .sw-unmark-btn { margin-top: 0.5em; padding: 0.3em 0.8em; border: 1px solid #888; background: #fff; color: #888; border-radius: 4px; cursor: pointer; font-size: 0.85em; margin-left: 0.5em; }
      .service-widget .sw-card-body .sw-unmark-btn:hover { background: #888; color: #fff; }
      .service-widget .sw-history { margin-top: 0.5em; font-size: 0.85em; color: #888; }
      .service-widget .sw-stat { display: flex; gap: 1em; flex-wrap: wrap; margin-bottom: 1em; }
      .service-widget .sw-stat-item { flex: 1; min-width: 100px; text-align: center; padding: 0.6em; border-radius: 6px; }
      .service-widget .sw-stat-item h5 { margin: 0; font-size: 0.8em; color: #666; }
      .service-widget .sw-stat-item .sw-stat-num { font-size: 1.3em; font-weight: 700; }
      .service-widget .sw-clear-history { color: #aaa; cursor: pointer; font-size: 0.8em; text-decoration: underline; }
      .service-widget .sw-clear-history:hover { color: #d32f2f; }
      @media (prefers-color-scheme: dark) {
        .service-widget .sw-body { border-color: #444; background: #1a1a1a; }
        .service-widget .sw-field input { background: #333; color: #eee; border-color: #555; }
        .service-widget .sw-field label { color: #aaa; }
        .service-widget .sw-upcoming h4 { color: #ccc; }
        .service-widget .sw-card { border-color: #444; }
        .service-widget .sw-card-header.overdue { background: #3a2020; }
        .service-widget .sw-card-header.due-soon { background: #3a3020; }
        .service-widget .sw-card-header.done { background: #1a3a1a; }
        .service-widget .sw-card-body { border-top-color: #333; background: #222; }
        .service-widget .sw-card-km { color: #64b5f6; }
        .service-widget .sw-stat-item { background: #2a2a2a; }
      }
    `;
    document.head.appendChild(style);

    const history = loadHistory();
    const doneKmSet = new Set(history.map(h => h.km));

    // ─── Контейнер ───────────────────────────────────────────────
    const wrapper = document.createElement('div');
    wrapper.className = 'service-widget';
    wrapper.innerHTML = `
      <div class="sw-header">
        <h3>📅 Планировщик обслуживания</h3>
        <p>Введите пробег — и увидите предстоящее ТО. Отмечайте выполненные работы.</p>
      </div>
      <div class="sw-body">
        <div class="sw-row">
          <div class="sw-field">
            <label>🔢 Текущий пробег (км)</label>
            <input type="number" id="sw-mileage" value="0" min="0" step="1000">
          </div>
          <div class="sw-field">
            <label>📆 Последнее ТО (км)</label>
            <input type="number" id="sw-last-service" value="0" min="0" step="1000">
          </div>
          <div style="display:flex;align-items:flex-end;gap:0.5em">
            <button class="sw-submit" id="sw-calc">Рассчитать</button>
            <button class="sw-reset" id="sw-reset">↺</button>
          </div>
        </div>
        <div class="sw-stat" id="sw-stat"></div>
        <div class="sw-upcoming" id="sw-upcoming"></div>
      </div>
    `;
    container.appendChild(wrapper);

    const mileageInput = document.getElementById('sw-mileage');
    const lastServiceInput = document.getElementById('sw-last-service');
    const calcBtn = document.getElementById('sw-calc');
    const resetBtn = document.getElementById('sw-reset');
    const statDiv = document.getElementById('sw-stat');
    const upcomingDiv = document.getElementById('sw-upcoming');

    // ─── Состояние ──────────────────────────────────────────────
    let currentMileage = 0;
    let lastServiceKm = 0;

    // ─── Сохранение/загрузка состояния ──────────────────────────
    function loadState() {
      try {
        const s = localStorage.getItem('renault_service_state');
        if (s) {
          const state = JSON.parse(s);
          currentMileage = state.mileage || 0;
          lastServiceKm = state.lastService || 0;
          mileageInput.value = currentMileage;
          lastServiceInput.value = lastServiceKm;
        }
      } catch {}
    }
    function saveState() {
      try {
        localStorage.setItem('renault_service_state', JSON.stringify({
          mileage: currentMileage,
          lastService: lastServiceKm,
        }));
      } catch {}
    }

    // ─── Расчёт предстоящих ТО ──────────────────────────────────
    function calculate() {
      currentMileage = parseInt(mileageInput.value) || 0;
      lastServiceKm = parseInt(lastServiceInput.value) || 0;
      saveState();

      // Статистика
      const totalDone = history.length;
      const pendingDue = serviceSchedule.filter(s => {
        if (doneKmSet.has(s.km)) return false;
        const nextKm = Math.max(s.km, lastServiceKm + s.km);
        return nextKm <= currentMileage + 15000;
      });
      const overdue = serviceSchedule.filter(s => {
        if (doneKmSet.has(s.km)) return false;
        const nextKm = Math.max(s.km, lastServiceKm + s.km);
        return nextKm <= currentMileage;
      });

      statDiv.innerHTML = `
        <div class="sw-stat-item" style="background:#e3f2fd"><h5>Пробег</h5><div class="sw-stat-num">${currentMileage.toLocaleString()}</div></div>
        <div class="sw-stat-item" style="background:#ffebee"><h5>Просрочено</h5><div class="sw-stat-num" style="color:${overdue.length ? '#d32f2f' : '#4caf50'}">${overdue.length}</div></div>
        <div class="sw-stat-item" style="background:#fff3e0"><h5>Предстоит</h5><div class="sw-stat-num" style="color:#ff6b00">${pendingDue.length}</div></div>
        <div class="sw-stat-item" style="background:#e8f5e9"><h5>Выполнено</h5><div class="sw-stat-num" style="color:#4caf50">${totalDone}</div></div>
      `;

      // Предстоящие обслуживания
      let html = '<h4>График обслуживания</h4>';
      for (const s of serviceSchedule) {
        const nextKm = lastServiceKm > 0 ? lastServiceKm + s.km : s.km;
        const isDone = doneKmSet.has(s.km);
        let statusClass = 'pending';
        let statusText = (nextKm - currentMileage > 15000) ? 'Ок' : 'Скоро';
        if (isDone) { statusClass = 'done'; statusText = '✅ Выполнено'; }
        else if (nextKm <= currentMileage) { statusClass = 'overdue'; statusText = '❗ Просрочено'; }
        else if (nextKm - currentMileage <= 5000) { statusClass = 'due-soon'; statusText = '⚠️ Скоро'; }

        const dueInfo = isDone ? '' : ` (через ${Math.max(0, nextKm - currentMileage).toLocaleString()} км)`;

        html += `<div class="sw-card ${statusClass}">
          <div class="sw-card-header ${statusClass}" data-target="sw-body-${s.km}">
            <span class="sw-card-km">${s.km.toLocaleString()} км</span>
            <span class="sw-card-label">${s.label}${dueInfo}</span>
            <span class="sw-card-status ${statusClass}">${statusText}</span>
          </div>
          <div class="sw-card-body" id="sw-body-${s.km}">
            <ul>${s.items.map(i => `<li>${i}</li>`).join('')}</ul>
            <div style="margin-top:0.5em">
              ${isDone
                ? `<button class="sw-unmark-btn" data-km="${s.km}">Отменить выполнение</button>`
                : `<button class="sw-mark-btn" data-km="${s.km}">✅ Отметить выполненным</button>`
              }
              <span class="sw-history" style="margin-left:1em">${isDone ? 'Выполнено: ' + history.find(h => h.km === s.km)?.date || '' : ''}</span>
            </div>
          </div>
        </div>`;
      }

      // Кнопка очистки истории
      if (history.length > 0) {
        html += '<p><span class="sw-clear-history" id="sw-clear-all">Очистить историю обслуживания</span></p>';
      }

      upcomingDiv.innerHTML = html;

      // Клик по заголовку — раскрытие
      document.querySelectorAll('.sw-card-header').forEach(el => {
        el.addEventListener('click', function(e) {
          e.stopPropagation();
          const target = document.getElementById(this.dataset.target);
          if (target) target.classList.toggle('open');
        });
      });

      // Клик по кнопке отметки
      document.querySelectorAll('.sw-mark-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
          e.stopPropagation();
          const km = parseInt(this.dataset.km);
          if (!doneKmSet.has(km)) {
            history.push({ km, date: new Date().toLocaleDateString('ru-RU') });
            doneKmSet.add(km);
            saveHistory(history);
            calculate(); // перерендер
          }
        });
      });

      document.querySelectorAll('.sw-unmark-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
          e.stopPropagation();
          const km = parseInt(this.dataset.km);
          const idx = history.findIndex(h => h.km === km);
          if (idx !== -1) {
            history.splice(idx, 1);
            doneKmSet.delete(km);
            saveHistory(history);
            calculate();
          }
        });
      });

      const clearAll = document.getElementById('sw-clear-all');
      if (clearAll) {
        clearAll.addEventListener('click', function() {
          if (confirm('Очистить всю историю обслуживания?')) {
            history.length = 0;
            doneKmSet.clear();
            saveHistory(history);
            calculate();
          }
        });
      }
    }

    // ─── Обработчики ──────────────────────────────────────────────
    calcBtn.addEventListener('click', calculate);
    resetBtn.addEventListener('click', function() {
      mileageInput.value = '0';
      lastServiceInput.value = '0';
      calculate();
    });
    mileageInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') calculate(); });
    lastServiceInput.addEventListener('keydown', function(e) { if (e.key === 'Enter') calculate(); });

    // ─── Инициализация ────────────────────────────────────────────
    loadState();
    calculate();
  }

  // ─── Запуск ───────────────────────────────────────────────────
  function init() {
    let container = document.getElementById('service-tracker');
    if (!container) {
      const content = document.querySelector('.content, article, main');
      if (content) {
        container = document.createElement('div');
        container.id = 'service-tracker';
        const target = content.querySelector('#полная-таблица-то, table');
        if (target) {
          target.parentNode.insertBefore(container, target);
        } else {
          const h2 = content.querySelector('h2');
          if (h2) h2.parentNode.insertBefore(container, h2);
          else content.insertBefore(container, content.firstChild);
        }
      } else {
        container = document.createElement('div');
        container.id = 'service-tracker';
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
