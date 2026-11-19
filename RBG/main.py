#!/usr/bin/env python3
"""
main.py — Точка входа приложения FileConvert & Sender v2.1
Режимы: Отправитель (архив → encode → GitHub push)
        Получатель  (GitHub pull → decode → распаковка → очистка репо)
"""

import os
import sys
from pathlib import Path
from config import INPUT_DIR, ENCODED_DIR, TEMP_RAR_DIR, DONE_DIR
from archiver import create_rar_archive
from encoder import encode_to_txt
from uploader import upload_to_github
from downloader import download_from_github
from cleaner import clean_github_repo
from decoder import run_decoder


def setup_dirs():
    """Создать рабочие директории если не существуют."""
    for d in [INPUT_DIR, ENCODED_DIR, TEMP_RAR_DIR, DONE_DIR]:
        Path(d).mkdir(parents=True, exist_ok=True)


# ════════════════════════════════════════════════
#  РЕЖИМ ОТПРАВИТЕЛЯ
# ════════════════════════════════════════════════

def sender_process_files() -> list[str]:
    """Архивировать и закодировать все файлы из INPUT_DIR."""
    files = [
        f for f in os.listdir(INPUT_DIR)
        if os.path.isfile(os.path.join(INPUT_DIR, f))
        and not f.startswith('.')
    ]

    if not files:
        print("\n⚠️  Папка input_files/ пуста. Добавьте файлы и запустите снова.\n")
        return []

    print(f"\n📁 Найдено файлов: {len(files)}")
    encoded_files = []

    for filename in files:
        file_path = os.path.join(INPUT_DIR, filename)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        print(f"\n{'─'*50}")
        print(f"📄 Обработка: {filename}  ({file_size_mb:.2f} МБ)")

        print("   🗜️  Архивация в RAR...")
        rar_parts = create_rar_archive(file_path, TEMP_RAR_DIR)
        print(f"   ✅ Томов создано: {len(rar_parts)}")

        print("   🔒 Кодирование Base64 → .txt...")
        txt_files = encode_to_txt(rar_parts, ENCODED_DIR)
        encoded_files.extend(txt_files)
        print(f"   ✅ .txt готово: {len(txt_files)}")

    print(f"\n{'─'*50}")
    print(f"✅ Все файлы обработаны! .txt файлы в: {ENCODED_DIR}/")
    print(f"   Всего .txt: {len(encoded_files)}\n")
    return encoded_files


def sender_menu():
    """Меню отправителя."""
    encoded_files = sender_process_files()
    if not encoded_files:
        return

    print("━" * 52)
    print("  📤 Что сделать с зашифрованными файлами?")
    print("━" * 52)
    print(f"  [1] 📂 Оставить в папке {ENCODED_DIR}/ (взять вручную)")
    print("  [2] ☁️  Загрузить в GitHub репозиторий")
    print("  [0] 🚪 Выход")
    print("━" * 52)

    choice = _ask("Ваш выбор", ['0', '1', '2'])

    if choice == '0':
        print("\n👋 Выход.\n"); sys.exit(0)
    elif choice == '1':
        print(f"\n📂 Файлы в папке: {ENCODED_DIR}/  — заберите вручную.\n")
    elif choice == '2':
        print("\n☁️  Загрузка в GitHub...")
        upload_to_github(encoded_files)


# ════════════════════════════════════════════════
#  РЕЖИМ ПОЛУЧАТЕЛЯ
# ════════════════════════════════════════════════

def receiver_menu():
    """Меню получателя: скачать → декодировать → распаковать → очистить."""
    print("━" * 52)
    print("  📥 Откуда брать зашифрованные .txt файлы?")
    print("━" * 52)
    print("  [1] ☁️  Скачать автоматически с GitHub")
    print("  [2] 📂 Файлы уже лежат в папке received_txt/")
    print("  [0] 🚪 Выход")
    print("━" * 52)

    choice = _ask("Ваш выбор", ['0', '1', '2'])

    if choice == '0':
        print("\n👋 Выход.\n"); sys.exit(0)

    elif choice == '1':
        print("\n☁️  Скачивание с GitHub...")
        downloaded = download_from_github()
        if not downloaded:
            print("⚠️  Нечего скачивать.\n")
            return

    # Декодирование и распаковка
    print("\n🔓 Декодирование и распаковка...")
    success = run_decoder()

    if success:
        ask_clean_repo()


def ask_clean_repo():
    """Спросить об очистке репозитория после успешного получения."""
    print("━" * 52)
    print("  🧹 Файлы успешно распакованы!")
    print("  Очистить репозиторий GitHub от .txt файлов?")
    print("━" * 52)
    print("  [1] 🧹 Да, удалить файлы из репозитория")
    print("  [2] ⏭️  Нет, оставить как есть")
    print("━" * 52)

    choice = _ask("Ваш выбор", ['1', '2'])
    if choice == '1':
        print("\n🧹 Очистка репозитория...")
        clean_github_repo()
    else:
        print("\n⏭️  Репозиторий оставлен без изменений.\n")


# ════════════════════════════════════════════════
#  УТИЛИТЫ
# ════════════════════════════════════════════════

def _ask(prompt: str, options: list[str]) -> str:
    """Безопасный ввод с проверкой допустимых значений."""
    opts = '/'.join(options)
    while True:
        val = input(f"  {prompt} ({opts}): ").strip()
        if val in options:
            return val
        print(f"  ⚠️  Введите одно из: {opts}")


# ════════════════════════════════════════════════
#  ГЛАВНОЕ МЕНЮ
# ════════════════════════════════════════════════

def main_menu():
    print("""
╔══════════════════════════════════════╗
║   FileConvert & Sender  v2.1         ║
║   RAR → Base64 ↔ GitHub  ↔  RAR      ║
╚══════════════════════════════════════╝""")
    print("━" * 52)
    print("  Выберите режим работы:")
    print("━" * 52)
    print("  [1] 📤 Отправитель  — упаковать и отправить файлы")
    print("  [2] 📥 Получатель   — скачать, декодировать, распаковать")
    print("  [3] 🧹 Очистка репо — удалить все .txt из GitHub вручную")
    print("  [0] 🚪 Выход")
    print("━" * 52)

    choice = _ask("Ваш выбор", ['0', '1', '2', '3'])

    if   choice == '0': print("\n👋 До свидания!\n"); sys.exit(0)
    elif choice == '1': sender_menu()
    elif choice == '2': receiver_menu()
    elif choice == '3':
        print("\n🧹 Ручная очистка репозитория...")
        clean_github_repo()


if __name__ == '__main__':
    while True:
        setup_dirs()
        main_menu()
