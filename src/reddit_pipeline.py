"""
Reddit Comment Analysis Pipeline

Полный пайплайн для анализа Reddit комментариев:
1. Парсинг постов из сабреддитов
2. Выбор топ-комментариев по engagement
3. Глубокий анализ структуры и психологических паттернов
4. Генерация рекомендаций
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

from reddit_parser import RedditParser
from reddit_engagement import RedditEngagementCalculator
from deep_analyzer import DeepCommentAnalyzer

load_dotenv()


class RedditAnalysisPipeline:
    """Полный пайплайн анализа Reddit комментариев"""

    def __init__(self):
        self.parser = RedditParser()
        self.engagement_calc = RedditEngagementCalculator()

        # Deep analyzer (требует API ключ)
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        if api_key:
            provider = "anthropic" if os.getenv('ANTHROPIC_API_KEY') else "openai"
            self.deep_analyzer = DeepCommentAnalyzer(api_key=api_key, provider=provider)
        else:
            self.deep_analyzer = None
            print("⚠ Deep analyzer недоступен (нет API ключа)")

        self.results_dir = 'data/analysis'
        os.makedirs(self.results_dir, exist_ok=True)

    def run(
        self,
        subreddits: List[str] = None,
        posts_per_subreddit: int = 10,
        top_comments_per_post: int = 3,
        deep_analyze_top_n: int = 5,
        min_comment_score: int = 10
    ) -> Dict[str, Any]:
        """
        Запуск полного пайплайна

        Args:
            subreddits: Список сабреддитов (если None, используются дефолтные)
            posts_per_subreddit: Количество постов на сабреддит
            top_comments_per_post: Топ N комментариев на пост
            deep_analyze_top_n: Сколько комментариев глубоко анализировать
            min_comment_score: Минимальный score для отбора

        Returns:
            Результаты всех этапов
        """

        print("=" * 70)
        print("REDDIT COMMENT ANALYSIS PIPELINE")
        print("=" * 70)

        results = {
            'timestamp': datetime.now().isoformat(),
            'config': {
                'subreddits': subreddits or self.parser.subreddits,
                'posts_per_subreddit': posts_per_subreddit,
                'top_comments_per_post': top_comments_per_post,
                'deep_analyze_top_n': deep_analyze_top_n,
                'min_comment_score': min_comment_score
            }
        }

        # === STEP 1: Парсинг Reddit ===
        print("\n📱 STEP 1: Парсинг Reddit...")
        print("-" * 70)

        if subreddits:
            # Временно заменяем список сабреддитов
            original_subs = self.parser.subreddits
            self.parser.subreddits = subreddits

        all_posts = self.parser.fetch_all_subreddits(
            limit_per_sub=posts_per_subreddit,
            time_filter='week',
            sort_by='hot'
        )

        if subreddits:
            self.parser.subreddits = original_subs

        # Статистика парсинга
        total_posts = sum(len(posts) for posts in all_posts.values())
        total_comments = sum(
            len(post.get('comments', []))
            for posts in all_posts.values()
            for post in posts
        )

        results['parsing'] = {
            'total_posts': total_posts,
            'total_comments': total_comments,
            'by_subreddit': {
                sub: {
                    'posts': len(posts),
                    'comments': sum(len(p.get('comments', [])) for p in posts)
                }
                for sub, posts in all_posts.items()
            }
        }

        print(f"\n✓ Спарсено постов: {total_posts}")
        print(f"✓ Всего комментариев: {total_comments}")

        # Сохранение постов
        self.parser.save_posts(all_posts)

        # === STEP 2: Анализ engagement ===
        print("\n🏆 STEP 2: Анализ engagement...")
        print("-" * 70)

        # Объединяем все посты для анализа
        all_posts_flat = []
        for posts in all_posts.values():
            all_posts_flat.extend(posts)

        # Топ комментарии по постам
        top_comments_by_post = self.engagement_calc.get_top_comments_from_posts(
            all_posts_flat,
            top_n_per_post=top_comments_per_post,
            min_score=min_comment_score
        )

        # Собираем все топ-комментарии
        all_top_comments = []
        for post_id, top_comments in top_comments_by_post.items():
            for comment, engagement in top_comments:
                all_top_comments.append({
                    'post_id': post_id,
                    'comment': comment,
                    'engagement': engagement
                })

        # Сортируем по engagement для deep analysis
        all_top_comments.sort(
            key=lambda x: x['engagement'].total_engagement,
            reverse=True
        )

        results['engagement'] = {
            'total_top_comments': len(all_top_comments),
            'avg_engagement': sum(c['engagement'].total_engagement for c in all_top_comments) / len(all_top_comments) if all_top_comments else 0,
            'tier_distribution': self._calculate_tier_distribution(all_top_comments)
        }

        print(f"\n✓ Выбрано топ-комментариев: {len(all_top_comments)}")
        print(f"✓ Средний engagement: {results['engagement']['avg_engagement']:.2f}")

        # === STEP 3: Статистика по сабреддитам ===
        print("\n📊 STEP 3: Статистика по сабреддитам...")
        print("-" * 70)

        subreddit_stats = {}
        for subreddit_name, posts in all_posts.items():
            stats = self.engagement_calc.analyze_subreddit_engagement(posts)
            subreddit_stats[subreddit_name] = stats

            print(f"\nr/{subreddit_name}:")
            print(f"  Комментариев: {stats.get('total_comments', 0)}")
            print(f"  Средний score: {stats.get('avg_score', 0):.1f}")
            print(f"  Средний engagement: {stats.get('avg_engagement', 0):.2f}")

        results['subreddit_stats'] = subreddit_stats

        # === STEP 4: Глубокий анализ ===
        if self.deep_analyzer and deep_analyze_top_n > 0:
            print("\n🧠 STEP 4: Глубокий анализ комментариев...")
            print("-" * 70)

            # Выбираем топ N для глубокого анализа
            comments_to_analyze = all_top_comments[:deep_analyze_top_n]

            # Нужно найти соответствующие посты
            comments_with_posts = []
            for item in comments_to_analyze:
                comment = item['comment']
                post_id = item['post_id']

                # Ищем пост
                post = None
                for posts in all_posts.values():
                    for p in posts:
                        if p.get('id') == post_id:
                            post = p
                            break
                    if post:
                        break

                if post:
                    comments_with_posts.append((comment, post))

            # Глубокий анализ
            deep_results = self.deep_analyzer.analyze_batch(
                comments_with_posts,
                save_results=True,
                output_dir=self.results_dir
            )

            results['deep_analysis'] = {
                'analyzed_count': len(deep_results),
                'results': [self._summarize_deep_result(r) for r in deep_results]
            }

            print(f"\n✓ Глубоко проанализировано: {len(deep_results)} комментариев")

        # === Сохранение отчета ===
        report_file = os.path.join(
            self.results_dir,
            f'reddit_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        # === Финальный отчет ===
        print("\n" + "=" * 70)
        print("РЕЗУЛЬТАТЫ")
        print("=" * 70)
        print(f"\n✓ Спарсено постов: {total_posts}")
        print(f"✓ Всего комментариев: {total_comments}")
        print(f"✓ Топ-комментариев отобрано: {len(all_top_comments)}")

        if self.deep_analyzer and deep_analyze_top_n > 0:
            print(f"✓ Глубоко проанализировано: {len(deep_results)}")

        print(f"\n📊 Отчет сохранен: {report_file}")

        return results

    def _calculate_tier_distribution(self, comments: List[Dict]) -> Dict[str, int]:
        """Распределение по категориям engagement"""
        distribution = {}
        for item in comments:
            tier = item['engagement'].engagement_tier
            distribution[tier] = distribution.get(tier, 0) + 1
        return distribution

    def _summarize_deep_result(self, result) -> Dict[str, Any]:
        """Краткое резюме глубокого анализа"""
        return {
            'comment_preview': result.comment_text[:100] + '...',
            'subreddit': result.subreddit,
            'why_it_works_count': len(result.why_it_works),
            'psychological_patterns_count': len(result.psychological_patterns),
            'engagement_score': result.engagement_metrics.get('score', 0)
        }


def main():
    """Точка входа"""

    # Проверка Reddit API
    if not os.getenv('REDDIT_CLIENT_ID') or not os.getenv('REDDIT_CLIENT_SECRET'):
        print("=" * 70)
        print("⚠ REDDIT API НЕ НАСТРОЕН")
        print("=" * 70)
        print("\n📝 Инструкция:")
        print("1. Перейдите на https://www.reddit.com/prefs/apps")
        print("2. Создайте приложение (тип: script)")
        print("3. Добавьте в .env:")
        print("   REDDIT_CLIENT_ID=your_client_id")
        print("   REDDIT_CLIENT_SECRET=your_secret")
        print("\nДля глубокого анализа также нужен AI API ключ:")
        print("   ANTHROPIC_API_KEY=sk-...")
        return

    # Конфигурация
    subreddits = os.getenv('REDDIT_SUBREDDITS', '').split(',')
    if not subreddits or subreddits == ['']:
        subreddits = None  # Используем дефолтные

    posts_limit = int(os.getenv('REDDIT_POSTS_LIMIT', '10'))
    top_comments = int(os.getenv('TOP_COMMENTS_PER_POST', '3'))
    deep_analyze = int(os.getenv('DEEP_ANALYZE_COUNT', '5'))
    min_score = int(os.getenv('MIN_COMMENT_SCORE', '10'))

    print("\n⚙️  КОНФИГУРАЦИЯ:")
    print(f"   Постов на сабреддит: {posts_limit}")
    print(f"   Топ-комментариев на пост: {top_comments}")
    print(f"   Глубокий анализ топ-N: {deep_analyze}")
    print(f"   Минимальный score: {min_score}")

    # Запуск пайплайна
    pipeline = RedditAnalysisPipeline()

    results = pipeline.run(
        subreddits=subreddits,
        posts_per_subreddit=posts_limit,
        top_comments_per_post=top_comments,
        deep_analyze_top_n=deep_analyze,
        min_comment_score=min_score
    )

    print("\n✨ Пайплайн завершен!")


if __name__ == '__main__':
    main()
