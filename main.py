import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

def parse_kindle_highlights(text):
    """Парсит текст экспорта Kindle и возвращает структурированные данные"""
    
    # Разделяем на отдельные записи
    entries = text.split('\n==========\n')
    
    books = defaultdict(list)
    current_book = None
    
    for entry in entries:
        if not entry.strip():
            continue
            
        lines = entry.strip().split('\n')
        
        # Первая строка - обычно название книги или метаданные
        if lines[0].startswith('﻿') or '(' in lines[0]:
            current_book = lines[0].replace('﻿', '').strip()
            
            # Извлекаем автора из названия книги
            book_match = re.search(r'(.*?)\s*\((.*?)\)', current_book)
            if book_match:
                book_title = book_match.group(1).strip()
                book_author = book_match.group(2).strip()
            else:
                book_title = current_book
                book_author = "Unknown"
            
            # Если есть метаданные и контент
            if len(lines) >= 2:
                metadata = lines[1] if lines[1].startswith('–') else None
                content = '\n'.join(lines[2:]).strip() if len(lines) > 2 else ""
                
                if metadata:
                    entry_data = {
                        'metadata': metadata,
                        'content': content,
                        'book_title': book_title,
                        'book_author': book_author
                    }
                    books[book_title].append(entry_data)
    
    return books

def create_obsidian_note(book_title, book_author, entries):
    """Создает markdown заметку для Obsidian"""
    
    # Создаем безопасное имя файла
    safe_filename = re.sub(r'[<>:"/\\|?*]', '', book_title)
    safe_filename = safe_filename[:100]  # Ограничиваем длину
    
    note = f"""---
title: {book_title}
author: {book_author}
type: book
tags: 
  - book
  - highlights
date: {datetime.now().strftime('%Y-%m-%d')}
---

# {book_title}

**Автор:** {book_author}

---

## Заметки и выделения

"""
    
    for i, entry in enumerate(entries, 1):
        metadata = entry['metadata']
        content = entry['content']
        
        # Определяем тип записи
        if 'заметка' in metadata.lower():
            entry_type = "💭 Заметка"
        elif 'выделенный отрывок' in metadata.lower() or 'highlighted' in metadata.lower():
            entry_type = "📌 Выделение"
        elif 'закладка' in metadata.lower():
            entry_type = "🔖 Закладка"
        else:
            entry_type = "📝 Запись"
        
        # Извлекаем местоположение
        location_match = re.search(r'(месте|странице|Место)\s+(\d+[\d–\-:,\s]*)', metadata)
        location = location_match.group(2) if location_match else "Unknown"
        
        # Извлекаем дату
        date_match = re.search(r'Добавлено:\s*(.+?)(?:\s*\||\s*$)', metadata)
        date_str = date_match.group(1) if date_match else ""
        
        note += f"""
### {entry_type} #{i}

**Местоположение:** {location}  
**Дата:** {date_str}

"""
        
        if content:
            note += f"> {content}\n\n"
        
        note += "---\n"
    
    return safe_filename, note

def main(input_file, output_dir='obsidian_notes'):
    """Основная функция для обработки файла Kindle"""
    
    # Читаем входной файл
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Парсим данные
    books = parse_kindle_highlights(text)
    
    # Создаем выходную директорию
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Создаем заметки для каждой книги
    for book_title, entries in books.items():
        if not entries:
            continue
            
        book_author = entries[0]['book_author']
        filename, note_content = create_obsidian_note(book_title, book_author, entries)
        
        # Сохраняем файл
        output_file = output_path / f"{filename}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(note_content)
        
        print(f"✓ Создана заметка: {filename}.md ({len(entries)} записей)")
    
    print(f"\n✅ Обработано {len(books)} книг")
    print(f"📁 Заметки сохранены в: {output_path.absolute()}")

if __name__ == "__main__":
    # Использование
    input_file = "My Clippings.txt"  # Ваш файл с экспортом
    output_dir = "obsidian_notes"  # Папка для заметок
    
    main(input_file, output_dir)
