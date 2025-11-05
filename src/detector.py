"""
Детектор AI vs Human комментариев

Анализирует комментарии и определяет признаки AI-генерации,
помогает создавать более человеческие комментарии
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum


class CommentType(Enum):
    """Тип комментария"""
    LIKELY_HUMAN = "likely_human"
    LIKELY_AI = "likely_ai"
    UNCERTAIN = "uncertain"


@dataclass
class DetectionResult:
    """Результат детекции"""
    comment_type: CommentType
    confidence: float  # 0-100
    ai_score: float  # Чем выше, тем больше похоже на AI
    human_score: float  # Чем выше, тем больше похоже на человека

    # Детальный анализ
    ai_indicators: List[str]
    human_indicators: List[str]

    # Рекомендации
    recommendations: List[str]


class AICommentDetector:
    """
    Детектор AI-генерированных комментариев

    Основан на исследованиях признаков AI-текстов:
    - Слишком формальный язык
    - Шаблонные фразы
    - Идеальная грамматика
    - Отсутствие личного опыта
    - Повторяющаяся структура
    """

    # Признаки AI
    AI_PHRASES = [
        # Английские
        'it\'s worth noting', 'it\'s important to', 'furthermore', 'moreover',
        'in conclusion', 'in summary', 'to summarize', 'that being said',
        'delve into', 'dive deep', 'unpack', 'leverage', 'utilize',
        'multifaceted', 'paradigm shift', 'holistic approach',
        'it\'s crucial to understand', 'at the end of the day',

        # Русские
        'стоит отметить', 'важно понимать', 'более того', 'кроме того',
        'в заключение', 'подводя итог', 'таким образом', 'следовательно',
        'тем не менее', 'в данном контексте', 'необходимо учитывать',
        'комплексный подход', 'многогранный', 'в конечном счете',
    ]

    OVERLY_FORMAL_WORDS = [
        'следовательно', 'таким образом', 'соответственно', 'безусловно',
        'consequently', 'therefore', 'accordingly', 'undoubtedly',
        'furthermore', 'nevertheless', 'subsequently', 'henceforth'
    ]

    # Признаки человека
    HUMAN_INDICATORS = {
        'typos': [r'(\w)\1{2,}'],  # Повторяющиеся буквы: "крутооо"
        'slang': ['круто', 'топ', 'кек', 'лол', 'имхо', 'окей', 'cool', 'awesome', 'lol', 'lmao', 'tbh'],
        'contractions': ['не', 'бы', 'ж', 'же', "n't", "'ll", "'ve", "'re"],
        'casual_start': [
            r'^(Блин|Вау|Ого|Хм|Ну|Да|Wow|Whoa|Hmm|Well|Yeah)',
            r'^(Эх|Ох|Ах|Эээ|Ммм|Ugh|Uhh|Umm|Eh)',
        ],
        'personal': [
            r'\b(я |мне |мой |моя |у меня |по моему опыту)\b',
            r'\b(i |my |mine |in my experience|from my perspective)\b',
        ],
        'questions': [r'\?+'],
        'ellipsis': [r'\.{2,}', r'…'],
        'exclamations': [r'!{2,}'],
    }

    def detect(self, text: str) -> DetectionResult:
        """
        Определить, AI или человек написал комментарий

        Args:
            text: Текст комментария

        Returns:
            DetectionResult с анализом
        """
        ai_score = 0
        human_score = 0
        ai_indicators = []
        human_indicators = []

        text_lower = text.lower()

        # === ПРОВЕРКА AI ПРИЗНАКОВ ===

        # 1. Шаблонные AI фразы
        ai_phrases_found = [phrase for phrase in self.AI_PHRASES if phrase in text_lower]
        if ai_phrases_found:
            ai_score += len(ai_phrases_found) * 15
            ai_indicators.append(f"Шаблонные AI фразы: {', '.join(ai_phrases_found[:3])}")

        # 2. Слишком формальные слова
        formal_words = [word for word in self.OVERLY_FORMAL_WORDS if word in text_lower]
        if len(formal_words) >= 2:
            ai_score += len(formal_words) * 10
            ai_indicators.append(f"Формальный язык: {', '.join(formal_words)}")

        # 3. Идеальная структура (все предложения примерно одинаковой длины)
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if len(sentences) >= 3:
            lengths = [len(s) for s in sentences]
            avg_len = sum(lengths) / len(lengths)
            variance = sum((l - avg_len) ** 2 for l in lengths) / len(lengths)

            if variance < 100:  # Слишком однородные предложения
                ai_score += 15
                ai_indicators.append("Подозрительно однородная структура предложений")

        # 4. Отсутствие личного опыта в длинном тексте
        if len(text) > 200:
            personal_patterns = self.HUMAN_INDICATORS['personal']
            has_personal = any(re.search(p, text_lower) for p in personal_patterns)
            if not has_personal:
                ai_score += 10
                ai_indicators.append("Отсутствие личного опыта в длинном тексте")

        # 5. Слишком идеальная грамматика (нет сокращений, разговорных форм)
        if len(text) > 100:
            has_contractions = any(c in text for c in self.HUMAN_INDICATORS['contractions'])
            has_ellipsis = bool(re.search(r'\.{2,}|…', text))
            if not has_contractions and not has_ellipsis:
                ai_score += 10
                ai_indicators.append("Слишком идеальная грамматика")

        # 6. Типичные AI вводные фразы
        ai_starters = [
            'as an ai', 'as a language model', 'i don\'t have personal',
            'как языковая модель', 'я не могу иметь личный'
        ]
        if any(starter in text_lower for starter in ai_starters):
            ai_score += 100  # Очевидный AI
            ai_indicators.append("Прямое упоминание AI")

        # === ПРОВЕРКА ЧЕЛОВЕЧЕСКИХ ПРИЗНАКОВ ===

        # 1. Опечатки и повторяющиеся буквы
        if re.search(self.HUMAN_INDICATORS['typos'][0], text):
            human_score += 20
            human_indicators.append("Эмоциональные повторы букв (круутоо)")

        # 2. Сленг
        slang_found = [word for word in self.HUMAN_INDICATORS['slang'] if word in text_lower]
        if slang_found:
            human_score += len(slang_found) * 15
            human_indicators.append(f"Сленг: {', '.join(slang_found)}")

        # 3. Разговорные начала
        casual_starts = self.HUMAN_INDICATORS['casual_start']
        if any(re.match(p, text, re.IGNORECASE) for p in casual_starts):
            human_score += 15
            human_indicators.append("Разговорное начало комментария")

        # 4. Личный опыт
        personal_patterns = self.HUMAN_INDICATORS['personal']
        if any(re.search(p, text_lower) for p in personal_patterns):
            human_score += 20
            human_indicators.append("Упоминание личного опыта")

        # 5. Множественные вопросы
        question_count = text.count('?')
        if question_count >= 2:
            human_score += 10
            human_indicators.append(f"Множественные вопросы ({question_count})")

        # 6. Эллипсисы
        if re.search(r'\.{2,}|…', text):
            human_score += 10
            human_indicators.append("Использование эллипсисов (...)")

        # 7. Множественные восклицательные знаки
        if re.search(r'!{2,}', text):
            human_score += 10
            human_indicators.append("Эмоциональные восклицания (!!!)")

        # 8. Эмодзи
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "]+", flags=re.UNICODE
        )
        if emoji_pattern.search(text):
            human_score += 15
            human_indicators.append("Использование эмодзи")

        # 9. Неформальная пунктуация
        if '...' in text or '…' in text or '??' in text or '!!' in text:
            human_score += 5
            human_indicators.append("Неформальная пунктуация")

        # === ОПРЕДЕЛЕНИЕ ТИПА ===

        # Нормализация scores
        total_score = ai_score + human_score
        if total_score > 0:
            ai_normalized = (ai_score / total_score) * 100
            human_normalized = (human_score / total_score) * 100
        else:
            ai_normalized = 50
            human_normalized = 50

        # Определение типа
        if human_normalized >= 65:
            comment_type = CommentType.LIKELY_HUMAN
            confidence = human_normalized
        elif ai_normalized >= 65:
            comment_type = CommentType.LIKELY_AI
            confidence = ai_normalized
        else:
            comment_type = CommentType.UNCERTAIN
            confidence = 100 - abs(human_normalized - ai_normalized)

        # Генерация рекомендаций
        recommendations = self._generate_recommendations(
            comment_type, ai_indicators, human_indicators, text
        )

        return DetectionResult(
            comment_type=comment_type,
            confidence=confidence,
            ai_score=ai_normalized,
            human_score=human_normalized,
            ai_indicators=ai_indicators,
            human_indicators=human_indicators,
            recommendations=recommendations
        )

    def _generate_recommendations(
        self,
        comment_type: CommentType,
        ai_indicators: List[str],
        human_indicators: List[str],
        text: str
    ) -> List[str]:
        """Генерация рекомендаций для улучшения"""

        recommendations = []

        if comment_type == CommentType.LIKELY_AI:
            recommendations.append("⚠ Комментарий выглядит AI-генерированным. Рекомендации:")

            if not human_indicators:
                recommendations.append("• Добавьте личный опыт ('я сталкивался с...', 'у меня был случай...')")
                recommendations.append("• Используйте разговорный язык и сленг")
                recommendations.append("• Добавьте эмодзи для эмоциональности")
                recommendations.append("• Используйте неформальную пунктуацию (..., !!, ??)")

            if "Формальный язык" in str(ai_indicators):
                recommendations.append("• Замените формальные слова на разговорные")

            if "Шаблонные AI фразы" in str(ai_indicators):
                recommendations.append("• Избегайте шаблонных фраз типа 'стоит отметить', 'в заключение'")

            recommendations.append("• Добавьте эмоциональности и спонтанности")

        elif comment_type == CommentType.LIKELY_HUMAN:
            recommendations.append("✓ Комментарий выглядит естественным")

            # Но можно улучшить
            if len(text) < 50:
                recommendations.append("• Можно добавить больше деталей или примеров")

        else:
            recommendations.append("? Неопределенный тип. Рекомендации:")
            recommendations.append("• Добавьте больше личных элементов")
            recommendations.append("• Используйте естественный, разговорный стиль")

        return recommendations

    def batch_detect(self, comments: List[str]) -> List[DetectionResult]:
        """Массовая детекция комментариев"""
        return [self.detect(comment) for comment in comments]

    def get_human_score(self, text: str) -> float:
        """Получить только human score (0-100)"""
        result = self.detect(text)
        return result.human_score


def main():
    """Пример использования"""

    detector = AICommentDetector()

    # Примеры комментариев
    test_comments = [
        {
            'name': 'AI-подобный',
            'text': 'It\'s worth noting that this approach has several important advantages. '
                    'Furthermore, it\'s crucial to understand the underlying mechanisms. '
                    'In conclusion, this represents a paradigm shift in the industry.'
        },
        {
            'name': 'Человеческий',
            'text': 'Блин, это реально круто! 🔥 Я сам сталкивался с такой проблемой, '
                    'когда работал в стартапе... Попробую этот подход, спс за инсайт!'
        },
        {
            'name': 'Смешанный',
            'text': 'Согласен с вашей точкой зрения. Действительно, данный подход '
                    'имеет множество преимуществ. У меня был похожий опыт.'
        }
    ]

    print("=" * 60)
    print("ДЕТЕКЦИЯ AI vs HUMAN КОММЕНТАРИЕВ")
    print("=" * 60)

    for comment in test_comments:
        print(f"\n{'='*60}")
        print(f"📝 {comment['name']}:")
        print(f"   {comment['text'][:80]}...")

        result = detector.detect(comment['text'])

        print(f"\n🎯 Результат: {result.comment_type.value.upper()}")
        print(f"   Уверенность: {result.confidence:.1f}%")
        print(f"   AI Score: {result.ai_score:.1f}%")
        print(f"   Human Score: {result.human_score:.1f}%")

        if result.ai_indicators:
            print(f"\n🤖 AI признаки:")
            for indicator in result.ai_indicators:
                print(f"   - {indicator}")

        if result.human_indicators:
            print(f"\n👤 Человеческие признаки:")
            for indicator in result.human_indicators:
                print(f"   - {indicator}")

        print(f"\n💡 Рекомендации:")
        for rec in result.recommendations:
            print(f"   {rec}")


if __name__ == '__main__':
    main()
