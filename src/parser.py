"""
Парсер постов и комментариев из социальных сетей

Поддерживает:
- LinkedIn (через linkedin-api)
- Пример структуры для других платформ
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


class SocialMediaParser:
    """Базовый класс для парсеров"""

    def __init__(self, platform: str):
        self.platform = platform
        self.data_dir = 'data/posts'
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_posts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Получить последние посты"""
        raise NotImplementedError

    def fetch_comments(self, post_id: str) -> List[Dict[str, Any]]:
        """Получить комментарии к посту"""
        raise NotImplementedError

    def save_posts(self, posts: List[Dict[str, Any]], filename: str = None):
        """Сохранить посты в JSON"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'{self.platform}_posts_{timestamp}.json'

        filepath = os.path.join(self.data_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=2)

        print(f"✓ Сохранено {len(posts)} постов: {filepath}")
        return filepath


class LinkedInParser(SocialMediaParser):
    """Парсер для LinkedIn"""

    def __init__(self):
        super().__init__('linkedin')
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.api = None

    def authenticate(self):
        """Аутентификация в LinkedIn"""
        try:
            from linkedin_api import Linkedin
            self.api = Linkedin(self.email, self.password)
            print("✓ Успешная аутентификация в LinkedIn")
            return True
        except ImportError:
            print("⚠ linkedin-api не установлен. Установите: pip install linkedin-api")
            return False
        except Exception as e:
            print(f"✗ Ошибка аутентификации: {e}")
            return False

    def fetch_posts(self, limit: int = 50, profile_id: str = None) -> List[Dict[str, Any]]:
        """
        Получить последние посты из LinkedIn

        Args:
            limit: Количество постов
            profile_id: ID профиля (если None, то из фида)
        """
        if not self.api:
            if not self.authenticate():
                return []

        try:
            posts = []

            if profile_id:
                # Посты конкретного профиля
                profile_posts = self.api.get_profile_posts(profile_id, post_count=limit)
            else:
                # Посты из фида
                print("⚠ Получение постов из фида требует доп. настройки")
                return []

            for post in profile_posts:
                parsed_post = self._parse_linkedin_post(post)

                # Получаем комментарии
                if 'urn' in post:
                    comments = self.fetch_comments(post['urn'])
                    parsed_post['comments'] = comments

                posts.append(parsed_post)

            print(f"✓ Получено {len(posts)} постов")
            return posts

        except Exception as e:
            print(f"✗ Ошибка получения постов: {e}")
            return []

    def fetch_comments(self, post_urn: str) -> List[Dict[str, Any]]:
        """Получить комментарии к посту LinkedIn"""
        if not self.api:
            return []

        try:
            comments_data = self.api.get_post_comments(post_urn)
            comments = []

            for comment in comments_data:
                parsed_comment = self._parse_linkedin_comment(comment)
                comments.append(parsed_comment)

            return comments

        except Exception as e:
            print(f"⚠ Ошибка получения комментариев: {e}")
            return []

    def _parse_linkedin_post(self, post: Dict) -> Dict[str, Any]:
        """Парсинг поста LinkedIn в единый формат"""
        return {
            'id': post.get('urn', ''),
            'platform': 'linkedin',
            'text': post.get('commentary', {}).get('text', ''),
            'author': post.get('actor', {}).get('name', ''),
            'author_id': post.get('actor', {}).get('urn', ''),
            'created_at': post.get('created', {}).get('time', 0),
            'likes': post.get('socialDetail', {}).get('totalSocialActivityCounts', {}).get('numLikes', 0),
            'comments_count': post.get('socialDetail', {}).get('totalSocialActivityCounts', {}).get('numComments', 0),
            'shares': post.get('socialDetail', {}).get('totalSocialActivityCounts', {}).get('numShares', 0),
            'url': f"https://www.linkedin.com/feed/update/{post.get('urn', '')}",
            'raw_data': post
        }

    def _parse_linkedin_comment(self, comment: Dict) -> Dict[str, Any]:
        """Парсинг комментария LinkedIn в единый формат"""

        # Расчет возраста комментария
        created_time = comment.get('created', {}).get('time', 0)
        if created_time:
            age_hours = (datetime.now().timestamp() * 1000 - created_time) / (1000 * 60 * 60)
        else:
            age_hours = 0

        return {
            'id': comment.get('$URN', ''),
            'text': comment.get('message', {}).get('text', ''),
            'author': comment.get('commenter', {}).get('name', ''),
            'author_id': comment.get('commenter', {}).get('urn', ''),
            'author_followers': comment.get('commenter', {}).get('followersCount', 0),
            'created_at': created_time,
            'age_hours': age_hours,
            'likes': comment.get('socialDetail', {}).get('totalSocialActivityCounts', {}).get('numLikes', 0),
            'replies': len(comment.get('comments', [])),
            'reactions': self._parse_reactions(comment.get('socialDetail', {})),
            'raw_data': comment
        }

    def _parse_reactions(self, social_detail: Dict) -> Dict[str, int]:
        """Парсинг реакций LinkedIn"""
        reactions = {}

        # LinkedIn имеет разные типы реакций
        reaction_types = social_detail.get('reactionTypeCounts', [])
        for reaction in reaction_types:
            reaction_type = reaction.get('reactionType', 'LIKE').lower()
            count = reaction.get('count', 0)
            reactions[reaction_type] = count

        return reactions


class GenericParser(SocialMediaParser):
    """
    Универсальный парсер для демо/тестирования
    Загружает данные из JSON файлов
    """

    def __init__(self, platform: str = 'generic'):
        super().__init__(platform)

    def fetch_posts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Загрузка постов из JSON (для тестирования)"""

        # Пример структуры постов
        sample_posts = [
            {
                'id': f'post_{i}',
                'platform': self.platform,
                'text': f'Пример поста #{i} с интересным контентом',
                'author': f'User {i}',
                'author_id': f'user_{i}',
                'created_at': datetime.now().timestamp() * 1000,
                'likes': 10 + i * 5,
                'comments_count': 3 + i,
                'shares': i,
                'url': f'https://example.com/post/{i}',
                'comments': self._generate_sample_comments(3 + i, i)
            }
            for i in range(1, min(limit, 10) + 1)
        ]

        return sample_posts

    def _generate_sample_comments(self, count: int, post_id: int) -> List[Dict[str, Any]]:
        """Генерация примеров комментариев"""

        sample_texts = [
            "Отличный пост! Полностью согласен 👍",
            "Интересная мысль! У меня был похожий опыт когда...",
            "Спасибо за инсайты! Попробую применить на практике",
            "Не согласен с этим подходом. По моему опыту...",
            "Круто! А можете рассказать подробнее про...?",
        ]

        comments = []
        for i in range(count):
            age_hours = i * 2.5
            comments.append({
                'id': f'comment_{post_id}_{i}',
                'text': sample_texts[i % len(sample_texts)],
                'author': f'Commenter {i}',
                'author_id': f'commenter_{i}',
                'author_followers': 500 + i * 100,
                'created_at': (datetime.now().timestamp() - age_hours * 3600) * 1000,
                'age_hours': age_hours,
                'likes': 5 + i * 3,
                'replies': i % 3,
                'shares': 0,
                'reactions': {'like': 5 + i * 2, 'love': i % 2}
            })

        return comments

    def fetch_comments(self, post_id: str) -> List[Dict[str, Any]]:
        """Получить комментарии к посту"""
        return self._generate_sample_comments(5, 0)


def get_parser(platform: str) -> SocialMediaParser:
    """
    Фабрика для создания парсера нужной платформы

    Args:
        platform: 'linkedin', 'twitter', 'facebook', 'generic'
    """
    if platform.lower() == 'linkedin':
        return LinkedInParser()
    else:
        return GenericParser(platform)


def main():
    """Пример использования"""

    print("=" * 60)
    print("ПАРСЕР ПОСТОВ И КОММЕНТАРИЕВ")
    print("=" * 60)

    # Выбор платформы
    platform = os.getenv('PLATFORM', 'generic')
    print(f"\n📱 Платформа: {platform}")

    # Создание парсера
    parser = get_parser(platform)

    # Получение постов
    max_posts = int(os.getenv('MAX_POSTS', '50'))
    print(f"\n⏳ Получение последних {max_posts} постов...")

    posts = parser.fetch_posts(limit=max_posts)

    if posts:
        # Статистика
        total_comments = sum(len(post.get('comments', [])) for post in posts)
        print(f"\n✓ Получено постов: {len(posts)}")
        print(f"✓ Всего комментариев: {total_comments}")

        # Сохранение
        parser.save_posts(posts)

        # Вывод примера
        print("\n📝 Пример первого поста:")
        first_post = posts[0]
        print(f"  Автор: {first_post['author']}")
        print(f"  Текст: {first_post['text'][:100]}...")
        print(f"  Лайки: {first_post['likes']} | Комментарии: {first_post['comments_count']}")

        if first_post.get('comments'):
            print(f"\n💬 Пример комментария:")
            first_comment = first_post['comments'][0]
            print(f"  {first_comment['text'][:80]}...")
            print(f"  Лайки: {first_comment['likes']}")
    else:
        print("\n⚠ Не удалось получить посты")


if __name__ == '__main__':
    main()
