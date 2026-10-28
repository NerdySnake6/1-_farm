"""Generate the dairy farm configuration in the native Designer XML format."""
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL
from xml.sax.saxutils import escape
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'configuration'
HEADER = (ROOT / 'scripts/templates/Configuration.xml').read_text(encoding='utf-8-sig').split('<Configuration uuid=')[0]


def uid(name):
    """Return a stable identifier for a metadata object."""
    return str(uuid5(NAMESPACE_URL, 'dairy-farm-1c/' + name))


def syn(text):
    """Serialize a Russian localized string."""
    return '<v8:item><v8:lang>ru</v8:lang><v8:content>' + escape(text) + '</v8:content></v8:item>'


def prop(name, value):
    """Serialize a metadata property."""
    return f'<{name}>{value}</{name}>'


def obj(kind, name, properties='', children='', synonym=None, info=''):
    """Write a top-level metadata object and return its reference."""
    folder = {'Catalog':'Catalogs', 'Document':'Documents', 'Subsystem':'Subsystems', 'InformationRegister':'InformationRegisters', 'AccumulationRegister':'AccumulationRegisters', 'Role':'Roles', 'CommonModule':'CommonModules', 'Report':'Reports', 'Style':'Styles', 'CommonForm':'CommonForms'}[kind]
    path = OUT / folder / (name + '.xml')
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind in ('Catalog', 'Document', 'InformationRegister', 'AccumulationRegister'):
        cats = ['Object', 'Ref', 'Selection', 'List', 'Manager'] if kind in ('Catalog', 'Document') else ['Record', 'Selection', 'List', 'RecordSet', 'RecordKey', 'Manager']
        if kind == 'InformationRegister':
            cats.append('RecordManager')
        info = internal(kind, name, cats)
    body = f'<{kind} uuid="{uid(kind+name)}">{info}<Properties><Name>{name}</Name><Synonym>{syn(synonym or name)}</Synonym><Comment/>{properties}</Properties>'
    if kind not in ('Role', 'Style', 'CommonModule', 'CommonForm'):
        body += '<ChildObjects>' + children + '</ChildObjects>'
    path.write_text(HEADER + body + f'</{kind}></MetaDataObject>', encoding='utf-8')
    return prop(kind, name)


def internal(kind, name, categories):
    """Serialize stable generated runtime type identities."""
    return '<InternalInfo>' + ''.join(f'<xr:GeneratedType name="{kind}{cat}.{name}" category="{cat}"><xr:TypeId>{uid(kind+name+cat+"type")}</xr:TypeId><xr:ValueId>{uid(kind+name+cat+"value")}</xr:ValueId></xr:GeneratedType>' for cat in categories) + '</InternalInfo>'


def typ(value):
    """Serialize a value type and its qualifiers."""
    if value == 'number':
        return '<v8:Type>xs:decimal</v8:Type><v8:NumberQualifiers><v8:Digits>15</v8:Digits><v8:FractionDigits>3</v8:FractionDigits><v8:AllowedSign>Any</v8:AllowedSign></v8:NumberQualifiers>'
    if value == 'money':
        return '<v8:Type>xs:decimal</v8:Type><v8:NumberQualifiers><v8:Digits>15</v8:Digits><v8:FractionDigits>2</v8:FractionDigits><v8:AllowedSign>Any</v8:AllowedSign></v8:NumberQualifiers>'
    if value == 'string':
        return '<v8:Type>xs:string</v8:Type><v8:StringQualifiers><v8:Length>200</v8:Length><v8:AllowedLength>Variable</v8:AllowedLength></v8:StringQualifiers>'
    return '<v8:Type>' + value + '</v8:Type>'


def attr(parent, name, value, kind='Attribute', label=None, extra=''):
    """Serialize an attribute, register dimension or resource."""
    return f'<{kind} uuid="{uid(parent+name)}"><Properties><Name>{name}</Name><Synonym>{syn(label or name)}</Synonym><Comment/><Type>{typ(value)}</Type>{extra}</Properties></{kind}>'


def build():
    """Create the configuration and all required metadata objects."""
    shutil.copytree(ROOT / 'scripts/templates/Languages', OUT / 'Languages', dirs_exist_ok=True)
    children = prop('Language', 'Русский')
    catalogs = {'Номенклатура':[('ЕдиницаИзмерения','string'),('Фотография','v8:ValueStorage')], 'Покупатели':[('Телефон','string')], 'Организации':[('ИНН','string')], 'Поставщики':[('Телефон','string')], 'Склады':[]}
    for name, attrs in catalogs.items():
        children += obj('Catalog',name,'<Hierarchical>false</Hierarchical><CodeLength>9</CodeLength><DescriptionLength>100</DescriptionLength><CodeType>String</CodeType><CodeAllowedLength>Variable</CodeAllowedLength><Autonumbering>true</Autonumbering><CheckUnique>true</CheckUnique><DefaultPresentation>AsDescription</DefaultPresentation><EditType>InDialog</EditType>', ''.join(attr(name,n,t) for n,t in attrs))
    for name in ['Приход','Расход']:
        attrs = [('Организация','cfg:CatalogRef.Организации'),('Склад','cfg:CatalogRef.Склады'),('Поставщик' if name=='Приход' else 'Покупатель','cfg:CatalogRef.'+('Поставщики' if name=='Приход' else 'Покупатели'))]
        tabattrs = [('Номенклатура','cfg:CatalogRef.Номенклатура'),('Количество','number'),('Цена','money'),('Сумма','money')]
        tab = f'<TabularSection uuid="{uid(name+"Товары")}">{internal("DocumentTabularSection",name+".Товары",["TabularSection","TabularSectionRow"])}<Properties><Name>Товары</Name><Synonym>{syn("Продукция")}</Synonym></Properties><ChildObjects>' + ''.join(attr(name+'Товары',n,t) for n,t in tabattrs) + '</ChildObjects></TabularSection>'
        children += obj('Document',name,'<NumberType>String</NumberType><NumberLength>9</NumberLength><NumberAllowedLength>Variable</NumberAllowedLength><Autonumbering>true</Autonumbering><CheckUnique>true</CheckUnique><NumberPeriodicity>Year</NumberPeriodicity><Posting>Allow</Posting><RealTimePosting>Deny</RealTimePosting><RegisterRecords><xr:Item xsi:type="xr:MDObjectRef">AccumulationRegister.ОстаткиПродукции</xr:Item></RegisterRecords>', ''.join(attr(name,n,t) for n,t in attrs)+tab)
    dims = ''.join(attr('Цены',n,t,'Dimension') for n,t in [('Номенклатура','cfg:CatalogRef.Номенклатура')])
    children += obj('InformationRegister','Цены','<InformationRegisterPeriodicity>Day</InformationRegisterPeriodicity><WriteMode>Independent</WriteMode><MainFilterOnPeriod>true</MainFilterOnPeriod>',dims+attr('Цены','Цена','money','Resource'))
    dims = ''.join(attr('Остатки',n,t,'Dimension') for n,t in [('Организация','cfg:CatalogRef.Организации'),('Склад','cfg:CatalogRef.Склады'),('Номенклатура','cfg:CatalogRef.Номенклатура')])
    children += obj('AccumulationRegister','ОстаткиПродукции','<RegisterType>Balance</RegisterType><EnableTotalsSplitting>true</EnableTotalsSplitting>',dims+attr('Остатки','Количество','number','Resource'),synonym='Остатки продукции')
    for name, document in [('Покупка','Приход'),('Продажа','Расход')]:
        content = [f'Document.{document}', 'Catalog.Номенклатура','Catalog.Организации','Catalog.Склады','InformationRegister.Цены','AccumulationRegister.ОстаткиПродукции','Catalog.'+('Поставщики' if name=='Покупка' else 'Покупатели')]
        children += obj('Subsystem',name,'<IncludeHelpInContents>false</IncludeHelpInContents><IncludeInCommandInterface>true</IncludeInCommandInterface><UseOneCommand>false</UseOneCommand><Content>'+''.join('<xr:Item xsi:type="xr:MDObjectRef">'+v+'</xr:Item>' for v in content)+'</Content>')
    config = (ROOT / 'scripts/templates/Configuration.xml').read_text(encoding='utf-8-sig')
    config = config.replace('<Name>Конфигурация</Name>', '<Name>МолочнаяФерма</Name>',1).replace('<Synonym/>','<Synonym>'+syn('Молочная ферма')+'</Synonym>',1).replace('<Version/>','<Version>1.0.0</Version>',1)
    start=config.index('<ChildObjects>'); end=config.index('</ChildObjects>',start)+len('</ChildObjects>')
    config=config[:start]+'<ChildObjects>'+children+'</ChildObjects>'+config[end:]
    (OUT / 'Configuration.xml').write_text(config,encoding='utf-8')

if __name__ == '__main__':
    build()
