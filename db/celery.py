from pydantic_settings import BaseSettings


def create_celery_client(env: BaseSettings):
    from celery import Celery

    celery_app = Celery(
        "worker" if env.is_worker else "main",
        broker=env.REDIS_URL + f"/{env.REDIS_TASK_INDEX}",
        backend=env.REDIS_URL + f"/{env.REDIS_TASK_RESULT_INDEX}",  # result storage
    )
    return celery_app
