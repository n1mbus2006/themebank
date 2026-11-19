/* topic.js — обновление карточки темы без перезагрузки (занятие 9, FR-23).
 *
 * Пока студент заполняет заявку, кто-то другой может закрепить тему.
 * Раз в 30 секунд страница тихо спрашивает свой JSON-адрес
 * (topics/<id>/status.json/) и перерисовывает бейдж статуса и строку
 * «Закреплено X из Y». Если тему забрали — кнопка отключается и
 * появляется предупреждение; отправлять форму уже бессмысленно, а
 * серверная проверка всё равно отклонит заявку.
 */
(function () {
  'use strict';

  var root = document.querySelector('[data-topic-status]');
  if (!root) {
    return;
  }
  var url = root.getAttribute('data-topic-url');
  var badge = root.querySelector('[data-badge]');
  var loadLine = root.querySelector('.js-topic-load');
  var hintLine = root.querySelector('.supervisor-card__hint');
  var applyForm = root.querySelector('.apply-block form');
  var applyButton = applyForm ? applyForm.querySelector('button[type="submit"]') : null;
  var takenAlert = root.querySelector('[data-taken-alert]');
  var timer = null;

  function hideAlert() {
    if (takenAlert && !takenAlert.hidden) {
      takenAlert.hidden = true;
    }
  }

  /* Строка «Закреплено 3 из 5» на плитке руководителя. */
  function loadText(data) {
    if (data.status === 'taken') {
      return 'Тема закреплена';
    }
    if (!data.max_students) {
      return 'Лимит не задан';
    }
    return 'Закреплено ' + data.occupied + ' из ' + data.max_students;
  }

  function applyData(data) {
    // Бейдж статуса: меняется текст и класс цвета (свободна — зелёный).
    if (badge) {
      var wasTaken = badge.getAttribute('data-status') === 'taken';
      badge.textContent = data.status_label;
      badge.setAttribute('data-status', data.status);
      badge.classList.toggle('badge--success', data.is_free);
      badge.classList.toggle('badge--neutral', !data.is_free);
      if (!wasTaken && data.status === 'taken') {
        if (takenAlert) {
          takenAlert.hidden = false;
        }
        if (applyButton) {
          applyButton.disabled = true;
          applyButton.setAttribute('aria-disabled', 'true');
        }
      }
    }

    if (loadLine) {
      loadLine.textContent = loadText(data);
    }

    // Подсказка «…остаток 2»: меняем только число, год оставляем как был.
    if (hintLine && data.max_students) {
      var hint = hintLine.textContent;
      if (/остаток \d+/.test(hint)) {
        hintLine.textContent = hint.replace(/остаток \d+/, 'остаток ' + data.remaining);
      } else if (hint.trim() === '') {
        hintLine.textContent = 'лимит · остаток ' + data.remaining;
      }
    }
  }

  function ask() {
    fetch(url, { headers: { 'Accept': 'application/json' } })
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Сервер вернул ' + response.status);
        }
        return response.json();
      })
      .then(applyData)
      .catch(function () {
        // Сеть пропала или сервер перезапущен — просто ждём следующей
        // попытки, сообщать об ошибке в консоль не нужно (занятие 9).
      });
  }

  function schedule() {
    timer = window.setInterval(function () {
      // В фоне опрос не нужен: вкладка всё равно не видна.
      if (!document.hidden) {
        ask();
      }
    }, 30000);
  }

  // Вернулись на вкладку — сразу узнаём судьбу темы, не дожидаясь таймера.
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) {
      ask();
    }
  });

  // Закрыть предупреждение можно крестиком, как обычное уведомление.
  if (takenAlert) {
    var close = takenAlert.querySelector('.alert__close');
    if (close) {
      close.addEventListener('click', hideAlert);
    }
  }

  ask();
  schedule();
})();
