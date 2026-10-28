"""Include recorded UI observations without certifying unfinished test cases."""
import json

from document_common import PROTOCOLS, page, paragraph, table
from document_screenshots import add_cropped_screenshot


RUN_ID = 'RUN-20261024-01'


def add_recorded_results(document):
    """Append the saved partial run and distinguish it from the test program."""
    source = PROTOCOLS / 'Ручные' / RUN_ID / 'results.json'
    if not source.exists():
        return
    data = json.loads(source.read_text())
    for item in document.paragraphs:
        if 'Ручная программа подготовлена отдельно и пока не выполнена.' in item.text:
            item.text = item.text.replace(
                'Ручная программа подготовлена отдельно и пока не выполнена.',
                '24 октября начат прогон через интерфейс. Подтверждены запуск, '
                'исходные остатки и создание резерва под Администратором. '
                'Полные ручные сценарии не завершены; фактические результаты '
                'и снимки приведены в приложении В.',
            )
        elif 'подготовлены к выполнению и не имеют фактических результатов.' in item.text:
            item.text = item.text.replace(
                'подготовлены к выполнению и не имеют фактических результатов.',
                'выполнены частично. SM01 успешен; наблюдения по SM02, SM04 '
                'и SM07 приведены в приложении В. Остальные шаги не подтверждены.',
            )
        elif 'Статус всего smoke-теста: Не выполнен.' in item.text:
            item.text = (
                'Статус smoke-теста на 24.10.2026: Не завершён. SM01 успешен. '
                'SM02 и SM04 проверены частично; операции SM07 выполнены '
                'под Администратором, поэтому проверка роли Продажа остаётся открытой. '
                'Фактические результаты отделены от программы ниже и приведены в приложении В.'
            )
        elif 'Сейчас этот путь является правилом хранения' in item.text:
            item.text = (
                'Фактические материалы первого прогона находятся в '
                'Протоколы/Ручные/RUN-20261024-01: results.json, журнал '
                'ui-actions.jsonl и исходные PNG. Приложение В содержит '
                'заполненные результаты; таблицы выше оставлены для последующих прогонов.'
            )
        elif 'имеют статус Не выполнен.' in item.text:
            item.text = (
                'По сохранённым протоколам автоматическая регрессия версии 1.2.0 '
                'содержит 83 успешные проверки. Ручной прогон от 24.10.2026 '
                'не завершён: успешен SM01, отдельные действия SM02, SM04 и SM07 '
                'подтверждены снимками. Ни один подробный пользовательский '
                'сценарий полностью не завершён. Допуск по критериям ручной приёмки '
                'пока не подтверждён.'
            )
    for grid in document.tables:
        for row in grid.rows:
            if row.cells[0].text == 'Smoke-тест':
                row.cells[-1].text = 'Начат, не завершён'
            elif row.cells[0].text == 'Ручные сценарии':
                row.cells[-1].text = '0 из 12 завершены'

    current_case = None
    partial = {'MS02', 'MS05', 'MA01', 'MA03'}
    for item in document.paragraphs:
        if item.style.name == 'Heading 2' and item.text[:4] in partial:
            current_case = item.text[:4]
        elif item.style.name in {'Heading 1', 'Heading 2'}:
            current_case = None
        elif current_case and item.text.startswith('Роль: '):
            item.text = item.text.replace('Статус: Не выполнен.', 'Статус: Частично, см. приложение В.')
        elif current_case and item.text.startswith('Фактический результат:'):
            item.text = (
                'Фактический результат: отдельные действия выполнены под '
                'Администратором в прогоне RUN-20261024-01. '
                'Полный сценарий, его роль и возврат к S0 не подтверждены.'
            )

    page(document, 'Приложение В Фактические результаты ручного прогона')
    paragraph(document, 'Прогон RUN-20261024-01 от 24 октября 2026 года не завершён. '
              'В этом приложении зафиксированы только наблюдавшиеся результаты. '
              '83 исторические автоматические проверки учитываются отдельно.')
    table(document, ['Параметр', 'Значение'], [
        ('Конфигурация и платформа', data['configuration'] + '; ' + data['platform']),
        ('Среда и окно', data['os'] + '; ' + data['window']),
        ('Исполнитель и пользователь', data['executor'] + '; роль ' + data['role']),
        ('Тестовая база', data['base']),
        ('Источник поставки', data['source_dt']),
        ('Дата отчёта и отборы', data['report_date'] + '; без отбора организации и склада'),
    ], [2.0, 4.65])
    paragraph(document, 'Проверки выполнялись щелчками и вводом через AppleScript '
              'и события мыши macOS. Обработчики 1С программно не вызывались. '
              'Восстановление DT выполнено штатной командной строкой платформы '
              'и не засчитано как ручное прохождение диалога Конфигуратора.')
    paragraph(document, data['notes'])
    paragraph(document, data['end_state'], bold=True)
    paragraph(document, 'Далее требуется проверить продажу сверх свободного '
              'остатка, отмену и продажу брони, восстановить S0, затем выполнить '
              'проверки под рабочими ролями и остальные сценарии. '
              'Трудности внешнего управления окном не зарегистрированы как дефекты конфигурации.')

    for number, observations in enumerate([data['rows'][:3], data['rows'][3:]], 1):
        page(document, f'Приложение В{number} Журнал наблюдений')
        for observation in observations:
            document.add_heading(observation['id'] + ' ' + observation['status'], level=2)
            paragraph(document, observation['actual'])
            paragraph(document, 'Доказательства: ' + '; '.join(observation['evidence']) + '.')
        paragraph(document, 'PNG и журнал действий сохранены в папке прогона '
                  'Протоколы/Ручные/RUN-20261024-01. Успех отдельного действия '
                  'не означает завершение всего пользовательского сценария.')

    page(document, 'Приложение В3 Бронь до проведения')
    paragraph(document, 'Бронь №000000001 записана без проведения. '
              'На форме указано, что она не действует; в отчёте резерва нет.')
    add_cropped_screenshot(document, 'current/booking-saved-unposted.png', (2800, 1706),
                           (10, 325, 2780, 1280), 'Записанная непроведённая бронь', width=6.6)
    paragraph(document, 'Рисунок В.1 Бронь 20 л на 1800 руб. до проведения')
    add_cropped_screenshot(document, 'current/report-unposted.png', (2800, 1706),
                           (15, 900, 2780, 1230), 'Отчёт без резервных движений', width=6.6)
    paragraph(document, 'Рисунок В.2 После записи без проведения молоко 75 / 0 / 75 л')

    page(document, 'Приложение В4 Бронь после проведения')
    paragraph(document, 'Та же бронь проведена под Администратором. '
              'Состояние изменилось на Забронирована; 20 л исключены из свободного остатка.')
    add_cropped_screenshot(document, 'current/booking-posted-clean.png', (2800, 1706),
                           (10, 325, 2780, 1280), 'Проведённая бронь на 20 литров', width=6.6)
    paragraph(document, 'Рисунок В.3 Состояние Забронирована и строка 20 × 90 = 1800 руб.')
    add_cropped_screenshot(document, 'current/report-booked.png', (2800, 1706),
                           (15, 900, 2780, 1230), 'Отчёт после проведения брони', width=6.6)
    paragraph(document, 'Рисунок В.4 После проведения молоко 75 / 20 / 55 л')
    paragraph(document, 'Порядок значений: на складе / в резерве / свободно. '
              'В исходном окне заголовок последней колонки частично уходит '
              'за правую границу; сами значения 55, 15 и 12 видны. '
              'Снимки не содержат дорисованных элементов или изменённых значений.')
