# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from datetime import datetime
from threading import Thread, Event

from PySide6.QtCore import Qt, QSettings, Signal, QObject, QByteArray
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame, QLineEdit,
    QMessageBox, QPlainTextEdit, QProgressBar, QSizePolicy
)

APP_ORG = "DeepParser"
APP_NAME = "Парсер веб-новелл"
DEFAULT_ACCENT = "#00E5FF"

from site_profiles import detect_profile
from utils_docx import save_chapter_docx

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

class Signals(QObject):
    progress = Signal(int, str)
    done = Signal(str)
    error = Signal(str)

class ProjectStore:
    def __init__(self, workdir: Path):
        self.workdir = workdir
        self.db = ensure_dir(workdir) / "config.db"
        import sqlite3
        conn = sqlite3.connect(self.db); cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );""")
        conn.commit(); conn.close()
    def list(self, status="active"):
        import sqlite3
        conn = sqlite3.connect(self.db); cur = conn.cursor()
        cur.execute("SELECT id,name,status,created_at,updated_at FROM projects WHERE status=? ORDER BY id DESC",(status,))
        rows = cur.fetchall(); conn.close(); return rows
    def create(self, name: str):
        import sqlite3
        now = datetime.utcnow().isoformat()
        conn = sqlite3.connect(self.db); cur = conn.cursor()
        cur.execute("INSERT INTO projects(name,status,created_at,updated_at) VALUES(?, 'active', ?, ?)", (name, now, now))
        conn.commit(); pid = cur.lastrowid; conn.close()
        base = ensure_dir(self.workdir / name)
        ensure_dir(base / "Original"); ensure_dir(base / "Translation")
        return pid

class ProjectPanel(QFrame):
    def __init__(self, store: ProjectStore, on_select):
        super().__init__(); self.store=store; self.on_select=on_select
        self.setMinimumWidth(220)
        self.setMaximumWidth(6000)

        v = QVBoxLayout(self); v.setContentsMargins(8,8,8,8); v.setSpacing(6)
        self.left_split = QSplitter(Qt.Vertical)
        v.addWidget(self.left_split)

        # Projects block
        proj_block = QFrame(); pv = QVBoxLayout(proj_block); pv.setContentsMargins(0,0,0,0); pv.setSpacing(6)
        head = QHBoxLayout(); head.addWidget(QLabel("Проекты"))
        self.btn_add = QPushButton("+"); self.btn_add.setFixedWidth(28); self.btn_add.clicked.connect(self._add)
        head.addStretch(1); head.addWidget(self.btn_add); pv.addLayout(head)
        self.active = QListWidget(); self.active.setMinimumHeight(120)
        self.active.itemClicked.connect(lambda it:self.on_select(it.data(Qt.UserRole)))
        pv.addWidget(self.active)

        # Archive block
        arch_block = QFrame(); av = QVBoxLayout(arch_block); av.setContentsMargins(0,0,0,0); av.setSpacing(6)
        arch_head = QHBoxLayout(); arch_head.addWidget(QLabel("Архив")); arch_head.addStretch(1); av.addLayout(arch_head)
        self.archive = QListWidget(); self.archive.setMinimumHeight(80)
        self.archive.itemClicked.connect(lambda it:self.on_select(it.data(Qt.UserRole)))
        av.addWidget(self.archive)

        self.left_split.addWidget(proj_block)
        self.left_split.addWidget(arch_block)
        self.left_split.setSizes([300,150])

        self.refresh()

    def refresh(self):
        self.active.clear(); self.archive.clear()
        for r in self.store.list("active"):
            it=QListWidgetItem(r[1]); it.setData(Qt.UserRole, r[0]); self.active.addItem(it)
        for r in self.store.list("archived"):
            it=QListWidgetItem(r[1]); it.setData(Qt.UserRole, r[0]); self.archive.addItem(it)

    def _add(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self,"Новый проект","Название:")
        if ok and name.strip():
            self.store.create(name.strip())
            self.refresh()

class ParserPanel(QFrame):
    def __init__(self, on_parse, on_pause, on_stop):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(8,8,8,8); lay.setSpacing(8)
        self.url = QLineEdit(); self.url.setPlaceholderText("Вставьте ссылку на книгу…")
        self.btn_parse = QPushButton("Спарсить")
        self.btn_pause = QPushButton("Пауза")
        self.btn_stop = QPushButton("Стоп")
        self.progress = QProgressBar(); self.progress.setMinimum(0); self.progress.setMaximum(100)
        self.btn_parse.clicked.connect(lambda: on_parse(self.url.text().strip()))
        self.btn_pause.clicked.connect(on_pause)
        self.btn_stop.clicked.connect(on_stop)
        lay.addWidget(QLabel("Ссылка:")); lay.addWidget(self.url,1); lay.addWidget(self.btn_parse)
        lay.addWidget(self.btn_pause); lay.addWidget(self.btn_stop); lay.addWidget(self.progress,1)

class EditorArea(QFrame):
    def __init__(self):
        super().__init__()
        self.signals = Signals()
        self._thread = None
        self._pause = Event(); self._stop = Event()
        self._pause.clear(); self._stop.clear()
        self.project_path: Path|None = None

        v = QVBoxLayout(self); v.setContentsMargins(8,8,8,8); v.setSpacing(8)
        self.panel = ParserPanel(self._start_parse, self._toggle_pause, self._stop_parse)
        v.addWidget(self.panel)

        self.split = QSplitter(Qt.Vertical); v.addWidget(self.split,1)
        self.text_split = QSplitter(Qt.Horizontal)
        self.orig = QPlainTextEdit(); self.orig.setPlaceholderText("Оригинал главы…")
        self.tran = QPlainTextEdit(); self.tran.setPlaceholderText("Перевод главы…")
        self.text_split.addWidget(self.orig); self.text_split.addWidget(self.tran); self.text_split.setSizes([600,600])
        self.split.addWidget(self.text_split)
        bottom = QFrame(); vb=QVBoxLayout(bottom); vb.setContentsMargins(0,0,0,0); vb.addWidget(QLabel("Мини‑промпт")); self.prompt = QPlainTextEdit(); vb.addWidget(self.prompt); self.split.addWidget(bottom); self.split.setSizes([800,200])

        self.signals.progress.connect(self._on_progress)
        self.signals.done.connect(self._on_done)
        self.signals.error.connect(self._on_error)

    def bind_project(self, project_path: Path):
        self.project_path = project_path

    def _start_parse(self, url: str):
        if not url: QMessageBox.warning(self,"Нет ссылки","Вставьте ссылку."); return
        prof = detect_profile(url)
        if not prof: QMessageBox.warning(self,"Неизвестный сайт","Пока не поддерживается."); return
        if self._thread and self._thread.is_alive(): QMessageBox.information(self,"Идёт парсинг","Дождитесь завершения/остановите."); return

        self._pause.clear(); self._stop.clear()

        def worker():
            try:
                book, chapters = prof.parse_book(url)
                if not chapters: self.signals.error.emit("Не удалось найти главы."); return
                base = self.project_path or Path.cwd()
                target = ensure_dir(base / "Original" / book)
                total = len(chapters)
                for i, ch in enumerate(chapters, start=1):
                    while self._pause.is_set():
                        import time; time.sleep(0.2)
                        if self._stop.is_set(): break
                    if self._stop.is_set(): break

                    self.signals.progress.emit(int((i-1)/total*100), f"Глава {i}/{total}: {ch.title}")
                    title, body = prof.fetch_chapter(ch.url)
                    save_chapter_docx(target, title or ch.title, body or "", index=i)
                if not self._stop.is_set():
                    self.signals.progress.emit(100, "Готово")
                    self.signals.done.emit(str(target))
            except Exception as e:
                self.signals.error.emit(str(e))

        self._thread = Thread(target=worker, daemon=True); self._thread.start()

    def _toggle_pause(self):
        if self._pause.is_set():
            self._pause.clear()
            self.panel.btn_pause.setText("Пауза")
        else:
            self._pause.set()
            self.panel.btn_pause.setText("Продолжить")

    def _stop_parse(self):
        self._stop.set()
        self._pause.clear()
        self.panel.btn_pause.setText("Пауза")

    def _on_progress(self, p: int, msg: str):
        self.panel.progress.setValue(p); self.panel.progress.setFormat(msg+" (%p%)")

    def _on_done(self, folder: str):
        QMessageBox.information(self, "Парсинг завершён", f"Файлы сохранены в:\n{folder}")

    def _on_error(self, err: str):
        QMessageBox.critical(self, "Ошибка парсинга", err)

    def set_reading_mode(self, active: bool):
        if active:
            self._text_state = self.text_split.saveState()
            self.orig.setVisible(False)
            self.text_split.setSizes([0, 1])
        else:
            self.orig.setVisible(True)
            state = getattr(self, '_text_state', None)
            if isinstance(state, QByteArray):
                self.text_split.restoreState(state)
            else:
                self.text_split.setSizes([600, 600])

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME); self.resize(1400,900)
        self.settings = QSettings(APP_ORG, APP_NAME)

        self.workdir = self._ensure_workdir()
        self.store = ProjectStore(Path(self.workdir))

        root = QWidget(); self.setCentralWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout(); top_bar.setContentsMargins(8,6,8,6); top_bar.setSpacing(8)
        self.btn_burger = QPushButton("☰"); self.btn_burger.setFixedWidth(32); self.btn_burger.clicked.connect(self._toggle_left_panel)
        self.btn_reading = QPushButton("Режим чтения"); self.btn_reading.setCheckable(True); self.btn_reading.clicked.connect(self._toggle_reading_mode)
        self.btn_fullscreen = QPushButton("⛶"); self.btn_fullscreen.setFixedWidth(32); self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        title = QLabel(APP_NAME)
        top_bar.addWidget(self.btn_burger); top_bar.addWidget(title); top_bar.addStretch(1); top_bar.addWidget(self.btn_reading); top_bar.addWidget(self.btn_fullscreen)
        lay.addLayout(top_bar)

        # Main splitter: left | editor
        self.main_split = QSplitter(Qt.Horizontal); lay.addWidget(self.main_split,1)
        self.left_panel = ProjectPanel(self.store, on_select=self._bind_project)
        self.main_split.addWidget(self.left_panel)
        self.editor = EditorArea(); self.main_split.addWidget(self.editor)
        self.main_split.setCollapsible(0, True)
        self.main_split.setSizes([280, 1120])

        # Shortcuts
        act_toggle = QAction("Скрыть/показать левую панель", self); act_toggle.setShortcut(QKeySequence("Ctrl+B")); act_toggle.triggered.connect(self._toggle_left_panel); self.addAction(act_toggle)
        act_full = QAction("Полноэкранный", self); act_full.setShortcut(QKeySequence("F11")); act_full.triggered.connect(self._toggle_fullscreen); self.addAction(act_full)
        act_esc = QAction("Выход из полноэкранного", self); act_esc.setShortcut(QKeySequence("Esc")); act_esc.triggered.connect(self._exit_fullscreen); self.addAction(act_esc)

        # Restore splitter state
        bs = self.settings.value("ui/main_split_state", None)
        if isinstance(bs, QByteArray):
            self.main_split.restoreState(bs)

        # Restore modes
        if self.settings.value("ui/reading_mode", False, type=bool):
            self.btn_reading.setChecked(True)
            self._toggle_reading_mode()
        self.fullscreen_mode = 0
        mode = int(self.settings.value("ui/fullscreen_mode", 0))
        if mode == 1:
            self.showMaximized()
            self.fullscreen_mode = 1
        elif mode == 2:
            self._enter_borderless()
            self.fullscreen_mode = 2

    def _toggle_left_panel(self):
        if self.left_panel.isVisible():
            self.main_split.setSizes([0, 1])
            self.left_panel.setVisible(False)
        else:
            self.left_panel.setVisible(True)
            self.main_split.setSizes([280, 1120])
        self.settings.setValue("ui/main_split_state", self.main_split.saveState())

    def _toggle_reading_mode(self):
        active = self.btn_reading.isChecked()
        if active:
            self._left_was_visible = self.left_panel.isVisible()
            if self.left_panel.isVisible():
                self._toggle_left_panel()
        else:
            if getattr(self, '_left_was_visible', True) and not self.left_panel.isVisible():
                self._toggle_left_panel()
        self.editor.set_reading_mode(active)
        self.settings.setValue("ui/reading_mode", active)

    def _toggle_fullscreen(self):
        if getattr(self, 'fullscreen_mode', 0) == 0:
            self.showMaximized()
            self.fullscreen_mode = 1
        elif self.fullscreen_mode == 1:
            self._enter_borderless()
            self.fullscreen_mode = 2
        else:
            self._exit_fullscreen()
            self.fullscreen_mode = 0
        self.settings.setValue("ui/fullscreen_mode", getattr(self, 'fullscreen_mode', 0))

    def _exit_fullscreen(self):
        mode = getattr(self, 'fullscreen_mode', 0)
        if mode == 2:
            self.setWindowFlag(Qt.FramelessWindowHint, False)
            self.showNormal()
        elif mode == 1 and self.isMaximized():
            self.showNormal()
        else:
            self.showNormal()
        self.fullscreen_mode = 0
        self.settings.setValue("ui/fullscreen_mode", 0)

    def _enter_borderless(self):
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.showFullScreen()

    def _ensure_workdir(self)->str:
        wd = self.settings.value("app/workdir","")
        if wd and Path(wd).exists(): return wd
        dlg = QFileDialog(self,"Выберите рабочую папку")
        dlg.setFileMode(QFileDialog.Directory); dlg.setOption(QFileDialog.ShowDirsOnly, True); dlg.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        if dlg.exec(): chosen = dlg.selectedFiles()[0]
        else:
            chosen = str(Path.home() / "Documents" / "Парсер веб-новелл"); ensure_dir(Path(chosen))
        self.settings.setValue("app/workdir", chosen); return chosen

    def _bind_project(self, pid: int):
        rows = self.store.list("active")
        name = next((r[1] for r in rows if r[0]==pid), None)
        if name: self.editor.bind_project(Path(self.workdir)/name)

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(APP_ORG); app.setApplicationName(APP_NAME)
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
