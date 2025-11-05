"""
Step 2: Анализатор структуры комментариев

Разбирает структуру комментариев, выделяет ключевые идеи и паттерны,
которые делают комментарии успешными и "человеческими"
"""

import json
import re
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
from collections import Counter
import os


@dataclass
class CommentStructure:
    """Структура анализа комментария"""

    # Базовая информация
    text: str
    length: int
    word_count: int
    sentence_count: int

    # Структурный анализ
    has_paragraphs: bool
    paragraph_count: int
    avg_paragraph_length: float

    # Стиль и тон
    has_question: bool
    has_exclamation: bool
    has_emoji: bool
    emoji_count: int
    emoji_list: List[str]

    # Паттерны начала
    starts_with_agreement: bool  # "Согласен", "Точно", "Да"
    starts_with_question: bool
    starts_with_personal: bool  # "Я", "У меня", "Мой опыт"
    starts_with_gratitude: bool  # "Спасибо", "Благодарю"

    # Грамматические особенности
    has_contractions: bool  # "не", "бы", "ж"
    has_slang: bool
    has_typos: bool  # умышленные опечатки для человечности
    uses_ellipsis: bool  # "..."

    # Контент
    mentions_personal_experience: bool
    asks_followup_question: bool
    provides_value: bool  # советы, инсайты
    uses_storytelling: bool

    # Engagement паттерны
    call_to_action: bool
    controversial_take: bool
    humor_attempt: bool

    # Ключевые фразы
    key_phrases: List[str]
    transition_words: List[str]

    # AI детекция (обратные признаки)
    too_formal: bool
    too_perfect_grammar: bool
    generic_phrases: bool
    repetitive_structure: bool


class CommentAnalyzer:
    """Анализатор комментариев"""

    # Паттерны для детекции
    AGREEMENT_PATTERNS = [
        r'^(Согласен|Согласна|Точно|Абсолютно|Да|Именно|Верно)',
        r'^(I agree|Exactly|Absolutely|Yes|Indeed|True)',
    ]

    PERSONAL_PATTERNS = [
        r'^(Я |У меня |Мой |Моя |Мне |По моему опыту)',
        r'^(I |My |In my experience|From my perspective)',
    ]

    GRATITUDE_PATTERNS = [
        r'^(Спасибо|Благодарю|Спс|Thx|Thanks|Thank you)',
    ]

    GENERIC_AI_PHRASES = [
        'dive deep', 'delve into', 'in conclusion', 'in summary',
        'it\'s worth noting', 'it\'s important to', 'furthermore',
        'moreover', 'однако стоит отметить', 'в заключение',
        'подводя итог', 'более того', 'кроме того'
    ]

    TRANSITION_WORDS = [
        'но', 'однако', 'хотя', 'поэтому', 'таким образом',
        'например', 'в частности', 'кстати', 'вообще',
        'but', 'however', 'although', 'therefore', 'for example'
    ]

    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )

    def analyze_comment(self, text: str) -> CommentStructure:
        """Полный анализ структуры комментария"""

        # Базовый анализ
        length = len(text)
        words = text.split()
        word_count = len(words)
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len([s for s in sentences if s.strip()])

        # Анализ параграфов
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        paragraph_count = len(paragraphs)
        has_paragraphs = paragraph_count > 1
        avg_paragraph_length = length / paragraph_count if paragraph_count > 0 else length

        # Эмодзи
        emojis = self.EMOJI_PATTERN.findall(text)
        emoji_count = len(emojis)
        has_emoji = emoji_count > 0

        # Пунктуация
        has_question = '?' in text
        has_exclamation = '!' in text
        uses_ellipsis = '...' in text or '…' in text

        # Паттерны начала
        starts_with_agreement = any(re.match(p, text, re.IGNORECASE) for p in self.AGREEMENT_PATTERNS)
        starts_with_question = text.strip().startswith(('?', 'Как', 'Что', 'Почему', 'Где', 'How', 'What', 'Why', 'Where'))
        starts_with_personal = any(re.match(p, text, re.IGNORECASE) for p in self.PERSONAL_PATTERNS)
        starts_with_gratitude = any(re.match(p, text, re.IGNORECASE) for p in self.GRATITUDE_PATTERNS)

        # Грамматические особенности
        has_contractions = any(word in text.lower() for word in ['не', 'бы', 'ж', 'же', "n't", "'ll", "'ve"])
        has_slang = self._detect_slang(text)
        has_typos = self._detect_intentional_typos(text)

        # Контент анализ
        mentions_personal_experience = self._mentions_experience(text)
        asks_followup_question = has_question and '?' in text[len(text)//2:]
        provides_value = self._provides_value(text)
        uses_storytelling = self._uses_storytelling(text)

        # Engagement
        call_to_action = self._has_call_to_action(text)
        controversial_take = self._is_controversial(text)
        humor_attempt = self._has_humor(text)

        # Ключевые элементы
        key_phrases = self._extract_key_phrases(text)
        transition_words = [w for w in self.TRANSITION_WORDS if w in text.lower()]

        # AI детекция
        too_formal = self._is_too_formal(text)
        too_perfect_grammar = self._has_perfect_grammar(text)
        generic_phrases = any(phrase in text.lower() for phrase in self.GENERIC_AI_PHRASES)
        repetitive_structure = self._has_repetitive_structure(sentences)

        return CommentStructure(
            text=text,
            length=length,
            word_count=word_count,
            sentence_count=sentence_count,
            has_paragraphs=has_paragraphs,
            paragraph_count=paragraph_count,
            avg_paragraph_length=avg_paragraph_length,
            has_question=has_question,
            has_exclamation=has_exclamation,
            has_emoji=has_emoji,
            emoji_count=emoji_count,
            emoji_list=emojis,
            starts_with_agreement=starts_with_agreement,
            starts_with_question=starts_with_question,
            starts_with_personal=starts_with_personal,
            starts_with_gratitude=starts_with_gratitude,
            has_contractions=has_contractions,
            has_slang=has_slang,
            has_typos=has_typos,
            uses_ellipsis=uses_ellipsis,
            mentions_personal_experience=mentions_personal_experience,
            asks_followup_question=asks_followup_question,
            provides_value=provides_value,
            uses_storytelling=uses_storytelling,
            call_to_action=call_to_action,
            controversial_take=controversial_take,
            humor_attempt=humor_attempt,
            key_phrases=key_phrases,
            transition_words=transition_words,
            too_formal=too_formal,
            too_perfect_grammar=too_perfect_grammar,
            generic_phrases=generic_phrases,
            repetitive_structure=repetitive_structure
        )

    def _detect_slang(self, text: str) -> bool:
        """Детекция сленга"""
        slang_words = ['круто', 'классно', 'топ', 'топчик', 'кек', 'лол', 'имхо', 'окей', 'ок',
                       'cool', 'awesome', 'lit', 'dope', 'sick', 'lol', 'lmao', 'imho']
        return any(word in text.lower() for word in slang_words)

    def _detect_intentional_typos(self, text: str) -> bool:
        """Детекция умышленных опечаток (для человечности)"""
        # Повторяющиеся буквы для эмоциональности
        return bool(re.search(r'(\w)\1{2,}', text))

    def _mentions_experience(self, text: str) -> bool:
        """Упоминание личного опыта"""
        experience_markers = [
            'опыт', 'сталкивался', 'случай', 'работал', 'делал',
            'experience', 'faced', 'worked', 'did', 'tried'
        ]
        return any(marker in text.lower() for marker in experience_markers)

    def _provides_value(self, text: str) -> bool:
        """Предоставляет ли ценность (советы, инсайты)"""
        value_markers = [
            'совет', 'рекомендую', 'попробуйте', 'можно', 'стоит',
            'advice', 'recommend', 'try', 'should', 'consider'
        ]
        return any(marker in text.lower() for marker in value_markers)

    def _uses_storytelling(self, text: str) -> bool:
        """Использование сторителлинга"""
        story_markers = [
            'однажды', 'когда-то', 'помню', 'был случай', 'история',
            'once', 'when', 'remember', 'story', 'happened'
        ]
        return any(marker in text.lower() for marker in story_markers)

    def _has_call_to_action(self, text: str) -> bool:
        """Есть ли призыв к действию"""
        cta_markers = [
            'попробуйте', 'посмотрите', 'проверьте', 'напишите', 'поделитесь',
            'try', 'check', 'share', 'let me know', 'tell me'
        ]
        return any(marker in text.lower() for marker in cta_markers)

    def _is_controversial(self, text: str) -> bool:
        """Спорная точка зрения"""
        controversial_markers = [
            'не согласен', 'против', 'ошибка', 'неправильно', 'спорно',
            'disagree', 'wrong', 'mistake', 'controversial', 'unpopular'
        ]
        return any(marker in text.lower() for marker in controversial_markers)

    def _has_humor(self, text: str) -> bool:
        """Попытка юмора"""
        humor_markers = ['хаха', 'ахах', 'lol', 'lmao', '😂', '😄', '🤣']
        return any(marker in text.lower() for marker in humor_markers)

    def _is_too_formal(self, text: str) -> bool:
        """Слишком формальный (признак AI)"""
        formal_markers = [
            'следовательно', 'таким образом', 'в данном случае',
            'furthermore', 'moreover', 'consequently', 'therefore'
        ]
        formal_count = sum(1 for marker in formal_markers if marker in text.lower())
        return formal_count >= 2

    def _has_perfect_grammar(self, text: str) -> bool:
        """Идеальная грамматика (подозрительно для соцсетей)"""
        # Упрощенная проверка: если нет сокращений, разговорных форм
        informal_markers = ['не', 'бы', 'ж', '...', "n't", "'ll", "'ve"]
        return not any(marker in text for marker in informal_markers) and len(text) > 100

    def _has_repetitive_structure(self, sentences: List[str]) -> bool:
        """Повторяющаяся структура предложений (признак AI)"""
        if len(sentences) < 3:
            return False

        # Проверка на одинаковую длину предложений
        lengths = [len(s.strip()) for s in sentences if s.strip()]
        if not lengths:
            return False

        avg_length = sum(lengths) / len(lengths)
        similar_lengths = sum(1 for l in lengths if abs(l - avg_length) < 10)
        return similar_lengths >= len(lengths) * 0.8

    def _extract_key_phrases(self, text: str, top_n: int = 5) -> List[str]:
        """Извлечение ключевых фраз"""
        # Простое извлечение биграмм и триграмм
        words = re.findall(r'\b\w+\b', text.lower())

        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
        trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]

        phrases = bigrams + trigrams
        phrase_counts = Counter(phrases)

        return [phrase for phrase, count in phrase_counts.most_common(top_n)]

    def analyze_multiple_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ множества комментариев для выявления общих паттернов"""

        analyses = [self.analyze_comment(comment['text']) for comment in comments]

        # Агрегация паттернов
        patterns = {
            'avg_length': sum(a.length for a in analyses) / len(analyses),
            'avg_word_count': sum(a.word_count for a in analyses) / len(analyses),
            'avg_sentence_count': sum(a.sentence_count for a in analyses) / len(analyses),

            'use_paragraphs_pct': sum(a.has_paragraphs for a in analyses) / len(analyses) * 100,
            'use_emoji_pct': sum(a.has_emoji for a in analyses) / len(analyses) * 100,
            'use_questions_pct': sum(a.has_question for a in analyses) / len(analyses) * 100,

            'starts_with_agreement_pct': sum(a.starts_with_agreement for a in analyses) / len(analyses) * 100,
            'starts_with_personal_pct': sum(a.starts_with_personal for a in analyses) / len(analyses) * 100,

            'mentions_experience_pct': sum(a.mentions_personal_experience for a in analyses) / len(analyses) * 100,
            'provides_value_pct': sum(a.provides_value for a in analyses) / len(analyses) * 100,

            'ai_warning_signs': {
                'too_formal_pct': sum(a.too_formal for a in analyses) / len(analyses) * 100,
                'generic_phrases_pct': sum(a.generic_phrases for a in analyses) / len(analyses) * 100,
                'repetitive_structure_pct': sum(a.repetitive_structure for a in analyses) / len(analyses) * 100,
            },

            'common_key_phrases': self._aggregate_key_phrases(analyses),
            'common_transition_words': self._aggregate_transition_words(analyses),
        }

        return {
            'individual_analyses': [asdict(a) for a in analyses],
            'aggregate_patterns': patterns,
            'recommendations': self._generate_recommendations(patterns)
        }

    def _aggregate_key_phrases(self, analyses: List[CommentStructure]) -> List[str]:
        """Агрегация ключевых фраз"""
        all_phrases = []
        for analysis in analyses:
            all_phrases.extend(analysis.key_phrases)

        phrase_counts = Counter(all_phrases)
        return [phrase for phrase, count in phrase_counts.most_common(10)]

    def _aggregate_transition_words(self, analyses: List[CommentStructure]) -> List[str]:
        """Агрегация переходных слов"""
        all_words = []
        for analysis in analyses:
            all_words.extend(analysis.transition_words)

        word_counts = Counter(all_words)
        return [word for word, count in word_counts.most_common(10)]

    def _generate_recommendations(self, patterns: Dict[str, Any]) -> List[str]:
        """Генерация рекомендаций на основе паттернов"""
        recommendations = []

        # Рекомендации по длине
        avg_length = patterns['avg_length']
        if avg_length < 100:
            recommendations.append(f"Цель: короткие комментарии (~{int(avg_length)} символов)")
        elif avg_length < 300:
            recommendations.append(f"Цель: средние комментарии (~{int(avg_length)} символов)")
        else:
            recommendations.append(f"Цель: длинные комментарии (~{int(avg_length)} символов)")

        # Рекомендации по эмодзи
        if patterns['use_emoji_pct'] > 50:
            recommendations.append("✓ Используйте эмодзи (50%+ успешных комментариев)")

        # Рекомендации по структуре
        if patterns['use_paragraphs_pct'] > 30:
            recommendations.append("✓ Разбивайте на параграфы для длинных комментариев")

        # Рекомендации по содержанию
        if patterns['mentions_experience_pct'] > 40:
            recommendations.append("✓ Упоминайте личный опыт (увеличивает engagement)")

        if patterns['provides_value_pct'] > 40:
            recommendations.append("✓ Предоставляйте ценность (советы, инсайты)")

        # Предупреждения об AI
        ai_warnings = patterns['ai_warning_signs']
        if ai_warnings['too_formal_pct'] < 20:
            recommendations.append("⚠ Избегайте формального тона")

        if ai_warnings['generic_phrases_pct'] < 20:
            recommendations.append("⚠ Избегайте шаблонных AI фраз")

        return recommendations

    def save_analysis(self, analysis_result: Dict[str, Any], output_path: str):
        """Сохранение результатов анализа"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)

        print(f"✓ Анализ сохранен: {output_path}")


def main():
    """Пример использования"""

    # Пример комментариев
    sample_comments = [
        {
            'text': 'Согласен! У меня был похожий опыт, когда работал в стартапе. '
                    'Главное - не бояться экспериментировать 🚀',
            'engagement': 45
        },
        {
            'text': 'Отличная статья! Особенно зацепил момент про work-life balance.\n\n'
                    'Кстати, вы пробовали технику Pomodoro? Мне помогла выйти из выгорания.',
            'engagement': 38
        },
        {
            'text': 'Интересная перспектива, хотя я не согласен с выводами. '
                    'По моему опыту, всё работает наоборот... '
                    'Но это спорный вопрос, конечно 😅',
            'engagement': 52
        }
    ]

    analyzer = CommentAnalyzer()

    # Анализ
    print("=" * 60)
    print("АНАЛИЗ КОММЕНТАРИЕВ (STEP 2)")
    print("=" * 60)

    result = analyzer.analyze_multiple_comments(sample_comments)

    # Вывод рекомендаций
    print("\n📊 РЕКОМЕНДАЦИИ ДЛЯ ГЕНЕРАЦИИ:\n")
    for rec in result['recommendations']:
        print(f"  {rec}")

    print("\n📈 КЛЮЧЕВЫЕ МЕТРИКИ:\n")
    patterns = result['aggregate_patterns']
    print(f"  Средняя длина: {patterns['avg_length']:.0f} символов")
    print(f"  Среднее кол-во слов: {patterns['avg_word_count']:.0f}")
    print(f"  Используют эмодзи: {patterns['use_emoji_pct']:.0f}%")
    print(f"  Упоминают опыт: {patterns['mentions_experience_pct']:.0f}%")

    # Сохранение
    analyzer.save_analysis(result, 'data/analysis/comment_patterns.json')

    print("\n✓ Анализ завершен!")


if __name__ == '__main__':
    main()
