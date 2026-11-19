"""
github_cleaner.py — Очистка папки uploads/ в GitHub репозитории.

Удаляет все .txt файлы из GITHUB_UPLOAD_DIR через GitHub REST API.
Вызывается после успешного получения и распаковки файлов.
"""

import json
from pathlib import Path

try:
    import requests
except ImportError:
    raise ImportError("Установите: pip install requests")

from config import (
    GITHUB_TOKEN, GITHUB_USERNAME,
    GITHUB_REPO, GITHUB_UPLOAD_DIR, GITHUB_BRANCH
)

API_BASE = "https://api.github.com"


def _headers() -> dict:
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept"       : "application/vnd.github.v3+json",
        "Content-Type" : "application/json",
    }


def _list_remote_files() -> list[dict]:
    """Получить список файлов из папки uploads/ в репозитории."""
    url = (
        f"{API_BASE}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
        f"/contents/{GITHUB_UPLOAD_DIR}?ref={GITHUB_BRANCH}"
    )
    r = requests.get(url, headers=_headers())

    if r.status_code == 404:
        print(f"   ℹ️  Папка '{GITHUB_UPLOAD_DIR}' уже пуста или не существует.")
        return []
    if r.status_code != 200:
        print(f"   ❌ Ошибка API: {r.status_code} — {r.text[:200]}")
        return []

    return [
        item for item in r.json()
        if item.get('type') == 'file'
    ]


def _delete_file(item: dict) -> bool:
    """
    Удалить один файл из репозитория через GitHub API.

    Для удаления нужен SHA файла, который берётся из списка.
    """
    url = (
        f"{API_BASE}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}"
        f"/contents/{item['path']}"
    )
    body = {
        "message": f"🧹 Clean: remove {item['name']}",
        "sha"    : item['sha'],
        "branch" : GITHUB_BRANCH,
    }
    r = requests.delete(url, headers=_headers(), data=json.dumps(body))

    if r.status_code == 200:
        print(f"   🗑️  Удалён: {item['name']}")
        return True
    else:
        print(f"   ❌ Не удалось удалить {item['name']}: {r.status_code}")
        return False


def clean_github_repo() -> None:
    """
    Основная функция: удалить все файлы из папки uploads/ в GitHub.

    Используется после успешного скачивания и распаковки на стороне
    получателя, чтобы освободить место и убрать следы передачи.
    """
    if not GITHUB_TOKEN or GITHUB_TOKEN == 'ghp_ВАШ_ТОКЕН_ЗДЕСЬ':
        print("\n❌ GitHub токен не настроен в config.py!\n")
        return

    print(f"\n🔍 Получение списка файлов из GitHub ({GITHUB_UPLOAD_DIR}/)...")
    files = _list_remote_files()

    if not files:
        print("   ✅ Репозиторий уже чист.\n")
        return

    print(f"   📋 Файлов для удаления: {len(files)}")

    deleted = 0
    for i, item in enumerate(files, 1):
        print(f"   [{i}/{len(files)}] Удаляю: {item['name']}")
        if _delete_file(item):
            deleted += 1

    status = '✅' if deleted == len(files) else '⚠️'
    print(f"\n{status} Удалено: {deleted}/{len(files)} файлов из репозитория.\n")
