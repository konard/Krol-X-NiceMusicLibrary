# Сущности

**Проект:** NiceMusicLibrary
**Версия документа:** 1.0
**Дата:** 2025-01

---

## Обзор

Данный документ описывает ключевые сущности системы персональной музыкальной библиотеки, их поля, типы данных и связи между ними.

---

## Пользователь (User)

Учётная запись пользователя системы.

**Таблица:** `users`

### Структура данных

```yaml
user:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор пользователя

    - name: email
      type: VARCHAR(255)
      unique: true
      nullable: false
      description: Email пользователя (используется для входа)

    - name: username
      type: VARCHAR(50)
      unique: true
      nullable: false
      description: Отображаемое имя пользователя

    - name: password_hash
      type: VARCHAR(255)
      nullable: false
      description: Хэш пароля (bcrypt)

    - name: avatar_url
      type: VARCHAR(500)
      nullable: true
      description: URL аватара пользователя

    - name: preferences
      type: JSONB
      nullable: true
      default: "{}"
      description: Настройки пользователя (тема, язык, громкость и т.д.)

    - name: role
      type: ENUM('user', 'admin')
      default: user
      description: Роль пользователя в системе

    - name: is_active
      type: BOOLEAN
      default: true
      description: Активен ли аккаунт

    - name: last_login_at
      type: TIMESTAMP
      nullable: true
      description: Время последнего входа

    - name: created_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Дата создания аккаунта

    - name: updated_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      on_update: CURRENT_TIMESTAMP
      description: Дата последнего обновления

  indexes:
    - columns: [email]
      unique: true
    - columns: [username]
      unique: true

  relationships:
    - type: has_many
      entity: song
      foreign_key: owner_id
    - type: has_many
      entity: playlist
      foreign_key: owner_id
    - type: has_many
      entity: mood_chain
      foreign_key: owner_id
    - type: has_many
      entity: listening_history
      foreign_key: user_id
```

---

## Песня (Song)

Музыкальный трек в библиотеке пользователя.

**Таблица:** `songs`

### Структура данных

```yaml
song:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор песни

    - name: owner_id
      type: UUID
      nullable: false
      foreign_key: users.id
      description: Владелец песни

    - name: title
      type: VARCHAR(255)
      nullable: false
      description: Название песни

    - name: artist
      type: VARCHAR(255)
      nullable: true
      description: Исполнитель

    - name: album
      type: VARCHAR(255)
      nullable: true
      description: Название альбома

    - name: album_artist
      type: VARCHAR(255)
      nullable: true
      description: Исполнитель альбома (для сборников)

    - name: genre
      type: VARCHAR(100)
      nullable: true
      description: Жанр музыки

    - name: year
      type: INTEGER
      nullable: true
      description: Год выпуска

    - name: track_number
      type: INTEGER
      nullable: true
      description: Номер трека в альбоме

    - name: disc_number
      type: INTEGER
      nullable: true
      default: 1
      description: Номер диска

    - name: duration_seconds
      type: INTEGER
      nullable: false
      description: Длительность в секундах

    - name: file_path
      type: VARCHAR(500)
      nullable: false
      description: Путь к аудиофайлу

    - name: file_size_bytes
      type: BIGINT
      nullable: false
      description: Размер файла в байтах

    - name: file_format
      type: VARCHAR(20)
      nullable: false
      description: Формат файла (mp3, flac, ogg и т.д.)

    - name: bitrate
      type: INTEGER
      nullable: true
      description: Битрейт в kbps

    - name: sample_rate
      type: INTEGER
      nullable: true
      description: Частота дискретизации в Hz

    - name: cover_art_path
      type: VARCHAR(500)
      nullable: true
      description: Путь к обложке альбома

    - name: lyrics
      type: TEXT
      nullable: true
      description: Текст песни

    - name: bpm
      type: INTEGER
      nullable: true
      description: Темп (beats per minute)

    - name: energy
      type: FLOAT
      nullable: true
      description: Энергичность (0.0 - 1.0), для рекомендаций

    - name: valence
      type: FLOAT
      nullable: true
      description: Позитивность/настроение (0.0 - 1.0)

    - name: play_count
      type: INTEGER
      default: 0
      description: Общее количество прослушиваний

    - name: last_played_at
      type: TIMESTAMP
      nullable: true
      description: Время последнего прослушивания

    - name: is_favorite
      type: BOOLEAN
      default: false
      description: Отмечена ли как любимая

    - name: rating
      type: SMALLINT
      nullable: true
      description: Рейтинг от 1 до 5

    - name: created_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Дата добавления в библиотеку

    - name: updated_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      on_update: CURRENT_TIMESTAMP
      description: Дата последнего обновления метаданных

  indexes:
    - columns: [owner_id]
    - columns: [owner_id, artist]
    - columns: [owner_id, album]
    - columns: [owner_id, genre]
    - columns: [owner_id, play_count]
      order: DESC
    - columns: [owner_id, last_played_at]
      order: DESC
    - columns: [owner_id, is_favorite]
    - type: fulltext
      columns: [title, artist, album]

  relationships:
    - type: belongs_to
      entity: user
      foreign_key: owner_id
    - type: has_many
      entity: playlist_song
      foreign_key: song_id
    - type: has_many
      entity: listening_history
      foreign_key: song_id
    - type: has_many
      entity: mood_chain_song
      foreign_key: song_id
```

---

## Плейлист (Playlist)

Пользовательская коллекция песен.

**Таблица:** `playlists`

### Структура данных

```yaml
playlist:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор плейлиста

    - name: owner_id
      type: UUID
      nullable: false
      foreign_key: users.id
      description: Создатель плейлиста

    - name: name
      type: VARCHAR(255)
      nullable: false
      description: Название плейлиста

    - name: description
      type: TEXT
      nullable: true
      description: Описание плейлиста

    - name: cover_image_path
      type: VARCHAR(500)
      nullable: true
      description: Путь к обложке плейлиста

    - name: is_public
      type: BOOLEAN
      default: false
      description: Виден ли плейлист другим пользователям

    - name: song_count
      type: INTEGER
      default: 0
      description: Количество песен (денормализовано для производительности)

    - name: total_duration_seconds
      type: INTEGER
      default: 0
      description: Общая длительность (денормализовано)

    - name: created_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Дата создания

    - name: updated_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      on_update: CURRENT_TIMESTAMP
      description: Дата последнего изменения

  indexes:
    - columns: [owner_id]
    - columns: [owner_id, name]

  relationships:
    - type: belongs_to
      entity: user
      foreign_key: owner_id
    - type: has_many
      entity: playlist_song
      foreign_key: playlist_id
```

---

## Песня в плейлисте (PlaylistSong)

Связь между плейлистом и песней с порядком.

**Таблица:** `playlist_songs`

### Структура данных

```yaml
playlist_song:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор записи

    - name: playlist_id
      type: UUID
      nullable: false
      foreign_key: playlists.id
      on_delete: CASCADE
      description: ID плейлиста

    - name: song_id
      type: UUID
      nullable: false
      foreign_key: songs.id
      on_delete: CASCADE
      description: ID песни

    - name: position
      type: INTEGER
      nullable: false
      description: Порядковый номер в плейлисте

    - name: added_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Когда песня была добавлена

  indexes:
    - columns: [playlist_id, position]
    - columns: [playlist_id, song_id]
      unique: true

  relationships:
    - type: belongs_to
      entity: playlist
      foreign_key: playlist_id
    - type: belongs_to
      entity: song
      foreign_key: song_id
```

---

## Цепочка настроений (MoodChain)

Последовательность треков, связанных по настроению/вайбу.

**Таблица:** `mood_chains`

### Структура данных

```yaml
mood_chain:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор цепочки

    - name: owner_id
      type: UUID
      nullable: false
      foreign_key: users.id
      description: Создатель цепочки

    - name: name
      type: VARCHAR(255)
      nullable: false
      description: Название цепочки

    - name: description
      type: TEXT
      nullable: true
      description: Описание настроения/вайба

    - name: mood_tags
      type: VARCHAR(255)[]
      nullable: true
      description: Теги настроения (happy, chill, energetic и т.д.)

    - name: cover_image_path
      type: VARCHAR(500)
      nullable: true
      description: Обложка цепочки

    - name: is_auto_generated
      type: BOOLEAN
      default: false
      description: Создана автоматически из истории

    - name: source_history_start
      type: TIMESTAMP
      nullable: true
      description: Начало периода истории (для авто-цепочек)

    - name: source_history_end
      type: TIMESTAMP
      nullable: true
      description: Конец периода истории (для авто-цепочек)

    - name: transition_style
      type: ENUM('smooth', 'random', 'energy_flow', 'genre_match')
      default: smooth
      description: Стиль перехода между треками

    - name: song_count
      type: INTEGER
      default: 0
      description: Количество песен в цепочке

    - name: play_count
      type: INTEGER
      default: 0
      description: Сколько раз цепочка была воспроизведена

    - name: last_played_at
      type: TIMESTAMP
      nullable: true
      description: Последнее воспроизведение

    - name: created_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Дата создания

    - name: updated_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      on_update: CURRENT_TIMESTAMP
      description: Дата обновления

  indexes:
    - columns: [owner_id]
    - columns: [owner_id, mood_tags]
      type: GIN
    - columns: [owner_id, play_count]
      order: DESC

  relationships:
    - type: belongs_to
      entity: user
      foreign_key: owner_id
    - type: has_many
      entity: mood_chain_song
      foreign_key: mood_chain_id
```

---

## Песня в цепочке настроений (MoodChainSong)

Связь песни с цепочкой, включая веса переходов.

**Таблица:** `mood_chain_songs`

### Структура данных

```yaml
mood_chain_song:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор

    - name: mood_chain_id
      type: UUID
      nullable: false
      foreign_key: mood_chains.id
      on_delete: CASCADE
      description: ID цепочки настроений

    - name: song_id
      type: UUID
      nullable: false
      foreign_key: songs.id
      on_delete: CASCADE
      description: ID песни

    - name: position
      type: INTEGER
      nullable: false
      description: Позиция в цепочке

    - name: transition_weight
      type: FLOAT
      default: 1.0
      description: Вес перехода к следующему треку (0.0 - 1.0)

    - name: added_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Когда добавлено

  indexes:
    - columns: [mood_chain_id, position]
    - columns: [mood_chain_id, song_id]

  relationships:
    - type: belongs_to
      entity: mood_chain
      foreign_key: mood_chain_id
    - type: belongs_to
      entity: song
      foreign_key: song_id
```

---

## История прослушиваний (ListeningHistory)

Запись каждого воспроизведения трека.

**Таблица:** `listening_history`

### Структура данных

```yaml
listening_history:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор записи

    - name: user_id
      type: UUID
      nullable: false
      foreign_key: users.id
      on_delete: CASCADE
      description: Пользователь

    - name: song_id
      type: UUID
      nullable: false
      foreign_key: songs.id
      on_delete: CASCADE
      description: Прослушанная песня

    - name: played_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Время начала воспроизведения

    - name: played_duration_seconds
      type: INTEGER
      nullable: true
      description: Сколько секунд прослушано

    - name: completed
      type: BOOLEAN
      default: false
      description: Дослушано ли до конца (>90%)

    - name: skipped
      type: BOOLEAN
      default: false
      description: Был ли пропущен трек (<30 секунд)

    - name: context_type
      type: ENUM('library', 'playlist', 'mood_chain', 'search', 'recommendation')
      nullable: true
      description: Откуда был запущен трек

    - name: context_id
      type: UUID
      nullable: true
      description: ID плейлиста/цепочки (если применимо)

    - name: previous_song_id
      type: UUID
      nullable: true
      foreign_key: songs.id
      description: Предыдущий трек (для анализа переходов)

    - name: device_type
      type: VARCHAR(50)
      nullable: true
      description: Тип устройства (web, mobile, desktop)

  indexes:
    - columns: [user_id, played_at]
      order: DESC
    - columns: [user_id, song_id]
    - columns: [song_id, played_at]
    - columns: [user_id, context_type, context_id]
    - columns: [previous_song_id, song_id]
      comment: Для анализа переходов между треками

  relationships:
    - type: belongs_to
      entity: user
      foreign_key: user_id
    - type: belongs_to
      entity: song
      foreign_key: song_id
```

---

## Тег (Tag)

Пользовательский тег для организации музыки.

**Таблица:** `tags`

### Структура данных

```yaml
tag:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор тега

    - name: owner_id
      type: UUID
      nullable: false
      foreign_key: users.id
      description: Создатель тега

    - name: name
      type: VARCHAR(100)
      nullable: false
      description: Название тега

    - name: color
      type: VARCHAR(7)
      nullable: true
      description: Цвет тега (HEX формат, например #FF5733)

    - name: created_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Дата создания

  indexes:
    - columns: [owner_id, name]
      unique: true

  relationships:
    - type: belongs_to
      entity: user
      foreign_key: owner_id
    - type: has_many
      entity: song_tag
      foreign_key: tag_id
```

---

## Тег песни (SongTag)

Связь между песней и тегом.

**Таблица:** `song_tags`

### Структура данных

```yaml
song_tag:
  fields:
    - name: id
      type: UUID
      primary_key: true
      description: Уникальный идентификатор

    - name: song_id
      type: UUID
      nullable: false
      foreign_key: songs.id
      on_delete: CASCADE
      description: ID песни

    - name: tag_id
      type: UUID
      nullable: false
      foreign_key: tags.id
      on_delete: CASCADE
      description: ID тега

    - name: created_at
      type: TIMESTAMP
      default: CURRENT_TIMESTAMP
      description: Когда тег был добавлен

  indexes:
    - columns: [song_id, tag_id]
      unique: true
    - columns: [tag_id]

  relationships:
    - type: belongs_to
      entity: song
      foreign_key: song_id
    - type: belongs_to
      entity: tag
      foreign_key: tag_id
```

---

## ER-диаграмма

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────┐
│    User     │       │      Song       │       │   Playlist  │
├─────────────┤       ├─────────────────┤       ├─────────────┤
│ id (PK)     │───┐   │ id (PK)         │   ┌───│ id (PK)     │
│ email       │   │   │ owner_id (FK)───│───┤   │ owner_id(FK)│───┐
│ username    │   │   │ title           │   │   │ name        │   │
│ password    │   │   │ artist          │   │   │ description │   │
│ ...         │   │   │ album           │   │   │ ...         │   │
└─────────────┘   │   │ play_count      │   │   └─────────────┘   │
      │           │   │ last_played_at  │   │         │           │
      │           │   │ ...             │   │         │           │
      │           │   └─────────────────┘   │         │           │
      │           │           │             │         │           │
      │           └───────────┼─────────────┘         │           │
      │                       │                       │           │
      │              ┌────────┴────────┐              │           │
      │              ▼                 ▼              ▼           │
      │    ┌─────────────────┐ ┌─────────────────┐                │
      │    │ PlaylistSong    │ │  MoodChainSong  │                │
      │    ├─────────────────┤ ├─────────────────┤                │
      │    │ playlist_id(FK) │ │ mood_chain_id   │                │
      │    │ song_id (FK)    │ │ song_id (FK)    │                │
      │    │ position        │ │ position        │                │
      │    └─────────────────┘ │ transition_wght │                │
      │                        └─────────────────┘                │
      │                               │                           │
      │                               ▼                           │
      │                     ┌─────────────────┐                   │
      │                     │   MoodChain     │                   │
      │                     ├─────────────────┤                   │
      └─────────────────────│ owner_id (FK)   │───────────────────┘
                            │ name            │
                            │ mood_tags       │
                            │ transition_style│
                            └─────────────────┘

      │
      ▼
┌─────────────────────────────────────────────────────────────┐
│                    ListeningHistory                          │
├─────────────────────────────────────────────────────────────┤
│ user_id (FK) │ song_id (FK) │ played_at │ context │ ...    │
└─────────────────────────────────────────────────────────────┘
```

---

## Дополнительные структуры данных

### Настройки пользователя (preferences)

Структура JSON-поля `preferences` в сущности User:

```yaml
user_preferences:
  theme:
    type: string
    enum: [light, dark, auto]
    default: auto
  language:
    type: string
    default: ru
  default_volume:
    type: number
    min: 0
    max: 1
    default: 0.8
  crossfade_seconds:
    type: integer
    min: 0
    max: 12
    default: 0
  show_lyrics:
    type: boolean
    default: true
  audio_quality:
    type: string
    enum: [low, medium, high, original]
    default: high
  notifications:
    new_recommendations:
      type: boolean
      default: true
    weekly_stats:
      type: boolean
      default: true
```

### Аудио-анализ песни

Результат аудио-анализа для рекомендаций (хранится в отдельной таблице или JSON):

```yaml
song_audio_analysis:
  key:
    type: integer
    description: Музыкальная тональность (0-11)
  mode:
    type: integer
    description: Мажор(1) или минор(0)
  acousticness:
    type: float
    description: Акустичность (0.0 - 1.0)
  danceability:
    type: float
    description: Танцевальность (0.0 - 1.0)
  instrumentalness:
    type: float
    description: Инструментальность (0.0 - 1.0)
  loudness:
    type: float
    description: Громкость в dB
  speechiness:
    type: float
    description: Наличие речи (0.0 - 1.0)
```

---

## Миграции и версионирование

### Инструмент версионирования

Использовать **Alembic** для Python или **Prisma Migrate** для Node.js.

### Порядок начальной миграции

1. `users`
2. `songs`
3. `playlists`
4. `playlist_songs`
5. `mood_chains`
6. `mood_chain_songs`
7. `listening_history`
8. `tags`
9. `song_tags`

### Рекомендации

- Все UUID генерировать на стороне приложения (uuid7 для сортируемости)
- Использовать TIMESTAMPTZ для временных меток
- Включить расширение `pg_trgm` для полнотекстового поиска
- Партиционировать `listening_history` по месяцам при больших объёмах
