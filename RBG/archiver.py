"""
archiver.py — Создание RAR архивов с авто-разбивкой на тома.

Требует установленного WinRAR или rar (Linux/macOS):
  Windows : C:\Program Files\WinRAR\rar.exe  (по умолчанию)
  Linux   : sudo apt install rar  /  brew install rar
"""

import os
import subprocess
import glob
import shutil
from pathlib import Path
from config import SPLIT_THRESHOLD_MB, VOLUME_SIZE_MB, DONE_DIR

# ❌ БЫЛО (вызов до определения функции → NameError):
# RAR_EXECUTABLE = _find_rar()
#
# ✅ СТАЛО: _find_rar() вызывается внутри create_rar_archive()
#    при каждом создании архива — никакой глобальной переменной


def _find_rar() -> str:
    """
    Найти исполняемый файл rar/WinRAR в системе.

    Проверяет стандартные пути Windows, затем PATH (Linux/macOS).
    Вызывается внутри create_rar_archive() при каждом запуске.

    Returns:
        str — путь к исполняемому файлу rar

    Raises:
        EnvironmentError — если rar не найден нигде
    """
    candidates = [
        r'C:\Program Files\WinRAR\rar.exe',
        r'C:\Program Files (x86)\WinRAR\rar.exe',
        'rar',    # Linux/macOS — ищет в PATH
        'rar5',   # некоторые дистрибутивы Linux
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
        if shutil.which(c):
            return c
    raise EnvironmentError(
        "❌ rar/WinRAR не найден!\n"
        "   Windows: установите WinRAR → https://www.rarlab.com\n"
        "   Linux  : sudo apt install rar\n"
        "   macOS  : brew install rar"
    )


def create_rar_archive(file_path: str, output_dir: str) -> list[str]:
    """
    Создать RAR архив из файла.

    Логика:
      - файл < SPLIT_THRESHOLD_MB  → один архив filename.rar
      - файл >= SPLIT_THRESHOLD_MB → тома filename.part1.rar, .part2.rar, ...

    Args:
        file_path : полный путь к исходному файлу
        output_dir: папка для сохранения архива/томов

    Returns:
        list[str] — отсортированный список путей к созданным .rar файлам
    """
    # _find_rar() вызывается здесь — после определения функции ✅
    rar_exe = _find_rar()

    file_path  = Path(file_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    archive_name = file_path.stem        # имя без расширения
    archive_path = output_dir / f"{archive_name}.rar"

    if file_size_mb < SPLIT_THRESHOLD_MB:
        # ── Один архив без разбивки ─────────────────
        cmd = [
            rar_exe,
            'a',               # add
            '-ep',             # не хранить пути внутри архива
            '-m5',             # максимальное сжатие
            '-y',              # yes to all (без интерактивных вопросов)
            str(archive_path),
            str(file_path),
        ]
    else:
        # ── Разбивка на тома по VOLUME_SIZE_MB МБ ───
        cmd = [
            rar_exe,
            'a',
            '-ep',
            '-m5',
            '-y',
            f'-v{VOLUME_SIZE_MB}m',  # размер одного тома
            str(archive_path),
            str(file_path),
        ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"❌ Ошибка RAR (код {result.returncode}):\n{result.stderr}"
        )

    # Собрать все созданные части (*.rar) в папке
    pattern = str(output_dir / f"{archive_name}*.rar")
    parts   = sorted(glob.glob(pattern))

    if not parts:
        raise RuntimeError(
            f"❌ RAR завершился без ошибок, но архив не найден: {pattern}"
        )

    # Переместить исходный файл в done_files/
    done = Path(DONE_DIR)
    done.mkdir(parents=True, exist_ok=True)
    shutil.move(str(file_path), str(done))

    return parts
