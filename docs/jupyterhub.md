# JupyterHub и PostgeSQL на Docker 

## Что это и зачем

JupyterHub — это платформа, которая позволяет запускать Jupyter Notebook для нескольких пользователей. 
Мы будем использовать Docker для удобного управления сервисами и NativeAuthenticator для аутентификации пользователей.

## Файлы конфигурации

1. **docker-compose.yaml** — описывает, какие сервисы запустить.
2. **Dockerfile.jupyterhub** — собирает образ JupyterHub.
3. **Dockerfile.notebook** — собирает образ для пользовательских Jupyter Notebook.
4. **jupyterhub_config.py** — настраивает работу JupyterHub.
5. **requirements.jupyterhub.txt** — список зависимостей jupyterhub.
6. **requirements.notebook.txt** — зависимости для ноутбуков.

## Основные команды

### Подготовка окружения
```bash
# Сборка образа для ноутбуков
docker build -f Dockerfile.notebook -t my-custom-jupyter-notebook .
```

### Запуск и управление
```bash
# Запустить все сервисы
docker compose up -d

# Остановить
docker compose down

# Перезапустить
docker compose restart
```

### Очистка
```bash
# Удаление всех ненужных данных
docker system prune -a --volumes -f
```

## Конфигурация сервисов (docker-compose.yaml)

```yaml
networks:
  jupyterhub-network:
    driver: bridge
    name: jupyterhub-network  # Создание сети для JupyterHub
  monitoring:
    driver: bridge
    name: monitoring  # Создание сети для мониторинга

volumes:
  prometheus_data: {}  # Том для хранения данных Prometheus
  grafana-storage:  # Том для хранения данных Grafana
  jupyterhub-data:  # Том для хранения данных JupyterHub
  notebook_data:  # Том для хранения данных пользовательских ноутбуков
  pg-data:  # Том для хранения данных PostgreSQL

services:

  jupyterhub:
    build:
      context: .
      dockerfile: Dockerfile.jupyterhub  # Сборка образа JupyterHub из указанного Dockerfile
    container_name: jupyterhub  # Имя контейнера
    restart: unless-stopped  # Автоматический перезапуск контейнера, если он не остановлен вручную
    networks:
      - jupyterhub-network  # Подключение к сети JupyterHub
      - monitoring  # Подключение к сети мониторинга
    volumes:
      # Конфигурационный файл JupyterHub
      - "./jupyterhub_config.py:/srv/jupyterhub/jupyterhub_config.py:ro"
      # Подключение сокета Docker для взаимодействия с Docker-демоном из контейнера
      - "/var/run/docker.sock:/var/run/docker.sock:rw"
      # Том для хранения базы данных и секретов JupyterHub
      - "jupyterhub-data:/data"
    ports:
      - "8000:8000"  # Порт для доступа к JupyterHub
    environment:
      # Имя администратора JupyterHub
      JUPYTERHUB_ADMIN: admin
      # Имя сети, к которой будут подключаться контейнеры
      DOCKER_NETWORK_NAME: jupyterhub-network
      # Образ, который будет использоваться для создания пользовательских ноутбуков
      DOCKER_NOTEBOOK_IMAGE: my-custom-jupyter-notebook:latest
      # Директория для ноутбуков внутри пользовательского образа
      DOCKER_NOTEBOOK_DIR: /home/jovyan/work

  postgres:
    image: postgres:17.0-alpine3.20  # Использование образа PostgreSQL
    container_name: postgres  # Имя контейнера
    ports:
      - "5433:5432"  # Порт для доступа к PostgreSQL
    environment:
      POSTGRES_PASSWORD: Postgres  # Пароль для пользователя PostgreSQL
      POSTGRES_DB: postgres  # Имя базы данных по умолчанию
      PGDATA: /var/lib/postgresql/data/pgdata  # Директория для данных PostgreSQL
    volumes:
      - pg-data:/var/lib/postgresql/data  # Том для хранения данных PostgreSQL
    restart: unless-stopped  # Автоматический перезапуск контейнера
    networks:
      - jupyterhub-network  # Подключение к сети JupyterHub
      - monitoring  # Подключение к сети мониторинга
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]  # Проверка здоровья PostgreSQL
      interval: 5s  # Интервал проверки
      timeout: 10s  # Тайм-аут проверки
      retries: 3  # Количество попыток
```

## Основные настройки (jupyterhub_config.py)

```python
# Конфигурационный файл для JupyterHub
import os

c = get_config()  # noqa: F821

# Мы полагаемся на переменные окружения для настройки JupyterHub, чтобы избежать
# необходимости пересобирать контейнер JupyterHub каждый раз при изменении
# параметра конфигурации.

# Запуск односерверных контейнеров как Docker-контейнеров
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"

# Запуск контейнеров из этого образа
c.DockerSpawner.image = os.environ["DOCKER_NOTEBOOK_IMAGE"]

# Подключение контейнеров к этой Docker-сети
network_name = os.environ["DOCKER_NETWORK_NAME"]
c.DockerSpawner.use_internal_ip = True
c.DockerSpawner.network_name = network_name

# Явное указание директории для записных книжек, так как мы будем монтировать том в неё.
# Большинство образов `jupyter/docker-stacks` *-notebook запускают сервер записных книжек
# от пользователя `jovyan` и устанавливают директорию для записных книжек в `/home/jovyan/work`.
# Мы следуем той же конвенции.
notebook_dir = os.environ.get("DOCKER_NOTEBOOK_DIR", "/home/jovyan/work")
c.DockerSpawner.notebook_dir = notebook_dir

# Монтирование тома Docker реального пользователя на хосте в директорию записных книжек
# пользователя в контейнере
c.DockerSpawner.volumes = {"jupyterhub-user-{username}": notebook_dir}

# Удаление контейнеров после их остановки
c.DockerSpawner.remove = True

# Для отладки аргументов, передаваемых в запускаемые контейнеры
c.DockerSpawner.debug = True

# Контейнеры пользователей будут обращаться к хабу по имени контейнера в Docker-сети
c.JupyterHub.hub_ip = "jupyterhub"
c.JupyterHub.hub_port = 8080

# Сохранение данных хаба на томе, смонтированном внутри контейнера
c.JupyterHub.cookie_secret_file = "/data/jupyterhub_cookie_secret"
c.JupyterHub.db_url = "sqlite:////data/jupyterhub.sqlite"

# Прокси
c.ConfigurableHTTPProxy.auth_token = 'super-secret-token'

# Разрешить вход всем зарегистрированным пользователям
c.Authenticator.allowed_users = {'admin', 'uuser', 'user1'}
# c.Authenticator.allow_all = False
c.Authenticator.allow_existing_users = False

# Аутентификация пользователей с помощью Native Authenticator
c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"

# Разрешить регистрацию всем без одобрения
c.NativeAuthenticator.open_signup = True

# Разрешенные администраторы
admin = os.environ.get("JUPYTERHUB_ADMIN")
if admin:
    c.Authenticator.admin_users = [admin]

# Метрики Prometheus
# c.JupyterHub.metric_handlers = ['prometheus']
c.JupyterHub.authenticate_prometheus = False
```

## Управление пользователями

1. Админ регистрируется на `http://your-domain:8000/hub/signup`.
2. Управляет пользователями в `/hub/admin` (можно запускать и останавливать их серверы).

## Решение проблем

### Пользователь не может войти
- Проверить `/hub/authorize`.
- Поменять пароль.

### Сервер не запускается
```bash
# Посмотреть логи
docker logs jupyterhub

# Проверить состояние контейнеров
docker ps -a

# Проверить исползование ресурсов контейнерами
docker stats --no-stream
```

### Файлы не сохраняются
```bash
# Проверить доступ к данным
docker run --rm -v jupyterhub_data:/data busybox ls -la /data
docker run --rm -v jupyterhub-user-<user>:/home/jovyan/work busybox ls -la /home/jovyan/work

```

## Обновление

```bash
# Обновить образы и перезапустить
docker compose pull
docker compose down
docker compose up -d
```

## Сохранение тетрадок пользователей

```bash
docker run --rm \
  -v jupyterhub-user-<user>:/home/jovyan/work \
  -u root \
  -v /tmp:/backups \
  quay.io/jupyter/minimal-notebook \
  tar cvf /backups/<user>-backup.tar /home/jovyan/work
```  
Или

docker volume inspect jupyterhub-user-admin
chmod +x backup_notebook.sh  
sudo sh backup_notebook.sh

```bash
#!/bin/sh

BACKUP_VOL=/backup/
DOCKER_VOL=/var/lib/docker/volumes/
mkdir $BACKUP_VOL
FOLDERS=$(ls $DOCKER_VOL | grep jupyterhub-user-)
echo $DOCKER_VOL$FOLDERS
if [ -z "$FOLDERS" ]; then
  echo "Папки по маске '$MASK' не найдены."
  exit 1
fi

# Перебор найденных папок и создание архивов
for FOLDER in $FOLDERS; do
  # Создание архива для каждой папки
  tar -czvf "$BACKUP_VOL$FOLDER.tar.gz" "$DOCKER_VOL$FOLDER"
  
  echo "Папка '$FOLDER' заархивирована в '$FOLDER.tar.gz'"
done

echo "Все папки заархивированы."
ls -la $BACKUP_VOL
```
