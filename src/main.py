"""
Главный файл - полный цикл работы системы

1. Парсинг постов
2. Выбор топ-3 комментариев по engagement
3. Анализ структуры комментариев (Step 2)
4. Генерация новых комментариев
"""

import os
import json
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv

from parser import get_parser
from utils.engagement import EngagementCalculator
from analyzer import CommentAnalyzer
from detector import AICommentDetector
from generator import CommentGenerator, GenerationConfig

load_dotenv()


class SocialCommentPipeline:
    """Полный пайплайн для работы с комментариями"""

    def __init__(self, platform: str = 'generic'):
        self.platform = platform
        self.parser = get_parser(platform)
        self.engagement_calc = EngagementCalculator()
        self.analyzer = CommentAnalyzer()
        self.detector = AICommentDetector()

        # Генератор инициализируется только при наличии API ключа
        self.generator = None
        self._init_generator()

        self.results_dir = 'data/analysis'
        os.makedirs(self.results_dir, exist_ok=True)

    def _init_generator(self):
        """Инициализация генератора"""
        api_key = os.getenv('ANTHROPIC_API_KEY') or os.getenv('OPENAI_API_KEY')
        if api_key:
            provider = "anthropic" if os.getenv('ANTHROPIC_API_KEY') else "openai"
            self.generator = CommentGenerator(api_key=api_key, provider=provider)
        else:
            print("⚠ API ключ не найден. Генерация будет недоступна.")

    def run_full_pipeline(
        self,
        max_posts: int = 50,
        top_comments_per_post: int = 3,
        generate_new: bool = False
    ) -> Dict[str, Any]:
        """
        Полный цикл работы

        Args:
            max_posts: Количество постов для парсинга
            top_comments_per_post: Топ N комментариев на пост
            generate_new: Генерировать ли новые комментарии

        Returns:
            Результаты всех этапов
        """

        print("=" * 70)
        print("SOCIAL COMMENT ANALYSIS & GENERATION PIPELINE")
        print("=" * 70)

        results = {
            'timestamp': datetime.now().isoformat(),
            'platform': self.platform,
            'config': {
                'max_posts': max_posts,
                'top_comments_per_post': top_comments_per_post,
            }
        }

        # === STEP 1: Парсинг постов ===
        print("\n📱 STEP 1: Парсинг постов...")
        print("-" * 70)

        posts = self.parser.fetch_posts(limit=max_posts)
        results['posts_count'] = len(posts)

        if not posts:
            print("✗ Не удалось получить посты")
            return results

        print(f"✓ Получено постов: {len(posts)}")

        # Сохранение постов
        posts_file = self.parser.save_posts(posts)
        results['posts_file'] = posts_file

        # === STEP 2: Выбор топ-комментариев по engagement ===
        print("\n🏆 STEP 2: Анализ engagement комментариев...")
        print("-" * 70)

        top_comments_by_post = self.engagement_calc.get_top_comments_from_posts(
            posts, top_n_per_post=top_comments_per_post
        )

        # Собираем все топ-комментарии
        all_top_comments = []
        for post_id, top_comments in top_comments_by_post.items():
            for comment, score in top_comments:
                all_top_comments.append({
                    'post_id': post_id,
                    'comment': comment,
                    'engagement_score': score.total_score,
                    'engagement_rate': score.engagement_rate
                })

        results['top_comments_count'] = len(all_top_comments)
        print(f"✓ Выбрано топ-комментариев: {len(all_top_comments)}")

        # === STEP 3: Анализ структуры комментариев ===
        print("\n📊 STEP 3: Анализ структуры комментариев (Step 2)...")
        print("-" * 70)

        # Извлекаем только комментарии для анализа
        comments_to_analyze = [item['comment'] for item in all_top_comments]

        # Анализ
        analysis_result = self.analyzer.analyze_multiple_comments(comments_to_analyze)

        results['comment_analysis'] = analysis_result

        # Вывод рекомендаций
        print("\n💡 РЕКОМЕНДАЦИИ НА ОСНОВЕ АНАЛИЗА:")
        for rec in analysis_result['recommendations']:
            print(f"   {rec}")

        # Ключевые метрики
        patterns = analysis_result['aggregate_patterns']
        print("\n📈 КЛЮЧЕВЫЕ МЕТРИКИ:")
        print(f"   Средняя длина: {patterns['avg_length']:.0f} символов")
        print(f"   Среднее кол-во слов: {patterns['avg_word_count']:.0f}")
        print(f"   Используют эмодзи: {patterns['use_emoji_pct']:.0f}%")
        print(f"   Начинают с согласия: {patterns['starts_with_agreement_pct']:.0f}%")
        print(f"   Упоминают опыт: {patterns['mentions_experience_pct']:.0f}%")

        # Сохранение анализа
        analysis_file = os.path.join(
            self.results_dir,
            f'analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        self.analyzer.save_analysis(analysis_result, analysis_file)
        results['analysis_file'] = analysis_file

        # === STEP 4: Детекция AI vs Human ===
        print("\n🤖 STEP 4: Детекция AI vs Human...")
        print("-" * 70)

        human_comments = []
        ai_like_comments = []

        for comment_data in comments_to_analyze:
            detection = self.detector.detect(comment_data['text'])

            if detection.human_score >= 60:
                human_comments.append(comment_data)
            else:
                ai_like_comments.append(comment_data)

        print(f"   Человеческих: {len(human_comments)} ({len(human_comments)/len(comments_to_analyze)*100:.1f}%)")
        print(f"   AI-подобных: {len(ai_like_comments)} ({len(ai_like_comments)/len(comments_to_analyze)*100:.1f}%)")

        results['human_comments_count'] = len(human_comments)
        results['ai_like_comments_count'] = len(ai_like_comments)

        # === STEP 5: Генерация новых комментариев ===
        if generate_new and self.generator:
            print("\n✍️  STEP 5: Генерация новых комментариев...")
            print("-" * 70)

            # Выбираем несколько постов для генерации
            posts_to_comment = posts[:min(5, len(posts))]

            # Конфигурация на основе анализа
            config = GenerationConfig(
                post_text="",  # Будет заполняться для каждого поста
                target_length=self._determine_target_length(patterns['avg_length']),
                tone="friendly",
                use_emoji=patterns['use_emoji_pct'] > 50,
                use_personal_experience=patterns['mentions_experience_pct'] > 40,
                start_pattern=self._determine_start_pattern(patterns),
                reference_patterns=analysis_result
            )

            generated_comments = []
            for post in posts_to_comment:
                print(f"\n   Генерация для поста {post['id']}...")

                config.post_text = post['text']
                result = self.generator.generate(config, max_attempts=3)

                generated_comments.append({
                    'post_id': post['id'],
                    'post_text': post['text'][:100] + '...',
                    'comment': result['comment'],
                    'human_score': result['human_score'],
                    'attempts': result['attempts']
                })

                print(f"   ✓ Human score: {result['human_score']:.1f}%")

            results['generated_comments'] = generated_comments
            results['generated_count'] = len(generated_comments)

            # Сохранение
            generated_file = os.path.join(
                self.results_dir,
                f'generated_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )
            with open(generated_file, 'w', encoding='utf-8') as f:
                json.dump(generated_comments, f, ensure_ascii=False, indent=2)

            results['generated_file'] = generated_file

            print(f"\n   ✓ Сгенерировано комментариев: {len(generated_comments)}")
            print(f"   ✓ Сохранено: {generated_file}")

        elif generate_new and not self.generator:
            print("\n⚠ Генерация невозможна: API ключ не настроен")

        # === Финальный отчет ===
        print("\n" + "=" * 70)
        print("РЕЗУЛЬТАТЫ")
        print("=" * 70)
        print(f"\n✓ Обработано постов: {results['posts_count']}")
        print(f"✓ Топ-комментариев: {results['top_comments_count']}")
        print(f"✓ Анализ сохранен: {results.get('analysis_file', 'N/A')}")

        if 'generated_count' in results:
            print(f"✓ Сгенерировано комментариев: {results['generated_count']}")

        # Сохранение полного отчета
        report_file = os.path.join(
            self.results_dir,
            f'report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)

        print(f"✓ Полный отчет: {report_file}")

        return results

    def _determine_target_length(self, avg_length: float) -> str:
        """Определение целевой длины на основе анализа"""
        if avg_length < 100:
            return "short"
        elif avg_length < 300:
            return "medium"
        else:
            return "long"

    def _determine_start_pattern(self, patterns: Dict) -> str:
        """Определение паттерна начала на основе анализа"""
        if patterns['starts_with_agreement_pct'] > 40:
            return "agreement"
        elif patterns['starts_with_personal_pct'] > 30:
            return "personal"
        else:
            return "insight"


def main():
    """Точка входа"""

    # Конфигурация из .env
    platform = os.getenv('PLATFORM', 'generic')
    max_posts = int(os.getenv('MAX_POSTS', '50'))
    top_comments = int(os.getenv('TOP_COMMENTS_PER_POST', '3'))
    generate_new = os.getenv('GENERATE_COMMENTS', 'false').lower() == 'true'

    # Создание пайплайна
    pipeline = SocialCommentPipeline(platform=platform)

    # Запуск
    results = pipeline.run_full_pipeline(
        max_posts=max_posts,
        top_comments_per_post=top_comments,
        generate_new=generate_new
    )

    print("\n✨ Пайплайн завершен!")


if __name__ == '__main__':
    main()
