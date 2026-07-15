/**
 * Кастомный поиск для кириллицы.
 *
 * mdBook использует elasticlunr с English pipeline — кириллица
 * вырезается на этапе индексации. Этот скрипт перехватывает поиск
 * и для запросов, содержащих кириллицу, выполняет substring-поиск
 * по предварительно извлечённому тексту документов.
 *
 * Интеграция: подключается как additional-js после searcher.js.
 */

(function () {
  'use strict';

  // Состояние
  var searchData = null;
  var searchDataUrl =
    (window.path_to_root || '') + 'data/search-text.json';

  // Загружаем текстовый индекс при первой необходимости
  function loadSearchData(callback) {
    if (searchData) {
      callback(searchData);
      return;
    }
    var xhr = new XMLHttpRequest();
    xhr.open('GET', searchDataUrl, true);
    xhr.onload = function () {
      if (xhr.status === 200) {
        try {
          searchData = JSON.parse(xhr.responseText);
          callback(searchData);
        } catch (e) {
          console.error('[ru-search] JSON parse error:', e);
          callback(null);
        }
      } else {
        console.error('[ru-search] HTTP', xhr.status, searchDataUrl);
        callback(null);
      }
    };
    xhr.onerror = function () {
      console.error('[ru-search] Network error loading', searchDataUrl);
      callback(null);
    };
    xhr.send();
  }

  // Проверка: содержит ли строка кириллицу
  function hasCyrillic(text) {
    return /[а-яё]/i.test(text);
  }

  // Простой substring-поиск
  function searchRussian(query, data) {
    var terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (terms.length === 0) return [];

    var results = [];
    for (var i = 0; i < data.length; i++) {
      var doc = data[i];
      var haystack = (doc.title + ' ' + doc.breadcrumbs + ' ' + doc.body).toLowerCase();
      var matchAll = true;
      for (var t = 0; t < terms.length; t++) {
        if (haystack.indexOf(terms[t]) === -1) {
          matchAll = false;
          break;
        }
      }
      if (matchAll) {
        results.push({
          ref: doc.url,
          doc: doc,
          score: 1.0,
        });
      }
    }
    return results;
  }

  // Перехватываем doSearch в window.search
  var origDoSearch = null;

  function interceptSearch() {
    if (typeof window.search !== 'object') {
      // searcher.js ещё не загрузился — ждём
      setTimeout(interceptSearch, 200);
      return;
    }

    // Сохраняем оригинальный doSearch (если есть)
    // В searcher.js doSearch — в замыкании, не на window.search.
    // Поэтому перехватываем через MutationObserver на результатах.
    // Альтернатива: вешаемся на keyup в searchbar.
    var searchbar = document.getElementById('mdbook-searchbar');
    if (!searchbar) {
      setTimeout(interceptSearch, 200);
      return;
    }

    console.log('[ru-search] active — кириллические запросы будут обработаны');
  }

  // Наблюдатель за результатами поиска
  function watchSearchResults() {
    var resultsContainer = document.getElementById('mdbook-searchresults');
    if (!resultsContainer) {
      setTimeout(watchSearchResults, 300);
      return;
    }

    var observer = new MutationObserver(function () {
      // Когда searcher.js обновил результаты — проверяем
      var searchbar = document.getElementById('mdbook-searchbar');
      var header = document.getElementById('mdbook-searchresults-header');
      if (!searchbar || !header) return;

      var query = searchbar.value.trim();
      if (!query || !hasCyrillic(query)) return;

      // Текущее количество результатов
      var currentCount = resultsContainer.children.length;

      // Если результатов нет или заголовок говорит "No results"
      if (currentCount === 0 || header.innerText.indexOf('No search results') >= 0) {
        // Запускаем наш поиск
        loadSearchData(function (data) {
          if (!data) return;
          var results = searchRussian(query, data);

          // Обновляем UI
          var resultCount = Math.min(results.length, 30);
          header.innerText = resultCount + ' search results for \'' + query + '\':';

          // Очищаем и заполняем
          while (resultsContainer.firstChild) {
            resultsContainer.removeChild(resultsContainer.firstChild);
          }

          for (var i = 0; i < resultCount; i++) {
            var r = results[i];
            var li = document.createElement('li');
            var teaser = r.doc.body.substring(0, 200).replace(/\s+/g, ' ');
            li.innerHTML =
              '<a href="' + (window.path_to_root || '') + r.doc.url + '">'
              + (r.doc.breadcrumbs || r.doc.title) + '</a>'
              + '<span class="teaser">' + teaser + '</span>';
            resultsContainer.appendChild(li);
          }
        });
      }
    });

    observer.observe(resultsContainer, { childList: true, subtree: true });
  }

  // Запускаем после загрузки DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      interceptSearch();
      watchSearchResults();
    });
  } else {
    interceptSearch();
    watchSearchResults();
  }
})();
