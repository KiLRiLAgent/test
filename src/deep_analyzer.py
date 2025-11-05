"""
Deep Comment Analyzer - Глубокий анализ комментариев

Разбирает структуру комментария, почему он работает,
психологические паттерны, контекст и способ воссоздания.

Промпт: "Break down the structure of this comments so that I can
recreate it from scratch. Break down why it works, the psychological
patterns involved, what context is needed from me, and anything else
I would need to understand how to recreate it."
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DeepAnalysisResult:
    """Результат глубокого анализа комментария"""

    # Исходные данные
    comment_text: str
    post_context: str
    subreddit: str

    # Структурный разбор
    structure_breakdown: Dict[str, Any]

    # Почему работает
    why_it_works: List[str]

    # Психологические паттерны
    psychological_patterns: List[Dict[str, str]]

    # Необходимый контекст
    required_context: List[str]

    # Как воссоздать
    recreation_guide: Dict[str, Any]

    # Engagement метрики (для корреляции)
    engagement_metrics: Dict[str, Any]


class DeepCommentAnalyzer:
    """
    Глубокий анализатор комментариев

    Использует AI для детального разбора успешных комментариев
    """

    ANALYSIS_PROMPT_TEMPLATE = """Analyze this Reddit comment in detail. Break down the structure so it can be recreated from scratch.

POST CONTEXT:
{post_title}
{post_text}

COMMENT:
{comment_text}

ENGAGEMENT METRICS:
- Score: {score}
- Awards: {awards}
- Replies: {replies}

Please provide a detailed breakdown:

1. STRUCTURE BREAKDOWN:
   - Opening (how it starts)
   - Body (main content organization)
   - Closing (how it ends)
   - Length and formatting
   - Use of emphasis, lists, quotes, etc.

2. WHY IT WORKS:
   - What makes this comment effective
   - Key elements that drive engagement
   - Timing and relevance factors
   - Unique value provided

3. PSYCHOLOGICAL PATTERNS:
   - What psychological triggers are used
   - Emotional appeals (if any)
   - Social proof elements
   - Authority/credibility signals
   - Storytelling techniques
   - Humor or wit patterns
   - Controversy or contrarian elements

4. REQUIRED CONTEXT:
   - What knowledge about the post is needed
   - Subreddit culture understanding
   - Current events or memes referenced
   - Technical knowledge required
   - Community in-jokes or language

5. RECREATION GUIDE:
   - Step-by-step formula to recreate this style
   - Key phrases or patterns to use
   - Tone and voice guidelines
   - What to avoid
   - When this pattern works best

Provide your analysis in a structured, actionable format."""

    def __init__(self, api_key: str = None, provider: str = "anthropic"):
        """
        Args:
            api_key: API ключ для AI провайдера
            provider: 'anthropic' или 'openai'
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.provider = provider
        self.client = None
        self._init_ai_client()

    def _init_ai_client(self):
        """Инициализация AI клиента"""
        try:
            if self.provider == "anthropic":
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
                print("✓ Anthropic AI подключен для глубокого анализа")
            elif self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                print("✓ OpenAI подключен для глубокого анализа")
        except ImportError as e:
            print(f"⚠ Не установлена библиотека {self.provider}: {e}")
        except Exception as e:
            print(f"⚠ Ошибка инициализации AI: {e}")

    def analyze_comment(
        self,
        comment: Dict[str, Any],
        post: Dict[str, Any]
    ) -> Optional[DeepAnalysisResult]:
        """
        Глубокий анализ комментария

        Args:
            comment: Данные комментария
            post: Данные поста (контекст)

        Returns:
            DeepAnalysisResult или None
        """
        if not self.client:
            print("⚠ AI клиент не инициализирован")
            return None

        # Подготовка промпта
        prompt = self.ANALYSIS_PROMPT_TEMPLATE.format(
            post_title=post.get('title', ''),
            post_text=post.get('text', '')[:500],  # Первые 500 символов
            comment_text=comment['text'],
            score=comment.get('score', 0),
            awards=comment.get('total_awards', 0),
            replies=comment.get('replies', 0)
        )

        try:
            # Вызов AI
            analysis_text = self._call_ai(prompt)

            if not analysis_text:
                return None

            # Парсинг результата
            result = self._parse_ai_response(
                analysis_text,
                comment,
                post
            )

            return result

        except Exception as e:
            print(f"✗ Ошибка анализа: {e}")
            return None

    def _call_ai(self, prompt: str) -> Optional[str]:
        """Вызов AI API"""
        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    temperature=0.3,  # Низкая температура для точного анализа
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.content[0].text

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    max_tokens=4000,
                    temperature=0.3,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                return response.choices[0].message.content

        except Exception as e:
            print(f"✗ Ошибка вызова AI: {e}")
            return None

    def _parse_ai_response(
        self,
        analysis_text: str,
        comment: Dict[str, Any],
        post: Dict[str, Any]
    ) -> DeepAnalysisResult:
        """Парсинг ответа AI в структурированный формат"""

        # Простой парсинг секций
        sections = self._extract_sections(analysis_text)

        return DeepAnalysisResult(
            comment_text=comment['text'],
            post_context=f"{post.get('title', '')} | {post.get('text', '')[:200]}",
            subreddit=post.get('subreddit', ''),

            structure_breakdown=sections.get('structure', {}),

            why_it_works=self._extract_list(sections.get('why_it_works', '')),

            psychological_patterns=self._extract_patterns(
                sections.get('psychological_patterns', '')
            ),

            required_context=self._extract_list(sections.get('required_context', '')),

            recreation_guide=sections.get('recreation_guide', {}),

            engagement_metrics={
                'score': comment.get('score', 0),
                'awards': comment.get('total_awards', 0),
                'replies': comment.get('replies', 0),
                'controversiality': comment.get('controversiality', 0)
            }
        )

    def _extract_sections(self, text: str) -> Dict[str, Any]:
        """Извлечение секций из ответа AI"""
        sections = {}

        # Ищем секции по заголовкам
        section_markers = {
            'structure': ['STRUCTURE BREAKDOWN', '1. STRUCTURE'],
            'why_it_works': ['WHY IT WORKS', '2. WHY'],
            'psychological_patterns': ['PSYCHOLOGICAL PATTERNS', '3. PSYCHOLOGICAL'],
            'required_context': ['REQUIRED CONTEXT', '4. REQUIRED'],
            'recreation_guide': ['RECREATION GUIDE', '5. RECREATION']
        }

        for key, markers in section_markers.items():
            section_text = ''
            for marker in markers:
                if marker in text:
                    # Извлекаем текст секции
                    start = text.find(marker)
                    # Ищем следующую секцию или конец
                    next_section = len(text)
                    for other_markers in section_markers.values():
                        for other_marker in other_markers:
                            if other_marker in text[start + len(marker):]:
                                pos = text.find(other_marker, start + len(marker))
                                if pos < next_section and pos != -1:
                                    next_section = pos

                    section_text = text[start:next_section].strip()
                    break

            sections[key] = section_text

        return sections

    def _extract_list(self, text: str) -> List[str]:
        """Извлечение списка из текста"""
        items = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            # Ищем маркеры списка
            if line.startswith(('-', '•', '*', '·')) or (len(line) > 0 and line[0].isdigit() and '.' in line[:3]):
                # Убираем маркер
                item = line.lstrip('-•*·0123456789. ').strip()
                if item:
                    items.append(item)

        return items

    def _extract_patterns(self, text: str) -> List[Dict[str, str]]:
        """Извлечение психологических паттернов"""
        patterns = []
        items = self._extract_list(text)

        for item in items:
            # Пытаемся разделить на паттерн и описание
            if ':' in item:
                parts = item.split(':', 1)
                patterns.append({
                    'pattern': parts[0].strip(),
                    'description': parts[1].strip()
                })
            else:
                patterns.append({
                    'pattern': item,
                    'description': ''
                })

        return patterns

    def analyze_batch(
        self,
        comments_with_posts: List[tuple],
        save_results: bool = True,
        output_dir: str = 'data/analysis'
    ) -> List[DeepAnalysisResult]:
        """
        Анализ множества комментариев

        Args:
            comments_with_posts: Список кортежей (comment, post)
            save_results: Сохранять ли результаты
            output_dir: Директория для сохранения

        Returns:
            Список результатов анализа
        """
        results = []

        print("=" * 70)
        print("ГЛУБОКИЙ АНАЛИЗ КОММЕНТАРИЕВ")
        print("=" * 70)

        for i, (comment, post) in enumerate(comments_with_posts, 1):
            print(f"\n[{i}/{len(comments_with_posts)}] Анализ комментария...")
            print(f"  Пост: {post.get('title', '')[:60]}...")
            print(f"  Комментарий: {comment['text'][:80]}...")
            print(f"  Engagement: {comment.get('score', 0)} score, {comment.get('total_awards', 0)} awards")

            result = self.analyze_comment(comment, post)

            if result:
                results.append(result)
                print(f"  ✓ Анализ завершен")

                # Краткий вывод
                if result.why_it_works:
                    print(f"\n  💡 Почему работает:")
                    for reason in result.why_it_works[:2]:
                        print(f"     • {reason[:80]}...")

        # Сохранение
        if save_results and results:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'deep_analysis_{timestamp}.json'
            filepath = os.path.join(output_dir, filename)

            # Конвертация в JSON
            results_dict = [asdict(r) for r in results]

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2)

            print(f"\n✓ Сохранено {len(results)} анализов: {filepath}")

        return results


def main():
    """Пример использования"""

    # Проверка API ключа
    api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')

    if not api_key:
        print("=" * 70)
        print("⚠ API КЛЮЧ НЕ НАЙДЕН")
        print("=" * 70)
        print("\nДля глубокого анализа нужен API ключ AI.")
        print("\nДобавьте в .env:")
        print("ANTHROPIC_API_KEY=sk-...")
        print("или")
        print("OPENAI_API_KEY=sk-...")
        return

    # Пример данных (замените на реальные из Reddit)
    example_post = {
        'title': 'Why I think Tesla is overvalued',
        'text': 'Looking at the fundamentals, PE ratio is insane...',
        'subreddit': 'wallstreetbets'
    }

    example_comment = {
        'text': 'This is exactly what I\'ve been saying! 🚀 The fundamentals don\'t matter '
                'when you have Elon tweeting. I learned this the hard way shorting TSLA '
                'in 2020. Lost 50k. Now I just buy calls whenever WSB goes bearish lol',
        'score': 856,
        'total_awards': 3,
        'replies': 42,
        'controversiality': 0
    }

    # Анализ
    provider = "anthropic" if os.getenv('ANTHROPIC_API_KEY') else "openai"
    analyzer = DeepCommentAnalyzer(api_key=api_key, provider=provider)

    print("\n⏳ Запуск глубокого анализа...\n")

    result = analyzer.analyze_comment(example_comment, example_post)

    if result:
        print("\n" + "=" * 70)
        print("РЕЗУЛЬТАТ АНАЛИЗА")
        print("=" * 70)

        print(f"\n📝 КОММЕНТАРИЙ:")
        print(f"   {result.comment_text[:100]}...")

        print(f"\n💡 ПОЧЕМУ РАБОТАЕТ:")
        for reason in result.why_it_works[:3]:
            print(f"   • {reason}")

        print(f"\n🧠 ПСИХОЛОГИЧЕСКИЕ ПАТТЕРНЫ:")
        for pattern in result.psychological_patterns[:3]:
            print(f"   • {pattern['pattern']}")
            if pattern['description']:
                print(f"     → {pattern['description']}")

        print(f"\n📚 НЕОБХОДИМЫЙ КОНТЕКСТ:")
        for ctx in result.required_context[:3]:
            print(f"   • {ctx}")

        print(f"\n📊 ENGAGEMENT:")
        print(f"   Score: {result.engagement_metrics['score']}")
        print(f"   Awards: {result.engagement_metrics['awards']}")
        print(f"   Replies: {result.engagement_metrics['replies']}")


if __name__ == '__main__':
    main()
