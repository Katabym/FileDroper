import os
from pathlib import Path


def reverse_txt_files(folder_path="."):
    # Превращаем путь в объект Path
    directory = Path(folder_path)

    # Ищем все файлы с расширением .txt
    txt_files = list(directory.glob("*.txt"))

    if not txt_files:
        print("Файлы .txt не найдены в указанной папке.")
        return

    for file_path in txt_files:
        # Пропускаем файлы, которые уже были обработаны ранее
        if file_path.stem.endswith("_reversed"):
            continue

        try:
            # Читаем файл (utf-8 гарантирует корректность всех символов)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Отзеркаливаем содержимое
            reversed_content = content[::-1]

            # Создаем имя для нового файла (например: test.txt -> test_reversed.txt)
            new_file_name = f"{file_path.stem}_reversed{file_path.suffix}"
            new_file_path = file_path.parent / new_file_name

            # Записываем развернутый текст в новый файл
            with open(new_file_path, "w", encoding="utf-8") as f:
                f.write(reversed_content)

            print(f"Успешно обработан: {file_path.name} -> {new_file_name}")

        except Exception as e:
            print(f"Ошибка при обработке файла {file_path.name}: {e}")


# Запуск скрипта
if __name__ == "__main__":
    # По умолчанию ищет файлы в той же папке, где лежит сам скрипт.
    # Если файлы в другом месте, укажите путь, например: reverse_txt_files("C:/my_folder")
    reverse_txt_files()
