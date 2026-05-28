from flask import Flask
from flask_apscheduler import APScheduler
import subprocess
import logging


# запускать из корня

logging.basicConfig(
    filename='scheduler/scheduler.log',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)

class Config:
    """App configuration."""

    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()


@scheduler.task(
    "cron",
    id="update_corpus",
    hour="3",   # 3 часа ночи
    minute="0",
    #minute="*/2", # для отладки
    misfire_grace_time=900,
    max_instances=1
)
def update_corpus():
    # обновить и переиндексировать корпус

    logging.info("Start update")

    tasks = [
        {
            "cwd": "data_raw",
            "cmd": ["python", "get_data.py"]
        },
        {
            "cwd": "src_convertors",
            "cmd": ["python", "hf2json.py"]
        },
        {
            "cwd": "indexator",
            "cmd": ["python", "indexator.py"]
        }
    ]

    for task in tasks:

        cmd_str = ' '.join(task['cmd'])
        logging.info(f"Running: {cmd_str}")

        task_input = "y\n" if "indexator.py" in task["cmd"][1] else None
        
        try:
            result = subprocess.run(
                task["cmd"],
                cwd=task["cwd"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                input=task_input
            )

            if result.stdout.strip():
                logging.info(f"Output from {task['cwd']}:\n{result.stdout.strip()}")

            if result.stderr.strip():
                logging.error(f"Error from {task['cwd']}:\n{result.stderr.strip()}")

        except Exception as e:
            logging.error(f"Failed to execute {cmd_str}: {str(e)}")
    
    logging.info("Finished update")

if __name__ == "__main__":
    app = Flask(__name__)
    app.config.from_object(Config())

    scheduler.init_app(app)
    scheduler.start()

    app.run() # на каком сервере запускать процесс?