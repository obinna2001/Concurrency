import csv
import logging

from .import (
    BATCH_SIZE,
    FETCH_QUERY,
    DATABASE_CONFIG,
    ROOT,
    connect_db
)

logger = logging.getLogger(__name__)


def single_threaded_download_process():
    # connect to db
    database_connection = connect_db(
        config=DATABASE_CONFIG
    )
    cursor = database_connection.cursor(buffered=False)
    cursor.execute(FETCH_QUERY)

    batch_count = 0
    total_rows = 0

    output_path = ROOT / "data" / "transaction.csv"
    temp_file_path = output_path.with_suffix(".csv.part")
    try:
        with open(temp_file_path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # write column names once
            column_names = [description[0] for description in (cursor.description or [])]
            writer.writerow(column_names)
            logger.info("Column name successfully written")

            batch_count = 0

            while True:
                rows = cursor.fetchmany(size=BATCH_SIZE)

                if not rows:
                    break

                logger.info("Batch %d downloading with batch size of %d", batch_count, len(rows))
                writer.writerows(rows)
                total_rows += len(rows)
                batch_count += 1

                logger.info("%d rows downloaded successfully so far", total_rows)

                if batch_count > 0:
                    break

            cursor.close()

            temp_file_path.replace(output_path)
            
    finally:
        database_connection.close()
        logging.info("Closing Database connection")