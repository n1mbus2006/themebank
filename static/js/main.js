/* main.js — общая клиентская логика (занятие 9).
 *
 * Здесь живёт то, что нужно сразу нескольким страницам:
 * бургер-меню мобильной шапки, меню пользователя, закрытие уведомлений,
 * раскрытие формы отклонения у руководителя, заливка полос нагрузки,
 * автосохранение сортировки и клиентская валидация форм.
 * Серверная валидация Django при этом сохраняется: JS только помогает
 * заметить ошибку до отправки.
 */
(function () {
  'use strict';

  /* ---------- Бургер-меню мобильной шапки (занятие 8) ---------- */
  var burger = document.querySelector('[data-burger]');
  var mobileMenu = document.getElementById('mobile-menu');
  if (burger && mobileMenu) {
    burger.addEventListener('click', function () {
      var open = mobileMenu.hidden;
      mobileMenu.hidden = !open;
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    // Закрываем меню при переходе по ссылке внутри него.
    mobileMenu.addEventListener('click', function (event) {
      if (event.target.closest('a, button')) {
        mobileMenu.hidden = true;
        burger.setAttribute('aria-expanded', 'false');
      }
    });
  }

  /* ---------- Меню пользователя в шапке (аватар) ---------- */
  var userChip = document.querySelector('[data-user-menu]');
  var userMenu = document.querySelector('.user-menu');
  if (userChip && userMenu) {
    userChip.addEventListener('click', function (event) {
      event.stopPropagation();
      userMenu.hidden = !userMenu.hidden;
    });
    document.addEventListener('click', function (event) {
      if (!userMenu.hidden && !userMenu.contains(event.target)) {
        userMenu.hidden = true;
      }
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape') {
        userMenu.hidden = true;
      }
    });
  }

  /* ---------- Закрытие уведомлений (messages framework) ---------- */
  document.addEventListener('click', function (event) {
    var close = event.target.closest('.alert__close');
    if (close) {
      var alert = close.closest('.alert');
      if (alert) {
        alert.remove();
      }
    }
  });

  /* ---------- Раскрытие формы отклонения у руководителя ---------- */
  document.addEventListener('click', function (event) {
    var toggle = event.target.closest('[data-reject-toggle]');
    if (toggle) {
      var form = document.getElementById(toggle.getAttribute('data-reject-toggle'));
      if (form) {
        form.hidden = false;
        var reason = form.querySelector('textarea');
        if (reason) {
          reason.focus();
        }
      }
      return;
    }
    var cancel = event.target.closest('[data-reject-cancel]');
    if (cancel) {
      var rejectForm = cancel.closest('.reject-form');
      if (rejectForm) {
        rejectForm.hidden = true;
      }
    }
  });

  /* ---------- Заливка полос нагрузки (плитка руководителя и график) ----------
   * Ширина/высота считаются в JS из data-атрибутов: никаких стилей в
   * атрибуте style, как требует задание занятия 8. У плитки руководителя
   * полоса горизонтальная, у графика в сводке столбцы растут вверх,
   * поэтому для них меняется высота.
   */
  document.querySelectorAll('[data-bar-fill]').forEach(function (bar) {
    var occupied = parseFloat(bar.getAttribute('data-occupied')) || 0;
    var total = parseFloat(bar.getAttribute('data-total')) || 0;
    var percent = total > 0 ? Math.min(100, Math.round(occupied * 100 / total)) : 0;
    if (bar.closest('.chart__bar')) {
      bar.style.height = percent + '%';
    } else {
      bar.style.width = percent + '%';
    }
  });

  /* ---------- Сайдбар фильтров: на desktop он раскрыт всегда ---------- */
  document.querySelectorAll('.filters__toggle').forEach(function (details) {
    if (window.matchMedia('(min-width: 768px)').matches) {
      details.open = true;
    }
  });

  /* ---------- Сортировка каталога отправляется сразу ---------- */
  document.querySelectorAll('[data-autosubmit]').forEach(function (form) {
    var select = form.querySelector('select');
    if (select) {
      select.addEventListener('change', function () {
        form.submit();
      });
    }
  });

  /* ---------- Кнопка «Печать» на ведомости ---------- */
  document.querySelectorAll('[data-print]').forEach(function (button) {
    button.addEventListener('click', function () {
      window.print();
    });
  });

  /* ================= Клиентская валидация форм (занятие 9) =================
   * Правила задаются атрибутом data-validate у поля:
   *   required            — поле не пустое;
   *   email               — похож на адрес почты;
   *   minlen:N / maxlen:N — минимальная и максимальная длина;
   *   match:имя           — совпадает с другим полем (повтор пароля);
   *   int, range:1-30     — целое число в диапазоне (лимит руководителя);
   *   filetype:pdf,jpg    — расширение файла из списка (приказ);
   *   filesize:5          — размер файла до 5 МБ (NFR-09);
   *   required-if-student / required-if-supervisor — обязательное только
   *   при выбранной роли на форме регистрации.
   * Серверные проверки это не отменяет, они сработают при любом обходе JS.
   */
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

  function fieldErrorText(rule) {
    switch (rule) {
      case 'required':
        return 'Заполните это поле.';
      case 'required-if-student':
        return 'Укажите группу и номер зачётной книжки.';
      case 'required-if-supervisor':
        return 'Укажите должность и подразделение.';
      case 'email':
        return 'Похоже, в адресе почты опечатка — проверьте формат.';
      case 'match':
        return 'Пароли не совпадают.';
      case 'int':
        return 'Укажите целое число.';
      case 'filetype':
        return 'Приказ можно прикрепить только в PDF, JPG или PNG.';
      case 'filesize':
        return 'Файл больше 5 МБ — уменьшите его и загрузите заново.';
    }
    if (rule.indexOf('minlen:') === 0) {
      return 'Слишком коротко — минимум ' + rule.slice(7) + ' симв.';
    }
    if (rule.indexOf('maxlen:') === 0) {
      return 'Слишком длинно — максимум ' + rule.slice(7) + ' симв.';
    }
    if (rule.indexOf('range:') === 0) {
      return 'Значение вне диапазона ' + rule.slice(6).replace('-', '–') + '.';
    }
    return 'Значение не прошло проверку.';
  }

  function validateField(field) {
    var rules = (field.getAttribute('data-validate') || '').split(',').filter(Boolean);
    if (!rules.length) {
      return true;
    }
    var value = field.value.trim();
    var roleInput = field.closest('form').querySelector('input[name="role"]:checked');
    var roleValue = roleInput ? roleInput.value : 'student';

    // Правила проверяются по порядку; первое нарушение даёт ошибку.
    for (var i = 0; i < rules.length; i++) {
      var rule = rules[i];

      // Обязательность полей регистрации зависит от выбранной роли.
      if (rule === 'required-if-student') {
        if (roleValue !== 'student') {
          continue;
        }
        rule = 'required';
      } else if (rule === 'required-if-supervisor') {
        if (roleValue !== 'supervisor') {
          continue;
        }
        rule = 'required';
      }

      var broken = null;
      if (rule === 'required') {
        if (value === '') {
          broken = rule;
        }
      } else if (value === '') {
        // Остальные правила пустое поле не беспокоят.
        continue;
      } else if (rule === 'email') {
        if (!EMAIL_RE.test(value)) {
          broken = rule;
        }
      } else if (rule.indexOf('minlen:') === 0) {
        if (value.length < parseInt(rule.slice(7), 10)) {
          broken = rule;
        }
      } else if (rule.indexOf('maxlen:') === 0) {
        if (value.length > parseInt(rule.slice(7), 10)) {
          broken = rule;
        }
      } else if (rule.indexOf('match:') === 0) {
        var partner = document.getElementById('id_' + rule.slice(6)) ||
                      document.querySelector('[name="' + rule.slice(6) + '"]');
        if (!partner || partner.value !== field.value) {
          broken = 'match';
        }
      } else if (rule === 'int') {
        if (!/^-?\d+$/.test(value)) {
          broken = rule;
        }
      } else if (rule.indexOf('range:') === 0) {
        var bounds = rule.slice(6).split('-');
        var number = parseInt(value, 10);
        if (number < parseInt(bounds[0], 10) || number > parseInt(bounds[1], 10)) {
          broken = rule;
        }
      } else if (rule.indexOf('filetype:') === 0) {
        var allowed = rule.slice(9).split(',');
        var name = (field.files[0] && field.files[0].name || '').toLowerCase();
        var dot = name.lastIndexOf('.');
        var ext = dot === -1 ? '' : name.slice(dot + 1);
        if (ext === '' || allowed.indexOf(ext) === -1) {
          broken = rule;
        }
      } else if (rule.indexOf('filesize:') === 0) {
        var maxMb = parseInt(rule.slice(9), 10) || 5;
        var size = field.files[0] ? field.files[0].size : 0;
        if (size > maxMb * 1024 * 1024) {
          broken = rule;
        }
      }

      if (broken) {
        showFieldError(field, fieldErrorText(rules[i]));
        return false;
      }
    }

    clearFieldError(field);
    return true;
  }

  function showFieldError(field, text) {
    clearFieldError(field);
    field.classList.add('field__input--error');
    field.setAttribute('aria-invalid', 'true');
    var message = document.createElement('p');
    message.className = 'field__error field__hint-js';
    message.textContent = text;
    field.parentElement.appendChild(message);
  }

  function clearFieldError(field) {
    field.classList.remove('field__input--error');
    field.setAttribute('aria-invalid', 'false');
    var oldMessage = field.parentElement.querySelector('.field__hint-js');
    if (oldMessage) {
      oldMessage.remove();
    }
  }

  document.querySelectorAll('[data-validate-form]').forEach(function (form) {
    var fields = form.querySelectorAll('[data-validate]');

    // Проверяем поле, когда пользователь его покинул — ошибки видны сразу.
    fields.forEach(function (field) {
      field.addEventListener('blur', function () {
        validateField(field);
      });
    });

    // Роль регистрации переключается — показываем её поля и
    // пересчитываем правила обязательности.
    var roleInputs = form.querySelectorAll('input[name="role"]');
    var roleBlocks = form.querySelectorAll('[data-fields-for]');
    roleInputs.forEach(function (input) {
      input.addEventListener('change', function () {
        roleBlocks.forEach(function (block) {
          block.hidden = block.getAttribute('data-fields-for') !== input.value;
        });
        fields.forEach(function (field) {
          var rules = field.getAttribute('data-validate') || '';
          if (rules.indexOf('required-if') === 0) {
            validateField(field);
          }
        });
      });
    });

    form.addEventListener('submit', function (event) {
      var firstInvalid = null;
      fields.forEach(function (field) {
        if (!validateField(field) && !firstInvalid) {
          firstInvalid = field;
        }
      });
      if (firstInvalid) {
        event.preventDefault();
        firstInvalid.focus();
      }
    });
  });
})();
