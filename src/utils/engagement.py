"""
Расчет engagement для комментариев
Помогает выбрать топ-3 комментария с наибольшей вовлеченностью
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class EngagementScore:
    """Метрики engagement для комментария"""
    comment_id: str
    likes: int
    replies: int
    shares: int
    reactions: Dict[str, int]  # {'like': 10, 'love': 5, 'insightful': 3}

    total_score: float
    engagement_rate: float

    # Дополнительные метрики
    author_followers: int
    comment_age_hours: float

    # Нормализованные метрики
    normalized_score: float


class EngagementCalculator:
    """Калькулятор engagement для комментариев"""

    # Веса для разных типов взаимодействия
    WEIGHTS = {
        'like': 1.0,
        'love': 1.5,
        'insightful': 2.0,
        'support': 1.5,
        'celebrate': 1.3,
        'curious': 1.2,
        'reply': 3.0,  # Ответы важнее лайков
        'share': 5.0,  # Репосты самые ценные
    }

    # Множители по времени (decay)
    TIME_DECAY = {
        1: 1.0,   # < 1 часа
        6: 0.9,   # < 6 часов
        24: 0.7,  # < 1 дня
        72: 0.5,  # < 3 дней
        168: 0.3, # < 1 недели
    }

    def calculate_score(
        self,
        comment_id: str,
        likes: int = 0,
        replies: int = 0,
        shares: int = 0,
        reactions: Dict[str, int] = None,
        author_followers: int = 0,
        comment_age_hours: float = 0,
    ) -> EngagementScore:
        """
        Расчет engagement score для комментария

        Args:
            comment_id: ID комментария
            likes: Количество лайков
            replies: Количество ответов
            shares: Количество репостов/шеров
            reactions: Словарь реакций {'like': 10, 'love': 5}
            author_followers: Количество подписчиков автора
            comment_age_hours: Возраст комментария в часах

        Returns:
            EngagementScore с рассчитанными метриками
        """
        if reactions is None:
            reactions = {'like': likes}

        # Базовый расчет score с весами
        base_score = 0.0

        # Реакции
        for reaction_type, count in reactions.items():
            weight = self.WEIGHTS.get(reaction_type.lower(), 1.0)
            base_score += count * weight

        # Ответы и репосты
        base_score += replies * self.WEIGHTS['reply']
        base_score += shares * self.WEIGHTS['share']

        # Применяем time decay
        time_multiplier = self._get_time_multiplier(comment_age_hours)
        total_score = base_score * time_multiplier

        # Engagement rate (нормализация по подписчикам автора)
        if author_followers > 0:
            engagement_rate = (total_score / author_followers) * 100
        else:
            engagement_rate = total_score

        # Нормализованный score (0-100)
        normalized_score = min(100, total_score / 10)  # Делим на 10 для нормализации

        return EngagementScore(
            comment_id=comment_id,
            likes=likes,
            replies=replies,
            shares=shares,
            reactions=reactions,
            total_score=total_score,
            engagement_rate=engagement_rate,
            author_followers=author_followers,
            comment_age_hours=comment_age_hours,
            normalized_score=normalized_score
        )

    def _get_time_multiplier(self, hours: float) -> float:
        """Получить множитель времени для decay"""
        for threshold, multiplier in sorted(self.TIME_DECAY.items()):
            if hours < threshold:
                return multiplier
        return 0.1  # Очень старые комментарии

    def rank_comments(
        self,
        comments: List[Dict[str, Any]],
        top_n: int = 3,
        sort_by: str = 'total_score'
    ) -> List[tuple]:
        """
        Ранжирование комментариев по engagement

        Args:
            comments: Список комментариев с метриками
            top_n: Количество топ-комментариев
            sort_by: Метрика для сортировки ('total_score', 'engagement_rate', 'normalized_score')

        Returns:
            Список топ-комментариев [(comment_data, engagement_score)]
        """
        scored_comments = []

        for comment in comments:
            score = self.calculate_score(
                comment_id=comment.get('id', ''),
                likes=comment.get('likes', 0),
                replies=comment.get('replies', 0),
                shares=comment.get('shares', 0),
                reactions=comment.get('reactions', {}),
                author_followers=comment.get('author_followers', 0),
                comment_age_hours=comment.get('age_hours', 0)
            )
            scored_comments.append((comment, score))

        # Сортировка по выбранной метрике
        scored_comments.sort(
            key=lambda x: getattr(x[1], sort_by),
            reverse=True
        )

        return scored_comments[:top_n]

    def get_top_comments_from_posts(
        self,
        posts: List[Dict[str, Any]],
        top_n_per_post: int = 3
    ) -> Dict[str, List[tuple]]:
        """
        Получить топ-комментарии для каждого поста

        Args:
            posts: Список постов с комментариями
            top_n_per_post: Количество топ-комментариев на пост

        Returns:
            Словарь {post_id: [(comment, score), ...]}
        """
        result = {}

        for post in posts:
            post_id = post.get('id', '')
            comments = post.get('comments', [])

            if comments:
                top_comments = self.rank_comments(comments, top_n_per_post)
                result[post_id] = top_comments

        return result


def main():
    """Пример использования"""

    # Пример комментариев
    sample_comments = [
        {
            'id': '1',
            'text': 'Отличный пост!',
            'likes': 10,
            'replies': 2,
            'shares': 0,
            'reactions': {'like': 8, 'love': 2},
            'author_followers': 1000,
            'age_hours': 2
        },
        {
            'id': '2',
            'text': 'Согласен! У меня был похожий опыт...',
            'likes': 25,
            'replies': 5,
            'shares': 1,
            'reactions': {'like': 20, 'insightful': 5},
            'author_followers': 500,
            'age_hours': 1
        },
        {
            'id': '3',
            'text': 'Спасибо за инсайты!',
            'likes': 5,
            'replies': 0,
            'shares': 0,
            'reactions': {'like': 5},
            'author_followers': 2000,
            'age_hours': 24
        }
    ]

    calculator = EngagementCalculator()

    print("=" * 60)
    print("РАСЧЕТ ENGAGEMENT")
    print("=" * 60)

    # Ранжирование
    top_comments = calculator.rank_comments(sample_comments, top_n=3)

    print("\n🏆 ТОП-3 КОММЕНТАРИЯ ПО ENGAGEMENT:\n")
    for i, (comment, score) in enumerate(top_comments, 1):
        print(f"{i}. {comment['text'][:50]}...")
        print(f"   Total Score: {score.total_score:.2f}")
        print(f"   Engagement Rate: {score.engagement_rate:.4f}%")
        print(f"   Likes: {score.likes} | Replies: {score.replies} | Shares: {score.shares}")
        print()


if __name__ == '__main__':
    main()
