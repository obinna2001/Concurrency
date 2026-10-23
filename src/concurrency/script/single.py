import csv
import logging

from ..utils.utils import connect_db

logger = logging.getLogger(__name__)

FETCH_QUERY = """
    SELECT statement_id, date, narration, amount, direction, balance
    FROM statement_clean.transactions_clean
"""

def single_threaded_download_process():
    # connect to db
    cursor = connect_db()
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
        if DATABASE_CONNECTION is not None:
            DATABASE_CONNECTION.close()

        logging.info("Closing Database connection")