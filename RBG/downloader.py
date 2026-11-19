"""
github_downloader.py — Скачивание .txt файлов из GitHub репозитория.

Скачивает все файлы из папки GITHUB_UPLOAD_DIR репозитория
и сохраняет их в локальную папку received_txt/.
"""

import base64
import os
from pathlib import Path

try:
    import requests
except ImportError:
    raise ImportError("Установите: pip install requests")

from config import (
    GITHUB_TOKEN, GITHUB_USERNAME,
    GITHUB_REPO, GITHUB_UPLOAD_DIR, GITHUB_BRANCH,
    RECEIVED_TXT_DIR
)

API_BASE = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept"       : "application/vnd.github.v3+json",
    }


def _list_remote_files() -> list[dict]:
    """Получить список файлов из GITHUB_UPLOAD_DIR в репозитории."""
    url = (
        f"{API_BASE}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
        f"/contents/{GITHUB_UPLOAD_DIR}?ref={GITHUB_BRANCH}"
    )
    r = requests.get(url, headers=_headers())

    if r.status_code == 404:
        print(f"   ⚠️  Папка '{GITHUB_UPLOAD_DIR}' в репозитории не найдена или пуста.")
        return []
    if r.status_code != 200:
        print(f"   ❌ Ошибка получения списка файлов: {r.status_code}")
        return []

    # Фильтруем только .txt файлы
    items = r.json()
    txt_files = [
        item for item in items
        if item.get('type') == 'file'
        and item.get('name', '').endswith('.txt')
    ]
    return txt_files


def download_file(item: dict, dest_dir: Path) -> str | None:
    """
    Скачать один файл из GitHub и сохранить локально.

    Args:
        item    : объект из GitHub API (name, download_url, sha ...)
        dest_dir: локальная папка назначения

    Returns:
        Путь к сохранённому файлу или None при ошибке
    """
    filename     = item['name']
    download_url = item['download_url']
    local_path   = dest_dir / filename

    # Если файл уже скачан — пропустить
    if local_path.exists():
        print(f"   ⏭️  Пропущен (уже есть): {filename}")
        return str(local_path)

    r = requests.get(download_url, headers=_headers(), stream=True)
    if r.status_code != 200:
        print(f"   ❌ Не удалось скачать {filename}: {r.status_code}")
        return None

    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = local_path.stat().st_size / 1024
    print(f"   ✅ Скачан: {filename}  ({size_kb:.1f} КБ)")
    return str(local_path)


def download_from_github() -> list[str]:
    """
    Основная функция: скачать все .txt файлы из GitHub.

    Returns:
        Список путей к скачанным файлам.
    """
    if not GITHUB_TOKEN or GITHUB_TOKEN == 'ghp_ВАШ_ТОКЕН_ЗДЕСЬ':
        print("\n❌ GitHub токен не настроен в config.py!\n")
        return []

    dest_dir = Path(RECEIVED_TXT_DIR)
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n🔍 Получение списка файлов из GitHub ({GITHUB_UPLOAD_DIR}/)...")
    remote_files = _list_remote_files()

    if not remote_files:
        print("   📭 В репозитории нет .txt файлов для скачивания.")
        return []

    print(f"   📋 Найдено файлов: {len(remote_files)}")
    downloaded = []

    for i, item in enumerate(remote_files, 1):
        print(f"   [{i}/{len(remote_files)}] {item['name']}")
        path = download_file(item, dest_dir)
        if path:
            downloaded.append(path)

    print(f"\n✅ Скачано: {len(downloaded)}/{len(remote_files)} файлов")
    print(f"📂 Сохранены в: {RECEIVED_TXT_DIR}/\n")
    return downloaded
