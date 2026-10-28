"""Build a standalone testing report from the recorded 1C test results."""
from pathlib import Path
import document_reservations
import document_refresh
import testing_handbook
from urllib.parse import quote

from docx import Document
from document_screenshots import add_cropped_screenshot
from document_common import add_contents, cover as common_cover
from docx.opc.constants import RELATIONSHIP_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'Документация/04_Тестирование/Документация_по_тестированию.docx'
AUTHOR = 'Калинин Игорь Вячеславович'


def read_results(filename):
    """Read successful checks and reject a protocol containing errors."""
    text = (ROOT / 'Документация/04_Тестирование/Протоколы' / filename).read_text(encoding='utf-8-sig')
    assert 'ERROR' not in text and 'FAIL' not in text, filename
    return [line.split(' | ', 1)[1] for line in text.splitlines() if line.startswith('PASS | ')]


def paragraph(document, text, bold=False):
    """Add a body paragraph with optional emphasis."""
    item = document.add_paragraph()
    item.add_run(text).bold = bold
    return item


def page(document, title):
    """Start a report section on a separate page."""
    item = document.add_heading(title, level=1)
    item.paragraph_format.page_break_before = True


def table(document, headers, rows, widths):
    """Create a bordered table with repeatable column headings."""
    item = document.add_table(rows=1, cols=len(headers))
    item.autofit = False
    for column, width in zip(item.columns, widths):
        column.width = Inches(width)
    for cell, text in zip(item.rows[0].cells, headers):
        cell.text = text
        shade = OxmlElement('w:shd')
        shade.set(qn('w:fill'), 'E8E8E8')
        cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    repeat = OxmlElement('w:tblHeader')
    item.rows[0]._tr.get_or_add_trPr().append(repeat)
    for values in rows:
        for cell, text in zip(item.add_row().cells, values):
            cell.text = str(text)
    for row in item.rows:
        properties = row._tr.get_or_add_trPr()
        properties.append(OxmlElement('w:cantSplit'))
        for cell, width in zip(row.cells, widths):
            cell.width = Inches(width)
            properties = cell._tc.get_or_add_tcPr()
            borders = OxmlElement('w:tcBorders')
            for edge in ['top', 'left', 'bottom', 'right']:
                border = OxmlElement('w:' + edge)
                for key, value in [('val', 'single'), ('sz', '4'), ('color', 'D9D9D9')]:
                    border.set(qn('w:' + key), value)
                borders.append(border)
            properties.append(borders)
            margins = OxmlElement('w:tcMar')
            for edge in ['top', 'left', 'bottom', 'right']:
                margin = OxmlElement('w:' + edge)
                margin.set(qn('w:w'), '80')
                margin.set(qn('w:type'), 'dxa')
                margins.append(margin)
            properties.append(margins)
            for body in cell.paragraphs:
                body.paragraph_format.space_after = Pt(3)
                body.paragraph_format.space_before = Pt(3)
                body.paragraph_format.line_spacing = 1.05
                for run in body.runs:
                    run.font.size = Pt(10.5)
    document.add_paragraph().paragraph_format.space_after = Pt(0)
    return item


def cover(document):
    """Add a title page using only the supplied author and project details."""
    common_cover(document, 'ДОКУМЕНТАЦИЯ ПО ТЕСТИРОВАНИЮ')



def add_testing_screenshots(document):
    """Illustrate the tested home form and the sample stock result."""
    page(document, 'Приложение А Снимки конфигурации')
    paragraph(document, 'Снимки предоставлены пользователем. Для размещения в документе выделены рабочие области окон; значения данных и подписи элементов сохранены.')
    document.add_heading('Рабочий стол', level=2)
    add_cropped_screenshot(
        document, 'Рабочий_стол.png', (1624, 1252), (35, 475, 1259, 995),
        'Рабочий стол фермы с командами документов, продукции, цен и отчетов', width=6.6,
    )
    paragraph(document, 'Рисунок А.1 Рабочий стол фермы')
    paragraph(document, 'Снимок сделан до добавления бронирования. Видны команды документов, журналы, продукция, цены и отчёты. Новые команды проверены сценарием BF06. Создание этой формы проверяется сценарием F06, вызов восьми переходов рабочего стола сценарием F08.')
    document.add_heading('Остатки контрольного примера', level=2)
    add_cropped_screenshot(
        document, 'Остатки.png', (1906, 840), (875, 530, 1752, 680),
        'Отчет с остатками молока 75, творога 15 и сметаны 12', width=6.6,
    )
    paragraph(document, 'Рисунок А.2 Фрагмент отчёта по остаткам')
    paragraph(document, 'Значения соответствуют сценариям T01, T02 и T03: молоко 75 л, творог 15 кг, сметана 12 кг. На снимке показан результат отчёта ранней версии; контрольные значения сохранены в версии 1.2.0. Проверка формирования отчёта и отбора по складу описана в сценарии F04.')


def protocol_links(document):
    """Add portable clickable references to the six primary protocols."""
    item = document.add_paragraph()
    for index, name in enumerate(['runtime-tests.txt', 'form-tests.txt', 'role-Покупка.txt', 'role-Продажа.txt', 'reservation-tests.txt', 'reservation-form-tests.txt']):
        if index:
            item.add_run('\n' if index == 3 else '  ·  ')
        relation = document.part.relate_to(quote('Протоколы/' + name), RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
        link = OxmlElement('w:hyperlink')
        link.set(qn('r:id'), relation)
        run = OxmlElement('w:r')
        properties = OxmlElement('w:rPr')
        underline = OxmlElement('w:u')
        underline.set(qn('w:val'), 'single')
        properties.append(underline)
        size = OxmlElement('w:sz')
        size.set(qn('w:val'), '20')
        properties.append(size)
        run.append(properties)
        text = OxmlElement('w:t')
        text.text = name
        run.append(text)
        link.append(run)
        item._p.append(link)


def build():
    """Generate the report and verify that it accounts for all 83 checks."""
    checks = {name: read_results(name) for name in [
        'runtime-tests.txt', 'form-tests.txt', 'role-Покупка.txt', 'role-Продажа.txt'
    ]}
    assert [len(items) for items in checks.values()] == [21, 10, 9, 9]
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(2), Cm(2)
    section.left_margin, section.right_margin = Cm(2.1), Cm(2)
    section.different_first_page_header_footer = True
    for name in ['Normal', 'Title', 'Heading 1', 'Heading 2']:
        style = document.styles[name]
        style.font.name = 'Times New Roman'
        style.font.color.rgb = RGBColor(0, 0, 0)
    normal = document.styles['Normal']
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.15
    normal.paragraph_format.space_after = Pt(7)
    document.styles['Heading 1'].font.size = Pt(17)
    document.styles['Heading 2'].font.size = Pt(13)
    document.styles['Heading 2'].paragraph_format.space_before = Pt(12)
    header = section.header.paragraphs[0]
    header.text = 'МОЛОЧНАЯ ФЕРМА ЛУГОВАЯ   /   ТЕСТИРОВАНИЕ'
    for run in header.runs:
        run.font.size = Pt(9)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    field = OxmlElement('w:fldSimple')
    field.set(qn('w:instr'), 'PAGE')
    footer._p.append(field)
    cover(document)

    page(document, '1 Объект и условия тестирования')
    paragraph(document, 'Проверена конфигурация «Молочная ферма Луговая», версия 1.2.0. Испытания охватывают учёт поступления и продажи продукции, расчёт остатков, работу форм и разграничение доступа. Документ составлен по сохранённым протоколам проверок от 23 октября 2026 года.')
    table(document, ['Параметр', 'Условия'], [
        ('Платформа', '1С:Предприятие 8.3.27.1688, учебная версия'),
        ('Операционная система', 'macOS'),
        ('База', 'Файловая, отдельная тестовая копия'),
        ('Пользователи', 'Администратор, Покупка, Продажа'),
        ('Способ проверки', 'Средства проверки конфигурации и сценарии на встроенном языке 1С'),
    ], [1.65, 5])
    document.add_heading('Контрольные данные', level=2)
    table(document, ['Продукция', 'Цена руб', 'Приход', 'Продажа', 'Остаток'], [
        ('Молоко, л', 90, 100, 25, 75), ('Творог, кг', 360, 20, 5, 15), ('Сметана, кг', 280, 15, 3, 12)
    ], [2.1, 1.1, 1.15, 1.15, 1.15])
    paragraph(document, 'Сумма продажи: 25 × 90 + 5 × 360 + 3 × 280 = 4 890 руб. Названия контрагентов и операции относятся к учебному примеру.')
    document.add_heading('Порядок выполнения', level=2)
    paragraph(document, 'Сначала выполнена проверка конфигурации. Затем запущены сценарии учёта и форм под администратором, после них проверки под пользователями Покупка и Продажа. Дополнительные тестовые документы откатываются транзакциями. Выгрузка DT восстановлена в отдельную базу; проверка конфигурации и основные сценарии повторены после восстановления.')
    paragraph(document, 'В протоколах PASS означает совпадение фактического результата с условием проверки. Ожидаемый отказ в проведении некорректного документа считается успешным результатом соответствующего сценария.')

    cases = [
        ('T01', 'Получить остаток молока', '75 л после прихода 100 л и продажи 25 л'),
        ('T02', 'Получить остаток творога', '15 кг после прихода 20 кг и продажи 5 кг'),
        ('T03', 'Получить остаток сметаны', '12 кг после прихода 15 кг и продажи 3 кг'),
        ('T04', 'Получить цену молока из регистра', 'Цена равна 90 руб.'),
        ('T05.1', 'Прочитать фотографию молока', 'Из хранилища получено значение'),
        ('T05.2', 'Прочитать фотографию творога', 'Из хранилища получено значение'),
        ('T05.3', 'Прочитать фотографию сметаны', 'Из хранилища получено значение'),
        ('T06', 'Провести продажу 76 л при остатке 75 л', 'Проведение отклонено'),
        ('T07', 'Проверить остаток после отказа', 'Остаток молока сохранился: 75 л'),
        ('T08', 'Записать расход с нулевым количеством', 'Операция отклонена'),
        ('T09', 'Записать приход с отрицательным количеством', 'Операция отклонена'),
        ('T10', 'Записать расход с нулевой ценой', 'Операция отклонена'),
        ('T11', 'Записать приход без склада', 'Операция отклонена'),
        ('T12', 'Записать приход без строк продукции', 'Операция отклонена'),
        ('T13', 'Провести дополнительную продажу 1 л молока', 'Остаток уменьшился с 75 до 74 л'),
        ('T14', 'Проверить сумму строки 1 л по 90 руб.', 'Сумма равна 90 руб.'),
        ('T15', 'Повторно провести документ продажи', 'Остаток остался 74 л, дублей движений нет'),
        ('T16', 'Отменить проведение дополнительной продажи', 'Остаток восстановлен до 75 л'),
        ('T17', 'Отменить приход при уже проданной продукции', 'Отмена отклонена из-за недостатка остатка'),
        ('T18', 'Продать 1 и 75 л молока в двух строках', 'Учтено суммарно 76 л, проведение отклонено'),
        ('T19', 'Получить сумму проведённых продаж', 'Сумма равна 4 890 руб.'),
    ]
    for part, subset in enumerate([cases[:11], cases[11:]], start=1):
        page(document, '2 Проверка учёта' if part == 1 else '2 Проверка учёта (продолжение)')
        paragraph(document, 'Для каждого сценария ожидаемый результат совпал с фактическим. Протокол runtime-tests.txt содержит 21 запись PASS и завершающую отметку COMPLETE.' if part == 1 else 'Проверки проведения и отмены документов выполнялись на контрольных данных. После завершения сценариев временные изменения откатывались.')
        actual = ['75 л','15 кг','12 кг','90 руб.','Есть значение','Есть значение','Есть значение','Отказ','75 л','Отказ','Отказ','Отказ','Отказ','Отказ','74 л','90 руб.','74 л','75 л','Отказ','Отказ','4 890 руб.']
        actual_by_code = {case[0]: result for case, result in zip(cases, actual)}
        table(document, ['Код', 'Действие и условие', 'Ожидаемый результат', 'Фактически'], [
            (*case, actual_by_code[case[0]]) for case in subset
        ], [.55, 2.25, 2.8, 1.05])
        if part == 1:
            paragraph(document, 'В исходном протоколе три проверки фотографий имеют общий код T05. Для различения в таблице использованы обозначения T05.1, T05.2 и T05.3.')
        else:
            paragraph(document, 'Проверка T05 подтверждает наличие значения фотографии в базе. Отображение изображения и загрузка нового файла через интерфейс требуют отдельной ручной проверки.')

    page(document, '3 Проверка форм и команд')
    paragraph(document, 'Выполнено 10 проверок форм. Сценарии программно получают и открывают реальные формы 1С, вызывают обработчики команд и проверяют результат. Все 10 записей протокола form-tests.txt имеют статус PASS.')
    form_rows = [
        ('F01', 'Карточка номенклатуры', 'Форма с полем фотографии создана'),
        ('F02', 'Добавление продукции в приход', 'Команда создаёт одну строку'),
        ('F03', 'Документ расхода', 'Форма создана без ошибки'),
        ('F04', 'Остатки и отбор по складу', 'Пустой склад даёт пустой результат; сброс отбора выполнен'),
        ('F05', 'Продажи за период', 'Отчёт сформирован без ошибки'),
        ('F06', 'Общий рабочий стол', 'Форма и команды операций созданы без ошибки'),
        ('F07', 'Итог и удаление строки', '2 × 90 = 180 руб.; после удаления итог равен нулю'),
        ('F08', 'Переходы рабочего стола', 'Выполнены все восемь обработчиков переходов'),
        ('F09', 'Страница Покупка', 'Дважды открыта; нужные команды найдены; справочники открыты'),
        ('F10', 'Страница Продажа', 'Дважды открыта; нужные команды найдены; справочники открыты'),
    ]
    expected_forms = [
        'Создана форма с полем фотографии', 'Добавлена одна строка',
        'Создана форма документа', 'Пустой склад: пустой результат; сброс отбора',
        'Отчёт сформирован', 'Созданы форма и команды',
        'Итог 180 руб.; после удаления 0', 'Выполнены восемь переходов',
        'Повторное открытие страницы и справочников без ошибки',
        'Повторное открытие страницы и справочников без ошибки',
    ]
    rows = [(code, action, expected, actual) for (code, action, actual), expected in zip(form_rows, expected_forms)]
    table(document, ['Код', 'Проверка', 'Ожидается', 'Фактически'], rows, [.45, 1.65, 2.1, 2.45])
    document.add_heading('Границы проверки интерфейса', level=2)
    paragraph(document, 'Сценарии F09 и F10 проверяют открытие страниц разделов и их команды. Они не воспроизводят нажатия мышью на верхнюю панель разделов. Переход по одному щелчку, читаемость полей и расположение элементов следует проверить вручную.')

    page(document, '4 Проверка прав пользователей')
    paragraph(document, 'Под пользователями Покупка и Продажа выполнено по девять проверок. Получено 18 записей PASS. Для разрешений сравнивалось значение права доступа с ожидаемым значением для роли. Рабочие пользователи не имеют административных прав.')
    table(document, ['Код', 'Предмет проверки', 'Покупка', 'Продажа'], [
        ('R01', 'Назначение рабочей роли', 'Только Покупка', 'Только Продажа'),
        ('R02', 'Право проведения прихода', 'Разрешено', 'Запрещено'),
        ('R03', 'Право проведения расхода', 'Запрещено', 'Разрешено'),
        ('R04', 'Изменение регистра цен', 'Разрешено', 'Запрещено'),
        ('R05', 'Администрирование', 'Запрещено', 'Запрещено'),
        ('R06', 'Кнопки общего рабочего стола', 'Нет создания продажи', 'Нет создания прихода'),
        ('R07', 'Страница раздела и справочники', 'Доступны', 'Доступны'),
        ('R08', 'Проведение бронирования', 'Запрещено', 'Разрешено'),
        ('R09', 'Чтение резервов', 'Разрешено', 'Разрешено'),
    ], [.55, 2.6, 1.75, 1.75])
    paragraph(document, 'Во всех строках таблицы фактические значения совпали с ожидаемыми. Протоколы: role-Покупка.txt и role-Продажа.txt.')
    paragraph(document, 'R07 включает открытие страницы своего раздела, организаций, складов и соответствующего справочника контрагентов. В Покупке открываются поставщики, в Продаже покупатели.')
    document.add_heading('Способ проверки разрешений', level=2)
    paragraph(document, 'Проверки R02, R03 и R04 обращаются к разрешениям метаданных. Они подтверждают настройку прав, но не заменяют ручную попытку проведения документа под каждой ролью. Основные сценарии учёта выполнялись под администратором.')

    page(document, '5 Результаты и оставшиеся проверки')
    table(document, ['Группа','Выполнено','Успешно'],[
        ('Учёт продукции',21,21),('Прежние формы и команды',10,10),
        ('Покупка',9,9),('Продажа',9,9),('Бронирование',28,28),
        ('Команды брони',6,6),('Всего',83,83),
    ],[3.65,1.5,1.5])
    paragraph(document,'Штатная проверка конфигурации не обнаружила ошибок. Во всех автоматических сценариях ожидаемые и фактические результаты совпали. Новые прогоны версии 1.2.0 выполнены 23 октября 2026 года; результаты бронирования приведены в разделах 6–8.')
    document.add_heading('План ручной проверки',level=2)
    table(document,['Действие','Ожидаемый результат'],[
        ('Открыть Покупку и Продажу одним щелчком','Открывается страница выбранного раздела.'),
        ('Открыть карточки трёх товаров','Фотографии и подписи видны.'),
        ('Загрузить фотографию и снова открыть карточку','Сохранённое изображение отображается.'),
        ('Изменить количество через интерфейс','Сумма и итог пересчитываются.'),
        ('Проверить запреты под рабочими ролями','Недоступные операции не выполняются.'),
        ('Проверить бронь мышью','Состояние и три количества читаются.'),
    ],[3.35,3.3])
    paragraph(document,'Это план, а не протокол выполненных щелчков. Автоматические сценарии вызывают формы и обработчики программно. Нагрузочные, сетевые и многопользовательские испытания не проводились; другие операционные системы не проверялись.')
    document.add_heading('Основание отчёта',level=2)
    paragraph(document,'Использованы шесть исходных протоколов в папке Протоколы и соответствующие модули конфигурации. Повторение после восстановления DT не увеличивает число уникальных сценариев. Отдельное наблюдение platform-limitations.txt подтверждает запрет печати и сохранения табличного документа в учебной лицензии.')

    document_reservations.testing(document)
    protocol_links(document)
    add_testing_screenshots(document)

    document.core_properties.title = 'Документация по тестированию Молочная ферма Луговая'
    document.core_properties.author = AUTHOR
    document.core_properties.last_modified_by = AUTHOR
    document.core_properties.subject = 'Условия, сценарии и результаты тестирования конфигурации 1С'
    for border in document.styles.element.xpath('.//w:pBdr'):
        border.getparent().remove(border)
    document_refresh.testing(document)
    testing_handbook.expand(document)
    add_contents(document, [p.text for p in document.paragraphs if p.style.name == 'Heading 1'])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    document.save(OUTPUT)
    print(OUTPUT)


if __name__ == '__main__':
    build()
