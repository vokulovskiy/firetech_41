# PostgreSQL для JupyterHub

Этот репозиторий содержит конфигурацию для развертывания PostgreSQL 15 в контейнере Docker с пользовательскими настройками для работы с JupyterHub.

## Состав репозитория

```
.
├── docker-compose.yml      # Конфигурация Docker Compose
├── Dockerfile             # Сборка образа PostgreSQL
├── init-scripts          # Директория для скриптов инициализации
├── postgresql.conf       # Настройки PostgreSQL
└── README.md            # Документация
```

## Установка и запуск

### 1. Подготовка окружения
```bash
# Создание необходимых сетей (если не существуют)
docker network create jupyter-network
docker network create postgres_network
```

### 2. Сборка и запуск контейнера
```bash
# Запуск с созданием томов
docker compose up -d

# Запуск с пересборкой
docker compose up -d --build
```

### 3. Проверка состояния
```bash
# Состояние контейнера
docker compose ps

# Просмотр логов
docker compose logs -f postgres
```

### 4. Остановка и удаление
```bash
# Остановка с сохранением данных
docker compose down

# Полная очистка с удалением томов
docker compose down -v
```

## Конфигурация PostgreSQL

### Основные параметры
- **База данных**: `jupyter_db`
- **Пользователь**: `jupyter_user`
- **Порт**: 5432
- **Data директория**: `/var/lib/postgresql/data/pgdata`
- **Backup директория**: `/backup`

### Системные ресурсы
- **Память для shared buffers**: 256MB
- **Рабочая память**: 16MB
- **Память для обслуживания**: 128MB
- **Effective cache**: 1GB
- **Shared memory**: 256MB

### Подключения
- **Максимум подключений**: 100
- **Зарезервировано для суперпользователя**: 3
- **Таймаут простоя транзакции**: не ограничен
- **Таймаут блокировок**: 1 секунда

### Журналирование
- **WAL уровень**: replica
- **Максимальный размер WAL**: 1GB
- **Минимальный размер WAL**: 80MB
- **Ротация логов**: ежедневно
- **Логирование**:
  - Подключения/отключения
  - Контрольные точки
  - Долгие запросы (>1000ms)
  - Блокировки
  - Временные файлы

### Автовакуум
- **Статус**: включен
- **Количество воркеров**: 3
- **Интервал**: 1 минута
- **Пороги запуска**: 50 записей

### Сети и доступ
- **Сети**: 
  - `postgres_network`: для внутренних сервисов
  - `jupyter-network`: для JupyterHub
- **Правила доступа**: разрешены подключения с любых адресов с аутентификацией
- **Порты**: 5432 (опубликован на хосте)

## Тома и данные

### Постоянные тома
```yaml
volumes:
  postgres_data:        # Данные PostgreSQL
    name: jupyter_postgres_data
  postgres_backup:      # Резервные копии
    name: jupyter_postgres_backup
```

### Монтирование
- `/var/lib/postgresql/data`: основные данные
- `/backup`: резервные копии
- `/docker-entrypoint-initdb.d/postgresql.conf`: конфигурация

## Мониторинг

### Проверка здоровья
```yaml
healthcheck:
  interval: 10s        # Интервал проверки
  timeout: 5s          # Таймаут
  retries: 5           # Количество попыток
  start_period: 10s    # Период инициализации
```

### Основные команды мониторинга
```bash
# Просмотр состояния контейнера
docker compose ps

# Просмотр логов
docker compose logs -f postgres

# Проверка использования ресурсов
docker stats jupyter_postgres

# Проверка подключений
docker exec jupyter_postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
```

## Подключение к БД

### Через docker exec
```bash
# Подключение к psql
docker exec -it jupyter_postgres psql -U jupyter_user -d jupyter_db

# Проверка статуса
docker exec -it jupyter_postgres pg_isready
```

### Через внешний клиент
```bash
# Параметры подключения
Host: localhost
Port: 5432
Database: jupyter_db
User: jupyter_user
Password: change_this_password
```

## Бэкапы

### Создание бэкапа
```bash
# Полный бэкап базы
docker exec jupyter_postgres pg_dump -U jupyter_user jupyter_db > backup.sql

# Бэкап с компрессией
docker exec jupyter_postgres pg_dump -U jupyter_user jupyter_db | gzip > backup.sql.gz
```

### Восстановление из бэкапа
```bash
# Восстановление из SQL файла
cat backup.sql | docker exec -i jupyter_postgres psql -U jupyter_user -d jupyter_db

# Восстановление из сжатого бэкапа
gunzip -c backup.sql.gz | docker exec -i jupyter_postgres psql -U jupyter_user -d jupyter_db
```

## Безопасность

### Основные настройки
- Все подключения требуют аутентификации
- Пароли хранятся в формате MD5
- Доступ к файловой системе ограничен пользователем postgres
- Права на директорию бэкапов: 700

### Рекомендации
- Изменить пароль по умолчанию
- Ограничить доступ к порту 5432 на уровне файрвола
- Регулярно обновлять образ PostgreSQL
- Настроить SSL для шифрования соединений