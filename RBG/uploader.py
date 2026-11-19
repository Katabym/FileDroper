"""
github_uploader.py — Загрузка файлов в GitHub через REST API.

Не требует git CLI — работает через requests + GitHub API.
Токен задаётся в config.py → GITHUB_TOKEN
"""

import base64
import json
import os
from pathlib import Path
from datetime import datetime

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


def _get_file_sha(remote_path: str) -> str | None:
    """Получить SHA файла если он уже существует (для обновления)."""
    url = f"{API_BASE}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{remote_path}"
    r = requests.get(url, headers=_headers())
    if r.status_code == 200:
        return r.json().get('sha')
    return None


def upload_file(local_path: str) -> bool:
    """
    Загрузить один файл в GitHub репозиторий.

    Args:
        local_path: путь к .txt файлу на диске

    Returns:
        True при успехе, False при ошибке
    """
    local_path = Path(local_path)
    filename = local_path.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    remote_path = f"{GITHUB_UPLOAD_DIR}/{timestamp}_{filename}"

    # Читаем и кодируем содержимое в base64 для API
    with open(local_path, 'rb') as f:
        content_b64 = base64.b64encode(f.read()).decode('utf-8')

    url = f"{API_BASE}/repos/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{remote_path}"
    sha = _get_file_sha(remote_path)

    body = {
        "message": f"Upload {filename} [{timestamp}]",
        "content": content_b64,
        "branch" : GITHUB_BRANCH,
    }
    if sha:
        body["sha"] = sha  # Обновить существующий файл

    r = requests.put(url, headers=_headers(), data=json.dumps(body))

    if r.status_code in (200, 201):
        html_url = r.json().get('content', {}).get('html_url', '')
        print(f"   ✅ {filename} → {html_url}")
        return True
    else:
        print(f"   ❌ Ошибка загрузки {filename}: {r.status_code} {r.text[:200]}")
        return False


def upload_to_github(txt_files: list[str]) -> None:
    """Загрузить список .txt файлов в GitHub."""
    if not GITHUB_TOKEN or GITHUB_TOKEN == 'ghp_ВАШ_ТОКЕН_ЗДЕСЬ':
        print("\n❌ GitHub токен не настроен!")
        print("   Укажите GITHUB_TOKEN в файле config.py\n")
        return

    success = 0
    for i, txt_file in enumerate(txt_files, 1):
        print(f"   [{i}/{len(txt_files)}] Загружаю: {Path(txt_file).name}")
        if upload_file(txt_file):
            success += 1

    print(f"\n{'✅' if success == len(txt_files) else '⚠️'} "
          f"Загружено: {success}/{len(txt_files)} файлов\n")
