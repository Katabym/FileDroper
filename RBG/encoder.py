"""
encoder.py — Кодирование RAR файлов в Base64 .txt
"""

import base64
import json
import os
from pathlib import Path
from config import CLEANUP_TEMP


def encode_to_txt(rar_parts: list[str], output_dir: str) -> list[str]:
    """
    Закодировать список RAR файлов в .txt (Base64 + JSON).

    Каждый .rar файл → отдельный .txt файл.

    Args:
        rar_parts  : список путей к .rar файлам
        output_dir : папка для сохранения .txt

    Returns:
        list[str] — пути к созданным .txt файлам
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    txt_files = []

    for rar_path in rar_parts:
        rar_path = Path(rar_path)
        txt_filename = rar_path.stem + '.txt'
        txt_path = output_dir / txt_filename

        # Читаем бинарные данные
        with open(rar_path, 'rb') as f:
            binary_data = f.read()

        # Кодируем в Base64
        b64_data = base64.b64encode(binary_data).decode('utf-8')

        # Формируем JSON пакет с метаданными
        payload = {
            'filename'    : rar_path.name,
            'original_name': rar_path.stem,
            'size_bytes'  : len(binary_data),
            'encoding'    : 'base64',
            'filedata'    : b64_data,
        }

        # Записываем .txt
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(payload, ensure_ascii=False))

        txt_files.append(str(txt_path))

        # Удалить временный RAR файл после кодирования
        if CLEANUP_TEMP:
            rar_path.unlink()

    return txt_files


def get_txt_info(txt_path: str) -> dict:
    """Прочитать метаданные из .txt файла (без декодирования)."""
    with open(txt_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if k != 'filedata'}
