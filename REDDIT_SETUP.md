# 🚀 Reddit Comment Analyzer - Быстрая настройка

Парсинг и глубокий анализ комментариев из Reddit с психологическими паттернами.

## Целевые сабреддиты

- r/ValueInvesting
- r/DeepFuckingValue
- r/StockMarket
- r/wallstreetbets
- r/WSBAfterHours

## Быстрая настройка (5 минут)

### 1. Установка зависимостей

```bash
pip install praw anthropic
```

### 2. Получение Reddit API ключей

1. Перейдите на https://www.reddit.com/prefs/apps
2. Прокрутите вниз и нажмите **"create another app..."**
3. Заполните форму:
   - **name**: `Comment Analyzer`
   - **App type**: выберите **"script"**
   - **description**: `Analyzing Reddit comments`
   - **about url**: (можно оставить пустым)
   - **redirect uri**: `http://localhost:8080`
4. Нажмите **"create app"**
5. Скопируйте данные:
   - **client_id** - строка под названием приложения (например: `dD3jk...`)
   - **secret** - строка справа от "secret"

### 3. Получение AI API ключа (для глубокого анализа)

#### Anthropic Claude (рекомендуется):
1. Перейдите на https://console.anthropic.com/
2. Зарегистрируйтесь/войдите
3. Перейдите в "API Keys"
4. Создайте новый ключ
5. Скопируйте ключ (начинается с `sk-ant-...`)

#### ИЛИ OpenAI GPT-4:
1. Перейдите на https://platform.openai.com/
2. Перейдите в API Keys
3. Создайте новый ключ
4. Скопируйте (начинается с `sk-...`)

### 4. Настройка .env

Создайте файл `.env` в корне проекта:

```bash
# Reddit API
REDDIT_CLIENT_ID=ваш_client_id_сюда
REDDIT_CLIENT_SECRET=ваш_secret_сюда
REDDIT_USER_AGENT=Comment Analyzer Bot 1.0

# AI для глубокого анализа (выберите один)
ANTHROPIC_API_KEY=sk-ant-ваш_ключ_сюда
# или
# OPENAI_API_KEY=sk-ваш_ключ_сюда

# Настройки (опционально, можно не менять)
REDDIT_POSTS_LIMIT=10
TOP_COMMENTS_PER_POST=3
DEEP_ANALYZE_COUNT=5
MIN_COMMENT_SCORE=10
```

### 5. Запуск

```bash
# Полный пайплайн
python src/reddit_pipeline.py
```

## Что делает система

### 1. Парсинг (Step 1)
- Получает последние hot посты из каждого сабреддита
- Собирает комментарии к каждому посту
- Сохраняет в `data/posts/`

### 2. Engagement Analysis (Step 2)
- Рассчитывает engagement для каждого комментария:
  - **Score** (upvotes)
  - **Awards** (награды = 10x вес)
  - **Replies** (ответы = 5x вес)
  - **Controversiality** (спорность)
- Выбирает топ-3 комментария на пост
- Ранжирует все комментарии

### 3. Deep Analysis (Step 3) ⭐

Для топ-N комментариев с помощью AI анализирует:

#### a) Структуру
- Как начинается
- Как организовано тело
- Как заканчивается
- Форматирование (списки, цитаты, эмодзи)

#### b) Почему работает
- Что делает комментарий эффективным
- Ключевые элементы engagement
- Факторы времени и релевантности
- Уникальная ценность

#### c) Психологические паттерны
- **Эмоциональные триггеры**
- **Социальное доказательство** (social proof)
- **Авторитет/кредибильность**
- **Сторителлинг** (истории)
- **Юмор** и остроумие
- **Контр-мнения** (противоречие)

#### d) Необходимый контекст
- Знание о посте
- Культура сабреддита (WSB жаргон, мемы)
- Текущие события
- Технические знания
- Инсайдерские шутки

#### e) Руководство по воссозданию
- Пошаговая формула
- Ключевые фразы и паттерны
- Тон и голос
- Что избегать
- Когда этот паттерн работает лучше всего

## Пример вывода

```json
{
  "structure_breakdown": {
    "opening": "Starts with agreement and emoji 🚀",
    "body": "Personal loss story (50k), lesson learned",
    "closing": "Contrarian strategy (inverse WSB)",
    "formatting": "Short sentences, casual tone"
  },
  "why_it_works": [
    "Self-deprecating humor builds trust",
    "Specific numbers (50k) add credibility",
    "Contrarian take creates discussion",
    "WSB-native language (YOLO, calls)"
  ],
  "psychological_patterns": [
    {
      "pattern": "Vulnerability",
      "description": "Sharing loss creates connection"
    },
    {
      "pattern": "Social proof",
      "description": "Learning from mistakes validates others"
    },
    {
      "pattern": "Humor",
      "description": "Self-deprecation reduces defensiveness"
    }
  ],
  "required_context": [
    "WSB meme culture (🚀, YOLO)",
    "Elon/Tesla dynamics",
    "Shorting = betting against stock",
    "2020 Tesla rally context"
  ],
  "recreation_guide": {
    "formula": "Agreement + Personal story with numbers + Lesson + Humor",
    "tone": "Casual, self-aware, slightly cynical",
    "key_phrases": ["learned the hard way", "now I just...", "lol"],
    "when_works": "When post is bearish but community sentiment bullish"
  }
}
```

## Результаты

После запуска вы получите:

```
data/
├── posts/
│   ├── reddit_wallstreetbets_20241105_120000.json
│   ├── reddit_ValueInvesting_20241105_120000.json
│   └── ...
└── analysis/
    ├── deep_analysis_20241105_120000.json  # Детальный анализ
    └── reddit_report_20241105_120000.json  # Общий отчет
```

## Частые вопросы

**Q: Нужны ли оба API (Reddit + AI)?**

A:
- Reddit API - **обязателен** для парсинга
- AI API - **опционален**, но без него не будет глубокого анализа

**Q: Какой AI лучше?**

A:
- **Anthropic Claude** - лучше понимает нюансы и психологию
- **OpenAI GPT-4** - тоже хорошо, более доступен

**Q: Сколько стоит?**

A:
- Reddit API - **бесплатно** (read-only)
- Claude/GPT-4 - ~$0.01-0.03 за анализ комментария

**Q: Безопасно ли парсить Reddit?**

A: Да, используем официальное API в read-only режиме. Reddit разрешает это.

**Q: Можно ли добавить свои сабреддиты?**

A: Да! Измените в .env:
```
REDDIT_SUBREDDITS=YourSub1,YourSub2,YourSub3
```

**Q: Как увеличить количество постов?**

A: В .env увеличьте:
```
REDDIT_POSTS_LIMIT=50
```

## Только парсинг (без AI)

Если хотите только спарсить данные без глубокого анализа:

```bash
python src/reddit_parser.py
```

Это сохранит все посты и комментарии в JSON.

## Troubleshooting

### "Reddit API не инициализирован"
- Проверьте client_id и client_secret в .env
- Убедитесь, что создали приложение типа "script"

### "AI клиент не инициализирован"
- Проверьте API ключ в .env
- Установите: `pip install anthropic` или `pip install openai`

### "Rate limit exceeded"
- Reddit ограничивает до 60 запросов в минуту
- Уменьшите REDDIT_POSTS_LIMIT
- Добавьте задержки в коде

## Следующие шаги

1. Запустите пайплайн: `python src/reddit_pipeline.py`
2. Изучите результаты в `data/analysis/`
3. Найдите паттерны успешных комментариев
4. Используйте для создания своего стиля
5. Тестируйте на реальных постах
6. Итерируйте на основе engagement

---

**Важно**: Используйте знания для понимания паттернов, не для спама! 🎯
