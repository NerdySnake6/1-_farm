"""Update the existing testing report while preserving recorded manual results."""

from copy import deepcopy
from pathlib import Path
import shutil

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image

from document_common import paragraph, table

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / 'Документация/04_Тестирование/Документация_по_тестированию.docx'
PROOFS = ROOT / 'Документация/04_Тестирование/Протоколы/Исправление_DEF-001_DEF-002'
SHOTS = ROOT / 'Документация/04_Тестирование/Протоколы/Ручные/RUN-20261028-01'
TITLES = [
    'Приложение Г Проверка исправлений',
    'Приложение Г1 Результаты перепроверки',
    'Приложение Д Разделы конфигурации',
    'Приложение Д1 Интерфейс рабочих ролей',
    'Приложение Е Ручная перепроверка',
    'Приложение Е1 Продажа и бронь',
    'Приложение Е2 Продажа по брони',
]


def replace_text(item, text):
    """Replace paragraph text without changing its paragraph or first-run style."""
    if item.runs:
        item.runs[0].text = text
        for run in item.runs[1:]:
            run.text = ''
    else:
        item.add_run(text)


def page(document, title):
    """Start a bookmarked appendix on a new page."""
    heading = document.add_heading(title, level=1)
    heading.paragraph_format.page_break_before = True
    index = TITLES.index(title)
    start = OxmlElement('w:bookmarkStart')
    start.set(qn('w:id'), str(3000 + index))
    start.set(qn('w:name'), f'fix121_{index}')
    end = OxmlElement('w:bookmarkEnd')
    end.set(qn('w:id'), str(3000 + index))
    heading._p.insert(1, start)
    heading._p.append(end)
    return heading


def screenshot(document, name, bottom, caption, width_pixels=None):
    """Embed a screenshot with an editable crop that removes empty areas only."""
    source = SHOTS / name
    with Image.open(source) as image:
        source_width, source_height = image.size
    right = width_pixels or source_width
    item = document.add_paragraph()
    item.paragraph_format.space_after = Pt(3)
    item.paragraph_format.keep_with_next = True
    picture = item.add_run().add_picture(str(source), width=Cm(16.6), height=Cm(16.6 * bottom / right))
    picture._inline.docPr.set('descr', caption)
    fill = picture._inline.xpath('.//pic:blipFill')[0]
    crop = OxmlElement('a:srcRect')
    for edge, value in [('l', 0), ('t', 0), ('r', round((source_width - right) / source_width * 100000)), ('b', round((source_height - bottom) / source_height * 100000))]:
        crop.set(edge, str(value))
    fill.insert(1, crop)
    item = document.add_paragraph(caption)
    item.paragraph_format.space_after = Pt(8)
    for run in item.runs:
        run.font.size = Pt(10)


def add_contents(document):
    """Extend existing contents without removing bookmarks or manual records."""
    first = next(p for p in document.paragraphs if p.text == '1 Объект и условия тестирования')
    template = next(p for p in document.paragraphs if p._p.findall(qn('w:hyperlink')))
    for index, title in enumerate(TITLES):
        node = deepcopy(template._p)
        for child in list(node):
            if child.tag != qn('w:pPr'):
                node.remove(child)
        link = OxmlElement('w:hyperlink')
        link.set(qn('w:anchor'), f'fix121_{index}')
        run = OxmlElement('w:r')
        text = OxmlElement('w:t')
        text.text = title
        run.append(text)
        link.append(run)
        node.append(link)
        number = OxmlElement('w:r')
        number.append(OxmlElement('w:tab'))
        text = OxmlElement('w:t')
        text.text = '0'
        number.append(text)
        node.append(number)
        first._p.addprevious(node)
    # Keep the complete contents on one page after adding four appendices.
    contents = False
    for item in document.paragraphs:
        if item.text == 'Содержание':
            contents = True
        elif item._p == first._p:
            break
        elif contents:
            item.paragraph_format.space_after = Pt(5)


def finish_layout(document):
    """Keep test conditions and each completed defect card together."""
    in_conditions = False
    for item in document.paragraphs:
        if item.text == '2 Порядок и условия испытаний':
            in_conditions = True
        elif item.style.name == 'Heading 1':
            in_conditions = False
        if in_conditions and item.style.name == 'Normal':
            item.paragraph_format.space_after = Pt(4)
            item.paragraph_format.line_spacing = 1.0
        if item.text in {'Идентификатор DEF-001', 'Идентификатор DEF-002'}:
            item.style = document.styles['Heading 2']
            item.paragraph_format.page_break_before = True
            item.paragraph_format.keep_with_next = True
        if item.text.startswith('Идентификатор DEF-номер.'):
            replace_text(item, 'Карточка сохраняет условия и сообщение исходного сбоя. После исправления отдельно фиксируются версия, способ перепроверки, фактические остатки и оставшиеся ручные действия.')
    for item in list(document.paragraphs):
        if item.text == 'Карточка дефекта' or item.text.startswith('Карточка сохраняет условия и сообщение исходного сбоя.'):
            item._p.getparent().remove(item._p)
    for grid in list(document.tables):
        if len(grid.rows) > 1 and grid.rows[1].cells[-1].text.startswith('Краткий наблюдаемый сбой, например'):
            grid._element.getparent().remove(grid._element)


def verify_protocols():
    """Require actual passing evidence for the claims added to the report."""
    for folder in ['После_исправления', 'Проверка_DT', 'Обновление_отчета']:
        for user, expected in [('Покупка', 9), ('Продажа', 20), ('Администратор', 26)]:
            text = (PROOFS / folder / ('posted-' + user + '.txt')).read_text(encoding='utf-8-sig')
            actual = sum(line.startswith('PASS |') for line in text.splitlines())
            if 'ERROR |' in text or 'COMPLETE' not in text or actual != expected:
                raise ValueError(f'Invalid evidence: {folder}/{user}')


def update():
    """Apply the 1.2.1 amendment in place without rebuilding the historical report."""
    verify_protocols()
    document = Document(REPORT)
    if any(p.text == TITLES[0] for p in document.paragraphs):
        print('Report already contains the 1.2.1 amendment.')
        return
    if not any('RUN-20261028-01' in p.text for p in document.paragraphs):
        raise ValueError('The report must contain the recorded manual run of 28 October.')
    backup = ROOT / '.build/testing-documentation-20261029/original.docx'
    backup.parent.mkdir(parents=True, exist_ok=True)
    if not backup.exists():
        shutil.copy2(REPORT, backup)
    current = None
    for item in document.paragraphs:
        text = item.text
        if text.startswith('Учёт продукции и бронирование в 1С версии'):
            replace_text(item, 'Учёт продукции и бронирование в 1С версии 1.2.1')
        elif text.startswith('Объект испытаний — конфигурация'):
            replace_text(item, 'Объект испытаний — конфигурация «Молочная ферма Луговая». Отчёт сохраняет результаты версии 1.2.0 и дополняет их перепроверкой исправлений DEF-001 и DEF-002 в версии 1.2.1 от 29 октября 2026 года. Ручной прогон Ефимова С.Р. от 28 октября приведён в разделах 4–8; результаты автоматической перепроверки — в приложении Г. Платформа: 1С:Предприятие 8.3.27.1688, учебная версия.')
        elif text.startswith('Документ объединяет результаты уже выполненных'):
            replace_text(item, 'Отчёт разделяет ручные и автоматические испытания. В ручном прогоне RUN-20261028-01 зафиксированы результаты 12 сценариев: 8 успешны, 4 не завершены успешно из-за DEF-001 и DEF-002. В версии 1.2.1 причины дефектов устранены; 55 проверок форм и прав успешны, повторены 83 проверки регрессии. Полный ручной smoke-тест после исправления не повторялся.')
        elif text.startswith('Статус smoke-теста на 28.10.2026:'):
            replace_text(item, 'Ручной smoke-тест 28.10.2026 не пройден: SM01–SM04 и SM12 успешны, SM05–SM11 заблокированы DEF-001 и DEF-002. В 1.2.1 причины устранены и проверены автоматически через формы. Эти результаты не заменяют повторный ручной проход SM01–SM12; он остаётся открытым. См. приложение Г.')
        elif text.startswith('По сохранённым протоколам автоматическая регрессия версии 1.2.0 содержит 83'):
            replace_text(item, 'DEF-001 и DEF-002 исправлены в версии 1.2.1. Автоматическая перепроверка от 29.10.2026: 55 проверок форм и прав успешны; новый прогон регрессии — 83 успешные проверки. После восстановления нового DT повторены те же 55 проверок. Движения не дублируются, изменение количества и отмена выполняются, резерв после отмены связанной продажи восстанавливается. Полная ручная приёмка требует повторного smoke-теста. Исторические отказы 28 октября сохранены.')
        elif text.startswith('Фактические материалы первого прогона находятся'):
            replace_text(item, 'Журнал RUN-20261028-01 приведён выше. Снимки сценариев находятся в Протоколы/Ручные/RUN-20261028-01. Ранний прогон 24 октября сохранён в приложении В. Автоматическая перепроверка исправлений приведена в приложении Г.')
        elif text.startswith('83 — количество уникальных'):
            replace_text(item, '83 — число проверок в историческом наборе регрессии. Этот же набор повторён после исправлений 1.2.1; дополнительно выполнены 55 проверок форм и прав, всего 138 различных автоматических проверок. Повторные прогоны из DT и при обновлении отчёта не увеличивают это число. Ручные сценарии и smoke-тест учитываются отдельно.')
        if item.style.name == 'Heading 2':
            current = text[:4] if text[:4] in {'MP03', 'MS01', 'MS02', 'MS03'} else None
        elif item.style.name == 'Heading 1':
            current = None
        elif current and text.startswith('Отклонение и номер дефекта:'):
            replace_text(item, text + '. Исправлено в 1.2.1; автоматическая перепроверка успешна, см. приложение Г. Ручной результат выше относится к 28.10.2026.')
    for grid in document.tables:
        for row in grid.rows:
            key = row.cells[0].text
            if key == 'Операционная система':
                row.cells[-1].text = 'macOS — автоматические прогоны; Windows — ручной прогон 28.10.2026'
            if key == 'Автоматическая регрессия' and len(row.cells) == 3:
                row.cells[1].text = 'Исторический набор 1.2.0 повторён после исправлений 1.2.1.'
                row.cells[2].text = '83 успешно'
            if key == 'Ручные сценарии' and len(row.cells) == 3:
                row.cells[2].text = '28.10: 8 успешны, 4 с дефектами'
            if key == 'Smoke-тест' and len(row.cells) == 3:
                row.cells[2].text = 'Ручной повтор после 1.2.1 ожидается'
            if key == 'Пользователь, ОС, масштаб окна':
                row.cells[-1].text = 'Администратор, Покупка, Продажа; Windows (по снимкам прогона); 100%'
        if any('MP03 шаги 4 и 5' in c.text or 'MS01 шаг 2, MS02 шаг 3' in c.text for row in grid.rows for c in row.cells):
            purchase = 'MP03' in grid.rows[1].cells[-1].text
            for row in grid.rows:
                if row.cells[0].text == 'Важность и состояние':
                    row.cells[-1].text = 'Высокая. Исправлен в 1.2.1. Автоперепроверка успешна; ручной повтор ожидается.'
                elif row.cells[0].text == 'Перепроверка':
                    row.cells[-1].text = ('29.10.2026, Codex, 1.2.1. Приход: повторное проведение, изменение 2 → 3 л и отмена успешны. См. приложение Г.' if purchase else '29.10.2026, Codex, 1.2.1. Расход и бронь: повторная запись, изменение количества и отмена успешны. Связанная продажа восстанавливает резерв. См. приложение Г.')
                elif row.cells[0].text == 'Доказательства':
                    row.cells[-1].text += '; протоколы После_исправления и Обновление_отчета в папке Исправление_DEF-001_DEF-002.'
    page(document, TITLES[0])
    paragraph(document, 'Перепроверка от 29 октября 2026 года подтверждает исправление двух дефектов прав. Проверки выполнены встроенным языком 1С через метод Записать управляемой формы под тремя пользователями. Это автоматизация работы формы; щелчки по меню «Ещё» в этом прогоне не выполнялись.')
    table(document, ['Условие', 'Зафиксировано'], [
        ('Версия и платформа', '1.2.1; 1С 8.3.27.1688, учебная версия; macOS'),
        ('База и источник', 'Новая отдельная база из Farm_Lugovaya_v1.2.1.dt; рабочие базы не менялись'),
        ('Исходные данные', 'Молоко: склад 75 л, резерв 0; цена 90 руб. После каждого сценария склад и резерв восстановлены'),
        ('Прогон', 'Обновление_отчета; исполнитель автоматизации — Codex'),
    ], [1.7, 4.85])
    document.add_heading('Причина и исправление', level=2)
    paragraph(document, 'Право InteractiveChangeOfPosted («Интерактивное изменение проведённых») отсутствовало, хотя проведение и отмена были разрешены. До исправления повторная запись формы воспроизвела сообщение «Недостаточно прав для изменения проведенных». Недостающее право добавлено только для документов соответствующей роли.')
    table(document, ['Роль', 'Документы', 'Результат'], [
        ('Покупка', 'Приход', '9 из 9 успешно'),
        ('Продажа', 'Расход, Бронирование', '20 из 20 успешно'),
        ('Полные права', 'Приход, Расход, Бронирование', '26 из 26 успешно'),
    ], [1.25, 3.8, 1.5])
    paragraph(document, 'Права сверены по XML ролей. Структурная проверка прав и штатная проверка конфигурации завершены без ошибок. Права Покупки на продажи и права Продажи на приход не расширялись.')
    paragraph(document, 'Исходные доказательства: Протоколы/Исправление_DEF-001_DEF-002. Подпапка До_исправления содержит воспроизведение ошибки; После_исправления — первый успешный прогон; Проверка_DT — повтор после восстановления; Обновление_отчета — текущая перепроверка.')
    page(document, TITLES[1])
    paragraph(document, 'Связь с ручными сценариями: DEF-001 — MP03; DEF-002 — MS01, MS02 и MS03. Ниже приведены фактические состояния после записи через форму. Успешная запись дополнительно проверяется запросом к регистрам.')
    table(document, ['Шаг', 'Действие', 'Приход\nсклад', 'Расход\nсклад', 'Бронь\nрезерв'], [
        ('1', 'Провести 2 л', '77', '73', '2'),
        ('2', 'Получить форму по ссылке и перепровести', '77', '73', '2'),
        ('3', 'Изменить количество на 3 л и провести', '78', '72', '3'),
        ('4', 'Отменить проведение', '75', '75', '0'),
        ('5', 'Снова провести', '78', '72', '3'),
        ('6', 'Снова отменить', '75', '75', '0'),
    ], [0.45, 3.1, 1.0, 1.0, 1.0])
    paragraph(document, 'В сценарии брони склад остаётся 75 л; при приходе и обычной продаже резерв остаётся нулевым. Повторное проведение не создаёт двойных движений. Все шесть шагов выполнены для каждого разрешённого документа, в том числе под Администратором.')
    table(document, ['Связанная операция', 'Склад', 'Резерв', 'Свободно'], [
        ('Провести бронь 20 л', '75', '20', '55'),
        ('Провести продажу по этой брони', '55', '0', '55'),
        ('Перепровести связанную продажу', '55', '0', '55'),
        ('Отменить связанную продажу', '75', '20', '55'),
        ('Отменить бронь', '75', '0', '75'),
    ], [3.55, 1.0, 1.0, 1.0])
    paragraph(document, 'Связанная цепочка успешна под Продажей и Администратором. Итого: 55 из 55 проверок текущего прогона успешны. В отдельном прогоне после исправления также успешны 83 проверки регрессии. Повторение из DT и текущая перепроверка не считаются новыми уникальными тестами.')
    paragraph(document, 'DEF-001 и DEF-002 исправлены и прошли автоматическую перепроверку. Для окончательной ручной приёмки нужно повторить команды перепроведения и отмены в MP03, MS01–MS03 и затем весь SM01–SM12. Старые ручные статусы не заменены отметками об автоматическом успехе.', bold=True)
    page(document, TITLES[2])
    paragraph(document, 'Снимки Ефимова С.Р. из RUN-20261028-01 показывают обновлённый интерфейс с отчётом доступности. Они относятся к прежнему ручному прогону и не служат доказательством исправления прав в 1.2.1. Убраны только пустые области справа и снизу; исходные PNG сохранены.')
    screenshot(document, 'MA01-purchase.png', 390, 'Рисунок Д.1 Раздел Покупка с командами поступления и отчётом доступности', 900)
    screenshot(document, 'MA01-sales.png', 390, 'Рисунок Д.2 Раздел Продажа с бронированием, продажей и отчётами', 900)
    page(document, TITLES[3])
    paragraph(document, 'На снимках видны пользователь и доступные разделы. Наличие команд показывает настройку интерфейса; выполнение операций подтверждается отдельными протоколами.')
    screenshot(document, 'MA02-purchase-role.png', 440, 'Рисунок Д.3 Рабочий стол пользователя Покупка')
    screenshot(document, 'MA02-sales-role.png', 505, 'Рисунок Д.4 Рабочий стол пользователя Продажа')
    screenshot(document, 'MA02-admin-role.png', 590, 'Рисунок Д.5 Рабочий стол Администратора с обоими разделами')
    from manual_recheck_report import apply
    apply(document, page, screenshot)
    add_contents(document)
    finish_layout(document)
    document.core_properties.last_modified_by = 'Калинин Игорь Вячеславович'
    document.core_properties.title = 'Документация по тестированию Молочная ферма Луговая'
    document.save(REPORT)
    print(REPORT)


if __name__ == '__main__':
    update()
