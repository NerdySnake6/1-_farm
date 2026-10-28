/** Build the complete dairy farm project presentation in its established style. */
import fs from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const modules = process.env.RUNTIME_NODE_MODULES;
if (!modules) throw new Error('Set RUNTIME_NODE_MODULES to the bundled packages.');
const require = createRequire(path.join(modules, '__runtime__.js'));
const { Presentation, PresentationFile, FileBlob } = await import(pathToFileURL(require.resolve('@oai/artifact-tool')).href);
const facts = JSON.parse(await fs.readFile(path.join(root, 'scripts/documentation_facts.json'), 'utf8'));
const skill = process.env.PRESENTATIONS_SKILL_DIR ?? '/Users/nerdysnake6/.codex/plugins/cache/openai-primary-runtime/presentations/26.1020.11127/skills/presentations';
const { finalizePresentation } = await import(pathToFileURL(path.join(skill, 'container_tools/artifact_tool_utils.mjs')).href);
const build = path.join(root, '.build/documentation/presentation');
const output = path.join(root, 'Документация/05_Презентация/Презентация_проекта.pptx');
const reference = path.join(root, 'assets/templates/Презентация_основа.pptx');
await fs.mkdir(build, { recursive: true });
const deck = Presentation.create({ slideSize: { width: 1280, height: 720 } });
const colors = { green:'#2F6B4F', dark:'#20382C', cream:'#F8F6EE', pale:'#E6EFE7', gray:'#5F6D63', white:'#FFFFFF' };

function text(slide, value, x, y, width, height, size=28, color=colors.dark, bold=false) {
  const shape = slide.shapes.add({ geometry:'textbox', position:{left:x,top:y,width,height}, fill:'none', line:{fill:'none',width:0} });
  shape.text=value;
  shape.text.style={typeface:'Arial',fontSize:size,color,bold};
  return shape;
}
function slide(title, number) {
  const item=deck.slides.add();
  item.background.fill=colors.cream;
  text(item,title,72,60,1140,100,44,colors.dark,true);
  text(item,`Молочная ферма Луговая · версия ${facts.configuration_version}`,72,675,1050,24,16,colors.gray);
  text(item,`${number} / 11`,1130,675,100,24,16,colors.gray);
  return item;
}
function table(item,values,x,y,width,height,widths) {
  const result=item.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,columnWidths:widths,values});
  for (let r=0;r<values.length;r++) for(let c=0;c<values[r].length;c++) {
    const cell=result.getCell(r,c);
    cell.fill=r===0?colors.green:(r%2===0?colors.pale:colors.white);
    cell.text.style={typeface:'Arial',fontSize:26,color:r===0?colors.white:colors.dark,bold:r===0};
  }
  result.borders.assign({style:'solid',fill:'#CED8D0',width:1});
  return result;
}

async function picture(item, file, x, y, width, height, alt, crop) {
  const bytes = await fs.readFile(path.join(root, file));
  return item.images.add({ blob: bytes, contentType: 'image/png', alt,
    fit: crop ? 'cover' : 'contain', position: { left:x, top:y, width, height },
    ...(crop ? { crop } : {}) });
}
function pair(item, heading, body, x, y, width=500) {
  text(item,heading,x,y,width,50,31,colors.green,true);
  text(item,body,x,y+62,width,130,27);
}

const cover=deck.slides.add();
cover.background.fill=colors.dark;
text(cover,'ПРОЕКТ НА ПЛАТФОРМЕ 1С',72,58,690,40,21,colors.pale);
text(cover,'Молочная ферма\nЛуговая',72,170,740,180,65,colors.white,true);
text(cover,'Учёт готовой молочной продукции\nи бронирование для покупателей',76,390,700,110,31,colors.pale);
text(cover,facts.author,76,565,710,45,26,colors.white);
text(cover,`Версия ${facts.configuration_version}     2026`,76,625,700,32,21,colors.pale);
await picture(cover,'assets/milk.png',855,80,350,535,'Учебное изображение молока из карточки продукции');

const purpose=slide('Назначение системы',2);
text(purpose,'Поступления и продажи в одной базе',75,175,620,115,43,colors.green,true);
text(purpose,'Сотрудник оформляет документы, а система рассчитывает суммы и доступное количество продукции.',75,320,615,150,30);
text(purpose,'Молоко учитывается в литрах.\nТворог и сметана в килограммах.',75,515,620,90,28);
await picture(purpose,'assets/curd.png',755,185,205,270,'Учебное изображение творога');
await picture(purpose,'assets/cream.png',990,185,205,270,'Учебное изображение сметаны');
text(purpose,'Творог 9%',755,475,220,40,26,colors.green,true);
text(purpose,'Сметана 20%',990,475,225,40,26,colors.green,true);
text(purpose,'Фотографии хранятся в карточках продукции',755,555,455,75,24,colors.gray);

const structure=slide('Структура конфигурации',3);
table(structure,[['Объекты','Назначение'],['5 справочников','Продукция, контрагенты, организации и склады'],['3 документа','Приход, Расход, Бронирование'],['Регистр сведений','Цены продукции по датам'],['2 регистра накопления','ОстаткиПродукции и РезервыПродукции']],75,190,1125,340,[395,730]);
text(structure,'Разделы Покупка и Продажа объединяют команды по задачам сотрудника.',75,575,1125,65,29);

const desktop=slide('Рабочий стол и оформление',4);
await picture(desktop,'assets/screenshots/Рабочий_стол.png',170,180,940,370,'Реальный рабочий стол ранней версии до добавления бронирования',{left:0.018,top:0.375,right:0.16,bottom:0.205});
text(desktop,'Зелёный акцент выделяет основные действия. Журналы имеют светлый фон.',75,565,1120,48,27);
text(desktop,'Снимок до добавления бронирования. Стандартные панели 1С сохраняют оформление платформы.',75,625,1120,35,18,colors.gray);

const accounting=slide('Поступление и продажа продукции',5);
text(accounting,'Документ Приход увеличивает складской остаток. Расход уменьшает его.',75,165,1120,70,29);
table(accounting,[['Продукция','Приход','Продажа','Остаток'],['Молоко 3,2%', '100 л','25 л','75 л'],['Творог 9%','20 кг','5 кг','15 кг'],['Сметана 20%','15 кг','3 кг','12 кг']],75,270,1125,260,[435,230,230,230]);
text(accounting,'4 890 руб.',75,565,430,65,48,colors.green,true);
text(accounting,'Сумма продажи по ценам 90, 360 и 280 руб. за единицу',530,570,670,75,26);

const reports=slide('Отчёты и контроль результата',6);
await picture(reports,'assets/screenshots/Остатки.png',75,220,1125,123.3,'Реальный фрагмент отчёта ранней версии со складскими остатками',{left:0,top:0.59,right:0.075,bottom:0.18});
pair(reports,'Остатки продукции','Количество по организации, складу и товару. В версии 1.2.0 отдельно видны резерв и свободный остаток.',75,460,525);
pair(reports,'Продажи за период','Количество и сумма продаж с отбором по организации и складу.',675,460,525);
text(reports,'Снимок ранней версии иллюстрирует складские количества контрольного примера.',75,625,1120,30,18,colors.gray);

const booking=slide('Бронирование для покупателя',7);
text(booking,'Проведённая бронь исключает товар из свободных остатков.',75,165,1120,65,30);
table(booking,[['Молоко, л','На складе','В резерве','Свободно'],['До брони',75,0,75],['Бронь 20 л',75,20,55]],75,270,1125,230,[435,230,230,230]);
text(booking,'Свободно = На складе − В резерве',75,540,1120,60,38,colors.green,true);
text(booking,'Обычная продажа 56 л при свободных 55 л отклоняется.',75,610,1120,40,26);

const outcomes=slide('Продажа по брони или отмена',8);
text(outcomes,'Исходное состояние: на складе 75 л, в резерве 20 л, свободно 55 л',75,165,1120,60,27,colors.gray);
text(outcomes,'Продать по брони',75,265,535,50,34,colors.green,true);
text(outcomes,'Отменить бронь',670,265,535,50,34,colors.green,true);
table(outcomes,[['Склад','Резерв','Свободно'],[55,0,55]],75,345,535,135,[178,178,179]);
table(outcomes,[['Склад','Резерв','Свободно'],[75,0,75]],670,345,535,135,[178,178,179]);
text(outcomes,'Товар уходит покупателю.\nРасход использует резерв.',75,515,535,95,28);
text(outcomes,'Товар остаётся на складе.\nВсё количество снова свободно.',670,515,535,95,28);
text(outcomes,'Это альтернативные исходы одной брони. Повторная продажа запрещена.',75,625,1120,35,21,colors.gray);

const rights=slide('Роли и доступ к операциям',9);
table(rights,[['Возможность','Покупка','Продажа','Полные права'],['Поступления','Да','Нет','Да'],['Изменение цен','Да','Нет','Да'],['Продажи и брони','Нет','Да','Да'],['Просмотр остатков','Да','Да','Да']],75,215,1125,340,[465,200,210,250]);
text(rights,'Система проверяет обязательные поля, положительные цены и количество.',75,595,1125,55,28);

const validation=slide('Проверка конфигурации',10);
text(validation,'83',75,180,440,165,132,colors.green,true);
text(validation,'успешные автоматические проверки',75,365,490,90,31);
table(validation,[['Группа','Проверок'],['Учёт, формы и права',49],['Бронирование',28],['Новые команды формы',6]],650,195,550,285,[390,160]);
text(validation,'Сценарии повторены после восстановления базы из DT.',75,520,1120,50,28);
text(validation,'Автоматические проверки вызывают обработчики программно. Щелчки мышью и читаемость требуют ручной проверки.',75,595,1120,65,23,colors.gray);

const result=slide('Результат проекта и развитие',11);
pair(result,'Готовая система','Поступление и продажа продукции, хранение цен и фотографий, отчёты и бронирование.',75,180,530);
pair(result,'Материалы проекта','База DT, конфигурация CF и исходники. Отдельные документы Word и презентация PowerPoint.',675,180,530);
pair(result,'Следующие доработки','Учёт партий и сроков годности. Частичная продажа и срок действия брони.',75,405,530);
pair(result,'Границы версии','Бронь продаётся целиком. Учебная лицензия блокирует печать табличных документов.',675,405,530);

const notes=[
'0:00–0:15. Представляю проект «Молочная ферма Луговая». Это конфигурация на платформе 1С для учёта готовой молочной продукции. Автор проекта Калинин Игорь Вячеславович. Далее покажу назначение системы, её устройство, интерфейс и доработку бронирования. Источник: configuration/Configuration.xml, версия 1.2.0.',
'0:15–0:40. Система предназначена для сотрудников, которые принимают продукцию на склад и продают её покупателям. В примере используются молоко, творог и сметана. Для каждого товара хранится единица измерения и изображение. Количество и суммы рассчитываются по документам. Производство молока и учёт животных в текущий проект не входят. Источник: общая документация, разделы 1–2. Изображения assets/ созданы ImageGen для учебного проекта и не являются фотографиями реальной фермы.',
'0:40–1:05. Структура соответствует учебному заданию. Пять справочников содержат номенклатуру, покупателей, поставщиков, организации и склады. Документы Приход и Расход отражают движение продукции. Регистр сведений хранит цены по датам. В версии 1.2.0 добавлены документ Бронирование и регистр резервов. Команды распределены между двумя подсистемами, Покупкой и Продажей. Источник: configuration/, метаданные и модули.',
'1:05–1:30. На реальном снимке показан рабочий стол до добавления бронирования. Слева находятся документы, по центру продукция и цены, справа отчёты. Зелёный цвет выделяет основные действия, а светлый фон обозначает переходы к журналам. Фирменный стиль связан с тематикой фермы. Жёлтые системные панели определяет сама платформа 1С. Источник: assets/screenshots/Рабочий_стол.png, предоставлен пользователем. Снимок ранней версии.',
'1:30–2:00. На контрольном примере поступило 100 литров молока, 20 килограммов творога и 15 килограммов сметаны. После продажи 25, 5 и 3 единиц соответственно остаются 75, 15 и 12. Цены составляют 90, 360 и 280 рублей. Сумма продажи равна 4890 рублей. Повторное проведение документа заменяет движения и не должно удваивать результат. Источник: документация по тестированию, runtime-tests.txt, T01–T04 и T19.',
'2:00–2:25. Отчёт остатков позволяет сверить количество по складу, организации и продукции. Реальный снимок ранней версии показывает те же контрольные остатки. В актуальной версии рядом со складским количеством выводятся резерв и свободное количество. Второй отчёт показывает продажи за период и их сумму. Для уточнения результата доступны отборы. Источник: assets/screenshots/Остатки.png, снимок пользователя, configuration/Reports/. На снимке ещё нет новых колонок.',
'2:25–3:00. Новое требование проекта состоит в бронировании товара для покупателя. При проведении документа товар остаётся на складе, но становится недоступен для обычной продажи. Например, из 75 литров бронируем 20. Склад остаётся 75, резерв становится 20, свободно 55. Поэтому обычная продажа 56 литров отклоняется. Для резерва недостаточно просто записать документ, его необходимо провести. Источник: reservation-tests.txt, B01–B06. Таблица является контрольным примером, а не снимком интерфейса.',
'3:00–3:35. У одной брони два альтернативных результата. Команда «Продать по брони» создаёт Расход на весь резерв. На складе остаются 55 литров, резерв равен нулю. При отмене до продажи товар не уходит со склада и все 75 литров снова доступны. Если отменить уже выполненную продажу, товар сначала вернётся на склад и в резерв. Для полного освобождения затем отменяют саму бронь. Повторная продажа одной брони запрещена. Источник: B14, B17, B20, B23–B24.',
'3:35–4:00. Роли разделяют обязанности сотрудников. Покупка оформляет поступления и изменяет цены. Продажа оформляет реализацию и бронирование. Полные права получает администратор. Обе рабочие роли видят остатки. Проверки обязательных полей, цен и количества помогают отклонять некорректные документы. Источник: configuration/Roles/, role-Покупка.txt, role-Продажа.txt.',
'4:00–4:30. В шести исходных протоколах сохранены 83 успешные автоматические проверки. Сорок девять относятся к прежнему учёту, формам и правам. Двадцать восемь проверяют бронирование, ещё шесть новые обработчики форм. Сценарии повторены после восстановления базы из DT. Автоматический вызов обработчика не подтверждает щелчок мышью, поэтому удобство интерфейса и читаемость остаются предметом ручной проверки. Источник: шесть протоколов PASS, release-validation.json.',
'4:30–4:55. Результат проекта включает готовую базу, конфигурацию, исходники и отдельные документы. Реализован основной цикл работы с готовой продукцией и бронированием. Ограничения версии: бронь продаётся только целиком, автоматического срока действия пока нет. Учебная лицензия запрещает печать табличных документов. Следующие доработки могут включать партии, сроки годности и частичную продажу брони. Источник: общая документация, инструкция пользователя, platform-limitations.txt.'
];
for(const [i,item] of deck.slides.items.entries()) item.speakerNotes.text=notes[i];
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const runId=Date.now();
const staged=path.join(build,`validated-${runId}.pptx`);
await finalizePresentation({
 workspaceDir:root,candidatePath:candidate,finalPath:staged,
 pythonExecutable:process.env.RUNTIME_PYTHON ?? '/Users/nerdysnake6/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit','--require-native-table-slide','3'],
 requiredNativeTableOwnerSlides:[3],requiredNativeChartOwnerSlides:[],
 fontPolicy:{basis:'reference',families:['Arial'],referencePath:reference,referenceSha256:crypto.createHash('sha256').update(await fs.readFile(reference)).digest('hex')},
 verifyArtifactToolImport:true,receiptPath:path.join(root,`.build/documentation/presentation-validation-${runId}.json`)
});
await fs.copyFile(staged,output);
const verified=await PresentationFile.importPptx(await FileBlob.load(output));
for(const [i,item] of verified.slides.items.entries()) {
 const png=await verified.export({slide:item,format:'png',scale:1});
 await fs.writeFile(path.join(build,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));
}
await fs.writeFile(path.join(build,'notes.json'),JSON.stringify({durationSeconds:295,wordCount:notes.join(' ').split(/\s+/u).length,notes},null,2));
console.log(output);
