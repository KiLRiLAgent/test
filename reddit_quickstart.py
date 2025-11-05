#!/usr/bin/env python3
"""
Reddit Comment Analyzer - Быстрый старт

Демонстрация анализа Reddit комментариев
"""

import os
import sys

def check_setup():
    """Проверка настройки"""
    print("=" * 70)
    print("REDDIT COMMENT ANALYZER - ПРОВЕРКА НАСТРОЙКИ")
    print("=" * 70)

    issues = []
    warnings = []

    # Проверка Reddit API
    reddit_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_secret = os.getenv('REDDIT_CLIENT_SECRET')

    if not reddit_id or not reddit_secret or 'your_' in reddit_id:
        issues.append("Reddit API ключи не настроены")
        print("\n❌ Reddit API: не настроен")
    else:
        print("\n✓ Reddit API: настроен")

    # Проверка AI API
    ai_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')

    if not ai_key or 'your_' in (ai_key or ''):
        warnings.append("AI API ключ не настроен (глубокий анализ будет недоступен)")
        print("⚠ AI API: не настроен (опционально)")
    else:
        provider = "Anthropic Claude" if os.getenv('ANTHROPIC_API_KEY') else "OpenAI GPT-4"
        print(f"✓ AI API: настроен ({provider})")

    # Проверка PRAW
    try:
        import praw
        print("✓ PRAW библиотека: установлена")
    except ImportError:
        issues.append("PRAW не установлен")
        print("❌ PRAW библиотека: не установлена")

    # Результат
    print("\n" + "=" * 70)

    if issues:
        print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ:\n")
        for issue in issues:
            print(f"   • {issue}")

        print("\n📝 КАК ИСПРАВИТЬ:\n")
        print("1. Установите PRAW:")
        print("   pip install praw\n")

        print("2. Получите Reddit API ключи:")
        print("   https://www.reddit.com/prefs/apps")
        print("   Создайте приложение типа 'script'\n")

        print("3. Добавьте в .env файл:")
        print("   REDDIT_CLIENT_ID=ваш_id")
        print("   REDDIT_CLIENT_SECRET=ваш_secret\n")

        print("📖 Подробная инструкция: REDDIT_SETUP.md\n")
        return False

    if warnings:
        print("⚠ ПРЕДУПРЕЖДЕНИЯ:\n")
        for warning in warnings:
            print(f"   • {warning}")

        print("\n💡 Для глубокого анализа добавьте в .env:")
        print("   ANTHROPIC_API_KEY=sk-ant-...")
        print("   или")
        print("   OPENAI_API_KEY=sk-...")
        print("\nПарсинг и базовый анализ будут работать!\n")

    print("=" * 70)
    print("✓ ГОТОВО К РАБОТЕ")
    print("=" * 70)
    return True


def show_examples():
    """Показать примеры использования"""
    print("\n📚 ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:\n")

    print("1. Парсинг Reddit (только сбор данных):")
    print("   python src/reddit_parser.py\n")

    print("2. Полный пайплайн (парсинг + анализ engagement + глубокий анализ):")
    print("   python src/reddit_pipeline.py\n")

    print("3. Анализ конкретного сабреддита:")
    print("   # В .env установите:")
    print("   REDDIT_SUBREDDITS=wallstreetbets")
    print("   python src/reddit_pipeline.py\n")

    print("\n📊 ЧТО ПРОИСХОДИТ:\n")
    print("Step 1: Парсинг")
    print("   → Получает последние hot посты из каждого сабреддита")
    print("   → Собирает все комментарии")
    print("   → Сохраняет в data/posts/\n")

    print("Step 2: Engagement Analysis")
    print("   → Рассчитывает engagement (score + awards×10 + replies×5)")
    print("   → Выбирает топ-3 комментария на пост")
    print("   → Статистика по сабреддитам\n")

    print("Step 3: Deep Analysis (требует AI API)")
    print("   → Анализирует СТРУКТУРУ комментария")
    print("   → Объясняет ПОЧЕМУ он работает")
    print("   → Выявляет ПСИХОЛОГИЧЕСКИЕ паттерны")
    print("   → Определяет необходимый КОНТЕКСТ")
    print("   → Дает РУКОВОДСТВО по воссозданию\n")

    print("🎯 ЦЕЛЕВЫЕ САБРЕДДИТЫ:\n")
    subs = [
        'r/ValueInvesting',
        'r/DeepFuckingValue',
        'r/StockMarket',
        'r/wallstreetbets',
        'r/WSBAfterHours'
    ]
    for sub in subs:
        print(f"   • {sub}")

    print("\n" + "=" * 70)


def main():
    """Точка входа"""

    print()

    # Загрузка .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("⚠ python-dotenv не установлен. Установите: pip install python-dotenv\n")

    # Проверка настройки
    is_ready = check_setup()

    # Примеры
    show_examples()

    if not is_ready:
        print("Сначала настройте систему (см. выше)\n")
        return

    # Опция быстрого старта
    print("\n🚀 БЫСТРЫЙ СТАРТ:\n")
    print("Хотите запустить базовый парсинг (без глубокого анализа)?")
    print("Это соберет данные из Reddit и покажет топ-комментарии.\n")

    response = input("Запустить? (y/n): ").lower().strip()

    if response == 'y':
        print("\n⏳ Запуск парсинга...\n")
        try:
            from src.reddit_parser import RedditParser

            parser = RedditParser()

            if not parser.reddit:
                print("❌ Не удалось инициализировать Reddit API")
                print("Проверьте настройки в .env")
                return

            # Парсим по 5 постов для быстроты
            all_posts = parser.fetch_all_subreddits(
                limit_per_sub=5,
                time_filter='week',
                sort_by='hot'
            )

            # Статистика
            total_posts = sum(len(posts) for posts in all_posts.values())
            total_comments = sum(
                len(post.get('comments', []))
                for posts in all_posts.values()
                for post in posts
            )

            print("\n" + "=" * 70)
            print("✓ ПАРСИНГ ЗАВЕРШЕН")
            print("=" * 70)
            print(f"Постов: {total_posts}")
            print(f"Комментариев: {total_comments}")

            # Топ комментарий
            from src.reddit_engagement import RedditEngagementCalculator

            calc = RedditEngagementCalculator()
            all_posts_flat = []
            for posts in all_posts.values():
                all_posts_flat.extend(posts)

            top_by_post = calc.get_top_comments_from_posts(all_posts_flat, top_n_per_post=1)

            if top_by_post:
                print("\n🏆 ПРИМЕРЫ ТОПОВЫХ КОММЕНТАРИЕВ:\n")
                count = 0
                for post_id, top_comments in list(top_by_post.items())[:3]:
                    if top_comments:
                        comment, engagement = top_comments[0]
                        print(f"{count+1}. {comment['text'][:100]}...")
                        print(f"   Engagement: {engagement.total_engagement:.0f} | Score: {engagement.score} | Awards: {engagement.total_awards}")
                        print()
                        count += 1

            print("Данные сохранены в data/posts/")
            print("\nДля глубокого анализа:")
            print("1. Добавьте AI API ключ в .env")
            print("2. Запустите: python src/reddit_pipeline.py\n")

        except Exception as e:
            print(f"\n❌ Ошибка: {e}")
            print("\nПроверьте настройки и попробуйте снова")

    else:
        print("\nХорошо! Запустите вручную когда будете готовы:\n")
        print("python src/reddit_pipeline.py\n")


if __name__ == '__main__':
    main()
