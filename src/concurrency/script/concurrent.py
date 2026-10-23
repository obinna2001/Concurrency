import csv
import logging
from uuid import uuid4
from queue import Queue
from pathlib import Path
from threading import Event, Thread

from .import (
    BATCH_SIZE,
    FETCH_QUERY,
    DATABASE_CONFIG,
    ROOT,
    connect_db
)

BATCH_QUEUE = Queue(maxsize=3)
FAILED = Event()
ERRORS = Queue()
WORKER_COUNT: int = 3

logger = logging.getLogger(__name__)


def save_batch(batch_id, rows, column_names, output_dir: Path):
    output_path = output_dir / f"batch_{batch_id:06d}.csv"
    partial_path = output_path.with_suffix(".csv.part")

    # Add your batch-processing logic here if needed.
    with partial_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(column_names)
        writer.writerows(rows)

    # Rename only after the file has been written and closed successfully.
    partial_path.replace(output_path)


def worker(column_names: list[str], directory: Path):
    while True:
        logger.info("Retrieving SQL batch item from Queue")
        item = BATCH_QUEUE.get()
        logger.info("Item retriever successful")

        try:
            # None is the posion pill to graceful shutdown all threads
            if item is None:
                return 

            # Determines what the various workers in the thread should do to jobs in the queue -
            # after an error has being registered.
            # Currently it skips the job and implictly marks it as done. It repeats this until all job
            # in the Queue is marked as done and item is now None.
            if FAILED.is_set():
                logger.warning("Skipping Queued row processing steps")
                continue

            batch_id, rows = item
            save_batch(
                batch_id=batch_id,
                column_names=column_names,
                output_dir=directory,
                rows=rows
            )
            logger.info("Saved batch %s: %s rows", batch_id, len(rows))

        except Exception as error:
            ERRORS.put(error)   # Insert error to Error Queue
            FAILED.set()        # set event to True
            logger.exception("Batch processing failed")    # log error message

        finally:
            # cleanup block for all cases. Normal or exception case
            # it runs before "return", "continues" and runs after try and exception block runs.
            BATCH_QUEUE.task_done()     # set retrieved task as done

            # reset item and rows reference before waiting or retrieving another item in Queue
            item = None
            rows = None 


def multi_threaded_download_process():
    connection= connect_db(
        config=DATABASE_CONFIG
    )
    output_directory = ROOT / "data" / uuid4().hex
    threads = []

    try:
        output_directory.mkdir(parents=True, exist_ok=False)
        logger.info("Output directory: %s", output_directory)

        cursor = connection.cursor(buffered=False)
        cursor.execute(FETCH_QUERY)
        column_names: list[str] = [description[0] for description in (cursor.description or [])]

        # start sub threads of WORKER_COUNT to process jobs in BATCH_QUEUE
        for number in range(WORKER_COUNT):
            thread = Thread(
                target=worker,
                args=(column_names, output_directory),
                name=f"worker-{number + 1}"
            )

            thread.start()
            threads.append(thread)

        batch_number = 0
        total_rows = 0

        # This loop is the producer.
        # Only it can access the database cursor and inserts or put rows into the Queue so that
        # the background thread workers can consume or process them.
        while not FAILED.is_set():
            # while no error has being recorded or all rows have not being fetched this loop runs
            rows = cursor.fetchmany(size=BATCH_SIZE)

            if not rows:
                break       # Exit loop is there is no more row to retrieve from the database

            batch_number += 1
            BATCH_QUEUE.put((batch_number, rows))    # insert fetched row into QUEUE for workers to consume
            total_rows += len(rows)
            logger.info(
                "Queued batch %s; fetched %s total rows so far", batch_number, total_rows
            )

            # reset rows reference
            rows = None

        if not FAILED.is_set():
            cursor.close()      # close cursor if all rows were consumed successfully

    # catch and raise all Exceptions including keyboard interruption 
    except BaseException:
        FAILED.set()
        logger.exception("Expoer interrupted or reader failed")
        raise       # raise error after finally block runs

    finally:
        try:
            # send a posion kill to the Queue to set all Queue job as done
            for _ in threads:
                BATCH_QUEUE.put(None)

            BATCH_QUEUE.join()   # waits for all threads to process the posion kill and set all queue job as done
            for thread in threads:
                thread.join()       # wait and close all threads

        finally:
            # close database connection. This also closes the cursor if fetching ending early
            connection.close()

    # This only runs if an error was inserted inside ERROR by the worker thread
    if FAILED.is_set():
        raise RuntimeError(f"Export failed. Incomplete output remains in {output_directory}") from ERRORS.get_nowait()

    # finally log message to detail the status recorded during run (both successful and unsuccessful ones)
    logger.info(
        "Export complete: %s rows, %s files. File are stored in %s",
        total_rows, batch_number, output_directory
    )
