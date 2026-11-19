"""
decoder.py — Декодирование и распаковка файлов.

Вызывается из main.py (режим получателя) или напрямую:
  python decoder.py

Ожидает .txt файлы в RECEIVED_TXT_DIR (config.py).
Итоговые файлы сохраняет в OUTPUT_DIR.
Для распаковки RAR нужен WinRAR или unrar.
"""

import base64
import json
import os
import glob
import shutil
import subprocess
from pathlib import Path
from config import RECEIVED_TXT_DIR, DECODED_RAR_DIR, OUTPUT_DIR


def _setup():
    for d in [RECEIVED_TXT_DIR, DECODED_RAR_DIR, OUTPUT_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)


def _find_rar_tool() -> str:
    """Найти unrar или rar для распаковки."""
    candidates = [
        r'C:\Program Files\WinRAR\unrar.exe',
        r'C:\Program Files\WinRAR\rar.exe',
        'unrar', 'rar',
    ]
    for c in candidates:
        if os.path.isfile(c) or shutil.which(c):
            return c
    raise EnvironmentError("❌ unrar/WinRAR не найден! Установите и добавьте в PATH.")


def _decode_txt_to_rar(txt_path: str) -> str | None:
    """Декодировать один .txt файл обратно в .rar."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        filename  = payload['filename']
        rar_bytes = base64.b64decode(payload['filedata'])

        rar_path = Path(DECODED_RAR_DIR) / filename
        with open(rar_path, 'wb') as f:
            f.write(rar_bytes)

        size_kb = len(rar_bytes) / 1024
        print(f"   ✅ Декодирован: {filename}  ({size_kb:.1f} КБ)")
        return str(rar_path)

    except (KeyError, json.JSONDecodeError) as e:
        print(f"   ❌ Ошибка чтения {Path(txt_path).name}: {e}")
        return None


def _extract_rar(rar_path: str) -> bool:
    """Распаковать .rar архив в OUTPUT_DIR. Возвращает True при успехе."""
    tool = _find_rar_tool()
    # unrar e archive.rar ./output/ -y  (-y = yes to all prompts)
    cmd = [tool, 'e', rar_path, str(Path(OUTPUT_DIR)) + '/', '-y']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ⚠️  Ошибка распаковки: {result.stderr[:200]}")
        return False
    print(f"   📦 Распаковано → {OUTPUT_DIR}/")
    return True


def run_decoder() -> bool:
    """
    Основная функция декодирования.

    Читает .txt из RECEIVED_TXT_DIR, восстанавливает .rar,
    распаковывает в OUTPUT_DIR.

    Returns:
        True  — если хотя бы один файл успешно распакован
        False — при ошибке или отсутствии файлов
    """
    _setup()

    txt_files = sorted(glob.glob(
        os.path.join(RECEIVED_TXT_DIR, '*.txt')
    ))

    if not txt_files:
        print(f"\n⚠️  В папке {RECEIVED_TXT_DIR}/ нет .txt файлов.\n")
        return False

    print(f"\n📥 .txt файлов для декодирования: {len(txt_files)}")

    # ШАГ 1: Декодирование .txt → .rar
    print("\n🔓 Декодирование Base64 → .rar ...")
    rar_files = []
    for txt in txt_files:
        rar = _decode_txt_to_rar(txt)
        if rar:
            rar_files.append(rar)

    if not rar_files:
        print("\n❌ Ни один файл не был декодирован.\n")
        return False

    # ШАГ 2: Найти первые части (для многотомных архивов)
    # WinRAR/unrar сам найдёт остальные части по имени part1
    # Одиночный архив: name.rar (без part) → тоже берём
    first_parts = []
    seen_bases  = set()

    for rar in sorted(rar_files):
        stem = Path(rar).stem            # e.g. "video.part1" or "doc"
        if 'part' in stem:
            # Многотомный: берём только part1
            base = stem.rsplit('.', 1)[0]   # "video"
            if base not in seen_bases and stem.endswith('part01'):
                first_parts.append(rar)
                seen_bases.add(base)
        else:
            # Одиночный архив
            first_parts.append(rar)

    # ШАГ 3: Распаковка
    print(f"\n📦 Распаковка ({len(first_parts)} архив(ов))...")
    ok_count = 0
    for rar in first_parts:
        print(f"   Архив: {Path(rar).name}")
        if _extract_rar(rar):
            ok_count += 1

    if ok_count > 0:
        print(f"\n✅ Успешно распаковано: {ok_count}/{len(first_parts)}")
        print(f"📂 Файлы в папке: {OUTPUT_DIR}/\n")
        return True
    else:
        print("\n❌ Распаковка не удалась.\n")
        return False


# ────────────────────────────────────────────────
# Запуск напрямую (без main.py)
# ────────────────────────────────────────────────
if __name__ == '__main__':
    run_decoder()
