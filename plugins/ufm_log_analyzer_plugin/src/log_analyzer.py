#
# Copyright © 2013-2024 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# author: Samer Deeb
# date:   Mar 02, 2024
#
# pylint: disable=broad-exception-caught
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring

import argparse
from functools import partial
import glob
from multiprocessing import Process
import os
import re
import sys
import time
from pathlib import Path
import traceback
from typing import Callable, List, Set, Tuple


from log_analyzers.base_analyzer import BaseImageCreator
from logs_extraction.directory_extractor import DirectoryExtractor
from log_analyzers.ufm_top_analyzer import UFMTopAnalyzer
from logs_extraction.tar_extractor import DumpFilesExtractor
from log_parsing.log_parser import LogParser
from log_parsing.logs_regex import logs_regex_csv_headers_list
from logs_csv.csv_handler import CsvHandler

from log_analyzers.ufm_log_analyzer import UFMLogAnalyzer
from log_analyzers.ufm_health_analyzer import UFMHealthAnalyzer
from log_analyzers.ibdiagnet_log_analyzer import IBDIAGNETLogAnalyzer
from log_analyzers.events_log_analyzer import EventsLogAnalyzer
from log_analyzers.console_log_analyzer import ConsoleLogAnalyzer
from log_analyzers.rest_api_log_analyzer import RestApiAnalyzer
from log_analyzers.link_flapping_analyzer import LinkFlappingAnalyzer

from pdf_creator import PDFCreator
from utils.common import delete_files_by_types

import logger as log

LOGS_TO_EXTRACT = [
    "event.log",
    "ufmhealth.log",
    "ufm.log",
    "ibdiagnet2.log",
    "console.log",
    "rest_api.log"
]

DIRECTORIES_TO_EXTRACT = [
    "telemetry_samples"
]

def run_both_functions(parser_func, action_func, save_func):
    parser_func(action_func)
    save_func()


def create_parsers_processes(log_files_and_regex: List[
            Tuple[str, List[str], Callable[[Tuple], None], Callable]
        ],):
    """
    Per log files, creates the log parser process class that will 
    handle that log.
    """
    processes = []
    for log_file, regex_list_and_fn, action_func, save_func in log_files_and_regex:
        parser = LogParser(log_file, regex_list_and_fn)
        process = Process(
            target=run_both_functions,
            args=(
                parser.parse,
                action_func,
                save_func,
            ),
        )
        processes.append(process)
    return processes


def run_parsers_processes(processes:List[Process]):
    """
    Runs all the parsing process and waits for the to finish
    """
    start_time = time.perf_counter()
    for process in processes:
        process.start()
    for process in processes:
        process.join()
    end_time = time.perf_counter()
    total_run_time = end_time - start_time
    log.LOGGER.debug(f"It took {total_run_time:.3f} seconds to parse all the logs")


def create_logs_regex_csv_handler_list(logs: Set[str]):
    """
    Creates a list of tuples where each is a log location, the regex we should
    apply on it and a csv handler to use the matched results.
    """
    result_list = []
    pattern_of_gz = r"\.\d+\.gz$"
    for path in logs:
        base_filename = os.path.basename(path)
        base_filename = re.sub(pattern_of_gz, "", base_filename)
        for filename, patterns_and_fn, csv_headers in logs_regex_csv_headers_list:
            if base_filename == filename:
                file_as_path = Path(path)
                cur_path_suffix = file_as_path.suffix
                if cur_path_suffix == ".gz":
                    csv_path = file_as_path.with_suffix(".csv")
                else:
                    csv_path = file_as_path.with_suffix(cur_path_suffix + ".csv")
                csv_handler = CsvHandler(csv_headers, csv_path)
                result_list.append((path, patterns_and_fn,
                                    csv_handler.add_line, csv_handler.save_file))
    return result_list


def sorting_logs(log_path):
    """
    This function is used to sorted the logs making sure
    the result order is log and after that the gz files
    by order
    """
    base_name = os.path.basename(log_path)
    count = 0
    for c in base_name:
        count += ord(c)
    return count


def get_files_in_dest_by_type(location: str,
                              base_name: str,
                              extraction_level: int,
                              file_type="csv"):
    """
    Return a list of all the files by type that were parsed and part of the current
    extraction level requested
    """
    files_by_type = glob.glob(os.path.join(location, f"*.{file_type}"))
    matched_files = [file for file in files_by_type if base_name in os.path.basename(file)]
    full_paths = [os.path.abspath(file) for file in matched_files]
    sorted_files = sorted(full_paths, key=sorting_logs)
    sliced_files = sorted_files[: (extraction_level + 1)]
    return sliced_files


def parse_args():
    """parses the CLI arguments"""
    parser = argparse.ArgumentParser(
        description="Analyze ufm logs . If no option is passed, "
        "we assume you would like to do all ops"
    )
    parser.add_argument(
        "-l",
        "--location",
        help="Location of dump tar file.",
        required=True,
        action="store",
    )
    parser.add_argument(
        "-d",
        "--destination",
        default="/tmp/ufm_log_analyzer",
        help="Where should be place the extracted logs and the CSV files.",
    )
    parser.add_argument(
        "--extract-level",
        default=1,
        type=int,
        help="Depth of logs tar extraction, default is 1",
    )
    parser.add_argument(
        "--hours",
        help="How many hours to process from last logs. Default is 6 hours",
        default=6,
        type=int,
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Should an interactive Ipython session start. Default is False",
    )
    parser.add_argument(
        "--skip-tar-extract",
        action="store_true",
        help="If the location is to an existing extracted tar, skip the " \
            "tar extraction and only copy the needed logs. Default is False"
    )
    parser.add_argument(
        '--interval',
        type=str,
        nargs='?',
        default='1h',
        choices=['1min', '10min', '1h', '24h'],
        help="Time interval for the graphs. Choices are: '1min'- Every minute, "
             "'10min'- Every ten minutes, '1h'- Every one hour, "
             "'24h'- Every 24 hours. Default is '1H'."
    )
    parser.add_argument(
        '--log-level',
        help="Tool log level, default is CRITICAL",
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    )

    return parser.parse_args()


def add_extraction_levels_to_files_set(
    files_to_extract: List[str], extraction_level: int
):
    """
    For a given log name e.g. ufm.log, we need to also
    look for the gz logs, this function returns a list of
    all the logs including the gz, according to the extraction
    level.
    """
    combined_logs_named = list(files_to_extract)
    for file in files_to_extract:
        for i in range(1, extraction_level + 1):
            new_file_name = file + f".{i}.gz"
            combined_logs_named.append(new_file_name)
    return combined_logs_named


def create_analyzer(parsed_args, full_extracted_logs_list,
                    ufm_top_analyzer_obj, log_name,  analyzer_clc):
    """
    Create the analyzer based on the given inputs.
    Also adds it to the top_analyzer so it can be used
    in the full report.
    Returns the created analyzer
    """
    if log_name in full_extracted_logs_list:
        log_csvs = get_files_in_dest_by_type(parsed_args.destination,
                                             log_name,
                                             parsed_args.extract_level)
        analyzer = analyzer_clc(log_csvs, parsed_args.hours, parsed_args.destination)
        ufm_top_analyzer_obj.add_analyzer(analyzer)
        return analyzer
    return None


if __name__ == "__main__":
    args = parse_args()
    log.setup_logger("Logs_analyzer", args.log_level)
    log.LOGGER.info("Starting analysis, this might take a few minutes"
                    " depending on the amount of data in the logs")
    if not os.path.exists(args.location):
        log.LOGGER.critical(f"-E- Cannot find dump file at {args.location}")
        sys.exit(1)
    ufm_top_analyzer = UFMTopAnalyzer()
    try:
        # Extracting the files from the tar
        full_logs_list = add_extraction_levels_to_files_set(
            LOGS_TO_EXTRACT, args.extract_level
        )
        log.LOGGER.debug(f"Going to extract {full_logs_list} logs from {args.location}")
        if args.skip_tar_extract:
            extractor = DirectoryExtractor(args.location)
        else:
            extractor = DumpFilesExtractor(args.location)

        logs_to_work_with, failed_extract = extractor.extract_files(
            full_logs_list, DIRECTORIES_TO_EXTRACT, args.destination
        )

        if len(failed_extract) > 0:
            log.LOGGER.debug(f"Failed to get some logs - {failed_extract}, skipping them")
        logs_regex_csv_handler_list = create_logs_regex_csv_handler_list(
            logs_to_work_with
        )
        # Parsing the logs into CSV files
        parsers_processes = create_parsers_processes(logs_regex_csv_handler_list)
        run_parsers_processes(parsers_processes)
        log.LOGGER.debug("Done saving all CSV files")


        # Setting the time granularity for the graphs
        BaseImageCreator.time_interval = args.interval

        # Analyze the CSV and be able to query the data
        start = time.perf_counter()
        log.LOGGER.debug("Starting analyzing the data")
        partial_create_analyzer = partial(create_analyzer,
                                          parsed_args=args,
                                          full_extracted_logs_list=full_logs_list,
                                          ufm_top_analyzer_obj=ufm_top_analyzer)

        # Creating the analyzer for each log
        # By assigning them, a user can query the data via
        # the interactive session
        ibdiagnet_analyzer = partial_create_analyzer(log_name="ibdiagnet2.log",
                                                     analyzer_clc=IBDIAGNETLogAnalyzer)

        event_log_analyzer = partial_create_analyzer(log_name="event.log",
                                                     analyzer_clc=EventsLogAnalyzer)

        ufm_health_analyzer = partial_create_analyzer(log_name="ufmhealth.log",
                                                     analyzer_clc=UFMHealthAnalyzer)

        ufm_log_analyzer = partial_create_analyzer(log_name="ufm.log",
                                                   analyzer_clc=UFMLogAnalyzer)

        console_log_analyzer = partial_create_analyzer(log_name="console.log",
                                                       analyzer_clc=ConsoleLogAnalyzer)

        rest_api_log_analyzer = partial_create_analyzer(log_name="rest_api.log",
                                                        analyzer_clc=RestApiAnalyzer)
        second_telemetry_samples = get_files_in_dest_by_type(args.destination,
                                                                 "secondary_",
                                                                 1000,
                                                                 "gz")
        if len(second_telemetry_samples):

            links_flapping_analyzer = LinkFlappingAnalyzer(second_telemetry_samples,
                                                       args.destination)
            ufm_top_analyzer.add_analyzer(links_flapping_analyzer)
        else:
            links_flapping_analyzer = None # pylint: disable=invalid-name
        end = time.perf_counter()
        log.LOGGER.debug(f"Took {end-start:.3f} to load the parsed data")

        all_images_outputs_and_title = ufm_top_analyzer.full_analysis()
        png_images =[]
        images_and_title_to_present = []
        for image_title in all_images_outputs_and_title:
            image, title = image_title
            if image.endswith(".png"):
                png_images.append(image)
            else:
                images_and_title_to_present.append((image, title))
        # Next section is to create a summary PDF
        pdf_path = os.path.join(args.destination, "UFM_Dump_analysis.pdf")
        pdf_header = (
            f"{os.path.basename(args.location)}, hours={args.hours}"
        )

        used_ufm_version = console_log_analyzer.ufm_versions
        text_to_show_in_pdf = f"Used ufm version in console log {used_ufm_version}"
        fabric_info = "fabric info:" + os.linesep + str(ibdiagnet_analyzer.get_fabric_size()) \
                        if ibdiagnet_analyzer else "No Fabric Info found" # pylint: disable=invalid-name
        if links_flapping_analyzer:
            link_flapping = links_flapping_analyzer.get_link_flapping_last_week() \
                            if links_flapping_analyzer else "No link flapping info"
            text_to_show_in_pdf += os.linesep + str(fabric_info) + os.linesep + \
            "Link Flapping:" + os.linesep + str(link_flapping)

        critical_events_burst = event_log_analyzer.get_critical_event_bursts()
        critical_events_text = "The minute           event_type     event    count" # pylint: disable=invalid-name
        for critical_event in critical_events_burst:
            timestamp = critical_event['timestamp']
            event_type = critical_event['event_type']
            event = critical_event['event']
            counter = critical_event['count']
            event_text = f"{timestamp} {event_type} {event} {counter}"
            critical_events_text = critical_events_text + os.linesep + event_text

        text_to_show_in_pdf += os.linesep + os.linesep + "More than 5 events burst over a minute:" \
            + os.linesep + critical_events_text

        # PDF creator gets all the images and to add to the report
        pdf = PDFCreator(pdf_path, pdf_header, png_images, text_to_show_in_pdf)
        pdf.created_pdf()
        # Generated a report that can be located in the destination
        log.LOGGER.info("Analysis is done, please see the following outputs:")
        for image, title in images_and_title_to_present:
            log.LOGGER.info(f"{title}: {image}")
        log.LOGGER.info(f"Summary PDF was created! you can open here at {pdf_path}")
        # Clean some unended files created during run
        files_types_to_delete = set()
        files_types_to_delete.add("png") #png images created for PDF report
        files_types_to_delete.add("log") #logs taken from the logs
        files_types_to_delete.add("csv") #tmp csv + telemetery samples
        files_types_to_delete.add("gz") #gz files of logs and samples
        delete_files_by_types(args.destination, files_types_to_delete)

    except Exception as exc:
        print("-E-", str(exc))
        traceback.print_exc()
        sys.exit(1)
