# -*- coding: utf-8 -*-
"""
site_profiles.py — профили сайтов (M2.1, fixed)
- RoyalRoad (устойчивые селекторы)
- MVLEmpyr
- Novatls
- Ellotl
"""

import re
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"
}

def get(url, **kw):
    kw.setdefault("headers", HEADERS)
    resp = requests.get(url, **kw, timeout=30)
    resp.raise_for_status()
    return resp

def normalize_whitespace(text: str) -> str:
    text = re.sub(r'\r\n?', '\n', text)
    text = re.sub(r'\u00A0', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def text_from_nodes(soup, selectors: List[str]) -> str:
    for sel in selectors:
        node = soup.select_one(sel)
        if node:
            for bad in node.select('script,style,ins,iframe,nav,header,footer'):
                bad.decompose()
            for br in node.find_all("br"):
                br.replace_with("\n")
            txt = node.get_text("\n", strip=False)
            return normalize_whitespace(txt)
    return ""

@dataclass
class Chapter:
    title: str
    url: str

class BaseProfile:
    domains: List[str] = []
    def detect(self, url: str) -> bool:
        host = urllib.parse.urlparse(url).netloc.lower()
        return any(d in host for d in self.domains)
    def parse_book(self, url: str) -> Tuple[str, List[Chapter]]:
        raise NotImplementedError
    def fetch_chapter(self, url: str) -> Tuple[str, str]:
        raise NotImplementedError

# ---------- RoyalRoad (fixed) ----------
class RoyalRoadProfile(BaseProfile):
    domains = ["royalroad.com", "www.royalroad.com"]

    def _fiction_base(self, url: str) -> str:
        p = urllib.parse.urlparse(url)
        parts = p.path.strip("/").split("/")
        if len(parts) >= 3 and parts[0] == "fiction":
            base_path = "/" + "/".join(parts[:3])
        else:
            base_path = p.path
        return urllib.parse.urlunparse((p.scheme, p.netloc, base_path, "", "", ""))

    def parse_book(self, url: str) -> Tuple[str, List[Chapter]]:
        r = get(url)
        soup = BeautifulSoup(r.text, "lxml")

        title_el = soup.select_one("h1.fiction-title, h1")
        book_title = title_el.get_text(strip=True) if title_el else "RoyalRoad_Fiction"

        base = self._fiction_base(url)
        chapters: List[Chapter] = []

        # Ссылки, начинающиеся с <base>/chapter/
        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href:
                continue
            abs_url = urllib.parse.urljoin(url, href)
            if abs_url.startswith(base + "/chapter/"):
                txt = a.get_text(strip=True)
                if txt:
                    chapters.append(Chapter(txt, abs_url))

        # Запасной вариант
        if not chapters:
            for a in soup.select("table#chapters a, .chapter-list a, a.chapter-title"):
                href = a.get("href")
                if not href:
                    continue
                abs_url = urllib.parse.urljoin(url, href)
                if "/chapter/" in abs_url:
                    txt = a.get_text(strip=True)
                    if txt:
                        chapters.append(Chapter(txt, abs_url))

        uniq, seen = [], set()
        for ch in chapters:
            if ch.url not in seen:
                uniq.append(ch); seen.add(ch.url)
        return book_title, uniq

    def fetch_chapter(self, url: str) -> Tuple[str, str]:
        r = get(url)
        soup = BeautifulSoup(r.text, "lxml")
        title = soup.select_one("h1.chapter-title, h1, .chapter-title")
        ch_title = title.get_text(strip=True) if title else "Chapter"
        body = text_from_nodes(
            soup,
            ["div.chapter-content", "div.chapter-inner", "div.fic-section", "article", "div#chapter-content"]
        )
        return ch_title, body

# ---------- MVLEmpyr ----------
class MVLEmpyrProfile(BaseProfile):
    domains = ["mvlempyr.com", "www.mvlempyr.com"]
    def parse_book(self, url: str) -> Tuple[str, List[Chapter]]:
        r = get(url); soup = BeautifulSoup(r.text, "lxml")
        title_el = soup.select_one("h1.entry-title, h1[class*=novel], h1")
        book_title = title_el.get_text(strip=True) if title_el else "MVLEmpyr_Novel"
        chapters: List[Chapter] = []
        for a in soup.select(".chapter-list a, .epl-list a, .wp-block-list a, .su-posts a"):
            txt = a.get_text(strip=True); href = a.get("href")
            if href and txt:
                chapters.append(Chapter(txt, urllib.parse.urljoin(url, href)))
        if not chapters:
            for a in soup.select("a[href]"):
                href = a.get("href")
                if href and "/chapter" in href:
                    txt = a.get_text(strip=True)
                    if txt:
                        chapters.append(Chapter(txt, urllib.parse.urljoin(url, href)))
        uniq, seen = [], set()
        for ch in chapters:
            if ch.url not in seen:
                uniq.append(ch); seen.add(ch.url)
        return book_title, uniq
    def fetch_chapter(self, url: str) -> Tuple[str, str]:
        r = get(url); soup = BeautifulSoup(r.text, "lxml")
        t = soup.select_one("h1.entry-title, h1[class*=chapter], h1")
        ch_title = t.get_text(strip=True) if t else "Chapter"
        body = text_from_nodes(soup, ["article","div.entry-content","div#chapter-content","div.text-left"])
        return ch_title, body

# ---------- Novatls ----------
class NovatlsProfile(BaseProfile):
    domains = ["novatls.com", "www.novatls.com"]
    def parse_book(self, url: str) -> Tuple[str, List[Chapter]]:
        r = get(url); soup = BeautifulSoup(r.text, "lxml")
        title_el = soup.select_one("h1.entry-title, h1")
        book_title = title_el.get_text(strip=True) if title_el else "Novatls_Series"
        chapters: List[Chapter] = []
        for a in soup.select(".epl-list a, .chapter-list a, .wp-block-list a"):
            txt = a.get_text(strip=True); href = a.get("href")
            if href and txt:
                chapters.append(Chapter(txt, urllib.parse.urljoin(url, href)))
        if not chapters:
            for a in soup.select("a[href*='/chapter']"):
                txt = a.get_text(strip=True); href = a.get("href")
                chapters.append(Chapter(txt, urllib.parse.urljoin(url, href)))
        uniq, seen = [], set()
        for ch in chapters:
            if ch.url not in seen:
                uniq.append(ch); seen.add(ch.url)
        return book_title, uniq
    def fetch_chapter(self, url: str) -> Tuple[str, str]:
        r = get(url); soup = BeautifulSoup(r.text, "lxml")
        t = soup.select_one("h1.entry-title, h1")
        ch_title = t.get_text(strip=True) if t else "Chapter"
        body = text_from_nodes(soup, ["article","div.entry-content","div#chapter-content"])
        return ch_title, body

# ---------- Ellotl ----------
class EllotlProfile(BaseProfile):
    domains = ["ellotl.com","www.ellotl.com"]
    def parse_book(self, url: str) -> Tuple[str, List[Chapter]]:
        r = get(url); soup = BeautifulSoup(r.text, "lxml")
        title_el = soup.select_one("h1.entry-title, h1")
        book_title = title_el.get_text(strip=True) if title_el else "Ellotl_Series"
        chapters: List[Chapter] = []
        for a in soup.select(".chapter-list a, .epl-list a, .wp-block-list a"):
            txt = a.get_text(strip=True); href = a.get("href")
            if href and txt:
                chapters.append(Chapter(txt, urllib.parse.urljoin(url, href)))
        uniq, seen = [], set()
        for ch in chapters:
            if ch.url not in seen:
                uniq.append(ch); seen.add(ch.url)
        return book_title, uniq
    def fetch_chapter(self, url: str) -> Tuple[str, str]:
        r = get(url); soup = BeautifulSoup(r.text, "lxml")
        t = soup.select_one("h1.entry-title, h1")
        ch_title = t.get_text(strip=True) if t else "Chapter"
        body = text_from_nodes(soup, ["article","div.entry-content","div#chapter-content"])
        return ch_title, body

# Registry
PROFILES = [RoyalRoadProfile(), MVLEmpyrProfile(), NovatlsProfile(), EllotlProfile()]

def detect_profile(url: str) -> Optional[BaseProfile]:
    for p in PROFILES:
        if p.detect(url):
            return p
    return None
