# Система мониторинга и логированияна базе Prometheus, Grafana, Loki #

## Краткое описание конфигурационных файлов

1. **docker-compose.yml**
   - Основной файл для запуска всех сервисов мониторинга
   - Включает Prometheus, Grafana, cAdvisor, Alertmanager, Netdata и Postgres Exporter

2. **prometheus.yml**
   - Главный конфигурационный файл Prometheus
   - Определяет источники метрик и интервалы сбора данных

3. **alerts.rules.yml**
   - Правила оповещений для Prometheus
   - Определяет условия срабатывания алертов

4. **alertmanager.yml**
   - Конфигурация системы оповещений prometheus
   - Настройки отправки уведомлений по email

5. **grafana.ini**
   - Конфигурация системы оповещений grafana
   - Настройки отправки уведомлений по email

6. **prometheussql.queries.yml**
   - Конфигурация PrometheusSQL exporter

## Команды управления


### Запуск и остановка
```bash
# Запуск всех сервисов
docker compose up -d

# Запуск с пересборкой образов
docker compose up -d --build

# Остановка сервисов
docker compose down

# Полная остановка с удалением томов
docker compose down -v
```

### Перезапуск и обновление
```bash
# Перезапуск всех сервисов
docker compose restart

# Перезапуск отдельного сервиса
docker compose restart prometheus
docker compose restart grafana

# Обновление образов
docker compose pull
```

## Описание конфигурационных файлов

### docker-compose.yml
```yaml
  # PostgreSQL Exporter - сбор метрик PostgreSQL
  postgres_exporter:
    image: prometheuscommunity/postgres-exporter  # Использование образа для экспорта метрик PostgreSQL
    container_name: postgres_exporter  # Имя контейнера
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:Postgres@postgres:5432/postgres?sslmode=disable"  # Источник данных для подключения к PostgreSQL
      PG_EXPORTER_AUTO_DISCOVER_DATABASES: 1  # Автоматическое обнаружение всех баз данных для сбора метрик
    ports:
      - "9187:9187"  # Порт для доступа к экспортеру
    networks:
      - monitoring  # Подключение к сети мониторинга
    depends_on:
      - postgres  # Зависимость от контейнера PostgreSQL

  node-exporter:
    image: prom/node-exporter:latest  # Использование образа для сбора метрик узла
    container_name: node-exporter  # Имя контейнера
    restart: unless-stopped  # Автоматический перезапуск контейнера
    volumes:
      - /proc:/host/proc:ro  # Подключение директории /proc для сбора метрик
      - /sys:/host/sys:ro  # Подключение директории /sys для сбора метрик
      - /:/rootfs:ro  # Подключение корневой файловой системы для сбора метрик
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'  # Исключение определенных точек монтирования
    ports:
      - 9100:9100  # Порт для доступа к экспортеру
    networks:
      - monitoring  # Подключение к сети мониторинга

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.49.1  # Использование образа cAdvisor для мониторинга контейнеров
    container_name: cadvisor  # Имя контейнера
    volumes:
      - /:/rootfs:ro  # Подключение корневой файловой системы
      - /var/run:/var/run:rw  # Подключение директории /var/run
      - /sys:/sys:ro  # Подключение директории /sys
      - /var/lib/docker:/var/lib/docker:ro  # Подключение директории Docker
      - /dev/disk/:/dev/disk:ro  # Подключение директории /dev/disk
    restart: unless-stopped  # Автоматический перезапуск контейнера
    ports:
      - "8080:8080"  # Порт для доступа к cAdvisor
    networks:
      - monitoring  # Подключение к сети мониторинга

  prometheus:
    image: prom/prometheus:latest  # Использование образа Prometheus
    container_name: prometheus  # Имя контейнера
    restart: unless-stopped  # Автоматический перезапуск контейнера
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml  # Подключение конфигурационного файла Prometheus
      - ./alert.rules.yml:/etc/prometheus/alert.rules.yml  # Подключение файла с правилами оповещений
      - prometheus_data:/prometheus  # Том для хранения данных Prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'  # Указание конфигурационного файла
      - '--storage.tsdb.path=/prometheus'  # Указание пути для хранения данных
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'  # Включение управления жизненным циклом через API
    ports:
      - 9090:9090  # Порт для доступа к Prometheus
    networks:
      - monitoring  # Подключение к сети мониторинга

  sqlagent:
    image: dbhi/sql-agent  # Использование образа SQL Agent
    container_name: sqlagent  # Имя контейнера
    networks:
      - monitoring  # Подключение к сети мониторинга
    ports: 
      - 5000:5000  # Порт для доступа к SQL Agent

  prometheussql:
    image: dbhi/prometheus-sql  # Использование образа Prometheus SQL
    container_name: prometheussql  # Имя контейнера
    networks:
      - monitoring  # Подключение к сети мониторинга
    links:
      - sqlagent:sqlagent  # Связь с контейнером SQL Agent
    ports:
      - 8090:8080  # Порт для доступа к Prometheus SQL
    volumes:
      - ./prometheussql.queries.yml:/queries.yml  # Подключение файла с запросами

  alertmanager:
    image: prom/alertmanager:latest  # Использование образа Alertmanager
    container_name: alertmanager  # Имя контейнера
    ports:
      - "9093:9093"  # Порт для доступа к Alertmanager
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml  # Подключение конфигурационного файла Alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'  # Указание конфигурационного файла
    restart: unless-stopped  # Автоматический перезапуск контейнера
    networks:
      - monitoring  # Подключение к сети мониторинга

  netdata:
    image: netdata/netdata  # Использование образа Netdata
    container_name: netdata  # Имя контейнера
    ports:
      - "19999:19999"  # Порт веб-интерфейса Netdata
    restart: unless-stopped  # Автоматический перезапуск контейнера
    cap_add:
      - SYS_PTRACE  # Добавление возможностей для мониторинга
      - SYS_ADMIN
    security_opt:
      - apparmor:unconfined  # Отключение AppArmor
    environment:
      - NETDATA_CLAIM_URL=https://app.netdata.cloud  # URL для подключения к облаку Netdata
      - DISABLE_TELEMETRY=1  # Отключение телеметрии
      - NETDATA_BIND=0.0.0.0:19999  # Привязка к порту
      - DISABLE_WEB_ACCESS_LOGS=1  # Отключение логов доступа
      - NETDATA_DISABLE_CLOUD=1  # Отключение облака
    volumes:
      - /:/host/root:ro,rslave  # Подключение корневой файловой системы
      - /etc/passwd:/host/etc/passwd:ro  # Подключение файла /etc/passwd
      - /etc/group:/host/etc/group:ro  # Подключение файла /etc/group
      - /etc/localtime:/etc/localtime:ro  # Подключение временной зоны
      - /proc:/host/proc:ro  # Подключение директории /proc
      - /sys:/host/sys:ro  # Подключение директории /sys
      - /etc/os-release:/host/etc/os-release:ro  # Подключение информации о системе
      - /var/log:/host/var/log:ro  # Подключение логов
      - /var/run/docker.sock:/var/run/docker.sock:ro  # Подключение сокета Docker
      - /run/dbus:/run/dbus:ro  # Подключение D-Bus
    networks:
      - monitoring  # Подключение к сети мониторинга

  loki:
    image: grafana/loki:latest  # Использование образа Loki
    container_name: loki  # Имя контейнера
    ports:
      - "3100:3100"  # Порт для доступа к Loki
    command: -config.file=/etc/loki/local-config.yaml  # Указание конфигурационного файла
    networks:
      - loki  # Подключение к сети Loki

  promtail:
    image: grafana/promtail:latest  # Использование образа Promtail
    container_name: promtail  # Имя контейнера
    volumes:
      - /var/log:/var/log  # Подключение директории логов
    command: -config.file=/etc/promtail/config.yml  # Указание конфигурационного файла
    networks:
      - loki  # Подключение к сети Loki

  grafana:
    container_name: grafana  # Имя контейнера
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin  # Пароль администратора Grafana
      - GF_PATHS_PROVISIONING=/etc/grafana/provisioning  # Путь к конфигурации Grafana
      - GF_AUTH_ANONYMOUS_ENABLED=true  # Разрешение анонимного доступа
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin  # Роль анонимного пользователя
      - GF_FEATURE_TOGGLES_ENABLE=alertingSimplifiedRouting,alertingQueryAndExpressionsStepMode  # Включение дополнительных функций
    volumes:
      - grafana-storage:/var/lib/grafana  # Том для хранения данных Grafana
      - ./grafana.ini:/etc/grafana/grafana.ini  # Подключение конфигурационного файла Grafana
    restart: unless-stopped  # Автоматический перезапуск контейнера
    image: grafana/grafana:latest  # Использование образа Grafana
    ports:
      - "3000:3000"  # Порт для доступа к Grafana
    networks:
      - loki  # Подключение к сети Loki
      - monitoring  # Подключение к сети мониторинга
```

### prometheus.yml
```yaml
global:
  scrape_interval:     30s

rule_files:
  - /etc/prometheus/alert.rules.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  - job_name: "prometheus"
    scrape_interval: 5s
    static_configs:
    - targets: ["localhost:9090"]

  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres_exporter:9187']

  - job_name: 'jupyterhub'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['jupyterhub:8000']

  - job_name: 'prometheussql'
    scrape_interval: 60m
    metrics_path: '/metrics'
    static_configs:
      - targets: ['prometheussql:8080']

  - job_name: 'netdata'          
    metrics_path: '/api/v1/allmetrics'
    params:
      format: [ prometheus ]
    static_configs:
      - targets: ['netdata:19999']
```

### alertmanager.yml
```yaml
global:
  smtp_smarthost: 'smtp.mail.ru:465'
  smtp_from: 'vlad_ok@mail.ru'
  smtp_auth_username: 'vlad_ok@mail.ru'
  smtp_auth_password: 'cy38nEaLktKyLnpn90WP1'  
  smtp_require_tls: false

route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h
  receiver: 'email-notifications'

receivers:
- name: 'email-notifications'
  email_configs:
  - to: 'vasyapupkin441780@gmail.com'
```

### alert.rules.yml
```yaml
groups:
  - name: container_alerts
    rules:
      - alert: HighContainerUsage
        expr: rate(container_cpu_usage_seconds_total{name=~".+"}[2m]) * 100 > 80
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "High resource usage in {{ $labels.name }}"
          description: "Container {{ $labels.name }} using more than 80% CPU for 2 minutes"

  - name: ssh_alerts
    rules:
      - alert: SSHLogin
        expr: netdata_systemd_service_pids_current_pids_average{service_name="ssh"} > 0
        for: 30s
        labels:
          severity: info
        annotations:
          summary: "Multiple SSH Sessions Detected"
          description: "Current SSH processes value: {{ $value }}"

  - name: instance_alerts
    rules:
      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Instance {{ $labels.instance }} down"
          description: "{{ $labels.instance }} of job {{ $labels.job }} has been down for more than 1 minute"
```

## Экспортеры и метрики

### Netdata
Комплексная система мониторинга с автоматическим обнаружением метрик.

#### Доступ
- URL: `http://localhost:19999`
- Метрики Prometheus: `http://localhost:19999/api/v1/allmetrics?format=prometheus`

#### Основные метрики:
```text
# Системные ресурсы CPU
netdata_system_cpu_percentage_average         # Среднее использование CPU
netdata_cpu_cpu_percentage_used              # Использование CPU по ядрам
netdata_cpu_interrupts_percentage_average    # Прерывания CPU

# Память
netdata_system_ram_MB_average               # Использование RAM
netdata_system_swap_MB_average              # Использование SWAP
netdata_system_slab_KB_average              # Использование SLAB

# Диски и I/O
netdata_disk_space_GB_average               # Использование дискового пространства
netdata_disk_inodes_average                 # Использование inodes
netdata_disk_io_reads_average               # Операции чтения
netdata_disk_io_writes_average              # Операции записи

# Сеть
netdata_system_net_kilobits_average         # Сетевой трафик
netdata_system_net_packets_average          # Сетевые пакеты
netdata_system_net_errors_average           # Ошибки сети
netdata_system_net_drops_average            # Потерянные пакеты

# Процессы
netdata_system_processes_running_average     # Запущенные процессы
netdata_system_processes_blocked_average     # Заблокированные процессы
netdata_system_processes_zombies_average     # Процессы-зомби
```

### cAdvisor
Экспортер для сбора метрик контейнеров Docker.

#### Доступ
- URL: `http://localhost:8080`
- Метрики: `http://localhost:8080/metrics`

#### Основные метрики:
```text
# Использование CPU
container_cpu_usage_seconds_total           # Общее время CPU
container_cpu_system_seconds_total          # Системное время CPU
container_cpu_user_seconds_total            # Пользовательское время CPU
container_cpu_cfs_throttled_seconds_total   # Время throttling CPU

# Использование памяти
container_memory_usage_bytes                # Текущее использование памяти
container_memory_rss                        # Resident Set Size
container_memory_cache                      # Размер кэша
container_memory_swap                       # Использование swap
container_memory_failcnt                    # Количество ошибок выделения памяти
container_memory_max_usage_bytes            # Максимальное использование памяти

# Использование диска
container_fs_reads_bytes_total             # Общий объем чтения
container_fs_writes_bytes_total            # Общий объем записи
container_fs_usage_bytes                   # Использование диска
container_fs_limit_bytes                   # Лимит использования диска

# Сетевая активность
container_network_receive_bytes_total      # Принятые байты
container_network_transmit_bytes_total     # Переданные байты
container_network_receive_packets_total    # Принятые пакеты
container_network_transmit_packets_total   # Переданные пакеты
container_network_receive_errors_total     # Ошибки приема
container_network_transmit_errors_total    # Ошибки передачи
```

### Postgres Exporter
Экспортер для сбора метрик PostgreSQL.

#### Доступ
- URL метрик: `http://localhost:9187/metrics`

#### Основные метрики:
```text
# Состояние базы данных
pg_up                                      # Доступность базы
pg_database_size_bytes                     # Размер базы данных
pg_stat_database_tup_fetched              # Количество прочитанных строк
pg_stat_database_tup_inserted             # Количество вставленных строк
pg_stat_database_tup_updated              # Количество обновленных строк
pg_stat_database_tup_deleted              # Количество удаленных строк

# Подключения и блокировки
pg_stat_database_numbackends              # Количество активных подключений
pg_stat_activity_count                    # Статистика активности
pg_locks_count                            # Количество блокировок
pg_stat_database_deadlocks                # Количество взаимных блокировок

# Производительность и кэш
pg_stat_database_blks_hit                 # Попадания в кэш
pg_stat_database_blks_read               # Чтения с диска
pg_stat_database_xact_commit             # Успешные транзакции
pg_stat_database_xact_rollback           # Откаты транзакций

# Репликация
pg_stat_replication_lag_bytes            # Отставание репликации в байтах
pg_stat_replication_application_lag      # Отставание репликации во времени
```

### JupyterHub Exporter
Встроенный экспортер метрик JupyterHub.

#### Основные метрики:
```text
# Пользователи и серверы
jupyterhub_active_users_total             # Активные пользователи
jupyterhub_running_servers_total          # Запущенные серверы
jupyterhub_total_users                    # Общее количество пользователей

# Запросы и производительность
jupyterhub_request_duration_seconds       # Длительность запросов
jupyterhub_request_total                  # Общее количество запросов
jupyterhub_hub_request_duration_seconds   # Длительность запросов к хабу

# События жизненного цикла
jupyterhub_spawn_duration_seconds         # Время запуска сервера
jupyterhub_stop_duration_seconds          # Время остановки сервера
jupyterhub_spawn_failed_total            # Количество неудачных запусков
jupyterhub_stop_failed_total             # Количество неудачных остановок
```


## Полезные запросы Prometheus

### Мониторинг контейнеров
```promql
# Использование CPU контейнерами (в процентах)
rate(container_cpu_usage_seconds_total{name=~".+"}[5m]) * 100

# Использование памяти (в MB)
container_memory_usage_bytes{name=~".+"} / 1024 / 1024

# Топ-5 контейнеров по использованию CPU
topk(5, rate(container_cpu_usage_seconds_total{name=~".+"}[5m]) * 100)
```

### Мониторинг PostgreSQL
```promql
# Активные подключения к базе данных
pg_stat_activity_count{state="active"}

# Размер баз данных (в GB)
pg_database_size_bytes / 1024 / 1024 / 1024

# Количество транзакций в секунду
rate(pg_stat_database_xact_commit[5m]) + rate(pg_stat_database_xact_rollback[5m])
```

### Мониторинг JupyterHub
```promql
# Количество активных пользователей
jupyterhub_active_users_total

# Среднее время запуска сервера
rate(jupyterhub_spawn_duration_seconds_sum[5m]) / rate(jupyterhub_spawn_duration_seconds_count[5m])

# Количество неудачных запусков
increase(jupyterhub_spawn_failed_total[1h])
```

## Доступ к компонентам системы

### Веб-интерфейсы

#### Grafana
- URL: `http://localhost:3000`
- Логин по умолчанию: `admin`
- Пароль по умолчанию: `admin`
- Основные разделы:
  - Dashboards → Browse: просмотр доступных дашбордов
  - Configuration → Data Sources: настройка источников данных
  - Administration → Users: управление пользователями
  - Explore: исследование метрик и создание запросов

#### Prometheus
- URL: `http://localhost:9090`
- Основные разделы:
  - Graph: построение графиков и запросов
  - Alerts: просмотр текущих алертов
  - Status → Targets: проверка состояния экспортеров
  - Status → Rules: просмотр правил алертов

#### Alertmanager
- URL: `http://localhost:9093`
- Разделы:
  - Alerts: текущие алерты
  - Silences: управление отключением оповещений
  - Status: состояние системы оповещений

#### cAdvisor
- URL: `http://localhost:8080`
- Разделы:
  - Containers: метрики контейнеров
  - Docker: метрики Docker
  - Performance: производительность системы

#### Netdata
- URL: `http://localhost:19999`
- Real-time мониторинг с автообновлением
- Детальные метрики системы и приложений

#### Postgres Exporter
- URL метрик: `http://localhost:9187/metrics`
- Сырые метрики в формате Prometheus

### Рекомендуемые дашборды Grafana

#### Система
- Netdata Overview (ID: 2701)
- Docker Containers (ID: 893)
- Custom System Monitor (включен в документацию)

#### PostgreSQL
- PostgreSQL Database (ID: 9628)
- PostgreSQL Tables Overview (включен в документацию)

#### JupyterHub
- Jupyter Resources Usage (включен в документацию)
- Jupyter User Activity (включен в документацию)

#### JupyterHub
- JupyterHub Metrics (custom)
- User Activity Dashboard (custom)

### Пример запросов для PostgreSQL

#### Проверка активных подключений
```sql
SELECT * FROM pg_stat_activity 
WHERE state = 'active';
```

#### Размер баз данных
```sql
SELECT 
    datname as database_name,
    pg_size_pretty(pg_database_size(datname)) as size
FROM pg_database
ORDER BY pg_database_size(datname) DESC;
```

#### Блокировки
```sql
SELECT blocked_locks.pid AS blocked_pid,
       blocking_locks.pid AS blocking_pid,
       blocked_activity.usename AS blocked_user,
       blocking_activity.usename AS blocking_user,
       blocked_activity.query AS blocked_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_locks blocking_locks 
    ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_catalog.pg_stat_activity blocked_activity 
    ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_stat_activity blocking_activity 
    ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### Настройка дополнительных оповещений

#### PostgreSQL Alerts
```yaml
groups:
  - name: postgres_alerts
    rules:
      - alert: PostgreSQLHighConnections
        expr: pg_stat_activity_count > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High number of PostgreSQL connections"
          description: "PostgreSQL instance has more than 100 connections for 5 minutes"

      - alert: PostgreSQLSlowQueries
        expr: rate(pg_stat_activity_max_tx_duration{datname!=""}[1m]) > 300
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Slow PostgreSQL queries detected"
          description: "PostgreSQL queries are taking more than 5 minutes to execute"
```

#### Системные алерты
```yaml
groups:
  - name: system_alerts
    rules:
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage detected"
          description: "CPU usage is above 80% for 5 minutes"

      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage detected"
          description: "Memory usage is above 80% for 5 minutes"
```