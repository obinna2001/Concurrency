import csv
import io
import runpy
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from concurrency import cli
from concurrency.script import concurrent, single


class CommandLineTests(unittest.TestCase):
    def test_modes_dispatch_to_the_selected_exporter(self):
        for arguments, selected in (
            ([], "concurrent"),
            (["concurrent"], "concurrent"),
            (["sequential"], "sequential"),
        ):
            with self.subTest(arguments=arguments):
                with (
                    patch("sys.argv", ["concurrency", *arguments]),
                    patch.object(cli.logging, "basicConfig"),
                    patch.object(concurrent, "multi_threaded_download_process") as concurrent_run,
                    patch.object(single, "single_threaded_download_process") as sequential_run,
                ):
                    cli.main()
                    self.assertEqual(concurrent_run.call_count, selected == "concurrent")
                    self.assertEqual(sequential_run.call_count, selected == "sequential")

    def test_invalid_mode_is_rejected_before_exporting(self):
        with (
            patch("sys.argv", ["concurrency", "invalid"]),
            patch.object(concurrent, "multi_threaded_download_process") as concurrent_run,
            patch.object(single, "single_threaded_download_process") as sequential_run,
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as error,
        ):
            cli.main()
        self.assertEqual(error.exception.code, 2)
        concurrent_run.assert_not_called()
        sequential_run.assert_not_called()

    def test_module_entry_point_uses_the_same_cli(self):
        with patch.object(cli, "main") as main:
            runpy.run_module("concurrency", run_name="__main__")
        main.assert_called_once_with()


class ExportTests(unittest.TestCase):
    def make_connection(self, batches):
        connection = MagicMock()
        cursor = connection.cursor.return_value
        cursor.description = [("id",), ("value",)]
        cursor.fetchmany.side_effect = [*batches, []]
        return connection, cursor

    def test_sequential_export_creates_directory_and_writes_all_batches(self):
        connection, cursor = self.make_connection([[(1, "first")], [(2, "second")]])
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(single, "ROOT", root),
                patch.object(single, "connect_db", return_value=connection),
            ):
                single.single_threaded_download_process()
            output = root / "data" / "transaction.csv"
            with output.open(newline="") as file:
                self.assertEqual(
                    list(csv.reader(file)),
                    [["id", "value"], ["1", "first"], ["2", "second"]],
                )
            self.assertFalse(output.with_suffix(".csv.part").exists())
        self.assertEqual(cursor.fetchmany.call_count, 3)
        cursor.close.assert_called_once_with()
        connection.close.assert_called_once_with()

    def test_sequential_empty_export_writes_the_header(self):
        connection, _ = self.make_connection([])
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(single, "ROOT", root),
                patch.object(single, "connect_db", return_value=connection),
            ):
                single.single_threaded_download_process()
            with (root / "data" / "transaction.csv").open(newline="") as file:
                self.assertEqual(list(csv.reader(file)), [["id", "value"]])
        connection.close.assert_called_once_with()

    def test_sequential_query_failure_closes_the_connection(self):
        connection, cursor = self.make_connection([])
        cursor.execute.side_effect = RuntimeError("Query failed")
        with TemporaryDirectory() as directory:
            with (
                patch.object(single, "ROOT", Path(directory)),
                patch.object(single, "connect_db", return_value=connection),
                self.assertRaisesRegex(RuntimeError, "Query failed"),
            ):
                single.single_threaded_download_process()
        connection.close.assert_called_once_with()

    def test_concurrent_export_writes_every_batch_and_finishes_workers(self):
        connection, cursor = self.make_connection([[(1, "first")], [(2, "second")]])
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with (
                patch.object(concurrent, "ROOT", root),
                patch.object(concurrent, "connect_db", return_value=connection),
            ):
                concurrent.multi_threaded_download_process()
            files = sorted((root / "data").glob("*/batch_*.csv"))
            self.assertEqual(len(files), 2)
            contents = []
            for output in files:
                with output.open(newline="") as file:
                    rows = list(csv.reader(file))
                self.assertEqual(rows[0], ["id", "value"])
                contents.extend(rows[1:])
            self.assertEqual(contents, [["1", "first"], ["2", "second"]])
            self.assertEqual(list(root.rglob("*.part")), [])
        self.assertEqual(cursor.fetchmany.call_count, 3)
        self.assertEqual(concurrent.BATCH_QUEUE.unfinished_tasks, 0)
        self.assertFalse(concurrent.FAILED.is_set())
        connection.close.assert_called_once_with()
