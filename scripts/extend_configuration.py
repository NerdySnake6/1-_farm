"""Add application modules, managed forms, reports, roles and demo tools."""
import build_configuration as base
import ui_forms
import reservation_extension

ROOT = base.ROOT
OUT = base.OUT
FORM_HEADER = base.HEADER.replace('xmlns="http://v8.1c.ru/8.3/MDClasses"', 'xmlns="http://v8.1c.ru/8.3/xcf/logform"').replace('<MetaDataObject', '<Form')
EXTRA = []


def write(relative, text):
    """Write a UTF-8 configuration source file."""
    path = OUT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def add_form(folder, owner, main_type, code, events=None):
    """Attach a managed main form to an object."""
    ownerpath = OUT / folder / (owner + '.xml')
    source = ownerpath.read_text()
    default = 'DefaultObjectForm' if folder in ['Catalogs','Documents'] else 'DefaultForm'
    kind = {'Catalogs':'Catalog','Documents':'Document','Reports':'Report','DataProcessors':'DataProcessor'}[folder]
    source = source.replace('</Properties><ChildObjects>', f'<{default}>{kind}.{owner}.Form.Форма</{default}></Properties><ChildObjects>',1)
    source = source.replace('</ChildObjects></'+kind+'>','<Form>Форма</Form></ChildObjects></'+kind+'>')
    ownerpath.write_text(source)
    write(f'{folder}/{owner}/Forms/Форма.xml',base.HEADER+f'<Form uuid="{base.uid(owner+"form")}"><Properties><Name>Форма</Name><Synonym/><Comment/><FormType>Managed</FormType><IncludeHelpInContents>false</IncludeHelpInContents></Properties></Form></MetaDataObject>')
    attrs = ''
    if main_type:
        attrs = f'<Attributes><Attribute name="Объект" id="1"><Type><v8:Type>{main_type}</v8:Type></Type><MainAttribute>true</MainAttribute></Attribute></Attributes>'
    extra_attrs = [('АдресФото','xs:string')] if folder=='Catalogs' else ([('НачалоПериода','xs:dateTime'),('КонецПериода','xs:dateTime'),('ОтборОрганизация','cfg:CatalogRef.Организации'),('ОтборСклад','cfg:CatalogRef.Склады'),('РезультатОтчета','v8:SpreadsheetDocument')] if folder=='Reports' else ([('ИтогоДокумента','xs:decimal')] if folder=='Documents' else []))
    if extra_attrs:
        attrs = attrs.replace('</Attributes>', '') or '<Attributes>'
        for index,(name,value_type) in enumerate(extra_attrs, 10):
            attrs += f'<Attribute name="{name}" id="{index}"><Type><v8:Type>{value_type}</v8:Type></Type></Attribute>'
        attrs += '</Attributes>'
    event_nodes = '<Events>' + ''.join(f'<Event name="{name}">{handler}</Event>' for name,handler in (events or {'OnCreateAtServer':'ПриСозданииНаСервере'}).items()) + '</Events>'
    write(f'{folder}/{owner}/Forms/Форма/Ext/Form.xml',FORM_HEADER+'<AutoCommandBar name="ФормаКоманднаяПанель" id="-1"/>'+event_nodes+attrs+'</Form>')
    write(f'{folder}/{owner}/Forms/Форма/Ext/Form/Module.bsl',code)


FORM_HELPERS = '''
&НаСервере
Процедура ДобавитьПоле(Имя, Путь, Заголовок, Родитель = Неопределено)
    Поле = Элементы.Добавить(Имя, Тип("ПолеФормы"), Родитель);
    Поле.Вид = ВидПоляФормы.ПолеВвода;
    Поле.ПутьКДанным = Путь;
    Поле.Заголовок = Заголовок;
КонецПроцедуры

&НаСервере
Процедура ДобавитьКнопку(Имя, Заголовок, Родитель = Неопределено)
    Команда = Команды.Добавить(Имя);
    Команда.Заголовок = Заголовок;
    Команда.Действие = Имя;
    Кнопка = Элементы.Добавить(Имя, Тип("КнопкаФормы"), Родитель);
    Кнопка.ИмяКоманды = Имя;
    Кнопка.ЦветФона = Новый Цвет(47, 107, 79);
    Кнопка.ЦветТекста = Новый Цвет(255, 255, 255);
    Если Имя = "УдалитьСтроку" Или Имя = "СброситьОтборы"
        Или Имя = "ОткрытьПриходы" Или Имя = "ОткрытьРасходы" Тогда
        Кнопка.ЦветФона = Новый Цвет(230, 239, 231);
        Кнопка.ЦветТекста = Новый Цвет(32, 56, 44);
    КонецЕсли;
КонецПроцедуры
'''


def add_documents():
    """Add validation, register movements and price-aware document forms."""
    for name in ['Приход', 'Расход']:
        direction = 'Приход' if name == 'Приход' else 'Расход'
        counterparty = 'Поставщик' if name == 'Приход' else 'Покупатель'
        module = f'''Процедура ПередЗаписью(Отказ, РежимЗаписи, РежимПроведения)
    Если РежимЗаписи = РежимЗаписиДокумента.ОтменаПроведения Тогда
        Возврат;
    КонецЕсли;
    Если Не ЗначениеЗаполнено(Организация) Или Не ЗначениеЗаполнено(Склад)
        Или Не ЗначениеЗаполнено({counterparty}) Тогда
        Отказ = Истина;
        Сообщить("Заполните организацию, склад и контрагента.");
    КонецЕсли;
    Если Товары.Количество() = 0 Тогда
        Отказ = Истина;
        Сообщить("Добавьте продукцию в документ.");
    КонецЕсли;
    Для Каждого СтрокаТовара Из Товары Цикл
        Если Не ЗначениеЗаполнено(СтрокаТовара.Номенклатура)
            Или СтрокаТовара.Количество <= 0 Или СтрокаТовара.Цена <= 0 Тогда
            Отказ = Истина;
            Сообщить("В каждой строке укажите продукцию, положительное количество и цену.");
        КонецЕсли;
        СтрокаТовара.Сумма = Окр(СтрокаТовара.Количество * СтрокаТовара.Цена, 2);
    КонецЦикла;
КонецПроцедуры

Процедура ОбработкаПроведения(Отказ, РежимПроведения)
    Движения.ОстаткиПродукции.Записывать = Истина;
    Движения.ОстаткиПродукции.Очистить();
    Движения.ОстаткиПродукции.БлокироватьДляИзменения = Истина;
    Для Каждого СтрокаТовара Из Товары Цикл
        Движение = Движения.ОстаткиПродукции.Добавить();
        Движение.ВидДвижения = ВидДвиженияНакопления.{direction};
        Движение.Период = Дата;
        Движение.Организация = Организация;
        Движение.Склад = Склад;
        Движение.Номенклатура = СтрокаТовара.Номенклатура;
        Движение.Количество = СтрокаТовара.Количество;
    КонецЦикла;
    Движения.ОстаткиПродукции.Записать();
    УчетФермы.ПроверитьОстатки(Организация, Склад, Отказ);
КонецПроцедуры

Процедура ОбработкаУдаленияПроведения(Отказ)
    Движения.ОстаткиПродукции.Записывать = Истина;
    Движения.ОстаткиПродукции.Очистить();
    Движения.ОстаткиПродукции.БлокироватьДляИзменения = Истина;
    Движения.ОстаткиПродукции.Записать();
    УчетФермы.ПроверитьОстатки(Организация, Склад, Отказ);
КонецПроцедуры
'''
        write(f'Documents/{name}/Ext/ObjectModule.bsl',module)
        form = f'''&НаСервере
Процедура ПриСозданииНаСервере(Отказ, СтандартнаяОбработка)
    ЦветФона = Новый Цвет(248, 246, 238);
    ДобавитьПоле("Дата", "Объект.Дата", "Дата");
    ДобавитьПоле("Организация", "Объект.Организация", "Организация");
    ДобавитьПоле("Склад", "Объект.Склад", "Склад");
    ДобавитьПоле("{counterparty}", "Объект.{counterparty}", "{counterparty}");
    Таблица = Элементы.Добавить("Товары", Тип("ТаблицаФормы"));
    Таблица.ПутьКДанным = "Объект.Товары";
    ДобавитьПоле("ТоварыНоменклатура", "Объект.Товары.Номенклатура", "Продукция", Таблица);
    ДобавитьПоле("ТоварыКоличество", "Объект.Товары.Количество", "Количество", Таблица);
    ДобавитьПоле("ТоварыЦена", "Объект.Товары.Цена", "Цена, руб.", Таблица);
    ДобавитьПоле("ТоварыСумма", "Объект.Товары.Сумма", "Сумма, руб.", Таблица);
    Элементы.ТоварыСумма.ТолькоПросмотр = Истина;
    Элементы.ТоварыНоменклатура.УстановитьДействие("ПриИзменении", "ПродукцияПриИзменении");
    Элементы.ТоварыКоличество.УстановитьДействие("ПриИзменении", "СтрокаПриИзменении");
    Элементы.ТоварыЦена.УстановитьДействие("ПриИзменении", "СтрокаПриИзменении");
КонецПроцедуры

&НаКлиенте
Процедура СтрокаПриИзменении(Элемент)
    СтрокаТовара = Элементы.Товары.ТекущиеДанные;
    Если СтрокаТовара <> Неопределено Тогда
        СтрокаТовара.Сумма = Окр(СтрокаТовара.Количество * СтрокаТовара.Цена, 2);
    КонецЕсли;
КонецПроцедуры

&НаКлиенте
Процедура ПродукцияПриИзменении(Элемент)
    СтрокаТовара = Элементы.Товары.ТекущиеДанные;
    Если СтрокаТовара <> Неопределено Тогда
        СтрокаТовара.Цена = ЦенаПродукции(Объект.Дата, СтрокаТовара.Номенклатура);
        СтрокаПриИзменении(Элемент);
    КонецЕсли;
КонецПроцедуры

&НаСервереБезКонтекста
Функция ЦенаПродукции(ДатаДокумента, Номенклатура)
    Возврат УчетФермы.ПолучитьЦену(ДатаДокумента, Номенклатура);
КонецФункции
''' + FORM_HELPERS
        add_form('Documents',name,f'cfg:DocumentObject.{name}',ui_forms.enhance_document(name, form))


COMMON = '''Процедура ПроверитьОстатки(Организация, Склад, Отказ) Экспорт
    Запрос = Новый Запрос;
    Запрос.Текст = "ВЫБРАТЬ Номенклатура, КоличествоОстаток
    |ИЗ РегистрНакопления.ОстаткиПродукции.Остатки(,
    |Организация = &Организация И Склад = &Склад)
    |ГДЕ КоличествоОстаток < 0";
    Запрос.УстановитьПараметр("Организация", Организация);
    Запрос.УстановитьПараметр("Склад", Склад);
    Выборка = Запрос.Выполнить().Выбрать();
    Пока Выборка.Следующий() Цикл
        Отказ = Истина;
        Сообщить("Недостаточно продукции: " + Строка(Выборка.Номенклатура)
            + ". Нехватка: " + Строка(-Выборка.КоличествоОстаток));
    КонецЦикла;
КонецПроцедуры

Функция ПолучитьЦену(ДатаДокумента, Номенклатура) Экспорт
    Запрос = Новый Запрос;
    Запрос.Текст = "ВЫБРАТЬ Цена ИЗ РегистрСведений.Цены.СрезПоследних(&Дата,
    |Номенклатура = &Номенклатура)";
    Запрос.УстановитьПараметр("Дата", КонецДня(ДатаДокумента));
    Запрос.УстановитьПараметр("Номенклатура", Номенклатура);
    Выборка = Запрос.Выполнить().Выбрать();
    Если Выборка.Следующий() Тогда
        Возврат Выборка.Цена;
    КонецЕсли;
    Возврат 0;
КонецФункции
'''

PHOTO_FORM = '''&НаСервере
Процедура ПриСозданииНаСервере(Отказ, СтандартнаяОбработка)
    Заголовок = "Карточка продукции";
    АвтоЗаголовок = Ложь;
    ЦветФона = Новый Цвет(248, 246, 238);
    ДобавитьПоле("Наименование", "Объект.Наименование", "Продукция");
    ДобавитьПоле("ЕдиницаИзмерения", "Объект.ЕдиницаИзмерения", "Единица измерения");
    Фото = Элементы.Добавить("Фото", Тип("ПолеФормы"));
    Фото.Вид = ВидПоляФормы.ПолеКартинки;
    Фото.ПутьКДанным = "АдресФото";
    Фото.Ширина = 40;
    Фото.Высота = 15;
    Фото.РазмерКартинки = РазмерКартинки.Пропорционально;
    ДобавитьКнопку("ЗагрузитьФото", "Загрузить фотографию");
    Если ЗначениеЗаполнено(Объект.Ссылка) Тогда
        АдресФото = ПолучитьНавигационнуюСсылку(Объект.Ссылка, "Фотография");
    КонецЕсли;
КонецПроцедуры

&НаКлиенте
Процедура ЗагрузитьФото(Команда)
    НачатьПомещениеФайла(Новый ОписаниеОповещения("ПослеЗагрузкиФото", ЭтаФорма), , , Истина, УникальныйИдентификатор);
КонецПроцедуры

&НаКлиенте
Процедура ПослеЗагрузкиФото(Результат, Адрес, ВыбранноеИмяФайла, ДополнительныеПараметры) Экспорт
    Если Результат Тогда
        АдресФото = Адрес;
        Модифицированность = Истина;
    КонецЕсли;
КонецПроцедуры

&НаСервере
Процедура ПередЗаписьюНаСервере(Отказ, ТекущийОбъект, ПараметрыЗаписи)
    Если ЭтоАдресВременногоХранилища(АдресФото) Тогда
        ТекущийОбъект.Фотография = Новый ХранилищеЗначения(ПолучитьИзВременногоХранилища(АдресФото));
    КонецЕсли;
КонецПроцедуры
''' + FORM_HELPERS


def add_reports():
    """Create two reports with editable period fields and spreadsheet output."""
    for name, label in [('ОстаткиПродукции','Остатки продукции'),('ПродажиЗаПериод','Продажи за период')]:
        info = base.internal('Report',name,['Object','Manager'])
        EXTRA.append(base.obj('Report',name,'<UseStandardCommands>true</UseStandardCommands>',synonym=label,info=info))
        code = ui_forms.report_module(name, label) + FORM_HELPERS
        add_form('Reports',name,None,code)


def add_roles():
    """Create explicit rights for purchase, sales and administrator roles."""
    for role in ['Покупка','Продажа','ПолныеПрава']:
        EXTRA.append(base.obj('Role',role,synonym='Полные права' if role=='ПолныеПрава' else role))
        rights = '<?xml version="1.0" encoding="UTF-8"?><Rights xmlns="http://v8.1c.ru/8.2/roles" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="2.20"><setForNewObjects>false</setForNewObjects><setForAttributesByDefault>true</setForAttributesByDefault><independentRightsOfChildObjects>false</independentRightsOfChildObjects>'
        def grant(ref, names):
            """Serialize explicitly granted rights for one metadata object."""
            return '<object><name>'+ref+'</name>'+''.join('<right><name>'+n+'</name><value>true</value></right>' for n in names)+'</object>'
        platform = ['ThinClient','ThickClient','WebClient','Output','MainWindowModeNormal']
        if role=='ПолныеПрава':
            platform += ['Administration','DataAdministration','ActiveUsers','EventLog','AllFunctionsMode','ExternalConnection']
        rights += grant('Configuration.МолочнаяФерма',platform)
        for sub in ['Покупка','Продажа']:
            if sub==role or role=='ПолныеПрава':
                rights += grant('Subsystem.'+sub,['View'])
        for cat in ['Номенклатура','Организации','Склады','Поставщики','Покупатели']:
            names = ['Read','View','InputByString']
            if role=='ПолныеПрава' or (role=='Покупка' and cat in ['Номенклатура','Поставщики']) or (role=='Продажа' and cat=='Покупатели'):
                names += ['Insert','Update','Edit','InteractiveInsert','InteractiveSetDeletionMark','InteractiveClearDeletionMark']
            if role=='ПолныеПрава':
                names += ['Delete','InteractiveDelete']
            rights += grant('Catalog.'+cat,names)
        for doc, owner in [('Приход','Покупка'),('Расход','Продажа')]:
            if role in [owner,'ПолныеПрава']:
                rights += grant('Document.'+doc,['Read','View','Insert','Update','Edit','Posting','UndoPosting','InteractiveInsert','InteractivePosting','InteractivePostingRegular','InteractiveUndoPosting','InteractiveSetDeletionMark','InteractiveClearDeletionMark'] + (['Delete','InteractiveDelete'] if role=='ПолныеПрава' else []))
        rights += grant('CommonForm.РабочийСтол',['View'])
        for section in ['Покупка', 'Продажа']:
            if role in [section, 'ПолныеПрава']:
                rights += grant('CommonForm.Панель' + section, ['View'])
        rights += grant('InformationRegister.Цены',['Read','View']+(['Update','Edit'] if role in ['Покупка','ПолныеПрава'] else []))
        rights += grant('AccumulationRegister.ОстаткиПродукции',['Read','View','Update'])
        rights += grant('Report.ОстаткиПродукции',['Use','View'])
        if role in ['Продажа','ПолныеПрава']:
            rights += grant('Report.ПродажиЗаПериод',['Use','View'])
        rights += '</Rights>'
        write(f'Roles/{role}/Ext/Rights.xml',rights)


def build():
    """Build the complete metadata tree."""
    base.build()
    EXTRA.clear()
    EXTRA.append(base.obj('CommonModule','УчетФермы','<Global>false</Global><ClientManagedApplication>false</ClientManagedApplication><Server>true</Server><ExternalConnection>true</ExternalConnection><ClientOrdinaryApplication>false</ClientOrdinaryApplication><ServerCall>false</ServerCall><Privileged>false</Privileged><ReturnValuesReuse>DontUse</ReturnValuesReuse>'))
    write('CommonModules/УчетФермы/Ext/Module.bsl',COMMON)
    EXTRA.append(base.obj('CommonModule','СервисФермы','<Global>false</Global><ClientManagedApplication>false</ClientManagedApplication><Server>true</Server><ExternalConnection>false</ExternalConnection><ClientOrdinaryApplication>false</ClientOrdinaryApplication><ServerCall>true</ServerCall><Privileged>false</Privileged><ReturnValuesReuse>DontUse</ReturnValuesReuse>'))
    write('CommonModules/СервисФермы/Ext/Module.bsl', (ROOT/'scripts/bsl/СервисФермы.bsl').read_text() + '\n' + (ROOT/'scripts/bsl/БронированиеТесты.bsl').read_text())
    application = (ROOT/'scripts/bsl/ManagedApplicationModule.bsl').read_text()
    application = application.replace('        СервисФермы.ПроверитьБронирование(Сред(ПараметрЗапуска, 22));', '        СервисФермы.ПроверитьБронирование(Сред(ПараметрЗапуска, 22));\n' + (ROOT/'scripts/bsl/БронированиеПроверкаФорм.bsl').read_text())
    write('Ext/ManagedApplicationModule.bsl', application)
    add_documents()
    add_form('Catalogs','Номенклатура','cfg:CatalogObject.Номенклатура',PHOTO_FORM,{'OnCreateAtServer':'ПриСозданииНаСервере','BeforeWriteAtServer':'ПередЗаписьюНаСервере'})
    add_reports()
    add_roles()
    EXTRA.append(base.obj('CommonForm','РабочийСтол','<FormType>Managed</FormType><IncludeHelpInContents>false</IncludeHelpInContents><UseStandardCommands>true</UseStandardCommands>',synonym='Рабочий стол фермы'))
    home_events = '<Events><Event name="OnCreateAtServer">ПриСозданииНаСервере</Event></Events>'
    write('CommonForms/РабочийСтол/Ext/Form.xml',FORM_HEADER+'<AutoCommandBar name="ФормаКоманднаяПанель" id="-1"/>'+home_events+'</Form>')
    write('CommonForms/РабочийСтол/Ext/Form/Module.bsl',ui_forms.HOME_MODULE + FORM_HELPERS)
    EXTRA.append(base.obj('Style','Луговой',synonym='Луговой'))
    for name in ['Покупка','Продажа']:
        p=OUT/'Subsystems'/f'{name}.xml'
        s=p.read_text()
        form_name = 'Панель' + name
        EXTRA.append(base.obj('CommonForm', form_name, '<FormType>Managed</FormType><IncludeHelpInContents>false</IncludeHelpInContents><UseStandardCommands>true</UseStandardCommands>', synonym=name + ' продукции'))
        write(f'CommonForms/{form_name}/Ext/Form.xml', FORM_HEADER + '<AutoCommandBar name="ФормаКоманднаяПанель" id="-1"/>' + home_events + '</Form>')
        write(f'CommonForms/{form_name}/Ext/Form/Module.bsl', ui_forms.section_module(name) + FORM_HELPERS)
        s = s.replace('<UseOneCommand>false</UseOneCommand>', '<UseOneCommand>true</UseOneCommand>')
        content_start = s.index('<Content>')
        content_end = s.index('</Content>', content_start) + len('</Content>')
        s = s[:content_start] + f'<Content><xr:Item xsi:type="xr:MDObjectRef">CommonForm.{form_name}</xr:Item></Content>' + s[content_end:]
        p.write_text(s)
        interface = OUT / 'Subsystems' / name / 'Ext' / 'CommandInterface.xml'
        interface.unlink(missing_ok=True)
    p=OUT/'Configuration.xml'
    s=p.read_text().replace('</ChildObjects>', ''.join(EXTRA)+'</ChildObjects>',1)
    s=s.replace('<Version>1.0.0</Version>', '<Version>1.1.1</Version>')
    s=s.replace('<DefaultStyle/>', '<DefaultStyle>Style.Луговой</DefaultStyle>')
    s=s.replace('<DefaultRoles/>','<DefaultRoles><xr:Item xsi:type="xr:MDObjectRef">Role.ПолныеПрава</xr:Item></DefaultRoles>')
    p.write_text(s)
    reservation_extension.install(__import__(__name__))

if __name__=='__main__':
    build()
