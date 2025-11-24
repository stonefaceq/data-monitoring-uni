import time
import random
import threading
import psycopg2
from faker import Faker
from prometheus_client import start_http_server, Gauge, Counter
from datetime import datetime

# configure prometheus and db

# use docker-compose config
DB_HOST = 'postgres' 
DB_NAME = 'metrics_db'
DB_USER = 'user'
DB_PASS = 'password'

# init Faker for fake data
fake = Faker()

# prometheus metrics init
DB_TOTAL_ROWS = Gauge('db_total_rows', 'Загальна кількість рядків у таблиці system_logs')
DB_OPERATIONS_TOTAL = Counter('db_operations_total', 'Загальна кількість операцій з БД', ['operation', 'status'])
DB_AVG_DURATION = Gauge('db_avg_operation_duration_ms', 'Середній час виконання операції, мс')

# db workflow funcs

def get_db_connection():
    """Створює та повертає з'єднання до PostgreSQL."""
    conn = psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

def insert_random_data():
    """Генерує випадкові записи та додає їх у БД."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        operation = random.choice(['READ', 'WRITE', 'DELETE', 'UPDATE'])
        duration = random.randint(5, 500) # тривалість операції від 5 до 500 мс

        sql = """
        INSERT INTO system_logs (operation_type, duration_ms) 
        VALUES (%s, %s);
        """
        cursor.execute(sql, (operation, duration))
        conn.commit()
        
        DB_OPERATIONS_TOTAL.labels(operation='insert', status='success').inc()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Додано запис: {operation} ({duration}ms)")

    except Exception as e:
        DB_OPERATIONS_TOTAL.labels(operation='insert', status='failure').inc()
        print(f"Помилка при вставці даних: {type(e).__name__}: {e}")
        if conn: 
            conn.rollback()
    finally:
        if conn:
            conn.close()

def collect_metrics():
    """Збирає агреговані метрики з бази даних і оновлює Prometheus Gauges."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # row count
        cursor.execute("SELECT COUNT(*) FROM system_logs;")
        total_rows = cursor.fetchone()[0]
        DB_TOTAL_ROWS.set(total_rows)

        # avg operation time
        cursor.execute("SELECT AVG(duration_ms) FROM system_logs;")
        avg_duration = cursor.fetchone()[0]
        if avg_duration is not None:
             DB_AVG_DURATION.set(avg_duration)

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Метрики оновлено. Рядків: {total_rows}, Середня тривалість: {avg_duration:.2f}ms")

    except Exception as e:
        print(f"Помилка при зборі метрик: {type(e).__name__}: {e}")
    finally:
        if conn:
            conn.close()

# loops

def data_generation_loop(interval=5):
    """Цикл для періодичної генерації нових даних."""
    while True:
        insert_random_data()
        time.sleep(interval)

def metrics_collection_loop(interval=10):
    """Цикл для періодичного збору та оновлення метрик."""
    while True:
        collect_metrics()
        time.sleep(interval)



if __name__ == '__main__':
    print("--- Запуск Data Generator & Metrics Exporter ---")

    # launch prometheus on 8000 port
    start_http_server(8000) 
    print("Prometheus HTTP-сервер запущено на порті 8000.")

    # generating data
    threading.Thread(target=data_generation_loop, daemon=True).start()
    # collect metrics
    threading.Thread(target=metrics_collection_loop, daemon=True).start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Додаток зупинено.")