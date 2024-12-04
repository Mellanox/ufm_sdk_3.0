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
# pylint: disable=missing-module-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring

import os
from io import StringIO
from fpdf import FPDF
import pandas as pd
from tabulate import tabulate


class PDFCreator(FPDF):
    def __init__(self, pdf_path, pdf_header, images_path, fabric_stats_list):
        super().__init__()
        self._pdf_path = pdf_path
        self._pdf_header = pdf_header
        self._images_path = images_path
        self._fabric_stats_list = fabric_stats_list

    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, self._pdf_header, 0, 1, "C")

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def add_images(self):
        """Adds images to the PDF."""
        x_start = 10
        y_start = 20
        image_width = 180
        image_height = 100
        spacing = 10

        x, y = x_start, y_start
        for image_path in self._images_path:
            if os.path.exists(image_path):
                self.image(
                    image_path, x=x, y=y, w=image_width, h=image_height, type="PNG"
                )
                y += image_height + spacing
                if y > self.h - image_height - 20:
                    self.add_page()
                    y = y_start

    def add_text(self):
        self.set_font("Arial", "", 12)
        output = StringIO()
        print(self._fabric_stats_list, file=output)
        text = output.getvalue().strip()
        self.multi_cell(0, 10, text)

    def add_list_of_dicts_as_text(self, data_list, title=None, headers=None):
        """Adds a list of dictionaries to the PDF as aligned text."""
        if not data_list or not isinstance(data_list, list):
            return

        if title:
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, title, 0, 1, "C")
            self.ln(5)

        self.set_font("Arial", "", 10)

        table_data = [
            [str(item.get(header, "")) for header in headers] for item in data_list
        ]
        table_str = tabulate(table_data, headers=headers, tablefmt="plain")

        self.multi_cell(0, 10, table_str)
        self.ln(10)

    def add_dataframe_as_text(self, data_frame, title=None):
        """Adds a DataFrame to the PDF as aligned text without row numbers."""
        if not isinstance(data_frame, pd.DataFrame) or data_frame.empty:
            return

        if title:
            self.set_font("Arial", "B", 12)
            self.cell(0, 10, title, 0, 1, "C")
            self.ln(5)

        num_columns = len(data_frame.columns)
        if num_columns > 10:
            self.set_font("Arial", "", 8)  # Smaller font for many columns
        elif num_columns > 5:
            self.set_font("Arial", "", 10)
        else:
            self.set_font("Arial", "", 12)

        # Converting and removing the row number as it is not needed
        table_str = tabulate(
            data_frame.values, headers=data_frame.columns, tablefmt="plain"
        )

        self.multi_cell(0, 10, table_str)
        self.ln(10)

    def create_pdf(self, data_frames_with_titles, lists_to_add):
        """Generates the PDF with images, text, and multiple tables."""
        self.set_display_mode("fullpage")
        self.add_page()
        self.add_images()
        self.add_page()

        for title, df in data_frames_with_titles:
            self.add_dataframe_as_text(data_frame=df, title=title)

        for data_list, title, headers in lists_to_add:
            self.add_list_of_dicts_as_text(data_list, title, headers)

        self.add_text()

        self.output(self._pdf_path)
