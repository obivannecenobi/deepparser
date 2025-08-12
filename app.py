# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from datetime import datetime
from threading import Thread, Event

from PySide6.QtCore import Qt, QSettings, Signal, QObject, QByteArray
from PySide6.QtGui import QAction, QKeySequence, QMenu
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
from projects import Archive, Project

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p

class Signals(QObject):
    progress = Signal(int, str)
    done = Signal(str)
    error = Signal(str)

class ProjectPanel(QFrame):
    def __init__(self, store: Archive, on_select):
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
        self.btn_del = QPushButton("−"); self.btn_del.setFixedWidth(28); self.btn_del.clicked.connect(self._delete)
        head.addStretch(1); head.addWidget(self.btn_add); head.addWidget(self.btn_del); pv.addLayout(head)
        self.active = QListWidget(); self.active.setMinimumHeight(120)
        self.active.itemClicked.connect(lambda it:self.on_select(it.data(Qt.UserRole).path))
        self.active.setContextMenuPolicy(Qt.CustomContextMenu)
        self.active.customContextMenuRequested.connect(self._active_menu)
        pv.addWidget(self.active)

        # Archive block
        arch_block = QFrame(); av = QVBoxLayout(arch_block); av.setContentsMargins(0,0,0,0); av.setSpacing(6)
        arch_head = QHBoxLayout(); arch_head.addWidget(QLabel("Архив")); arch_head.addStretch(1); av.addLayout(arch_head)
        self.archive = QListWidget(); self.archive.setMinimumHeight(80)
        self.archive.itemClicked.connect(lambda it:self.on_select(it.data(Qt.UserRole).path))
        av.addWidget(self.archive)

        self.left_split.addWidget(proj_block)
        self.left_split.addWidget(arch_block)
        self.left_split.setSizes([300,150])

        self.refresh()

    def refresh(self):
        self.active.clear(); self.archive.clear()
        for p in self.store.list("active"):
            it=QListWidgetItem(p.name); it.setData(Qt.UserRole, p); self.active.addItem(it)
        for p in self.store.list("completed"):
            it=QListWidgetItem(p.name); it.setData(Qt.UserRole, p); self.archive.addItem(it)

    def _add(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self,"Новый проект","Название:")
        if ok and name.strip():
            self.store.create(name.strip())
            self.refresh()

    def _delete(self):
        item = self.active.currentItem() or self.archive.currentItem()
        if not item: return
        proj = item.data(Qt.UserRole)
        self.store.delete(proj)
        self.refresh()

    def _active_menu(self, pos):
        it = self.active.itemAt(pos)
        if not it: return
        menu = QMenu(self)
        act_done = menu.addAction("Пометить как завершённый")
        chosen = menu.exec(self.active.mapToGlobal(pos))
        if chosen == act_done:
            proj = it.data(Qt.UserRole)
            self.store.mark_completed(proj)
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
        top = QSplitter(Qt.Horizontal)
        self.orig = QPlainTextEdit(); self.orig.setPlaceholderText("Оригинал главы…")
        self.tran = QPlainTextEdit(); self.tran.setPlaceholderText("Перевод главы…")
        top.addWidget(self.orig); top.addWidget(self.tran); top.setSizes([600,600])
        self.split.addWidget(top)
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME); self.resize(1400,900)
        self.settings = QSettings(APP_ORG, APP_NAME)

        self.workdir = self._ensure_workdir()
        self.store = Archive(Path(self.workdir))

        root = QWidget(); self.setCentralWidget(root)
        lay = QVBoxLayout(root); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)

        # Top bar
        top_bar = QHBoxLayout(); top_bar.setContentsMargins(8,6,8,6); top_bar.setSpacing(8)
        self.btn_burger = QPushButton("☰"); self.btn_burger.setFixedWidth(32); self.btn_burger.clicked.connect(self._toggle_left_panel)
        self.btn_fullscreen = QPushButton("⛶"); self.btn_fullscreen.setFixedWidth(32); self.btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        title = QLabel(APP_NAME)
        top_bar.addWidget(self.btn_burger); top_bar.addWidget(title); top_bar.addStretch(1); top_bar.addWidget(self.btn_fullscreen)
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

    def _toggle_left_panel(self):
        if self.left_panel.isVisible():
            self.main_split.setSizes([0, 1])
            self.left_panel.setVisible(False)
        else:
            self.left_panel.setVisible(True)
            self.main_split.setSizes([280, 1120])
        self.settings.setValue("ui/main_split_state", self.main_split.saveState())

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()

    def _ensure_workdir(self)->str:
        wd = self.settings.value("app/workdir","")
        if wd and Path(wd).exists(): return wd
        dlg = QFileDialog(self,"Выберите рабочую папку")
        dlg.setFileMode(QFileDialog.Directory); dlg.setOption(QFileDialog.ShowDirsOnly, True); dlg.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        if dlg.exec(): chosen = dlg.selectedFiles()[0]
        else:
            chosen = str(Path.home() / "Documents" / "Парсер веб-новелл"); ensure_dir(Path(chosen))
        self.settings.setValue("app/workdir", chosen); return chosen

    def _bind_project(self, path: Path):
        self.editor.bind_project(path)

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(APP_ORG); app.setApplicationName(APP_NAME)
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
