import time
from db import get_conn
from job_queue import fetch_and_lock_job
from process import process_job


def main():
    print("Worker started...")

    while True:
        conn = get_conn()

        try:
            job = fetch_and_lock_job(conn)
        finally:
            conn.close()

        if job:
            print(f"Processing job {job['id']}")
            process_job(job)  # БЕЗ conn
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()
