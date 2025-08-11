# -*- coding: utf-8 -*-
import re
from pathlib import Path
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from typing import Iterable, Tuple

INVALID = r'<>:"/\\|?*'

def safe_name(name: str, maxlen: int = 120) -> str:
    name = name.strip()
    for ch in INVALID:
        name = name.replace(ch, "_")
    name = re.sub(r'\s+', ' ', name).strip()
    if len(name) > maxlen:
        name = name[:maxlen].rstrip()
    return name or "chapter"

def save_chapter_docx(folder: Path, chapter_title: str, text: str, index: int = None):
    folder.mkdir(parents=True, exist_ok=True)
    base = safe_name(chapter_title)
    filename = f"{index:03d} {base}.docx" if index is not None else f"{base}.docx"
    path = folder / filename
    doc = Document()
    h = doc.add_heading(chapter_title, level=1)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for line in text.split("\n"):
        if line.strip():
            doc.add_paragraph(line.strip())
        else:
            doc.add_paragraph()
    doc.save(path)
    return path


def _add_toc(doc: Document):
    para = doc.add_paragraph()
    run = para.add_run()
    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "begin")
    run._r.append(fld_char)

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = 'TOC \\o "1-3" \\h \\z \\u'
    run._r.append(instr)

    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "separate")
    run._r.append(fld_char)

    fld_char = OxmlElement("w:fldChar")
    fld_char.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char)


def save_book_docx(chapters: Iterable[Tuple[str, str]], toc: bool = True, path: Path | str | None = None):
    """Create a single DOCX file from chapters.

    Args:
        chapters: iterable of (title, text)
        toc: include table of contents
        path: optional destination path to save

    Returns:
        Document object. If *path* provided, file is saved and path returned.
    """

    doc = Document()
    if toc:
        doc.add_heading("Оглавление", level=1)
        _add_toc(doc)
        doc.add_page_break()

    chapters = list(chapters)
    for i, (title, text) in enumerate(chapters, start=1):
        doc.add_heading(title, level=1)
        for line in text.split("\n"):
            if line.strip():
                doc.add_paragraph(line.strip())
            else:
                doc.add_paragraph()
        if i < len(chapters):
            doc.add_page_break()
    if path:
        doc.save(path)
        return path
    return doc


def save_book_pdf(chapters: Iterable[Tuple[str, str]], path: Path | str):
    """Save chapters as PDF using pdfkit."""
    import pdfkit

    html_parts = []
    for title, text in chapters:
        html_parts.append(f"<h1>{title}</h1>")
        html_parts.append("<p>" + "<br/>".join(map(lambda s: s.strip(), text.splitlines())) + "</p>")
    html = "\n".join(html_parts)
    pdfkit.from_string(html, str(path))
    return Path(path)


def save_book_epub(chapters: Iterable[Tuple[str, str]], path: Path | str):
    """Save chapters as EPUB using ebooklib."""
    from ebooklib import epub

    book = epub.EpubBook()
    book.set_identifier("id")
    book.set_title("Book")
    book.set_language("ru")

    toc = []
    spine = ['nav']
    for i, (title, text) in enumerate(chapters, start=1):
        c = epub.EpubHtml(title=title, file_name=f"chap_{i}.xhtml", lang='ru')
        content = text.replace("\n", "<br/>")
        c.content = f"<h1>{title}</h1><p>{content}</p>"
        book.add_item(c)
        toc.append(c)
        spine.append(c)

    book.toc = tuple(toc)
    book.spine = spine
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    epub.write_epub(str(path), book)
    return Path(path)
