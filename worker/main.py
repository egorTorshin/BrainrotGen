import time


from db import get_conn
from queue import fetch_and_lock_job
from process import process_job


def main():
    conn = get_conn()

    print("Worker started...")

    while True:
        job = fetch_and_lock_job(conn)

        if job:
            print(f"Processing job {job['id']}")
            process_job(conn, job)
        else:
            time.sleep(1)


if __name__ == "__main__":
    main()