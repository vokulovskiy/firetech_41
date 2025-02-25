from prometheus_client import start_http_server, Gauge
import docker
import time

# Инициализация метрик Prometheus
NOTEBOOK_FILE_SIZE = Gauge('notebook_file_size_bytes', 'Size of the notebook file in bytes', ['container_name', 'file_name'])
NOTEBOOK_FILE_LINE_COUNT = Gauge('notebook_file_line_count', 'Number of lines in the notebook file', ['container_name', 'file_name'])

def collect_metrics():
    """
    Собирает метрики из контейнеров Docker и обновляет Prometheus метрики.
    """
    client = docker.from_env()

    # Получаем список всех запущенных контейнеров
    containers = client.containers.list()

    # Фильтруем контейнеры по образу 'pattern_notebook'
    container_with_notebook = [x for x in containers if 'pattern_notebook' in x.attrs['Config']['Image']]

    for cont in container_with_notebook:
        print(f"Обработка контейнера: {cont.name}")

        # Ищем файлы с расширениями .ipynb и .py в директории /home/jovyan/work
        find_command = r"find /home/jovyan/work -type f \( -name '*.ipynb' -o -name '*.py' \)"
        result = cont.exec_run(find_command)
        files = result.output.decode('utf-8').strip().split('\n')

        for file_path in files:
            if not file_path:  # Пропускаем пустые строки
                continue
            try:
                # Получаем размер файла
                size_result = cont.exec_run(f"stat -c%s {file_path}")
                file_size = int(size_result.output.decode('utf-8').strip())

                # Пропускаем файлы меньше или равные 1000 байт
                if file_size <= 1000:
                    continue

                # Получаем имя файла
                basename_result = cont.exec_run(f"basename {file_path}")
                file_name = basename_result.output.decode('utf-8').strip()

                # Получаем количество строк в файле
                line_count_result = cont.exec_run(f"wc -l {file_path}")
                line_count = int(line_count_result.output.decode('utf-8').strip().split()[0])

                # Обновляем метрики Prometheus
                NOTEBOOK_FILE_SIZE.labels(container_name=cont.name, file_name=file_name).set(file_size)
                NOTEBOOK_FILE_LINE_COUNT.labels(container_name=cont.name, file_name=file_name).set(line_count)

                print(f"Файл: {file_name}, Размер: {file_size} байт, Количество строк: {line_count}")

            except Exception as e:
                print(f"Ошибка при обработке файла {file_path}: {e}")

if __name__ == '__main__':
    # Запускаем HTTP-сервер Prometheus 
    start_http_server(17666)
    print("Prometheus exporter запущен на порту 17666")

    # Бесконечный цикл для периодического сбора метрик
    while True:
        collect_metrics()
        time.sleep(3600)  # Собираем метрики каждые 60 минут