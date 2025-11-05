"""
Reddit Parser для парсинга постов и комментариев

Сабреддиты для анализа:
- r/ValueInvesting
- r/DeepFuckingValue
- r/StockMarket
- r/wallstreetbets
- r/WSBAfterHours
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import time

load_dotenv()


class RedditParser:
    """Парсер для Reddit"""

    def __init__(self):
        """
        Инициализация Reddit парсера

        Требуется PRAW (Python Reddit API Wrapper):
        pip install praw

        Настройки в .env:
        REDDIT_CLIENT_ID=your_client_id
        REDDIT_CLIENT_SECRET=your_client_secret
        REDDIT_USER_AGENT=your_user_agent
        """
        self.reddit = None
        self.subreddits = [
            'ValueInvesting',
            'DeepFuckingValue',
            'StockMarket',
            'wallstreetbets',
            'WSBAfterHours'
        ]
        self._init_reddit()

    def _init_reddit(self):
        """Инициализация PRAW клиента"""
        try:
            import praw

            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'Comment Analyzer Bot 1.0')

            if not client_id or not client_secret:
                print("⚠ Reddit credentials не найдены в .env")
                print("Как получить:")
                print("1. Перейдите на https://www.reddit.com/prefs/apps")
                print("2. Создайте новое приложение (script)")
                print("3. Скопируйте client_id и client_secret")
                return

            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent=user_agent
            )

            # Проверка подключения
            self.reddit.user.me()
            print("✓ Reddit API подключен (read-only mode)")

        except ImportError:
            print("⚠ PRAW не установлен. Установите: pip install praw")
        except Exception as e:
            print(f"⚠ Ошибка инициализации Reddit API: {e}")

    def fetch_posts(
        self,
        subreddit_name: str = None,
        limit: int = 50,
        time_filter: str = 'week',
        sort_by: str = 'hot'
    ) -> List[Dict[str, Any]]:
        """
        Получить посты из сабреддита

        Args:
            subreddit_name: Имя сабреддита (без r/)
            limit: Количество постов
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
            sort_by: 'hot', 'new', 'top', 'rising'
        """
        if not self.reddit:
            print("✗ Reddit API не инициализирован")
            return []

        try:
            # Если не указан сабреддит, берем первый из списка
            if not subreddit_name:
                subreddit_name = self.subreddits[0]

            subreddit = self.reddit.subreddit(subreddit_name)

            # Получение постов в зависимости от сортировки
            if sort_by == 'hot':
                submissions = subreddit.hot(limit=limit)
            elif sort_by == 'new':
                submissions = subreddit.new(limit=limit)
            elif sort_by == 'top':
                submissions = subreddit.top(time_filter=time_filter, limit=limit)
            elif sort_by == 'rising':
                submissions = subreddit.rising(limit=limit)
            else:
                submissions = subreddit.hot(limit=limit)

            posts = []

            print(f"⏳ Парсинг r/{subreddit_name}...")

            for submission in submissions:
                post_data = self._parse_submission(submission)

                # Получаем комментарии
                print(f"  📝 {submission.title[:60]}... ({submission.num_comments} комментариев)")
                comments = self.fetch_comments(submission)
                post_data['comments'] = comments

                posts.append(post_data)

                # Небольшая задержка, чтобы не перегружать API
                time.sleep(0.5)

            print(f"✓ Получено {len(posts)} постов из r/{subreddit_name}")
            return posts

        except Exception as e:
            print(f"✗ Ошибка при получении постов: {e}")
            return []

    def fetch_comments(
        self,
        submission,
        limit: int = 50,
        sort: str = 'best'
    ) -> List[Dict[str, Any]]:
        """
        Получить комментарии к посту

        Args:
            submission: PRAW Submission объект
            limit: Максимальное количество комментариев
            sort: 'best', 'top', 'new', 'controversial', 'old', 'qa'
        """
        try:
            # Сортировка комментариев
            submission.comment_sort = sort

            # Раскрываем все комментарии (до лимита)
            submission.comments.replace_more(limit=0)

            comments = []

            for comment in submission.comments.list()[:limit]:
                # Пропускаем удаленные/удаленные модератором
                if hasattr(comment, 'body') and comment.body not in ['[deleted]', '[removed]']:
                    comment_data = self._parse_comment(comment)
                    comments.append(comment_data)

            return comments

        except Exception as e:
            print(f"  ⚠ Ошибка при получении комментариев: {e}")
            return []

    def _parse_submission(self, submission) -> Dict[str, Any]:
        """Парсинг поста в единый формат"""

        # Расчет возраста
        created_utc = submission.created_utc
        age_hours = (time.time() - created_utc) / 3600

        return {
            'id': submission.id,
            'platform': 'reddit',
            'subreddit': submission.subreddit.display_name,
            'title': submission.title,
            'text': submission.selftext,
            'url': f"https://reddit.com{submission.permalink}",
            'author': str(submission.author) if submission.author else '[deleted]',
            'created_utc': created_utc,
            'created_at': datetime.fromtimestamp(created_utc).isoformat(),
            'age_hours': age_hours,

            # Engagement метрики
            'score': submission.score,
            'upvote_ratio': submission.upvote_ratio,
            'num_comments': submission.num_comments,

            # Дополнительно
            'is_self': submission.is_self,
            'link_flair_text': submission.link_flair_text,
            'over_18': submission.over_18,
            'spoiler': submission.spoiler,
            'stickied': submission.stickied,

            # Будет заполнено позже
            'comments': []
        }

    def _parse_comment(self, comment) -> Dict[str, Any]:
        """Парсинг комментария в единый формат"""

        # Расчет возраста
        created_utc = comment.created_utc
        age_hours = (time.time() - created_utc) / 3600

        # Подсчет наград
        awards = {}
        total_awards = 0
        if hasattr(comment, 'all_awardings'):
            for award in comment.all_awardings:
                award_name = award.get('name', 'unknown')
                count = award.get('count', 1)
                awards[award_name] = count
                total_awards += count

        return {
            'id': comment.id,
            'text': comment.body,
            'author': str(comment.author) if comment.author else '[deleted]',
            'author_flair': comment.author_flair_text,
            'created_utc': created_utc,
            'created_at': datetime.fromtimestamp(created_utc).isoformat(),
            'age_hours': age_hours,

            # Engagement метрики
            'score': comment.score,
            'ups': comment.ups,
            'downs': comment.downs,
            'controversiality': comment.controversiality,

            # Награды
            'awards': awards,
            'total_awards': total_awards,

            # Структура
            'is_submitter': comment.is_submitter,  # Автор поста
            'depth': comment.depth,  # Глубина вложенности
            'parent_id': comment.parent_id,

            # Для калькулятора engagement
            'likes': comment.score,
            'replies': len(list(comment.replies)) if hasattr(comment, 'replies') else 0,
            'shares': 0,  # Reddit не показывает шеры
            'reactions': awards,  # Награды как реакции
        }

    def fetch_all_subreddits(
        self,
        limit_per_sub: int = 50,
        time_filter: str = 'week',
        sort_by: str = 'hot'
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Получить посты из всех настроенных сабреддитов

        Returns:
            Словарь {subreddit_name: [posts]}
        """
        if not self.reddit:
            print("✗ Reddit API не инициализирован")
            return {}

        results = {}

        print("=" * 70)
        print("ПАРСИНГ REDDIT SUBREDDITS")
        print("=" * 70)

        for subreddit_name in self.subreddits:
            print(f"\n📱 Сабреддит: r/{subreddit_name}")
            print("-" * 70)

            posts = self.fetch_posts(
                subreddit_name=subreddit_name,
                limit=limit_per_sub,
                time_filter=time_filter,
                sort_by=sort_by
            )

            results[subreddit_name] = posts

            # Задержка между сабреддитами
            time.sleep(2)

        return results

    def save_posts(self, posts_data: Dict[str, List[Dict[str, Any]]], output_dir: str = 'data/posts'):
        """Сохранение постов"""
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        for subreddit_name, posts in posts_data.items():
            filename = f'reddit_{subreddit_name}_{timestamp}.json'
            filepath = os.path.join(output_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(posts, f, ensure_ascii=False, indent=2)

            print(f"✓ Сохранено {len(posts)} постов: {filepath}")


def main():
    """Пример использования"""

    parser = RedditParser()

    if not parser.reddit:
        print("\n❌ Не удалось инициализировать Reddit API")
        print("\n📝 Инструкция по настройке:")
        print("1. Перейдите на https://www.reddit.com/prefs/apps")
        print("2. Нажмите 'create another app...' внизу страницы")
        print("3. Выберите тип 'script'")
        print("4. Заполните:")
        print("   - name: Comment Analyzer")
        print("   - redirect uri: http://localhost:8080")
        print("5. Нажмите 'create app'")
        print("6. Скопируйте client_id (под названием) и secret")
        print("7. Добавьте в .env:")
        print("   REDDIT_CLIENT_ID=ваш_client_id")
        print("   REDDIT_CLIENT_SECRET=ваш_secret")
        print("   REDDIT_USER_AGENT=Comment Analyzer Bot 1.0")
        return

    # Парсинг всех сабреддитов
    limit_per_sub = int(os.getenv('REDDIT_POSTS_LIMIT', '10'))

    print(f"\n⚙️  Настройки:")
    print(f"   Постов на сабреддит: {limit_per_sub}")
    print(f"   Временной фильтр: week")
    print(f"   Сортировка: hot\n")

    all_posts = parser.fetch_all_subreddits(
        limit_per_sub=limit_per_sub,
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
    print("СТАТИСТИКА")
    print("=" * 70)
    print(f"Всего постов: {total_posts}")
    print(f"Всего комментариев: {total_comments}")

    # Сохранение
    parser.save_posts(all_posts)

    print("\n✨ Парсинг завершен!")


if __name__ == '__main__':
    main()
