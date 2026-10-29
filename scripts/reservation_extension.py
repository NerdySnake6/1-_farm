"""Extend the farm with a reservation register, booking form and sale linkage."""
import build_configuration as base


def install(extension):
    """Add reservation metadata and modules after the existing 1.1.1 generator."""
    out = base.OUT
    metadata = out / 'Configuration.xml'
    source = metadata.read_text()
    sale_metadata = out / 'Documents/Расход.xml'
    sale = sale_metadata.read_text()
    # Generate runtime identities with the same helper as the other documents.
    attributes = [('Организация', 'cfg:CatalogRef.Организации'), ('Склад', 'cfg:CatalogRef.Склады'), ('Покупатель', 'cfg:CatalogRef.Покупатели')]
    tab = '<TabularSection uuid="' + base.uid('БронированиеТовары') + '">' + base.internal('DocumentTabularSection', 'Бронирование.Товары', ['TabularSection', 'TabularSectionRow'])
    tab += '<Properties><Name>Товары</Name><Synonym>' + base.syn('Продукция') + '</Synonym></Properties><ChildObjects>'
    tab += ''.join(base.attr('БронированиеТовары', name, typ) for name, typ in [('Номенклатура', 'cfg:CatalogRef.Номенклатура'), ('Количество', 'number'), ('Цена', 'money'), ('Сумма', 'money')])
    tab += '</ChildObjects></TabularSection>'
    properties = '<NumberType>String</NumberType><NumberLength>9</NumberLength><NumberAllowedLength>Variable</NumberAllowedLength><Autonumbering>true</Autonumbering><CheckUnique>true</CheckUnique><NumberPeriodicity>Year</NumberPeriodicity><Posting>Allow</Posting><RealTimePosting>Deny</RealTimePosting><RegisterRecords><xr:Item xsi:type="xr:MDObjectRef">AccumulationRegister.РезервыПродукции</xr:Item></RegisterRecords>'
    booking = base.obj('Document', 'Бронирование', properties, ''.join(base.attr('Бронирование', name, typ) for name, typ in attributes) + tab, synonym='Бронирование продукции')
    dimensions = [('Организация', 'cfg:CatalogRef.Организации'), ('Склад', 'cfg:CatalogRef.Склады'), ('Номенклатура', 'cfg:CatalogRef.Номенклатура'), ('Бронирование', 'cfg:DocumentRef.Бронирование')]
    register = base.obj('AccumulationRegister', 'РезервыПродукции', '<RegisterType>Balance</RegisterType><EnableTotalsSplitting>true</EnableTotalsSplitting>', ''.join(base.attr('Резервы', name, typ, 'Dimension') for name, typ in dimensions) + base.attr('Резервы', 'Количество', 'number', 'Resource'), synonym='Резервы продукции')
    metadata.write_text(source.replace('<Version>1.1.1</Version>', '<Version>1.2.1</Version>').replace('</ChildObjects>', booking + register + '</ChildObjects>', 1))
    sale = sale.replace('</RegisterRecords>', '<xr:Item xsi:type="xr:MDObjectRef">AccumulationRegister.РезервыПродукции</xr:Item></RegisterRecords>', 1)
    sale = sale.replace('<ChildObjects>', '<ChildObjects>' + base.attr('Расход', 'Бронирование', 'cfg:DocumentRef.Бронирование'), 1)
    sale_metadata.write_text(sale)
    common_path = out / 'CommonModules/УчетФермы/Ext/Module.bsl'
    common = common_path.read_text()
    keep_price = common[common.index('Функция ПолучитьЦену'):]
    common_path.write_text((base.ROOT / 'scripts/bsl/БронированиеУчет.bsl').read_text() + '\n' + keep_price)
    for name in ['Приход', 'Расход']:
        path = out / f'Documents/{name}/Ext/ObjectModule.bsl'
        code = path.read_text().replace('Процедура ПередЗаписью(Отказ, РежимЗаписи, РежимПроведения)\n', 'Процедура ПередЗаписью(Отказ, РежимЗаписи, РежимПроведения)\n    УчетФермы.ЗаблокироватьУчет();\n')
        code = code.replace('Процедура ОбработкаУдаленияПроведения(Отказ)\n', 'Процедура ОбработкаУдаленияПроведения(Отказ)\n    УчетФермы.ЗаблокироватьУчет();\n')
        if name == 'Расход':
            code = code.replace('Процедура ОбработкаПроведения(Отказ, РежимПроведения)\n', 'Процедура ОбработкаПроведения(Отказ, РежимПроведения)\n    УчетФермы.ПроверитьПродажуПоБрони(ЭтотОбъект);\n')
            release = '''    Движения.РезервыПродукции.Записывать = Истина;
    Движения.РезервыПродукции.Очистить();
    Если ЗначениеЗаполнено(Бронирование) Тогда
        Для Каждого Товар Из Товары Цикл
            Резерв = Движения.РезервыПродукции.Добавить();
            Резерв.ВидДвижения = ВидДвиженияНакопления.Расход;
            Резерв.Период = Дата;
            Резерв.Организация = Организация;
            Резерв.Склад = Склад;
            Резерв.Номенклатура = Товар.Номенклатура;
            Резерв.Бронирование = Бронирование;
            Резерв.Количество = Товар.Количество;
        КонецЦикла;
    КонецЕсли;
    Движения.РезервыПродукции.Записать();
'''
            code = code.replace('    Движения.ОстаткиПродукции.Записать();', '    Движения.ОстаткиПродукции.Записать();\n' + release, 1)
            undo_position = code.index('Процедура ОбработкаУдаленияПроведения')
            code = code[:undo_position] + code[undo_position:].replace('    Движения.ОстаткиПродукции.Записать();', '    Движения.ОстаткиПродукции.Записать();\n    Движения.РезервыПродукции.Записывать = Истина;\n    Движения.РезервыПродукции.Очистить();\n    Движения.РезервыПродукции.Записать();', 1)
        code += DELETE_GUARD
        path.write_text(code)
    extension.write('Documents/Бронирование/Ext/ObjectModule.bsl', (base.ROOT / 'scripts/bsl/БронированиеОбъект.bsl').read_text() + DELETE_GUARD)
    sale_form_path = out / 'Documents/Расход/Forms/Форма/Ext/Form/Module.bsl'
    form = sale_form_path.read_text()
    booking_form = form.replace('Заголовок = "Продажа продукции";', 'Заголовок = "Бронирование продукции";')
    booking_form = booking_form.replace('    ЦветФона =', '''    ДобавитьПоле("СостояниеБрони", "СостояниеБрони", "Состояние");
    Элементы.СостояниеБрони.ТолькоПросмотр = Истина;
    ОбновитьСостояние();
    ДобавитьКнопку("ПродатьБронь", "Продать по брони");
    ДобавитьКнопку("ОтменитьБронь", "Отменить бронь");
    ЦветФона =''', 1)
    booking_form += (base.ROOT / 'scripts/bsl/БронированиеФорма.bsl').read_text()
    extension.add_form('Documents', 'Бронирование', 'cfg:DocumentObject.Бронирование', booking_form, {'OnCreateAtServer': 'ПриСозданииНаСервере', 'AfterWriteAtServer': 'ПослеЗаписиНаСервере'})
    form_xml = out / 'Documents/Бронирование/Forms/Форма/Ext/Form.xml'
    form_xml.write_text(form_xml.read_text().replace('</Attributes>', '<Attribute name="СостояниеБрони" id="20"><Type><v8:Type>xs:string</v8:Type></Type></Attribute></Attributes>'))
    sale_form_path.write_text(form.replace('    ЦветФона =', '    ДобавитьПоле("Бронирование", "Объект.Бронирование", "Бронь (для продажи по резерву)");\n    ЦветФона =', 1))
    for role in ['Покупка', 'Продажа', 'ПолныеПрава']:
        path = out / f'Roles/{role}/Ext/Rights.xml'
        rights = path.read_text()
        booking_rights = ['Read', 'View'] if role in ['Продажа', 'ПолныеПрава'] else []
        if role in ['Продажа', 'ПолныеПрава']:
            booking_rights += ['Insert', 'Update', 'Edit', 'Posting', 'UndoPosting', 'InteractiveInsert', 'InteractivePosting', 'InteractivePostingRegular', 'InteractiveUndoPosting', 'InteractiveChangeOfPosted']
        if role == 'ПолныеПрава':
            booking_rights += ['Delete', 'InteractiveDelete']
        def grant(ref, names):
            """Serialize rights using the existing generator convention."""
            return '<object><name>' + ref + '</name>' + ''.join('<right><name>' + name + '</name><value>true</value></right>' for name in names) + '</object>'
        rights = rights.replace('</Rights>', grant('Document.Бронирование', booking_rights) + grant('AccumulationRegister.РезервыПродукции', ['Read', 'View'] + (['Update'] if role in ['Продажа', 'ПолныеПрава'] else [])) + '</Rights>')
        path.write_text(rights)
    for name in ['РабочийСтол', 'ПанельПродажа']:
        path = out / f'CommonForms/{name}/Ext/Form/Module.bsl'
        code = path.read_text().replace('        ДобавитьКнопку("СоздатьРасход",', '        ДобавитьКнопку("СоздатьБронь", "Забронировать продукцию", Операции);\n        ДобавитьКнопку("ОткрытьБрони", "Журнал бронирований", Операции);\n        ДобавитьКнопку("СоздатьРасход",', 1)
        code += '''
&НаКлиенте
Процедура СоздатьБронь(Команда) Экспорт
    ОткрытьФорму("Документ.Бронирование.ФормаОбъекта");
КонецПроцедуры

&НаКлиенте
Процедура ОткрытьБрони(Команда) Экспорт
    ОткрытьФорму("Документ.Бронирование.ФормаСписка");
КонецПроцедуры
'''
        path.write_text(code)
    report = out / 'Reports/ОстаткиПродукции/Forms/Форма/Ext/Form/Module.bsl'
    code = report.read_text()
    start = code.index('    Запрос.Текст = "')
    end = code.index(';', start) + 1
    code = code[:start] + '    Запрос.Текст = "' + STOCK_QUERY.replace('\n', '\n    |') + '";' + code[end:]
    report.write_text(code)


STOCK_QUERY = '''ВЫБРАТЬ Д.Организация, Д.Склад, Д.Номенклатура КАК Продукция,
Д.Номенклатура.ЕдиницаИзмерения КАК Единица,
СУММА(Д.НаСкладе) КАК НаСкладе, СУММА(Д.Резерв) КАК ВРезерве,
СУММА(Д.НаСкладе) - СУММА(Д.Резерв) КАК Свободно
ИЗ (ВЫБРАТЬ Организация, Склад, Номенклатура, КоличествоОстаток КАК НаСкладе, 0 КАК Резерв
ИЗ РегистрНакопления.ОстаткиПродукции.Остатки(&Конец)
ОБЪЕДИНИТЬ ВСЕ ВЫБРАТЬ Организация, Склад, Номенклатура, 0, КоличествоОстаток
ИЗ РегистрНакопления.РезервыПродукции.Остатки(&Конец)) КАК Д
ГДЕ (&ВсеОрганизации ИЛИ Д.Организация = &Организация)
И (&ВсеСклады ИЛИ Д.Склад = &Склад)
СГРУППИРОВАТЬ ПО Д.Организация, Д.Склад, Д.Номенклатура, Д.Номенклатура.ЕдиницаИзмерения
УПОРЯДОЧИТЬ ПО Организация, Склад, Продукция'''


DELETE_GUARD = """
Процедура ПередУдалением(Отказ)
    Если Проведен Тогда
        ВызватьИсключение "Сначала отмените проведение документа.";
    КонецЕсли;
КонецПроцедуры
"""
