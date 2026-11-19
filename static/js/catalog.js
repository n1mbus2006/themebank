/* catalog.js — живой поиск в шапке (занятие 9, динамический элемент).
 *
 * Набранный запрос уходит fetch-запросом к собственному JSON-представлению
 * (FR-23), под полем появляется список подходящих тем; страница при этом
 * не перезагружается. Enter по-прежнему отправляет форму в каталог.
 */
(function () {
  'use strict';

  var form = document.querySelector('.header-search');
  if (!form) {
    return;
  }
  var input = form.querySelector('input[type="search"]');
  var list = form.querySelector('.search-suggest');
  var url = form.getAttribute('data-suggest-url');
  var timer = null;

  function hideList() {
    list.hidden = true;
    list.innerHTML = '';
  }

  function renderItems(items) {
    if (!items.length) {
      list.innerHTML = '<li class="search-suggest__empty">По вашему запросу ничего не найдено</li>';
      list.hidden = false;
      return;
    }
    list.innerHTML = items.map(function (item) {
      var badge = item.is_free
        ? '<span class="badge badge--success">Свободна</span>'
        : '<span class="badge badge--neutral">Закреплена</span>';
      // Адрес темы приходит из JSON: сервер строит его reverse() по имени
      // маршрута, в JS адрес каталога руками не собирается.
      return '<li><a href="' + item.url + '">' +
             '<span class="search-suggest__title">' + item.title + '</span>' +
             badge + '</a></li>';
    }).join('');
    list.hidden = false;
  }

  input.addEventListener('input', function () {
    var query = input.value.trim();
    window.clearTimeout(timer);
    if (query.length < 2) {
      hideList();
      return;
    }
    // Задержка 300 мс: запрос не уходит на каждый нажатый символ.
    timer = window.setTimeout(function () {
      list.hidden = false;
      list.innerHTML = '<li class="search-suggest__empty">Ищу…</li>';
      fetch(url + '?q=' + encodeURIComponent(query), {
        headers: { 'Accept': 'application/json' },
      })
        .then(function (response) {
          if (!response.ok) {
            throw new Error('Сервер вернул ' + response.status);
          }
          return response.json();
        })
        .then(function (data) {
          renderItems(data.items);
        })
        .catch(function () {
          // Ошибка сети не должна ломать страницу: просто убираем подсказки,
          // пользователь может отправить запрос в каталог как обычно.
          hideList();
        });
    }, 300);
  });

  // Прячем подсказки при клике вне формы и по Escape.
  document.addEventListener('click', function (event) {
    if (!form.contains(event.target)) {
      hideList();
    }
  });
  input.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
      hideList();
    }
  });
})();
