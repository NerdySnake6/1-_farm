"""Add documented booking screenshots to the overview and user guide."""

from copy import deepcopy
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt
from PIL import Image
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parents[1]
SHOTS = ROOT / 'Документация/04_Тестирование/Протоколы/Ручные/RUN-20261028-01'
TARGETS = {
    'general': ROOT / 'Документация/01_Общее_описание/Общая_документация.docx',
    'user': ROOT / 'Документация/03_Пользователю/Инструкция_пользователя.docx',
}


def add_image(document, source, caption, top=0, bottom=None):
    """Embed an original PNG with an editable crop and descriptive caption."""
    with Image.open(source) as original:
        width, height = original.size
    bottom = bottom or height
    item = document.add_paragraph()
    item.paragraph_format.keep_with_next = True
    item.paragraph_format.space_after = Pt(3)
    shape = item.add_run().add_picture(
        str(source), width=Cm(16.5), height=Cm(16.5 * (bottom - top) / width),
    )
    shape._inline.docPr.set('descr', caption)
    crop = OxmlElement('a:srcRect')
    for edge, value in {'l': 0, 'r': 0, 't': top / height, 'b': (height - bottom) / height}.items():
        crop.set(edge, str(round(value * 100000)))
    shape._inline.xpath('.//pic:blipFill')[0].insert(1, crop)
    item = document.add_paragraph(caption)
    item.paragraph_format.space_after = Pt(8)
    for run in item.runs:
        run.font.size = Pt(10)


def append_screenshots(document, kind):
    """Append two illustrated pages once, preserving all existing content."""
    letter = 'Б' if kind == 'general' else 'А'
    titles = [f'Приложение {letter} Бронирование в интерфейсе',
              f'Приложение {letter}1 Продажа и отмена брони']
    if any(item.text == titles[0] for item in document.paragraphs):
        return []
    headings = []
    for index, title in enumerate(titles):
        heading = document.add_heading(title, level=1)
        heading.paragraph_format.page_break_before = True
        headings.append(heading)
        if index == 0:
            document.add_paragraph(
                'Карточка на рисунке ' + letter + '.1 показывает проведённую бронь 20 л молока '
                'по 90 руб. Состояние документа — «Забронирована», сумма — 1 800 руб. '
                'Доступны команды «Продать по брони» и «Отменить бронь».'
            )
            add_image(document, ROOT / 'assets/screenshots/current/booking-posted-clean.png',
                      f'Рисунок {letter}.1 Проведённая бронь и команды работы с ней', top=310, bottom=1280)
            document.add_paragraph(
                'После проведения товар остаётся на складе, но резерв уменьшает количество, '
                'доступное для обычной продажи: 75 − 20 = 55 л.'
            )
            add_image(document, SHOTS / 'MS02-booked.png',
                      f'Рисунок {letter}.2 Молоко после бронирования: склад 75 л, резерв 20 л, свободно 55 л')
            document.add_paragraph(
                'Рисунок ' + letter + '.1 — снимок версии 1.2.0 от 24 октября 2026 года; '
                'он иллюстрирует состав брони и команды. Рисунки ' + letter + '.2–' + letter +
                '.4 — снимки ручной перепроверки Ефимова С.Р. от 29 октября. '
                'Их исходные PNG сохранены в протоколах тестирования.'
            )
        else:
            document.add_paragraph(
                'Продажа и отмена показаны как альтернативные действия с бронью 20 л. '
                'При продаже по брони уменьшается складской остаток и освобождается резерв.'
            )
            add_image(document, SHOTS / 'MS03-linked-sale.png',
                      f'Рисунок {letter}.3 После продажи по брони: склад 55 л, резерв 0 л, свободно 55 л')
            document.add_paragraph(
                'Если товар не выдан, команда «Отменить бронь» освобождает резерв. '
                'Количество на складе сохраняется: все 75 л снова доступны для продажи.'
            )
            add_image(document, SHOTS / 'MS02-cancelled.png',
                      f'Рисунок {letter}.4 После отмены брони: склад 75 л, резерв 0 л, свободно 75 л')
            document.add_paragraph(
                'Эти кадры подтверждают резервирование, продажу и ручную отмену. '
                'Автоматическое снятие просроченной брони проверено отдельно '
                '29 октября в протоколе «Расписание_брони_20261029»: '
                'в существующем задании базы требуется настроить повторение каждые 60 секунд. '
                'Без этой настройки ожидание одной минуты не гарантирует снятия резерва.'
            )
    return headings


def extend_contents(document, headings):
    """Add internal contents links without replacing existing bookmarks."""
    template = next(item for item in document.paragraphs if item._p.findall(qn('w:hyperlink')))
    cursor = [item for item in document.paragraphs if item._p.findall(qn('w:hyperlink'))][-1]
    for index, heading in enumerate(headings):
        anchor = f'booking_screens_{index}'
        start = OxmlElement('w:bookmarkStart')
        start.set(qn('w:id'), str(8200 + index))
        start.set(qn('w:name'), anchor)
        end = OxmlElement('w:bookmarkEnd')
        end.set(qn('w:id'), str(8200 + index))
        heading._p.insert(1, start)
        heading._p.append(end)
        node = deepcopy(template._p)
        for child in list(node):
            if child.tag != qn('w:pPr'):
                node.remove(child)
        link = OxmlElement('w:hyperlink')
        link.set(qn('w:anchor'), anchor)
        run = OxmlElement('w:r')
        value = OxmlElement('w:t')
        value.text = heading.text
        run.append(value)
        link.append(run)
        node.append(link)
        run = OxmlElement('w:r')
        run.append(OxmlElement('w:tab'))
        value = OxmlElement('w:t')
        value.text = '0'
        run.append(value)
        node.append(run)
        cursor._p.addnext(node)
        cursor = Paragraph(node, document._body)


def main():
    """Update the two existing documents in place."""
    for kind, path in TARGETS.items():
        document = Document(path)
        headings = append_screenshots(document, kind)
        if headings:
            extend_contents(document, headings)
            document.save(path)
            print(path)


if __name__ == '__main__':
    main()
