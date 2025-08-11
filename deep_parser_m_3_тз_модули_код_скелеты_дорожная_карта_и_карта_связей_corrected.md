# DeepParser — полное ТЗ (пункты 1–52), модульная архитектура, код‑скелеты, дорожная карта и карта взаимодействий

> Документ предназначен для фиксации требований и продолжения разработки в будущих чатах. Содержит расширенный список фич (1–52), архитектуру модулей, примерные интерфейсы классов с код‑скелетами и комментариями, а также Roadmap и карту связей данных/сигналов.

---

## 0. Базовые принципы

- **Модульность:** каждый крупный блок — независимый пакет с чёткими интерфейсами.
- **Потоки:** длительные операции (парсинг/перевод/экспорт) — во вторичных потоках, общение с UI через сигналы/слоты.
- **Хранилище:** SQLite (FTS5 для полнотекстового поиска), файлы проекта на диске (`Original/`, `Translation/`, `.revisions/`, `.backup/`).
- **Расширяемость:** профили сайтов в JSON; переводчики — через драйверы `Translator`; QA/типографика — как фильтры post‑process.
- **Безопасность:** ключи API — через Windows DPAPI; логирование — ротация и фильтры.

---

## 1. Полный список функций (1–52) с деталями

### 1) Заголовок оригинала

**UI:** `QLabel` (read‑only) над левым редактором.\
**Данные:** `chapters.title_src`.\
**Источник:** парсер `fetch_chapter()`.\
**Сигналы:** `ChapterLoaded(title, text)` → MainWindow обновляет поле.

### 2) Заголовок перевода (редактируемый)

**UI:** `QLineEdit` над правым редактором. Имя файла берётся отсюда.\
**Данные:** `chapters.title_tgt`.\
**Сохранение:** при изменении — пометка dirty; при "Сохранить" — запись в БД/файл.

### 3) «Предыдущая / Следующая»

**UI:** две `QToolButton`.\
**Логика:** запрос главы через `ChapterController.load(prev/next)`; предварительная проверка незасейвленных изменений.

### 4) Выпадающий список глав (центр)

**UI:** `QComboBox` с `#N — title`. Поиск по вводу.\
**Данные:** `chapters (list)` из БД.\
**Переход:** `onChapterSelect(index)` → загрузка главы.

### 5) Сохранить перевод в DOCX

**UI:** кнопка/пункт меню.\
**Вызов:** `exporter.docx.save_chapter(...)`.\
**После:** отметка `exported_at` в БД, тост «Сохранено».

### 6) Логотип (svg/png, прозрачный фон)

**UI:** `QLabel+QPixmap` в шапке.\
**Ресурс:** `res/logo/*.png`. Поддержка светлой/тёмной тем.

### 7) Активная модель ИИ (селектор)

**UI:** `QComboBox` (Gemini/Qwen/…); рядом иконка статуса.\
**Сервис:** `translation/manager.py` держит активный драйвер.\
**Фолбэк:** п.33.

### 8) Левая панель проектов

**UI:** `QTreeView/QListView` + сворачиваемая панель.\
**Источник:** `ProjectStore.list(active/archived)`.

### 9) Архив (разворачиваемый)

**UI:** узел дерева «Архив».\
**Действия:** открыть/деархивировать.

### 10) Архивировать/вернуть из архива

**UI:** контекстное меню.\
**Хранилище:** `projects.status = archived/active`; опция перемещать папку.

### 11) Глоссарии: CRUD

**UI:** менеджер словарей (таблица пар), выбор активного.\
**Формат:** JSON + запись в БД.\
**Интеграция:** pre/post‑process перевода.

### 12) Мини‑иконки проектов (кастом)

**UI:** иконки слева рядом с проектами; диалог выбора пользовательской пиктограммы.

### 13) Неоновая палитра

**UI:** настройки цветового акцента (QColorDialog/предустановки).\
**Хранение:** `settings.ui.neon_color`.

### 14) Статусбар: активный проект

Лейбл «Active: ».

### 15) Меню «Настройки»

Вкладки: UI, Перевод, Сеть, Глоссарии, RU‑язык, Экспорт, Бэкапы.

### 16) Настройки форматирования для ИИ

**Опции:** сохранять жирный/курсив через плейсхолдеры, стратегия кавычек.\
**Интеграция:** `translation/preprocess.py` и `postprocess.py`.

### 17) Мини‑промпт снизу

Строка для доп. инструкций; добавляется в Context Pack сегмента.

### 18) Фон «звёзды» (анимация)

**UI:** `StarfieldWidget` (QPainter/QTimer).\
**Настройки:** тумблер вкл/выкл, скорость (ползунок). По умолчанию **выкл**.

### 19) Оригинал появляется слева

**Событие:** после парсинга главы → сигнал `ChapterLoaded` заполняет левый редактор.

### 20) Автоперевод при появлении

**Флаг:** «Автоперевод при загрузке».\
**Действие:** `Translator.translate(...)` → правый редактор.

### 21) Настройки форматирования (дубль для ясности)

См. п.16.

### 22) Прогрессбар и счётчик X/Y

**UI:** индикатор в шапке + текстовый счётчик.\
**Сигналы:** из рабочего потока парсинга/перевода.

### 23) Корректный парсинг (не HTML)

**Профили:** селекторы, фильтрация мусора, нормализация переносов.\
**Блокировки:** пауза/стоп, ретраи, таймауты.

### 24) Модульная архитектура

Пакеты: `ui/ parsing/ translation/ glossary/ tm/ qa/ ru_lang/ exporter/ telemetry/ network/ backup/ search/ analysis/ core/`.

### 25) Совместимость без регрессий

**Тесты:** smoke‑ и unit‑тесты на ключевые функции; контракты интерфейсов.

### 26) Логи

**Файлы:** `logs/deepparser.log` (ротация).\
**UI:** вкладка «Логи», фильтры каналов.

### 27) «Только новые»

Фильтр по `content_hash` и статусам `downloaded/translated`.

### 28) Автосохранение + история версий

**Механизм:** дебаунс → снапшоты в `.revisions/` + `revisions` (БД).\
**Откат:** список версий с diff‑превью.

### 29) Сравнение/дифф

Выравнивание по предложениям; подсветка отличий; переходы по проблемам.

### 30) QA‑проверки

Числа/даты, парность кавычек/скобок, пропуски предложений, длины абзацев. Авто‑фиксы где безопасно.

### 31) Память переводов (TM)

FTS5 хранилище `src→tgt` предложений; exact/fuzzy поиск; автоподстановка.

### 32) **Glossary PRO: many‑to‑one + режимы сопоставления**

Группы оригиналов → один канон; приоритеты; regex/normalized/fuzzy; импорт/экспорт CSV. См. также п.47.

### 33) Выбор модели + фолбэк

Активный драйвер `Gemini`/`Qwen`; на ошибках/лимитах — автоматическая попытка второй модели.

### 34) Менеджер API‑ключей

Хранение через DPAPI; проверка валидности/квоты; переключение ключей.

### 35) Сеть

Прокси, таймауты, повторы (экспоненциально), пользовательский User‑Agent; отдельный лог «network».

### 36) Обновляемые профили сайтов

Селекторы/правила в `profiles/*.json`; горячая подмена без релиза.

### 37) Типографика RU

«Ёлочки», тире, неразрывные пробелы, троеточия, тонкие пробелы.

### 38) Экспорт: DOCX/EPUB/PDF/MD

Единая шина `exporter`; сборка всего проекта (оглавление, обложка, метаданные).

### 39) Резервные копии проекта

Zip‑бэкапы по расписанию/событиям; храним N последних; восстановление/очистка.

### 40) Поиск/замена по проекту

Глобальный поиск (regex); массовая замена с предпросмотром и откатом.

### 41) Просмотр логов в UI

Вкладка «Логи», фильтры уровней/каналов, копирование отчёта.

### 42) Клик по слову → варианты перевода

Поп‑ап под словом: из TM, из глоссария, + быстрый рефраз от модели; уважение регистра/кавычек.

### 43) Орфография RU (спелл‑чекер)

Подчёркивания, предложения исправлений; личный словарь проекта/глобальный.

### 44) Морфология и согласование

Проверка рода/числа/падежа; предложения фиксов (по контексту).

### 45) Пунктуация

СПП/ССП, дееприч./прич. обороты, вводные, прямая речь, тире/двоеточия.

### 46) Капитализация, «ё/е», дефисы/слитность

Нормы РЯ; опция авто‑замены «е→ё» по словарю.

### 47) Инфлектор глоссария

Если не зафиксировано — склонение целевой формы термина по контексту; если `lock` — сохраняем канон.

### 48) Диалоги (прямая речь)

Правила тире/кавычек; подсказки и авто‑фиксы.

### 49) Режим «Корректор»

Кнопка «Причесать»: пакет сторонних безопасных правок (орфография/пунктуация/типографика/согласование) + отчёт diff.

### 50) Личный словарь/исключения

Исключения орфографии/пунктуации, принятые формы имён/техник; влияет на 43–49.

### 51) Предэкспортный лингвистический отчёт

Перед экспортом — чеклист нарушений, кнопки «исправить безопасное/перейти».

### 52) Настройки RU‑блока

Тумблеры и уровни строгости: Орфография, Пунктуация, Согласование, Диалоги, Ё/Е, Инфлектор.

---

## 2. Структура каталогов (пакетов)

```
app/
  main.py              # точка входа
  core/
    events.py          # общие Qt-сигналы/датаклассы
    settings.py        # загрузка/сохранение настроек
    logging.py         # конфиг логгера + ротация
    db.py              # SQLite init + ORM-хелперы
  ui/
    main_window.py
    project_panel.py
    parser_panel.py
    editor_panel.py
    chapter_nav.py     # prev/next + комбобокс
    glossary_manager.py
    qa_panel.py
    logs_panel.py
    preferences.py
    starfield.py
    toggles.py         # DeepL-подобные тумблеры (QSS)
    styles.qss
  parsing/
    profile_base.py
    royalroad.py
    mvlempyr.py
    novatls.py
    ellotl.py
    profiles_schema.json  # описание полей
    profiles/*.json       # селекторы
  translation/
    translator_base.py
    gemini.py
    qwen.py
    manager.py
    preprocess.py
    postprocess.py
    context_builder.py
  glossary/
    models.py
    manager.py
    matcher.py
  tm/
    store.py
    matcher.py
  qa/
    checks.py
    diffview.py
  ru_lang/
    spelling.py
    morphology.py
    punctuation.py
    inflector.py
  exporter/
    docx_exporter.py
    epub_exporter.py
    pdf_exporter.py
    md_exporter.py
  telemetry/
    stopwatch.py
    char_counter.py
  network/
    session.py
  backup/
    manager.py
  search/
    index.py
    replace.py
  analysis/
    ner_terms.py
    project_memory.py
res/
  logo/
  fonts/
  qml/
```

---

## 3. Схема БД (SQLite, ERD текстом)

```
projects(id PK, name, status, path, created_at, updated_at, icon_path)
chapters(id PK, project_id FK, idx, url, title_src, title_tgt, content_hash,
         downloaded_at, translated_at, edited_at, exported_at, qa_score)
revisions(id PK, chapter_id FK, ts, text_tgt, note)

# Glossary PRO
glossaries(id PK, project_id FK NULL, name, is_active)
terms(id PK, glossary_id FK, target_ru, match_mode, priority, lock_inflection, notes, tags)
term_sources(id PK, term_id FK, source_text)  # many-to-one варианты оригиналов

# Translation Memory
tm_segments(id PK, project_id FK, src, tgt, src_hash, ctx_left, ctx_right, ts)

# Project Memory / аналитика
entities(id PK, project_id FK, canon_ru, type, notes)
entity_aliases(id PK, entity_id FK, alias_src)
relations(id PK, project_id FK, a_id FK, rel, b_id FK)
events(id PK, project_id FK, chapter_id FK, summary_json)

# Search
fts_index(content)  -- виртуальная таблица FTS5

settings(key PK, value_json)
backups(id PK, project_id FK, path_zip, ts)
```

---

## 4. Код‑скелеты (ключевые интерфейсы)

### 4.1 core/events.py

```python
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal

@dataclass
class ChapterRef:
    project_id: int
    chapter_id: int
    idx: int
    title_src: str
    title_tgt: str

class AppSignals(QObject):
    chapter_loaded = Signal(ChapterRef, str)   # (ref, original_text)
    chapter_translated = Signal(ChapterRef, str)  # (ref, translated_text)
    progress = Signal(int, int, str)  # current, total, title
    error = Signal(str)
    done = Signal()
```

### 4.2 translation/translator\_base.py

```python
from abc import ABC, abstractmethod
from typing import Iterable, Dict

class Translator(ABC):
    """Базовый интерфейс любого движка перевода."""

    @abstractmethod
    def translate(self, segments: Iterable[str], *,
                  src_lang: str, tgt_lang: str,
                  context: Dict) -> Iterable[str]:
        """Переводит список сегментов. Возвращает такой же список переведённых сегментов.
        context: { 'glossary': [...], 'project_memory': {...}, 'format_policy': {...}, 'miniprompt': str }
        """
        raise NotImplementedError
```

### 4.3 translation/manager.py

```python
class TranslationManager:
    def __init__(self, drivers: dict[str, Translator]):
        self._drivers = drivers
        self.active = 'Gemini'
        self.fallback = 'Qwen'

    def translate(self, segments, **kw):
        drv = self._drivers[self.active]
        try:
            return drv.translate(segments, **kw)
        except Exception as e:
            # лог + фолбэк
            fb = self._drivers.get(self.fallback)
            if fb and self.fallback != self.active:
                return fb.translate(segments, **kw)
            raise
```

### 4.4 translation/preprocess.py

```python
import re

B_OPEN, B_CLOSE = '{B}', '{/B}'
I_OPEN, I_CLOSE = '{I}', '{/I}'

class Preprocessor:
    def __init__(self, glossary_matcher, placeholder_policy):
        self.gm = glossary_matcher
        self.ph = placeholder_policy  # high-priority lock terms

    def apply(self, text: str, context) -> tuple[str, dict]:
        """Возвращает (текст_с_плейсхолдерами, placeholder_map)."""
        ph_map = {}
        # пример плейсхолдеризации имён из глоссария с lock_inflection
        for ent in self.gm.high_priority_locked(text):
            token = f'⟦ENT#{len(ph_map)+1:03d}⟧'
            ph_map[token] = ent.target_ru
            text = re.sub(ent.regex, token, text)
        # маркеры форматирования уже проставлены в парсере (или тут)
        return text, ph_map
```

### 4.5 translation/context\_builder.py

```python
class ContextBuilder:
    def __init__(self, glossary_mgr, project_memory, settings):
        self.glossary_mgr = glossary_mgr
        self.pm = project_memory
        self.settings = settings

    def build(self, project_id: int, chapter_id: int, miniprompt: str) -> dict:
        gl_slice = self.glossary_mgr.slice_for_context(project_id, limit=self.settings.glossary_max)
        pm = self.pm.context_for(chapter_id)  # summary последних глав, каноны имён/ролей
        return {
            'glossary': gl_slice,
            'project_memory': pm,
            'miniprompt': miniprompt,
            'format_policy': self.settings.format_policy,
        }
```

### 4.6 translation/postprocess.py

```python
class Postprocessor:
    def __init__(self, glossary_matcher, typography, qa_checks, inflector):
        self.gm = glossary_matcher
        self.typography = typography
        self.qa = qa_checks
        self.inflector = inflector

    def apply(self, text: str, placeholder_map: dict, context) -> str:
        # вернуть плейсхолдеры
        for token, val in placeholder_map.items():
            text = text.replace(token, val)
        # глоссарий‑замены
        text = self.gm.replace(text)
        # инфлектор (если не lock)
        text = self.inflector.apply(text)
        # типографика
        text = self.typography.apply(text)
        # QA подсветка/фикс безопасного
        issues = self.qa.scan(text)
        text = self.qa.autofix_safe(text, issues)
        return text
```

### 4.7 glossary/models.py

```python
from dataclasses import dataclass

@dataclass
class GlossaryEntry:
    id: int | None
    target_ru: str
    match_mode: str  # exact|normalized|regex|fuzzy
    priority: int = 0
    lock_inflection: bool = True
    notes: str = ''
    tags: str = ''

@dataclass
class TermSource:
    id: int | None
    term_id: int
    source_text: str  # один из вариантов оригинала
```

### 4.8 glossary/matcher.py (эскиз)

```python
import re
from typing import Iterable

class GlossaryMatcher:
    def __init__(self, entries: Iterable[GlossaryEntry], sources: list[TermSource]):
        # подготовка индексов/регекспов
        ...

    def high_priority_locked(self, text: str):
        # вернуть записи с priority>=P и lock_inflection=True, которые есть в тексте
        ...

    def replace(self, text: str) -> str:
        # пройтись по записям и заменить в тексте на target_ru с учётом границ
        ...
```

### 4.9 tm/store.py

```python
class TMStore:
    def add(self, project_id: int, src: str, tgt: str, ctx_left: str, ctx_right: str):
        ...
    def lookup(self, project_id: int, src: str, fuzzy: bool = True):
        # вернуть список кандидатов с score
        ...
```

### 4.10 qa/checks.py (эскиз)

```python
class QAChecks:
    def scan(self, text: str) -> list[dict]:
        # правила: числа, кавычки, скобки, пропуски
        ...
    def autofix_safe(self, text: str, issues) -> str:
        # безопасные исправления
        ...
```

### 4.11 ru\_lang/\* (эскизы)

```python
# spelling.py
class Speller:
    def underline(self, editor): ...
    def suggest(self, word: str) -> list[str]: ...

# morphology.py
class Morph:
    def agree(self, sent: str) -> list[dict]:  # список найденных несогласований
        ...

# punctuation.py
class Punct:
    def check(self, text: str) -> list[dict]: ...

# inflector.py
class Inflector:
    def apply(self, text: str) -> str:
        # склонение терминов из глоссария, если lock=false
        ...
```

### 4.12 exporter/docx\_exporter.py (фрагмент)

```python
from docx import Document

def save_chapter(folder: str, index: int, title: str, text: str):
    doc = Document()
    doc.add_heading(title, level=1)
    for para in text.split('\n\n'):
        doc.add_paragraph(para)
    path = f"{folder}/{index:03d} {title}.docx"
    doc.save(path)
    return path
```

### 4.13 ui/starfield.py (эскиз)

```python
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer
from PySide6.QtGui import QPainter
import random

class Starfield(QWidget):
    def __init__(self, speed=1.0, enabled=False):
        super().__init__()
        self.enabled = enabled
        self.speed = speed
        self.stars = [(random.random(), random.random()) for _ in range(256)]
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.timer.start(33)

    def advance(self):
        if not self.enabled: return
        self.stars = [((x+self.speed*0.002)%1.0, (y-self.speed*0.002)%1.0) for x,y in self.stars]
        self.update()

    def paintEvent(self, ev):
        if not self.enabled: return
        p = QPainter(self)
        w,h = self.width(), self.height()
        for x,y in self.stars:
            p.drawPoint(int(x*w), int(y*h))
```

### 4.14 ui/toggles.py (DeepL‑стиль)

```python
# Стили QSS (в styles.qss):
# .toggle { background: #2ad1a3; border-radius: 12px; }
# .toggle::handle { background: white; border-radius: 10px; }
```

---

## 5. Потоки данных (карта взаимодействий)

### 5.1 Пользователь → Парсер → Переводчик → UI → Файлы

1. Пользователь вставляет URL → `ParserWorker.start(url)`.
2. `detect_profile(url)` → `parse_book()` → список `ChapterRef` + оглавление → UI (наполняет комбобокс, X/Y).
3. Цикл по главам: `fetch_chapter(url)` → `original_text` → сигнал `chapter_loaded` → левый редактор.
4. Если включён автоперевод:
   - `Preprocessor.apply` (плейсхолдеры имён, формат‑маркеры),
   - `ContextBuilder.build` (глоссарий slice + Project Memory + мини‑промпт),
   - `TranslationManager.translate` (Gemini/Qwen; при ошибке — фолбэк),
   - `Postprocessor.apply` (глоссарий, типографика, QA, инфлектор),
   - сигнал `chapter_translated` → правый редактор.
5. `TMStore.add` сохраняет пары `src→tgt`.
6. По клику «Сохранить»: `exporter.docx.save_chapter(...)` → отметка в `chapters`.

### 5.2 Glossary PRO и RU‑блок

- GlossaryManager даёт `GlossaryMatcher`у набор записей и вариантов original→target.
- RU‑модуль (spelling/punct/morph/inflector) работает **после** пост‑процессинга и перед/в момент редактирования, а также в «Корректоре».

### 5.3 Project Memory

- `analysis/ner_terms.py` парсит итоговый перевод/оригинал → `entities`, `relations`, `events`.
- `context_builder` вытягивает каноны + резюме последних глав в контекст следующей главы.

### 5.4 Сеть/ключи/фолбэк

- `network/session.py` создаёт `requests.Session` с прокси/таймаутами/повторами.
- `translation/*` используют его.
- `manager.translate()` оборачивает вызовы и делает фолбэк.

---

## 6. Дорожная карта (Roadmap)

### Этап P0 — Базовая надёжная версия

- Парсинг 4 сайтов + профили в JSON (пп. 23, 36) с ретраями/таймаутами/паузой/стопом.
- Структура проекта + SQLite/FTS5, статусы глав, хэш контента, «Только новые» (п.27).
- UI‑каркас: панель проектов, шапка навигации (названия, Prev/Next, комбобокс), автоперевод, прогресс, статусбар (пп. 1–5, 7–10, 14–22).
- Переводчики: драйверы Gemini и Qwen, менеджер, фолбэк, сетевые настройки (пп. 33–35).
- Glossary PRO (many‑to‑one, lock‑inflection, CSV), плейсхолдеризация имён (пп. 11, 32, 47).
- TM Store (запись/поиск), подсказки при клике по слову (пп. 31, 42).
- Типографика RU (п.37) + базовый QA (числа/кавычки/скобки/пропуски) (п.30).
- Экспорт DOCX, автосейв/ревизии и откат (пп. 5, 28, 38[DOCX]).
- Логи + вкладка «Логи», ротация (пп. 26, 41).

### Этап P1 — Качество языка и UX

- RU‑блок полностью: орфография, пунктуация, согласование, диалоги, инфлектор, настройки строгости (пп. 43–46, 48–52).
- Дифф/сравнение + панель QA с переходами и авто‑фиксами (пп. 29–30).
- Поиск/замена по проекту (regex, предпросмотр, откат) (п.40).
- Резервные копии проекта (zip) с настройками и списком бэкапов (п.39).
- Экспорт EPUB/MD/PDF и сборка всего проекта (п.38).

### Этап P2 — Производительность и удобство

- Конвейер: предзагрузка следующей главы при переводе текущей; оптимизация «Только новые».
- Улучшенный Starfield (GPU/QML), тонкие настройки неон‑тем (пп. 13, 18).
- Авто‑проверки и горячее обновление профилей без релиза (п.36).
- Расширенный Project Memory: умнее резюме и авто‑кандидаты в глоссарий; встроенные отчёты качества.

**Постоянно:** регрессионные тесты, сборка .exe (батники), ротация логов, мониторинг ошибок.

**Постоянно:** регрессионные тесты, сборка .exe (батники), ротация логов, мониторинг ошибок.

---

## 7. Примечания по интеграции переводчиков (Gemini/Qwen)

- Реализация драйверов изолирована. Код SDK может отличаться по версиям; используем абстракцию `Translator` и адаптируемся к актуальному API при сборке.
- Контекст (глоссарий/память/мини‑промпт) передаётся в начале запроса; формат — согласно движку (system+user для Gemini; user с префиксом CONTEXT для Qwen‑MT).
- Ограничения длины: сегментация по абзацам/предложениям; сбор ответа; контроль полноты.

---

## 8. Тест‑чек‑лист (сокр.)

- Парсинг каждой платформы (включая «первая глава vs оглавление»).
- Перевод длинной главы (разбиение/склейка), корректность плейсхолдеров.
- Glossary PRO: many‑to‑one, приоритеты, lock‑inflection, CSV.
- TM: exact/fuzzy попадания, подсказки по клику.
- RU‑блок: орфография/пунктуация/согласование на реальных главах.
- Экспорт DOCX, предэкспортный отчёт, бэкап/восстановление.
- Смена модели, фолбэк, сетевые сбои, прокси.
- Пауза/Стоп, автосейв и откат ревизий, логи в UI.

---

## 9. Что подготовить для сборки .exe

- `build_env.bat` — создать venv, `pip install -r requirements.txt`.
- `build_app.bat` — PyInstaller с .spec, datas (ресурсы, профили JSON, шрифты, стили, иконки), hidden‑imports.
- `run_dev.bat` — запуск dev‑версии с включённым логом.

---

## 10. Доп. стилистика UI

- Шрифт из вложения (для заголовков/кнопок), QSS аккуратно под тёмную тему.
- Тумблеры как у DeepL: зелёный/серый, плавный переход.
- Таймер в статусбаре + версия, полу‑прозрачный неон.

---

## 11. Подготовка до старта разработки — чек‑лист (Pro)

### 11.1 Product & UX

- **Definition of Done** по ключевым фичам (пп. 1–52): критерии готовности и метрики.
- Финальные **вайрфреймы** по твоему референсу + карта экранов.
- **Design tokens**: палитра (неон‑акцент, фон, текст, состояния), типографика (подключение твоего TTF), размеры/отступы, состояния тумблеров (DeepL‑стиль).
- Карта **горячих клавиш**: сохранение, навигация, перевод выделения, поиск/замена, дифф.

### 11.2 Техническая база

- Репозиторий git, модель ветвления (GitFlow/Trunk), **pre‑commit** (black/isort/ruff/mypy), `.editorconfig`.
- Версионирование (SemVer) + CHANGELOG.
- `pyproject.toml`/`requirements.txt` с пинованием версий.
- Контракты интерфейсов: `Translator`, `ParserProfile`, `Glossary`, `TM`, `QA`, `Exporter`.

### 11.3 Данные и тесты

- **Набор тест‑URL** по каждому сайту (оглавление + одиночная глава + «нестандартные»).
- **Golden‑наборы**: очищенный оригинал, ожидаемый перевод, ожидаемые правила глоссария.
- Метрики: сохранение чисел/кавычек ≥99%, «потерянные предложения» ≤1%, скорость перевода, доля авто‑фиксов RU‑блока.

### 11.4 API и ключи

- Ключи Gemini и Qwen, проверка работоспособности и лимитов; стратегия фолбэка и ретраев.
- Секреты: хранение через **Windows DPAPI**, `.env.example`, инструкция для пользователя.

### 11.5 Право и этика

- Проверка ToS сайтов, уважение rate‑limit; корректные заголовки User‑Agent; экспоненциальный backoff на 429/503.

### 11.6 Архитектура (ADR)

- ADR‑карточки по решениям: плейсхолдеризация имён, JSON‑профили парсинга и схема валидации, формат Project Memory и инъекция в промпт.

### 11.7 Тест‑стратегия

- Юнит: глоссарий (many‑to‑one), TM, типографика, RU‑чекеры, профили парсинга (замороженный HTML).
- Интеграция: конвейер «URL → DOCX» с заглушкой переводчика.
- E2E (pytest‑qt): навигация, автоперевод, сохранение, история версий.
- Контроль нестабильности LLM: низкая температура, сегментация, сравнение по числам/кавычкам/структуре.

### 11.8 Производительность

- Бюджеты: RAM, время парсинга/перевода на главу, отзывчивость UI (<16 мс кадр).
- Модель конкуренции: 1 поток перевода + предзагрузка; безопасные флаги паузы/стопа.
- Формат логов (JSON‑линии: time/level/module/event/latency/chapter\_id).

### 11.9 Сборка и релиз

- PyInstaller `.spec` с datas (шрифты, стили, профили JSON, иконки), батники `build_env.bat`, `build_app.bat`, `run_dev.bat`.
- (Опц.) Подпись exe, справка «Первый запуск».

## 12. Регистр рисков и исследовательские спайки

### 12.1 Риски

| Риск                       | Влияние          | Смягчение                                                                                      |
| -------------------------- | ---------------- | ---------------------------------------------------------------------------------------------- |
| Сайты меняют верстку       | Парсинг ломается | Профили в JSON + быстрые фиксы, авто‑обновление профилей, регресc‑тесты на «замороженном» HTML |
| Лимиты/сбои API LLM        | Простой перевода | Фолбэк Gemini↔Qwen, ретраи с backoff, сегментация                                              |
| Нестабильность ответов LLM | Шум в тексте     | Плейсхолдеры, строгие инструкции, QA‑чек + пост‑проц, TM                                       |
| Потеря правок              | Недовольство     | Автосейв + ревизии + бэкапы                                                                    |
| Производительность UI      | Лаги             | Потоки, дебаунсы, ленивые обновления, отключаемые эффекты                                      |
| Юридические ограничения    | Риски            | Rate‑limit, ToS, честный UA                                                                    |

### 12.2 Спайки (быстрые прототипы)

- **Spike 1:** Qwen MT API + контекст/глоссарий в запросе (проверить соблюдение правил).
- **Spike 2:** Профили парсинга в JSON на 2 «сложных» сайтах.
- **Spike 3:** RU‑блок — прототип морфо‑согласования и пунктуации на реальном тексте.

## 13. Design Tokens — палитра, типографика, размеры (v1)

> Токены заданы под тёмную тему и неоновый акцент. Цвета подобраны по референсу макета (звёздный фон, бирюзовый неон, холодные синие оттенки). При необходимости можем заменить HEX на те, что ты точно утвердишь из макета.

### 13.1 Цвета (HEX)

| Токен                     | Значение                    | Назначение                      |
| ------------------------- | --------------------------- | ------------------------------- |
| `color.bg`                | **#0B0F1A**                 | Глобальный фон (space/ночь)     |
| `color.surface.1`         | **#0E1422**                 | Поверхность панелей/баров       |
| `color.surface.2`         | **#12192B**                 | Приподнятые карточки/диалоги    |
| `color.border`            | **#1F2A44**                 | Разделители/бордеры             |
| `color.text.primary`      | **#E6ECFF**                 | Основной текст                  |
| `color.text.secondary`    | **#A9B4D0**                 | Вторичный текст/подписи         |
| `color.text.disabled`     | **#6C7796**                 | Отключённые элементы            |
| `color.accent`            | **#2AD1A3**                 | Главный неон (бирюзово‑зелёный) |
| `color.accent.alt`        | **#66E0FF**                 | Альтернативный акцент (циан)    |
| `color.accent.purple`     | **#9A6BFF**                 | Подсветка/фокус/лого‑детали     |
| `color.success`           | **#33D17A**                 | Успех/готово                    |
| `color.warn`              | **#FFB84D**                 | Предупреждение                  |
| `color.error`             | **#FF5D5D**                 | Ошибка                          |
| `color.info`              | **#66B3FF**                 | Информация/подсказки            |
| `color.progress.gradient` | **linear(#2AD1A3→#66E0FF)** | Градиент прогресса/индикаторов  |

### 13.2 Типографика

| Токен          | Шрифт/размер/межстрочный                                                                       |
| -------------- | ---------------------------------------------------------------------------------------------- |
| `font.display` | **Cattedrale[RUSbypenka220]** (заголовки/лейблы функций), fallback: `"Segoe UI", Inter, Arial` |
| `font.ui`      | **Inter/Segoe UI** для основного UI текста                                                     |
| `type.h1`      | 28px / 34px, `font.display`, 600                                                               |
| `type.h2`      | 22px / 28px, `font.display`, 600                                                               |
| `type.h3`      | 18px / 24px, `font.display`, 600                                                               |
| `type.body`    | 14px / 20px, `font.ui`, 400–500                                                                |
| `type.mono`    | 13px / 18px, `ui-monospace` (логи/техданные)                                                   |
| `type.badge`   | 11px / 14px, `font.ui`, 600 (бейджи статусов)                                                  |

> Подключение TTF: положить файл в `res/fonts/`, зарегистрировать через `QFontDatabase`, задать стили в QSS.

### 13.3 Отступы, радиусы, тени

| Токен         | Значение                                    |
| ------------- | ------------------------------------------- |
| `space.xs`    | 4px                                         |
| `space.sm`    | 8px                                         |
| `space.md`    | 12px                                        |
| `space.lg`    | 16px                                        |
| `space.xl`    | 24px                                        |
| `space.2xl`   | 32px                                        |
| `radius.sm`   | 6px                                         |
| `radius.md`   | 12px (кнопки/инпуты)                        |
| `radius.lg`   | 16px (карточки)                             |
| `radius.2xl`  | 24px (панели)                               |
| `elevation.1` | 0 2px 8px rgba(0,0,0,0.35)                  |
| `elevation.2` | 0 6px 18px rgba(0,0,0,0.45)                 |
| `neon.glow`   | внешняя тень 0 0 12px rgba(42,209,163,0.35) |

### 13.4 Компонентные токены

**Тумблер DeepL‑стиля**

- Track OFF: `background: #1F2A44`
- Track ON: `background: #2AD1A3`
- Handle: `#FFFFFF` (OFF), `#0B0F1A` (ON)
- Focus ring: 2px `#66E0FF`

**ProgressBar**

- Высота: 6px; Радиус: 999px
- Цвет: `color.progress.gradient`; Индикация X/Y рядом с баром.

**Строка статуса (низ экрана)**

- Метка активного проекта: `color.text.secondary`
- Версия+секундомер: `opacity: 0.55`
- Счётчик символов: `color.accent` + `neon.glow`

**Starfield**

- По умолчанию: `enabled=false`
- Speed slider: 0–100 → внутренний коэффициент 0.0–2.0
- Точки: 1px; частота обновления: 30 FPS

**Кнопки «Пред/След»**

- Размер: `space.lg` высота + `radius.md`; иконки стрелок 16px
- Hover: лёгкий неон‑свечение `neon.glow`

### 13.5 Пример QSS (фрагмент)

```css
/* Палитра (через переменные Qt 6.5+ можно задать в палитре приложения) */

QWidget { background: #0B0F1A; color: #E6ECFF; }
QFrame[role="surface"] { background: #0E1422; border: 1px solid #1F2A44; border-radius: 16px; }

/* Тумблер */
.Toggle { background: #1F2A44; border-radius: 12px; padding: 2px; }
.Toggle[checked="true"] { background: #2AD1A3; box-shadow: 0 0 12px rgba(42,209,163,0.35); }
.Toggle::handle { background: #FFFFFF; border-radius: 10px; width: 18px; }
.Toggle[checked="true"]::handle { background: #0B0F1A; }

/* Прогресс */
QProgressBar { background: #1F2A44; border: 0; height: 6px; border-radius: 999px; }
QProgressBar::chunk { background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 #2AD1A3, stop:1 #66E0FF); border-radius: 999px; }
```

---

## 14. Карта хоткеев (шорткаты)

> Горячие клавиши можно менять в настройках. Ниже дефолты под Windows.

| Действие                                      | Шорткат          | Контекст            |
| --------------------------------------------- | ---------------- | ------------------- |
| Новый проект                                  | **Ctrl+N**       | Везде               |
| Открыть проект                                | **Ctrl+O**       | Везде               |
| Сохранить перевод главы                       | **Ctrl+S**       | Редактор перевода   |
| Экспорт главы в DOCX                          | **Ctrl+E**       | Редактор/Глава      |
| Экспорт проекта (сборка)                      | **Ctrl+Shift+E** | Везде               |
| Предыдущая глава                              | **Ctrl+PgUp**    | Везде               |
| Следующая глава                               | **Ctrl+PgDn**    | Везде               |
| Перейти к главе (фокус на комбобокс)          | **Ctrl+L**       | Везде               |
| Глобальный поиск по проекту                   | **Ctrl+Shift+F** | Везде               |
| Замена по проекту                             | **Ctrl+H**       | Везде               |
| Сравнение/Дифф вкл/выкл                       | **Alt+D**        | Редактор            |
| Запустить/остановить автоперевод              | **Ctrl+Shift+A** | Везде               |
| Открыть глоссарий                             | **Ctrl+G**       | Везде               |
| Вставить подсказку модели (поп‑ап под словом) | **Enter**        | Когда открыт поп‑ап |
| Сменить модель перевода                       | **Alt+M**        | Везде               |
| Включить/выключить Starfield                  | **Ctrl+Shift+F** | Везде               |
| Панель логов                                  | **Ctrl+\`**      | Везде               |
| Режим «Корректор»                             | **Alt+Q**        | Редактор            |
| Пауза/Продолжить конвейер                     | **Ctrl+Space**   | Везде               |

**Навигация в поп‑апе вариантов перевода:** стрелки ↑/↓ — выбор; **Enter** — применить; **Esc** — закрыть.

---

> Готово. Документ можно использовать как «единый источник правды»: требования, архитектура, интерфейсы и план работ. Дальше — итеративная реализация по Roadmap P0 → P1 → P2.

