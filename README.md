# Проект FireTech(41)
## Развертывание JupyterHub, PostgeSQL, Prometheus, Loki, Grafana на Docker 

Предварительно нужно установить  [docker и docker-compose](./install_docker.md)  

### Установка приложений
```bash
cd ~
git clone https://github.com/vokulovskiy/firetech_41.git 
cd firetech_41
## Собираем образ пользовательского ноутбука
docker build -f Dockerfile.notebook -t 
## Запускаем приложения
docker compose up --build -d
```

[Установка JupyterHub и PostgeSQL](./jupyterhub.md)  
[Установка мониторинга и логирования](./monitoring.md.md)  