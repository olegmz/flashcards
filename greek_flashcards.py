import streamlit as st
import json
import random
from pathlib import Path
import os

# Настройка страницы
st.set_page_config(
    page_title="Учим греческий язык",
    page_icon="🇬🇷",
    layout="wide"
)

# Инициализация session state
if 'vocabulary_files' not in st.session_state:
    st.session_state.vocabulary_files = {}
if 'active_files' not in st.session_state:
    st.session_state.active_files = set()
if 'progress' not in st.session_state:
    st.session_state.progress = {}
if 'current_card' not in st.session_state:
    st.session_state.current_card = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'direction' not in st.session_state:
    st.session_state.direction = 'greek_to_russian'
if 'uploaded_files_dir' not in st.session_state:
    st.session_state.uploaded_files_dir = Path.home() / '.greek_flashcards'
    st.session_state.uploaded_files_dir.mkdir(exist_ok=True)
if 'excluded_words' not in st.session_state:
    st.session_state.excluded_words = set()
if 'excluded_words' not in st.session_state:
    st.session_state.excluded_words = set()

# CSS для карточек с увеличенным шрифтом
st.markdown("""
<style>
    .flashcard {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 60px 40px;
        margin: 30px auto;
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        text-align: center;
        min-height: 250px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    .flashcard:hover {
        transform: translateY(-5px);
    }
    .flashcard-text {
        color: white;
        font-size: 3em;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        line-height: 1.2;
    }
    .flashcard-example {
        color: rgba(255,255,255,0.9);
        font-size: 3em;
        margin-top: 20px;
        font-style: italic;
    }
    .stats-box {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    .stButton > button {
        font-size: 1.3em !important;
        padding: 12px 24px !important;
    }
</style>
""", unsafe_allow_html=True)

def load_vocabulary_from_file(file_path):
    """Загрузка словаря из JSON файла"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        st.error(f"Ошибка загрузки файла {file_path}: {e}")
        return []

def save_uploaded_file(uploaded_file):
    """Сохранение загруженного файла"""
    file_path = st.session_state.uploaded_files_dir / uploaded_file.name
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def get_all_active_words():
    """Получение всех слов из активных словарей"""
    all_words = []
    for file_name in st.session_state.active_files:
        if file_name in st.session_state.vocabulary_files:
            all_words.extend(st.session_state.vocabulary_files[file_name])
    return all_words

def get_next_card():
    """Выбор следующей карточки для изучения"""
    all_words = get_all_active_words()
    if not all_words:
        return None
    
    # Создаем список слов с приоритетом (чем меньше правильных ответов, тем выше приоритет)
    weighted_words = []
    for word in all_words:
        word_key = word['greek']
        
        # Пропускаем исключенные слова
        if word_key in st.session_state.excluded_words:
            continue
        
        correct_count = st.session_state.progress.get(word_key, {}).get('correct_streak', 0)
        
        # Пропускаем выученные слова (3+ правильных ответов)
        if correct_count >= 3:
            continue
            
        # Чем меньше правильных ответов, тем больше вес (больше вероятность показа)
        weight = max(1, 4 - correct_count)
        weighted_words.extend([word] * weight)
    
    if not weighted_words:
        # Все слова выучены!
        return None
    
    return random.choice(weighted_words)

def mark_answer(is_correct):
    """Отметка ответа как правильного или неправильного"""
    if st.session_state.current_card is None:
        return
    
    word_key = st.session_state.current_card['greek']
    
    if word_key not in st.session_state.progress:
        st.session_state.progress[word_key] = {
            'correct_streak': 0,
            'total_attempts': 0,
            'learned': False
        }
    
    st.session_state.progress[word_key]['total_attempts'] += 1
    
    if is_correct:
        st.session_state.progress[word_key]['correct_streak'] += 1
        if st.session_state.progress[word_key]['correct_streak'] >= 3:
            st.session_state.progress[word_key]['learned'] = True
    else:
        st.session_state.progress[word_key]['correct_streak'] = 0
    
    # Сброс для следующей карточки
    st.session_state.current_card = None
    st.session_state.show_answer = False

def get_statistics():
    """Получение статистики обучения"""
    all_words = get_all_active_words()
    total_words = len(all_words)
    
    if total_words == 0:
        return {'total': 0, 'learned': 0, 'in_progress': 0, 'not_started': 0, 'excluded': 0}
    
    learned = 0
    in_progress = 0
    not_started = 0
    excluded = 0
    
    for word in all_words:
        word_key = word['greek']
        
        # Подсчитываем исключенные слова
        if word_key in st.session_state.excluded_words:
            excluded += 1
            continue
        
        if word_key in st.session_state.progress:
            correct_streak = st.session_state.progress[word_key]['correct_streak']
            if correct_streak >= 3:
                learned += 1
            elif correct_streak > 0:
                in_progress += 1
            else:
                not_started += 1
        else:
            not_started += 1
    
    return {
        'total': total_words,
        'learned': learned,
        'in_progress': in_progress,
        'not_started': not_started,
        'excluded': excluded
    }

def exclude_word():
    """Исключить текущее слово из сессии"""
    if st.session_state.current_card is None:
        return
    
    word_key = st.session_state.current_card['greek']
    st.session_state.excluded_words.add(word_key)
    
    # Сброс для следующей карточки
    st.session_state.current_card = None
    st.session_state.show_answer = False

# Интерфейс приложения
st.title("🇬🇷 Учим греческий язык")

# Боковая панель для управления словарями
with st.sidebar:
    st.header("📚 Управление словарями")
    
    # Загрузка новых файлов
    uploaded_files = st.file_uploader(
        "Загрузить JSON файлы",
        type=['json'],
        accept_multiple_files=True,
        key='file_uploader'
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = save_uploaded_file(uploaded_file)
            vocabulary = load_vocabulary_from_file(file_path)
            if vocabulary:
                st.session_state.vocabulary_files[uploaded_file.name] = vocabulary
                st.session_state.active_files.add(uploaded_file.name)
                st.success(f"✅ {uploaded_file.name} загружен!")
    
    # Загрузка сохраненных файлов при старте
    for file_path in st.session_state.uploaded_files_dir.glob('*.json'):
        file_name = file_path.name
        if file_name not in st.session_state.vocabulary_files:
            vocabulary = load_vocabulary_from_file(file_path)
            if vocabulary:
                st.session_state.vocabulary_files[file_name] = vocabulary
    
    st.divider()
    
    # Список загруженных словарей
    st.subheader("Доступные словари")
    
    if st.session_state.vocabulary_files:
        for file_name in st.session_state.vocabulary_files.keys():
            col1, col2 = st.columns([3, 1])
            with col1:
                is_active = st.checkbox(
                    f"{file_name} ({len(st.session_state.vocabulary_files[file_name])} слов)",
                    value=file_name in st.session_state.active_files,
                    key=f"checkbox_{file_name}"
                )
            with col2:
                if st.button("🗑️", key=f"delete_{file_name}"):
                    # Удаление файла
                    file_path = st.session_state.uploaded_files_dir / file_name
                    if file_path.exists():
                        os.remove(file_path)
                    del st.session_state.vocabulary_files[file_name]
                    st.session_state.active_files.discard(file_name)
                    st.rerun()
            
            if is_active:
                st.session_state.active_files.add(file_name)
            else:
                st.session_state.active_files.discard(file_name)
    else:
        st.info("Загрузите JSON файлы со словами")
    
    st.divider()
    
    # Настройки направления
    st.subheader("⚙️ Настройки")
    direction = st.radio(
        "Направление перевода:",
        options=['greek_to_russian', 'russian_to_greek'],
        format_func=lambda x: 'Греческий → Русский' if x == 'greek_to_russian' else 'Русский → Греческий',
        key='direction_radio'
    )
    st.session_state.direction = direction

# Основная область
if not st.session_state.active_files:
    st.warning("⚠️ Выберите хотя бы один словарь для изучения")
else:
    # Статистика
    stats = get_statistics()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Всего слов", stats['total'])
    with col2:
        st.metric("Выучено", stats['learned'], delta=f"{(stats['learned']/stats['total']*100) if stats['total'] > 0 else 0:.0f}%")
    with col3:
        st.metric("В процессе", stats['in_progress'])
    with col4:
        st.metric("Новые", stats['not_started'])
    with col5:
        st.metric("Исключено", stats['excluded'])
    
    st.divider()
    
    # Карточка
    if st.session_state.current_card is None:
        st.session_state.current_card = get_next_card()
    
    if st.session_state.current_card is None:
        st.success("🎉 Поздравляю! Вы выучили все слова!")
        if st.button("🔄 Начать заново", use_container_width=True):
            st.session_state.progress = {}
            st.rerun()
    else:
        card = st.session_state.current_card
        
        # Определяем, что показывать
        if st.session_state.direction == 'greek_to_russian':
            question = card['greek']
            answer = card['russian']
        else:
            question = card['russian']
            answer = card['greek']
        
        # Прогресс текущего слова
        word_key = card['greek']
        correct_streak = st.session_state.progress.get(word_key, {}).get('correct_streak', 0)
        
        st.markdown(f"### Прогресс: {'✅' * correct_streak}{'⬜' * (3 - correct_streak)}")
        
        # Карточка
        if not st.session_state.show_answer:
            st.markdown(f"""
            <div class="flashcard" onclick="this.style.transform='rotateY(180deg)'">
                <div>
                    <p class="flashcard-text">{question}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("👁️ Показать ответ", use_container_width=True, type="primary"):
                    st.session_state.show_answer = True
                    st.rerun()
        else:
            st.markdown(f"""
            <div class="flashcard">
                <div>
                    <p class="flashcard-text">{answer}</p>
                    <p class="flashcard-example">{card.get('example', '')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### Вы знаете это слово?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Знаю", use_container_width=True, type="primary"):
                    mark_answer(True)
                    st.rerun()
            
            with col2:
                if st.button("❌ Не знаю", use_container_width=True):
                    mark_answer(False)
                    st.rerun()
            
            st.markdown("")
            if st.button("🚫 Убрать слово из сессии", use_container_width=True, help="Слово не будет показываться в текущей сессии"):
                st.session_state.excluded_words.add(word_key)
                st.session_state.current_card = None
                st.session_state.show_answer = False
                st.rerun()

# Кнопки сброса внизу
st.divider()
col1, col2 = st.columns(2)

with col1:
    if st.button("🔄 Сбросить весь прогресс"):
        st.session_state.progress = {}
        st.session_state.current_card = None
        st.success("Прогресс сброшен!")
        st.rerun()

with col2:
    if st.button("↩️ Вернуть исключенные слова"):
        st.session_state.excluded_words = set()
        st.session_state.current_card = None
        st.success("Исключенные слова возвращены!")
        st.rerun()
