"""
Reddit Engagement Calculator

Специализированный калькулятор для Reddit метрик
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass


@dataclass
class RedditEngagementScore:
    """Метрики engagement для Reddit комментария"""
    comment_id: str

    # Базовые метрики
    score: int
    total_awards: int
    replies: int
    controversiality: int

    # Вычисленные метрики
    total_engagement: float
    normalized_score: float  # 0-100
    quality_score: float  # Учитывает awards и replies

    # Категория
    engagement_tier: str  # 'low', 'medium', 'high', 'viral'


class RedditEngagementCalculator:
    """
    Калькулятор engagement для Reddit

    Учитывает специфику Reddit:
    - Score (upvotes - downvotes)
    - Awards (более ценны, чем простые upvotes)
    - Replies (показатель дискуссии)
    - Controversiality (спорные комментарии)
    """

    # Веса для разных метрик
    WEIGHTS = {
        'score': 1.0,
        'award': 10.0,  # Награда = 10 upvotes
        'reply': 5.0,   # Ответ = 5 upvotes
        'controversy_bonus': 2.0  # Бонус за спорность
    }

    # Пороги для категорий
    TIERS = {
        'viral': 500,
        'high': 100,
        'medium': 20,
        'low': 0
    }

    def calculate(
        self,
        comment_id: str,
        score: int = 0,
        total_awards: int = 0,
        replies: int = 0,
        controversiality: int = 0
    ) -> RedditEngagementScore:
        """
        Расчет engagement для Reddit комментария

        Args:
            comment_id: ID комментария
            score: Reddit score (ups - downs)
            total_awards: Количество наград
            replies: Количество ответов
            controversiality: Спорность (0 или 1)

        Returns:
            RedditEngagementScore
        """

        # Базовый score
        base_score = max(0, score)  # Не считаем негативные

        # Бонусы от наград (высокая ценность)
        award_score = total_awards * self.WEIGHTS['award']

        # Бонусы от ответов (показатель дискуссии)
        reply_score = replies * self.WEIGHTS['reply']

        # Бонус за спорность (обычно означает активную дискуссию)
        controversy_bonus = 0
        if controversiality > 0:
            controversy_bonus = base_score * self.WEIGHTS['controversy_bonus'] * 0.1

        # Общий engagement
        total_engagement = base_score + award_score + reply_score + controversy_bonus

        # Quality score (учитывает, что награды и replies ценнее простых upvotes)
        quality_score = (award_score * 2 + reply_score * 1.5 + base_score) / (total_engagement + 1)

        # Нормализация (0-100)
        normalized_score = min(100, (total_engagement / 10))

        # Определение категории
        engagement_tier = self._determine_tier(total_engagement)

        return RedditEngagementScore(
            comment_id=comment_id,
            score=score,
            total_awards=total_awards,
            replies=replies,
            controversiality=controversiality,
            total_engagement=total_engagement,
            normalized_score=normalized_score,
            quality_score=quality_score,
            engagement_tier=engagement_tier
        )

    def _determine_tier(self, engagement: float) -> str:
        """Определить категорию engagement"""
        for tier, threshold in self.TIERS.items():
            if engagement >= threshold:
                return tier
        return 'low'

    def rank_comments(
        self,
        comments: List[Dict[str, Any]],
        top_n: int = 3,
        min_score: int = 1
    ) -> List[Tuple[Dict[str, Any], RedditEngagementScore]]:
        """
        Ранжирование комментариев по engagement

        Args:
            comments: Список комментариев
            top_n: Количество топ-комментариев
            min_score: Минимальный score для рассмотрения

        Returns:
            Список [(comment, engagement_score)]
        """
        scored_comments = []

        for comment in comments:
            # Фильтруем низко-оцененные
            if comment.get('score', 0) < min_score:
                continue

            engagement = self.calculate(
                comment_id=comment.get('id', ''),
                score=comment.get('score', 0),
                total_awards=comment.get('total_awards', 0),
                replies=comment.get('replies', 0),
                controversiality=comment.get('controversiality', 0)
            )

            scored_comments.append((comment, engagement))

        # Сортировка по total_engagement
        scored_comments.sort(
            key=lambda x: x[1].total_engagement,
            reverse=True
        )

        return scored_comments[:top_n]

    def get_top_comments_from_posts(
        self,
        posts: List[Dict[str, Any]],
        top_n_per_post: int = 3,
        min_score: int = 1
    ) -> Dict[str, List[Tuple[Dict[str, Any], RedditEngagementScore]]]:
        """
        Получить топ-комментарии для каждого поста

        Args:
            posts: Список постов с комментариями
            top_n_per_post: Количество топ-комментариев на пост
            min_score: Минимальный score

        Returns:
            Словарь {post_id: [(comment, engagement_score), ...]}
        """
        results = {}

        for post in posts:
            post_id = post.get('id', '')
            comments = post.get('comments', [])

            if comments:
                top_comments = self.rank_comments(
                    comments,
                    top_n=top_n_per_post,
                    min_score=min_score
                )
                results[post_id] = top_comments

        return results

    def analyze_subreddit_engagement(
        self,
        posts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Анализ engagement по всему сабреддиту

        Returns:
            Статистика engagement
        """
        all_comments = []
        for post in posts:
            all_comments.extend(post.get('comments', []))

        if not all_comments:
            return {}

        # Расчет для всех комментариев
        engagements = [
            self.calculate(
                comment_id=c.get('id', ''),
                score=c.get('score', 0),
                total_awards=c.get('total_awards', 0),
                replies=c.get('replies', 0),
                controversiality=c.get('controversiality', 0)
            )
            for c in all_comments
        ]

        # Статистика
        total_scores = [e.total_engagement for e in engagements]
        avg_engagement = sum(total_scores) / len(total_scores) if total_scores else 0

        # Распределение по категориям
        tier_distribution = {}
        for e in engagements:
            tier = e.engagement_tier
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1

        # Топ комментарии
        top_engagements = sorted(engagements, key=lambda x: x.total_engagement, reverse=True)[:10]

        return {
            'total_comments': len(all_comments),
            'avg_engagement': avg_engagement,
            'tier_distribution': tier_distribution,
            'top_10_engagement_scores': [e.total_engagement for e in top_engagements],
            'avg_score': sum(e.score for e in engagements) / len(engagements),
            'avg_awards': sum(e.total_awards for e in engagements) / len(engagements),
            'avg_replies': sum(e.replies for e in engagements) / len(engagements),
        }


def main():
    """Пример использования"""

    calc = RedditEngagementCalculator()

    # Примеры комментариев
    sample_comments = [
        {
            'id': '1',
            'text': 'This is the way 🚀🚀🚀',
            'score': 1250,
            'total_awards': 5,
            'replies': 87,
            'controversiality': 0
        },
        {
            'id': '2',
            'text': 'Actually, the fundamentals suggest...',
            'score': 45,
            'total_awards': 1,
            'replies': 23,
            'controversiality': 1  # Спорный
        },
        {
            'id': '3',
            'text': 'YOLO all in',
            'score': 320,
            'total_awards': 0,
            'replies': 12,
            'controversiality': 0
        }
    ]

    print("=" * 70)
    print("REDDIT ENGAGEMENT CALCULATOR")
    print("=" * 70)

    ranked = calc.rank_comments(sample_comments, top_n=3)

    print("\n🏆 ТОП-3 КОММЕНТАРИЯ:\n")
    for i, (comment, engagement) in enumerate(ranked, 1):
        print(f"{i}. {comment['text'][:50]}...")
        print(f"   Total Engagement: {engagement.total_engagement:.2f}")
        print(f"   Tier: {engagement.engagement_tier}")
        print(f"   Quality Score: {engagement.quality_score:.2f}")
        print(f"   Score: {engagement.score} | Awards: {engagement.total_awards} | Replies: {engagement.replies}")
        print()


if __name__ == '__main__':
    main()
