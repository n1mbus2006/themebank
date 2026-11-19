Сводка проверок занятий 7-9 (проект «Банк тем», вариант 25, Ярочкин Максим ИСдо-46)
Дата проверки: 18.11.2026

1) W3C HTML (validator.w3.org/nu/, POST HTML страниц):
   catalog, topic_card, login, register, about, my_apps, supervisor, dashboard, vedomost
   -> ошибок 0, предупреждений 0 на всех 9 страницах
   (подробности в w3c_html_report.json)

2) W3C CSS (jigsaw.w3.org/css-validator, файл main.css):
   -> Valid CSS, ошибок 0, предупреждений 0 (css3svg profile)
   (подробности в w3c_css_report.html)

3) Lighthouse (инструмент среды разработки, вкладка):
   /topics/            -> Accessibility 100, Best Practices 100, SEO 100
   /accounts/login/    -> Accessibility 100, Best Practices 100, SEO 100
   /accounts/register/ -> Accessibility 100, Best Practices 100, SEO 100
   /about/             -> Accessibility 100, Best Practices 100, SEO 100
   Все оценки не ниже 85 (требование NFR занятия 9).
   (подробности в lighthouse_catalog.json / .html)

4) Консоль браузера: ошибок и предупреждений JS нет (проверено на каталоге,
   карточке темы, кабинете студента, сводке; инструмент console вкладки).
