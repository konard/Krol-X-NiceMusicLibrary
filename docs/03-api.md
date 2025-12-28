# API спецификация

**Проект:** NiceMusicLibrary
**Версия документа:** 1.0
**Дата:** 2025-01

---

## Общие настройки API

| Параметр | Значение |
|----------|----------|
| Base URL | `/api/v1` |
| Формат | JSON |
| Аутентификация | Bearer JWT Token |
| Content-Type | `application/json` |

### Заголовки

**Обязательные:**

| Заголовок | Формат | Описание |
|-----------|--------|----------|
| Authorization | `Bearer {access_token}` | JWT токен (кроме публичных эндпоинтов) |

**Опциональные:**

| Заголовок | Формат | По умолчанию | Описание |
|-----------|--------|--------------|----------|
| Accept-Language | `ru`, `en` | `ru` | Язык ответов и сообщений об ошибках |

### Пагинация

| Параметр | Тип | По умолчанию | Макс. | Описание |
|----------|-----|--------------|-------|----------|
| page | integer | 1 | - | Номер страницы |
| limit | integer | 20 | 100 | Количество элементов на странице |

### Формат ошибок

```yaml
error:
  code:
    type: string
    description: Код ошибки
  message:
    type: string
    description: Человекочитаемое описание
  details:
    type: object
    description: Дополнительные данные об ошибке
```

---

## Аутентификация

**Префикс:** `/auth`

### POST /auth/register

Регистрация нового пользователя.

**Требуется авторизация:** Нет

#### Запрос

```yaml
body:
  email:
    type: string
    format: email
    required: true
    example: "user@example.com"
  username:
    type: string
    min_length: 3
    max_length: 50
    required: true
    example: "musiclover"
  password:
    type: string
    min_length: 8
    required: true
    example: "SecureP@ss123"
```

#### Ответы

**201 - Успешная регистрация:**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "musiclover",
    "created_at": "2025-01-15T10:30:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 900
  }
}
```

**400 - Ошибка валидации:**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Ошибка валидации данных",
    "details": {
      "email": "Пользователь с таким email уже существует"
    }
  }
}
```

### POST /auth/login

Вход в систему.

**Требуется авторизация:** Нет

#### Запрос

```yaml
body:
  email:
    type: string
    required: true
    example: "user@example.com"
  password:
    type: string
    required: true
    example: "SecureP@ss123"
```

#### Ответы

**200 - Успешный вход:**

```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "username": "musiclover",
    "avatar_url": null,
    "last_login_at": "2025-01-15T10:30:00Z"
  },
  "tokens": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in": 900
  }
}
```

**401 - Неверные учётные данные:**

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Неверный email или пароль"
  }
}
```

### POST /auth/refresh

Обновление access токена.

**Требуется авторизация:** Нет

#### Запрос

```yaml
body:
  refresh_token:
    type: string
    required: true
```

#### Ответ

**200 - Токен обновлён:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_in": 900
}
```

### POST /auth/logout

Выход из системы.

**Требуется авторизация:** Да

#### Ответ

**200 - Успешный выход:**

```json
{
  "message": "Вы успешно вышли из системы"
}
```

### GET /auth/me

Получение данных текущего пользователя.

**Требуется авторизация:** Да

#### Ответ

**200 - Данные пользователя:**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "musiclover",
  "avatar_url": "https://storage.example.com/avatars/user123.jpg",
  "preferences": {
    "theme": "dark",
    "language": "ru",
    "default_volume": 0.8
  },
  "stats": {
    "total_songs": 1234,
    "total_playlists": 15,
    "total_listening_hours": 456
  },
  "created_at": "2025-01-01T00:00:00Z"
}
```

### PATCH /auth/me

Обновление профиля пользователя.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  username:
    type: string
    required: false
  avatar_url:
    type: string
    required: false
  preferences:
    type: object
    required: false
```

#### Ответ

**200 - Профиль обновлён**

---

## Песни (Songs)

**Префикс:** `/songs`

### GET /songs

Получение списка песен пользователя.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  page:
    type: integer
    default: 1
  limit:
    type: integer
    default: 20
    max: 100
  sort:
    type: string
    enum: [title, artist, album, added_at, play_count, last_played]
    default: added_at
  order:
    type: string
    enum: [asc, desc]
    default: desc
  search:
    type: string
    description: Поиск по названию, исполнителю, альбому
  artist:
    type: string
    description: Фильтр по исполнителю
  album:
    type: string
    description: Фильтр по альбому
  genre:
    type: string
    description: Фильтр по жанру
  is_favorite:
    type: boolean
    description: Только избранные
  year_from:
    type: integer
    description: Год выпуска (от)
  year_to:
    type: integer
    description: Год выпуска (до)
```

#### Ответ

**200 - Список песен:**

```json
{
  "items": [
    {
      "id": "song-uuid-1",
      "title": "Bohemian Rhapsody",
      "artist": "Queen",
      "album": "A Night at the Opera",
      "duration_seconds": 354,
      "cover_art_url": "https://storage.example.com/covers/song1.jpg",
      "play_count": 42,
      "last_played_at": "2025-01-14T20:30:00Z",
      "is_favorite": true,
      "rating": 5
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 1234,
    "total_pages": 62
  }
}
```

### GET /songs/{song_id}

Получение детальной информации о песне.

**Требуется авторизация:** Да

#### Ответ

**200 - Информация о песне:**

```json
{
  "id": "song-uuid-1",
  "title": "Bohemian Rhapsody",
  "artist": "Queen",
  "album": "A Night at the Opera",
  "album_artist": "Queen",
  "genre": "Rock",
  "year": 1975,
  "track_number": 11,
  "disc_number": 1,
  "duration_seconds": 354,
  "file_format": "flac",
  "bitrate": 1411,
  "sample_rate": 44100,
  "cover_art_url": "https://storage.example.com/covers/song1.jpg",
  "lyrics": "Is this the real life?...",
  "bpm": 72,
  "energy": 0.75,
  "valence": 0.45,
  "play_count": 42,
  "last_played_at": "2025-01-14T20:30:00Z",
  "is_favorite": true,
  "rating": 5,
  "tags": [
    {
      "id": "tag-1",
      "name": "classics",
      "color": "#FFD700"
    }
  ],
  "created_at": "2025-01-01T10:00:00Z"
}
```

**404 - Песня не найдена:**

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Песня не найдена"
  }
}
```

### POST /songs

Загрузка нового трека.

**Требуется авторизация:** Да
**Content-Type:** `multipart/form-data`

#### Запрос

```yaml
body:
  file:
    type: file
    required: true
    allowed_types: [audio/mpeg, audio/flac, audio/ogg, audio/wav, audio/aac]
    max_size_mb: 100
  title:
    type: string
    required: false
    description: Если не указано, берётся из метаданных файла
  artist:
    type: string
    required: false
  album:
    type: string
    required: false
```

#### Ответы

**201 - Песня загружена:**

```json
{
  "id": "new-song-uuid",
  "title": "Extracted Title",
  "artist": "Extracted Artist",
  "status": "processing",
  "message": "Файл загружен, метаданные обрабатываются"
}
```

**400 - Ошибка загрузки:**

```json
{
  "error": {
    "code": "INVALID_FILE",
    "message": "Неподдерживаемый формат файла"
  }
}
```

### PATCH /songs/{song_id}

Обновление метаданных песни.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  title:
    type: string
  artist:
    type: string
  album:
    type: string
  genre:
    type: string
  year:
    type: integer
  lyrics:
    type: string
  is_favorite:
    type: boolean
  rating:
    type: integer
    min: 1
    max: 5
```

#### Ответ

**200 - Песня обновлена**

### DELETE /songs/{song_id}

Удаление песни.

**Требуется авторизация:** Да

#### Ответ

**204 - Песня удалена**

### GET /songs/{song_id}/stream

Стриминг аудиофайла.

**Требуется авторизация:** Да
**Content-Type:** `audio/*`

#### Заголовки запроса

```yaml
headers:
  Range:
    type: string
    description: Диапазон байтов (для seek)
    example: "bytes=0-1048575"
```

#### Ответы

**200 - Полный файл:**

| Заголовок | Значение |
|-----------|----------|
| Content-Type | `audio/mpeg` |
| Content-Length | `5242880` |
| Accept-Ranges | `bytes` |

**206 - Частичный контент (byte-range):**

| Заголовок | Значение |
|-----------|----------|
| Content-Type | `audio/mpeg` |
| Content-Range | `bytes 0-1048575/5242880` |
| Content-Length | `1048576` |

### POST /songs/batch

Массовая загрузка треков.

**Требуется авторизация:** Да
**Content-Type:** `multipart/form-data`

#### Запрос

```yaml
body:
  files:
    type: array
    items:
      type: file
    max_count: 50
```

#### Ответ

**202 - Загрузка принята:**

```json
{
  "batch_id": "batch-uuid",
  "total_files": 25,
  "status": "processing",
  "status_url": "/songs/batch/batch-uuid/status"
}
```

---

## Плейлисты

**Префикс:** `/playlists`

### GET /playlists

Список плейлистов пользователя.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  page:
    type: integer
  limit:
    type: integer
  sort:
    type: string
    enum: [name, created_at, updated_at, song_count]
```

#### Ответ

**200 - Список плейлистов:**

```json
{
  "items": [
    {
      "id": "playlist-uuid-1",
      "name": "Для тренировки",
      "description": "Энергичные треки",
      "cover_image_url": "https://storage.example.com/playlists/1.jpg",
      "song_count": 45,
      "total_duration_seconds": 9720,
      "is_public": false,
      "created_at": "2025-01-10T12:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total_items": 15
  }
}
```

### POST /playlists

Создание нового плейлиста.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  name:
    type: string
    required: true
    max_length: 255
  description:
    type: string
  is_public:
    type: boolean
    default: false
  song_ids:
    type: array
    items:
      type: UUID
    description: Начальный набор песен
```

#### Ответ

**201 - Плейлист создан:**

```json
{
  "id": "new-playlist-uuid",
  "name": "Новый плейлист",
  "song_count": 0
}
```

### GET /playlists/{playlist_id}

Получение плейлиста с треками.

**Требуется авторизация:** Да

#### Ответ

**200 - Плейлист:**

```json
{
  "id": "playlist-uuid",
  "name": "Для тренировки",
  "description": "Энергичные треки",
  "cover_image_url": "...",
  "song_count": 45,
  "total_duration_seconds": 9720,
  "songs": [
    {
      "position": 1,
      "song": {
        "id": "song-uuid-1",
        "title": "Eye of the Tiger",
        "artist": "Survivor",
        "duration_seconds": 245
      }
    },
    {
      "position": 2,
      "song": {
        "id": "song-uuid-2",
        "title": "..."
      }
    }
  ]
}
```

### PATCH /playlists/{playlist_id}

Обновление плейлиста.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  name:
    type: string
  description:
    type: string
  is_public:
    type: boolean
```

#### Ответ

**200 - Плейлист обновлён**

### DELETE /playlists/{playlist_id}

Удаление плейлиста.

**Требуется авторизация:** Да

#### Ответ

**204 - Плейлист удалён**

### POST /playlists/{playlist_id}/songs

Добавление песен в плейлист.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  song_ids:
    type: array
    items:
      type: UUID
    required: true
  position:
    type: integer
    description: Позиция вставки (в конец, если не указано)
```

#### Ответ

**200 - Песни добавлены:**

```json
{
  "added_count": 5,
  "song_count": 50
}
```

### DELETE /playlists/{playlist_id}/songs/{song_id}

Удаление песни из плейлиста.

**Требуется авторизация:** Да

#### Ответ

**204 - Песня удалена из плейлиста**

### PUT /playlists/{playlist_id}/songs/order

Изменение порядка песен в плейлисте.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  song_ids:
    type: array
    items:
      type: UUID
    description: Новый порядок всех песен
```

#### Ответ

**200 - Порядок обновлён**

---

## Цепочки настроений

**Префикс:** `/mood-chains`

### GET /mood-chains

Список цепочек настроений.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  mood_tag:
    type: string
    description: Фильтр по тегу настроения
  is_auto_generated:
    type: boolean
    description: Только автоматически созданные
```

#### Ответ

**200 - Список цепочек:**

```json
{
  "items": [
    {
      "id": "chain-uuid-1",
      "name": "Вечерний чилл",
      "description": "Расслабляющая музыка для вечера",
      "mood_tags": ["chill", "relaxing", "evening"],
      "cover_image_url": "...",
      "song_count": 20,
      "play_count": 15,
      "transition_style": "smooth",
      "is_auto_generated": false
    }
  ]
}
```

### POST /mood-chains

Создание цепочки настроений.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  name:
    type: string
    required: true
  description:
    type: string
  mood_tags:
    type: array
    items:
      type: string
  transition_style:
    type: string
    enum: [smooth, random, energy_flow, genre_match]
    default: smooth
  song_ids:
    type: array
    items:
      type: UUID
```

#### Ответ

**201 - Цепочка создана**

### POST /mood-chains/from-history

Создание цепочки из истории прослушиваний.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  name:
    type: string
    required: true
  start_date:
    type: datetime
    required: true
    description: Начало периода истории
  end_date:
    type: datetime
    required: true
    description: Конец периода истории
  min_play_count:
    type: integer
    default: 1
    description: Минимальное количество прослушиваний для включения
  mood_tags:
    type: array
    items:
      type: string
```

#### Ответ

**201 - Цепочка создана из истории:**

```json
{
  "id": "chain-uuid",
  "name": "Январь 2025",
  "song_count": 35,
  "source_history_start": "2025-01-01T00:00:00Z",
  "source_history_end": "2025-01-31T23:59:59Z",
  "is_auto_generated": true
}
```

### GET /mood-chains/{chain_id}

Получение цепочки с треками.

**Требуется авторизация:** Да

#### Ответ

**200 - Цепочка настроений:**

```json
{
  "id": "chain-uuid",
  "name": "Вечерний чилл",
  "songs": [
    {
      "position": 1,
      "song": {
        "id": "song-uuid",
        "title": "..."
      },
      "transition_weight": 0.85
    },
    {
      "position": 2,
      "song": {
        "id": "..."
      },
      "transition_weight": 0.92
    }
  ]
}
```

### GET /mood-chains/{chain_id}/next

Получение следующего рекомендуемого трека.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  current_song_id:
    type: UUID
    required: true
    description: Текущий трек
  count:
    type: integer
    default: 3
    description: Количество рекомендаций
```

#### Ответ

**200 - Рекомендуемые следующие треки:**

```json
{
  "recommendations": [
    {
      "song": {
        "id": "song-uuid-1",
        "title": "Recommended Song 1",
        "artist": "Artist"
      },
      "score": 0.95,
      "reason": "Похожий темп и настроение"
    },
    {
      "song": {
        "id": "song-uuid-2",
        "title": "Recommended Song 2"
      },
      "score": 0.87,
      "reason": "Часто слушается после текущего трека"
    }
  ]
}
```

### PATCH /mood-chains/{chain_id}

Обновление цепочки.

**Требуется авторизация:** Да

#### Ответ

**200 - Цепочка обновлена**

### DELETE /mood-chains/{chain_id}

Удаление цепочки.

**Требуется авторизация:** Да

#### Ответ

**204 - Цепочка удалена**

---

## Статистика и история

**Префикс:** `/stats`

### POST /stats/play

Запись прослушивания трека.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  song_id:
    type: UUID
    required: true
  duration_seconds:
    type: integer
    description: Сколько секунд прослушано
  completed:
    type: boolean
    description: Дослушано ли до конца
  context_type:
    type: string
    enum: [library, playlist, mood_chain, search, recommendation]
  context_id:
    type: UUID
    description: ID плейлиста/цепочки
  previous_song_id:
    type: UUID
    description: Предыдущий трек
```

#### Ответ

**201 - Прослушивание записано:**

```json
{
  "id": "history-uuid",
  "song": {
    "play_count": 43,
    "last_played_at": "2025-01-15T12:30:00Z"
  }
}
```

### GET /stats/history

История прослушиваний.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  page:
    type: integer
  limit:
    type: integer
  start_date:
    type: datetime
  end_date:
    type: datetime
  song_id:
    type: UUID
    description: Фильтр по конкретной песне
```

#### Ответ

**200 - История прослушиваний:**

```json
{
  "items": [
    {
      "id": "history-uuid",
      "song": {
        "id": "song-uuid",
        "title": "Song Title",
        "artist": "Artist"
      },
      "played_at": "2025-01-15T12:30:00Z",
      "played_duration_seconds": 234,
      "completed": true,
      "context_type": "playlist"
    }
  ],
  "pagination": {
    "total_items": 5000
  }
}
```

### GET /stats/overview

Общая статистика пользователя.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  period:
    type: string
    enum: [week, month, year, all_time]
    default: month
```

#### Ответ

**200 - Обзор статистики:**

```json
{
  "period": "month",
  "total_listening_time_seconds": 86400,
  "total_songs_played": 450,
  "unique_songs": 120,
  "unique_artists": 45,
  "top_songs": [
    {
      "song": {
        "id": "...",
        "title": "..."
      },
      "play_count": 25
    }
  ],
  "top_artists": [
    {
      "artist": "Queen",
      "play_count": 85
    }
  ],
  "top_genres": [
    {
      "genre": "Rock",
      "play_count": 200
    }
  ],
  "listening_by_hour": [
    { "hour": 0, "count": 5 },
    { "hour": 1, "count": 2 }
  ],
  "listening_by_day": [
    { "date": "2025-01-01", "minutes": 120 }
  ]
}
```

### GET /stats/top-songs

Топ песен по прослушиваниям.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  period:
    type: string
    enum: [week, month, year, all_time]
  limit:
    type: integer
    default: 20
```

#### Ответ

**200 - Топ песен:**

```json
{
  "period": "month",
  "items": [
    {
      "rank": 1,
      "song": {
        "id": "...",
        "title": "Bohemian Rhapsody",
        "artist": "Queen"
      },
      "play_count": 42,
      "total_listen_time_seconds": 14868
    }
  ]
}
```

---

## Поиск и рекомендации

### GET /search

Глобальный поиск.

**Префикс:** `/search`
**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  q:
    type: string
    required: true
    description: Поисковый запрос
  type:
    type: string
    enum: [all, songs, artists, albums, playlists]
    default: all
  limit:
    type: integer
    default: 10
```

#### Ответ

**200 - Результаты поиска:**

```json
{
  "query": "queen",
  "songs": [
    {
      "id": "...",
      "title": "Bohemian Rhapsody",
      "artist": "Queen"
    }
  ],
  "artists": [
    {
      "name": "Queen",
      "song_count": 45
    }
  ],
  "albums": [
    {
      "name": "A Night at the Opera",
      "artist": "Queen",
      "song_count": 12
    }
  ],
  "playlists": [
    {
      "id": "...",
      "name": "Queen Best"
    }
  ]
}
```

### GET /recommendations/similar/{song_id}

Похожие песни.

**Префикс:** `/recommendations`
**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  limit:
    type: integer
    default: 10
```

#### Ответ

**200 - Похожие песни:**

```json
{
  "source_song": {
    "id": "...",
    "title": "..."
  },
  "similar": [
    {
      "song": {
        "id": "...",
        "title": "..."
      },
      "similarity_score": 0.92,
      "reasons": [
        "Похожий жанр",
        "Близкий темп"
      ]
    }
  ]
}
```

### GET /recommendations/discover

Рекомендации для открытия новой музыки.

**Требуется авторизация:** Да

#### Параметры запроса

```yaml
query:
  based_on:
    type: string
    enum: [listening_history, favorites, mood]
    default: listening_history
  mood:
    type: string
    description: Тег настроения (если based_on=mood)
```

#### Ответ

**200 - Рекомендации:**

```json
{
  "recommendations": [
    {
      "song": {
        "id": "...",
        "title": "..."
      },
      "reason": "Основано на ваших любимых треках",
      "confidence": 0.85
    }
  ]
}
```

---

## Теги

**Префикс:** `/tags`

### GET /tags

Список тегов пользователя.

**Требуется авторизация:** Да

#### Ответ

**200 - Список тегов:**

```json
{
  "items": [
    {
      "id": "tag-uuid",
      "name": "classics",
      "color": "#FFD700",
      "song_count": 45
    }
  ]
}
```

### POST /tags

Создание тега.

**Требуется авторизация:** Да

#### Запрос

```yaml
body:
  name:
    type: string
    required: true
  color:
    type: string
    format: hex_color
```

#### Ответ

**201 - Тег создан**

### POST /tags/{tag_id}/songs/{song_id}

Добавление тега к песне.

**Требуется авторизация:** Да

#### Ответ

**200 - Тег добавлен**

### DELETE /tags/{tag_id}/songs/{song_id}

Удаление тега с песни.

**Требуется авторизация:** Да

#### Ответ

**204 - Тег удалён**

---

## Коды ответов

### Успешные ответы

| Код | Описание |
|-----|----------|
| 200 | OK - Успешный запрос |
| 201 | Created - Ресурс создан |
| 202 | Accepted - Запрос принят в обработку |
| 204 | No Content - Успешно, без тела ответа |
| 206 | Partial Content - Частичный контент (для стриминга) |

### Ошибки клиента

| Код | Описание | Коды ошибок |
|-----|----------|-------------|
| 400 | Bad Request - Ошибка в запросе | VALIDATION_ERROR, INVALID_FILE, INVALID_FORMAT |
| 401 | Unauthorized - Требуется аутентификация | INVALID_TOKEN, TOKEN_EXPIRED, INVALID_CREDENTIALS |
| 403 | Forbidden - Доступ запрещён | ACCESS_DENIED, INSUFFICIENT_PERMISSIONS |
| 404 | Not Found - Ресурс не найден | NOT_FOUND, SONG_NOT_FOUND, PLAYLIST_NOT_FOUND |
| 409 | Conflict - Конфликт | ALREADY_EXISTS, DUPLICATE_ENTRY |
| 413 | Payload Too Large - Файл слишком большой | FILE_TOO_LARGE |
| 422 | Unprocessable Entity - Невалидные данные | INVALID_DATA |
| 429 | Too Many Requests - Превышен лимит запросов | RATE_LIMIT_EXCEEDED |

### Ошибки сервера

| Код | Описание | Коды ошибок |
|-----|----------|-------------|
| 500 | Internal Server Error - Внутренняя ошибка | INTERNAL_ERROR |
| 503 | Service Unavailable - Сервис недоступен | SERVICE_UNAVAILABLE |
