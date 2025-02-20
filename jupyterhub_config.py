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