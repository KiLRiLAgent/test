"""
Генератор человеческих комментариев

Использует AI для генерации комментариев, которые выглядят естественно
и учитывают паттерны успешных комментариев из анализа
"""

import os
import json
import random
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from analyzer import CommentAnalyzer
from detector import AICommentDetector

load_dotenv()


@dataclass
class GenerationConfig:
    """Конфигурация для генерации комментария"""

    # Цель генерации
    post_text: str
    target_length: str = "medium"  # short, medium, long

    # Стиль
    tone: str = "friendly"  # formal, friendly, casual, professional
    use_emoji: bool = True
    use_personal_experience: bool = True

    # Структура
    start_pattern: str = "agreement"  # agreement, question, personal, gratitude, insight
    include_question: bool = False
    include_call_to_action: bool = False

    # Паттерны из анализа
    reference_patterns: Optional[Dict] = None

    # Параметры AI
    temperature: float = 0.9  # Высокая температура для разнообразия
    max_tokens: int = 200


class CommentGenerator:
    """
    Генератор человеческих комментариев

    Процесс генерации в несколько этапов:
    1. Анализ поста и целевых паттернов
    2. Генерация базового комментария через AI
    3. Проверка на AI-признаки
    4. Улучшение для большей "человечности"
    5. Финальная валидация
    """

    def __init__(self, api_key: str = None, provider: str = "anthropic"):
        """
        Args:
            api_key: API ключ для AI провайдера
            provider: 'anthropic' или 'openai'
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.provider = provider

        self.analyzer = CommentAnalyzer()
        self.detector = AICommentDetector()

        self.client = None
        self._init_ai_client()

    def _init_ai_client(self):
        """Инициализация AI клиента"""
        try:
            if self.provider == "anthropic":
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            elif self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
        except ImportError as e:
            print(f"⚠ Не установлена библиотека {self.provider}: {e}")
            print(f"   Установите: pip install {self.provider}")

    def generate(self, config: GenerationConfig, max_attempts: int = 3) -> Dict[str, Any]:
        """
        Генерация комментария

        Args:
            config: Конфигурация генерации
            max_attempts: Максимальное количество попыток улучшения

        Returns:
            Словарь с комментарием и метаданными
        """

        # Подготовка промпта
        prompt = self._build_prompt(config)

        best_comment = None
        best_human_score = 0

        for attempt in range(max_attempts):
            # Генерация через AI
            raw_comment = self._call_ai(prompt, config.temperature, config.max_tokens)

            if not raw_comment:
                continue

            # Проверка на AI-признаки
            detection_result = self.detector.detect(raw_comment)

            # Если комментарий слишком AI-подобный, улучшаем
            if detection_result.human_score < 60:
                improved_comment = self._humanize_comment(
                    raw_comment, detection_result, config
                )
            else:
                improved_comment = raw_comment

            # Повторная проверка
            final_detection = self.detector.detect(improved_comment)

            # Сохраняем лучший вариант
            if final_detection.human_score > best_human_score:
                best_human_score = final_detection.human_score
                best_comment = improved_comment

            # Если достигли хорошего результата, прерываем
            if best_human_score >= 70:
                break

        # Анализ структуры финального комментария
        structure_analysis = self.analyzer.analyze_comment(best_comment)

        return {
            'comment': best_comment,
            'human_score': best_human_score,
            'detection': final_detection,
            'structure': structure_analysis,
            'attempts': attempt + 1
        }

    def _build_prompt(self, config: GenerationConfig) -> str:
        """Построение промпта для AI"""

        # Базовая инструкция
        prompt = f"""Напиши комментарий к посту в социальной сети.

ПОСТ:
{config.post_text}

ВАЖНО: Комментарий должен выглядеть написанным живым человеком, а НЕ AI.

ТРЕБОВАНИЯ:
"""

        # Длина
        length_guide = {
            "short": "50-100 символов (1-2 предложения)",
            "medium": "100-200 символов (2-4 предложения)",
            "long": "200-400 символов (4-7 предложений)"
        }
        prompt += f"- Длина: {length_guide.get(config.target_length, 'medium')}\n"

        # Тон
        tone_guide = {
            "formal": "формальный, профессиональный",
            "friendly": "дружелюбный, теплый",
            "casual": "неформальный, разговорный",
            "professional": "профессиональный, но не слишком формальный"
        }
        prompt += f"- Тон: {tone_guide.get(config.tone, 'friendly')}\n"

        # Паттерн начала
        start_patterns = {
            "agreement": "Начни с согласия ('Согласен!', 'Точно!', 'Да!', 'Абсолютно!')",
            "question": "Начни с вопроса автору",
            "personal": "Начни с личного опыта ('У меня был...', 'Я сталкивался...')",
            "gratitude": "Начни с благодарности ('Спасибо!', 'Благодарю!', 'Спс!')",
            "insight": "Начни с интересного инсайта или наблюдения"
        }
        if config.start_pattern in start_patterns:
            prompt += f"- {start_patterns[config.start_pattern]}\n"

        # Дополнительные элементы
        if config.use_emoji:
            prompt += "- Используй 1-2 эмодзи для эмоциональности (но не переборщи!)\n"

        if config.use_personal_experience:
            prompt += "- Упомяни личный опыт или пример из практики\n"

        if config.include_question:
            prompt += "- Заверши вопросом к автору или аудитории\n"

        if config.include_call_to_action:
            prompt += "- Добавь призыв к действию или дискуссии\n"

        # Паттерны из референсов
        if config.reference_patterns:
            prompt += "\nПАТТЕРНЫ УСПЕШНЫХ КОММЕНТАРИЕВ:\n"
            patterns = config.reference_patterns.get('aggregate_patterns', {})

            avg_length = patterns.get('avg_length', 0)
            if avg_length:
                prompt += f"- Средняя длина успешных: {int(avg_length)} символов\n"

            common_phrases = patterns.get('common_key_phrases', [])
            if common_phrases:
                prompt += f"- Частые фразы: {', '.join(common_phrases[:5])}\n"

        # Критически важно: избегать AI-признаков
        prompt += """
КРИТИЧЕСКИ ВАЖНО - ИЗБЕГАЙ:
- Шаблонных AI фраз ('стоит отметить', 'в заключение', 'более того', 'важно понимать')
- Слишком формального языка
- Идеальной грамматики (добавь неформальности!)
- Повторяющейся структуры предложений

ДЕЛАЙ:
- Пиши естественно, как в переписке с другом
- Используй разговорные обороты и сленг
- Добавь эмоции и спонтанность
- Можно использовать '...', '!!', '??'
- Добавь личный опыт или конкретный пример

Напиши ТОЛЬКО текст комментария, без пояснений."""

        return prompt

    def _call_ai(self, prompt: str, temperature: float, max_tokens: int) -> Optional[str]:
        """Вызов AI API"""

        if not self.client:
            print("⚠ AI клиент не инициализирован")
            return None

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.content[0].text.strip()

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"✗ Ошибка вызова AI: {e}")
            return None

    def _humanize_comment(
        self,
        comment: str,
        detection_result,
        config: GenerationConfig
    ) -> str:
        """
        Улучшение комментария для большей "человечности"

        Применяет трансформации на основе найденных AI-признаков
        """

        improved = comment

        # Замена формальных слов на разговорные
        replacements = {
            # Русский
            'следовательно': random.choice(['поэтому', 'так что', 'получается']),
            'таким образом': random.choice(['так что', 'в итоге', 'короче']),
            'более того': random.choice(['и еще', 'да и вообще', 'плюс ко всему']),
            'в заключение': random.choice(['в общем', 'короче', 'подводя итог']),
            'стоит отметить': random.choice(['кстати', 'интересно что', 'заметил что']),

            # English
            'furthermore': random.choice(['also', 'plus', 'and']),
            'moreover': random.choice(['also', 'plus', 'besides']),
            'it\'s worth noting': random.choice(['btw', 'interesting that', 'noticed that']),
            'in conclusion': random.choice(['so', 'basically', 'anyway']),
        }

        for formal, casual in replacements.items():
            improved = improved.replace(formal, casual)
            improved = improved.replace(formal.capitalize(), casual.capitalize())

        # Добавление эмоциональности если её нет
        if not detection_result.human_indicators:

            # Добавление эмодзи (если разрешено)
            if config.use_emoji and '😊🔥👍✨💡🚀😄👏' not in improved:
                emoji = random.choice(['👍', '🔥', '😊', '✨', '💡'])
                improved += f' {emoji}'

            # Добавление неформальной пунктуации
            if not any(p in improved for p in ['...', '!', '??']):
                if improved.endswith('.'):
                    improved = improved[:-1] + random.choice(['!', '...', ''])

        # Добавление разговорных вставок
        casual_insertions = [
            'кстати,', 'вообще,', 'честно,', 'имхо,',
            'btw,', 'honestly,', 'tbh,', 'imo,'
        ]

        # С вероятностью 30% добавляем разговорную вставку
        if random.random() < 0.3 and not any(ins in improved.lower() for ins in casual_insertions):
            insertion = random.choice(casual_insertions)
            # Вставляем после первого предложения
            sentences = improved.split('. ')
            if len(sentences) > 1:
                sentences[0] += f', {insertion}'
                improved = '. '.join(sentences)

        return improved

    def generate_batch(
        self,
        posts: List[Dict[str, Any]],
        config_template: GenerationConfig = None
    ) -> List[Dict[str, Any]]:
        """
        Генерация комментариев для множества постов

        Args:
            posts: Список постов
            config_template: Шаблон конфигурации

        Returns:
            Список результатов генерации
        """

        results = []

        for post in posts:
            # Копируем конфиг и обновляем текст поста
            config = config_template or GenerationConfig(post_text="")
            config.post_text = post.get('text', '')

            # Генерация
            result = self.generate(config)
            result['post_id'] = post.get('id', '')
            result['post_text'] = post.get('text', '')[:100] + '...'

            results.append(result)

            print(f"✓ Сгенерирован комментарий для поста {post.get('id', '')}")

        return results


def main():
    """Пример использования"""

    # Проверка наличия API ключа
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("=" * 60)
        print("⚠ API ключ не найден!")
        print("=" * 60)
        print("\nДобавьте в .env файл:")
        print("ANTHROPIC_API_KEY=your_key")
        print("или")
        print("OPENAI_API_KEY=your_key")
        print("\nПока покажу пример без реальной генерации...\n")

        # Демо режим
        config = GenerationConfig(
            post_text="Сегодня понял важную вещь про work-life balance. "
                      "Работать 24/7 - это путь к выгоранию.",
            target_length="medium",
            tone="friendly",
            use_emoji=True,
            use_personal_experience=True,
            start_pattern="agreement"
        )

        print("=" * 60)
        print("ГЕНЕРАТОР КОММЕНТАРИЕВ (DEMO)")
        print("=" * 60)
        print(f"\n📝 Пост:")
        print(f"   {config.post_text}\n")
        print(f"📊 Конфигурация:")
        print(f"   Длина: {config.target_length}")
        print(f"   Тон: {config.tone}")
        print(f"   Паттерн: {config.start_pattern}")
        print(f"   Эмодзи: {'✓' if config.use_emoji else '✗'}")
        print(f"   Личный опыт: {'✓' if config.use_personal_experience else '✗'}")

        print("\n💡 Для реальной генерации:")
        print("   1. Добавьте API ключ в .env")
        print("   2. Установите: pip install anthropic или pip install openai")
        print("   3. Запустите снова")

        return

    # Реальная генерация
    provider = "anthropic" if os.getenv('ANTHROPIC_API_KEY') else "openai"
    generator = CommentGenerator(api_key=api_key, provider=provider)

    # Пример поста
    sample_post = {
        'id': 'post_1',
        'text': 'Сегодня понял важную вещь про work-life balance. '
                'Работать 24/7 - это путь к выгоранию. Нужно уметь отключаться.'
    }

    # Конфигурация
    config = GenerationConfig(
        post_text=sample_post['text'],
        target_length="medium",
        tone="friendly",
        use_emoji=True,
        use_personal_experience=True,
        start_pattern="agreement",
        include_question=False
    )

    print("=" * 60)
    print("ГЕНЕРАЦИЯ КОММЕНТАРИЯ")
    print("=" * 60)
    print(f"\n📝 Пост:")
    print(f"   {sample_post['text']}\n")

    print("⏳ Генерация...")
    result = generator.generate(config, max_attempts=3)

    print(f"\n💬 СГЕНЕРИРОВАННЫЙ КОММЕНТАРИЙ:\n")
    print(f'   "{result["comment"]}"')

    print(f"\n📊 МЕТРИКИ:")
    print(f"   Human Score: {result['human_score']:.1f}%")
    print(f"   Попыток: {result['attempts']}")
    print(f"   Длина: {result['structure'].length} символов")
    print(f"   Слов: {result['structure'].word_count}")

    detection = result['detection']
    if detection.human_indicators:
        print(f"\n✓ Человеческие признаки:")
        for indicator in detection.human_indicators[:5]:
            print(f"   - {indicator}")

    if detection.ai_indicators:
        print(f"\n⚠ AI признаки:")
        for indicator in detection.ai_indicators[:3]:
            print(f"   - {indicator}")


if __name__ == '__main__':
    main()
