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
from fpdf import FPDF  # Import FPDF from fpdf module


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

    def created_pdf(self):
        self.set_display_mode("fullpage")
        self.add_page()

        # Initial coordinates for images
        x_start = 10
        y_start = 20
        image_width = 180
        image_height = 100
        spacing = 10

        # Add each image
        x = x_start
        y = y_start
        for image_path in self._images_path:
            if os.path.exists(image_path):
                self.image(
                    image_path, x=x, y=y, w=image_width, h=image_height, type="PNG"
                )

                # Update coordinates for the next image
                y += image_height + spacing

                # Check if next image exceeds page height
                if y > self.h - image_height - 20:
                    self.add_page()  # Add a new page if needed
                    y = y_start

            # Add text on a new page
        self.add_page()  # Add a new page for the text
        self.set_font("Arial", "", 12)

        output = StringIO()
        print(self._fabric_stats_list, file=output)
        text = (
            output.getvalue().strip()
        ) 

        self.multi_cell(0, 10, text)

        # Output PDF
        self.output(self._pdf_path)
