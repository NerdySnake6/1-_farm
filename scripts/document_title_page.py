"""Create a formal title page for the dairy farm documentation."""
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


def add_title_page(document):
    """Prepend a title page and record the supplied author's full name."""
    first = document.paragraphs[0]
    first.text = 'Общие сведения'
    first.style = document.styles['Heading 1']
    first.paragraph_format.page_break_before = True
    section = document.sections[0]
    section.different_first_page_header_footer = True
    section.first_page_header.paragraphs[0].text = ''
    section.first_page_footer.paragraphs[0].text = ''

    def line(text, size=12, bold=False, before=0, after=8, right=False, title=False):
        """Insert one consistently styled cover paragraph before the body."""
        paragraph = document.add_paragraph(style='Title' if title else 'Normal')
        paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT if right else WD_ALIGN_PARAGRAPH.CENTER
        paragraph.paragraph_format.space_before = Pt(before)
        paragraph.paragraph_format.space_after = Pt(after)
        paragraph.paragraph_format.line_spacing = 1.15
        paragraph.paragraph_format.keep_with_next = False
        if right:
            paragraph.paragraph_format.left_indent = Inches(3.1)
        run = paragraph.add_run(text)
        run.font.name = 'Arial'
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = RGBColor(0, 0, 0)
        first._p.addprevious(paragraph._p)
        return paragraph

    line('ДОКУМЕНТАЦИЯ ИНФОРМАЦИОННОЙ СИСТЕМЫ', size=17, bold=True, before=135, after=16)
    line('Молочная ферма Луговая', size=24, bold=True, after=14, title=True)
    line('Конфигурация на платформе «1С:Предприятие 8.3»', after=8)
    line('Дисциплина «Управление проектами»', after=0)
    line('Выполнил', before=75, after=5, right=True)
    line('Калинин Игорь Вячеславович', bold=True, after=10, right=True)
    line('2026', before=160, after=0)
    document.core_properties.author = 'Калинин Игорь Вячеславович'
    document.core_properties.last_modified_by = 'Калинин Игорь Вячеславович'
