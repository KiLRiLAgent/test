#!/usr/bin/env python3
"""
Быстрый старт - демонстрация всех возможностей системы
"""

import sys
import os

# Добавляем src в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from analyzer import CommentAnalyzer
from detector import AICommentDetector


def main():
    print("=" * 70)
    print("SOCIAL COMMENT ANALYZER - БЫСТРЫЙ СТАРТ")
    print("=" * 70)

    # Примеры комментариев
    sample_comments = [
        {
            'text': 'Согласен! У меня был похожий опыт, когда работал в стартапе. '
                    'Главное - не бояться экспериментировать 🚀 А как у вас?',
            'name': 'Успешный человеческий'
        },
        {
            'text': 'It is worth noting that this approach has several important advantages. '
                    'Furthermore, it is crucial to understand the underlying mechanisms. '
                    'In conclusion, this represents a paradigm shift.',
            'name': 'AI-подобный'
        },
        {
            'text': 'Отличная статья! Особенно зацепил момент про work-life balance.\n\n'
                    'Кстати, вы пробовали технику Pomodoro? Мне помогла выйти из выгорания 💡',
            'name': 'Человеческий с ценностью'
        }
    ]

    # === STEP 1: Анализ структуры (Step 2 из задания) ===
    print("\n" + "=" * 70)
    print("STEP 2: АНАЛИЗ СТРУКТУРЫ КОММЕНТАРИЕВ")
    print("=" * 70)

    analyzer = CommentAnalyzer()
    analysis_result = analyzer.analyze_multiple_comments(sample_comments)

    print("\n📊 РЕКОМЕНДАЦИИ НА ОСНОВЕ АНАЛИЗА:\n")
    for rec in analysis_result['recommendations']:
        print(f"  {rec}")

    patterns = analysis_result['aggregate_patterns']
    print("\n📈 КЛЮЧЕВЫЕ МЕТРИКИ:")
    print(f"  Средняя длина: {patterns['avg_length']:.0f} символов")
    print(f"  Среднее кол-во слов: {patterns['avg_word_count']:.0f}")
    print(f"  Используют эмодзи: {patterns['use_emoji_pct']:.0f}%")
    print(f"  Упоминают опыт: {patterns['mentions_experience_pct']:.0f}%")

    # === STEP 2: Детекция AI vs Human ===
    print("\n" + "=" * 70)
    print("ДЕТЕКЦИЯ AI vs HUMAN")
    print("=" * 70)

    detector = AICommentDetector()

    for i, comment in enumerate(sample_comments, 1):
        print(f"\n{'-' * 70}")
        print(f"КОММЕНТАРИЙ #{i}: {comment['name']}")
        print(f"{'-' * 70}")
        print(f"Текст: {comment['text'][:80]}...")

        result = detector.detect(comment['text'])

        print(f"\n🎯 Результат: {result.comment_type.value.upper()}")
        print(f"   Уверенность: {result.confidence:.1f}%")
        print(f"   Human Score: {result.human_score:.1f}%")
        print(f"   AI Score: {result.ai_score:.1f}%")

        if result.human_indicators:
            print(f"\n✓ Человеческие признаки:")
            for indicator in result.human_indicators[:3]:
                print(f"   • {indicator}")

        if result.ai_indicators:
            print(f"\n⚠ AI признаки:")
            for indicator in result.ai_indicators[:3]:
                print(f"   • {indicator}")

    # === NEXT STEPS ===
    print("\n" + "=" * 70)
    print("СЛЕДУЮЩИЕ ШАГИ")
    print("=" * 70)

    print("\n1️⃣  НАСТРОЙКА ПАРСЕРА:")
    print("   • Отредактируйте .env файл")
    print("   • Укажите платформу (PLATFORM=linkedin/twitter/generic)")
    print("   • Для LinkedIn добавьте учетные данные")

    print("\n2️⃣  ЗАПУСК ПОЛНОГО АНАЛИЗА:")
    print("   python src/parser.py     # Парсинг постов")
    print("   python src/analyzer.py   # Анализ комментариев")
    print("   python src/main.py       # Полный пайплайн")

    print("\n3️⃣  ГЕНЕРАЦИЯ КОММЕНТАРИЕВ:")
    print("   • Добавьте ANTHROPIC_API_KEY или OPENAI_API_KEY в .env")
    print("   • python src/generator.py")

    print("\n4️⃣  JUPYTER АНАЛИЗ:")
    print("   • jupyter notebook notebooks/analysis.ipynb")

    print("\n💡 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
    print("   • Документация: README.md")
    print("   • Конфигурация паттернов: config/patterns.json")
    print("   • Результаты анализа: data/analysis/")

    print("\n" + "=" * 70)
    print("✨ Быстрый старт завершен!")
    print("=" * 70)


if __name__ == '__main__':
    main()
