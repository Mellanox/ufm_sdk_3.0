"""
@copyright:
    Copyright (C) Mellanox Technologies Ltd. 2021. ALL RIGHTS RESERVED.

    This software product is a proprietary product of Mellanox Technologies
    Ltd. (the "Company") and all right, title, and interest in and to the
    software product, including all associated intellectual property rights,
    are and shall remain exclusively with the Company.

    This software product is governed by the End User License Agreement
    provided with the software product.

@author: Nahum Kilim
@date:   September 20, 2021
"""

import json
import os
from flask_restful import Resource
from flask import request
import datetime
from topo_diff.topo_diff import main


def read_json_file(file_name):
    try:
        with open(file_name) as file:
            data = json.load(file)
    except Exception as ex:
        print("Exception, %s" % ex)
        data = {}
    return data


class UFMResource(Resource):
    def __init__(self):
        self.response_file = ""
        self.reports_dir = "reports"
        self.ndt_files_dir = "ndt_files"
        self.reports_list_file = os.path.join(self.reports_dir, "reports_list.json")
        self.ndts_list_file = os.path.join(self.ndt_files_dir, "ndts_list.json")
        try:
            # create file for reports list
            if not os.path.exists(self.reports_list_file):
                with open(self.reports_list_file, "w") as file:
                    json.dump([], file)

            # create file for NDTs list
            if not os.path.exists(self.ndts_list_file):
                with open(self.ndts_list_file, "w") as file:
                    json.dump([], file)

        except Exception as ex:
            print("Exception, %s" % ex)

    def get_ndt_path(self, file_name, file_type):
        return os.path.join(self.ndt_files_dir,
                            "{}_{}".format(file_type, file_name))

    def get(self):
        return read_json_file(self.response_file)

    def post(self):
        pass


def get_timestamp():
    return str(datetime.datetime.now())


class UploadMetadata(UFMResource):
    def post(self):
        try:
            json_data = request.get_json(force=True)
            for file_dict in json_data:
                # parse request
                file_name = file_dict["file_name"]
                file_content = file_dict["file"]
                file_type = file_dict["file_type"]

                # upload the file
                with open(self.get_ndt_path(file_name, file_type), "w") as file:
                    json.dump(file_content, file)

                # update ndts list
                with open(self.ndts_list_file, "r+") as file:
                    data = json.load(file)
                    entry = {"file": file_name,
                             "last_uploaded": get_timestamp(),
                             "sha-1": "abracadabra",
                             "file_type": file_type}
                    data.append(entry)
                    file.seek(0)
                    json.dump(data, file)
        except Exception as ex:
            print("Exception, %s" % ex)


class Delete(UFMResource):
    def post(self):
        try:
            json_data = request.get_json(force=True)

            # update ndts list
            with open(self.ndts_list_file, "r") as file:
                data = json.load(file)

                # iterate over request
                for file_dict in json_data:
                    file_name = file_dict["file_name"]

                    # iterate over the list of all NDTs
                    for entry in list(data):
                        if entry["file"] == file_name:
                            data.remove(entry)

                            # delete the file
                            os.remove(self.get_ndt_path(file_name, entry["file_type"]))

            # update NDTs list
            with open(self.ndts_list_file, "w") as file:
                json.dump(data, file)

        except Exception as ex:
            print("Exception, %s" % ex)


class Compare(UFMResource):
    def post(self):
        try:
            timestamp = get_timestamp()
            self.response_file = os.path.join(self.reports_dir, "report_{}.json".format(timestamp))

            # run compare
            response = main(timestamp)

            # dump result into file
            with open(self.response_file, "w") as file:
                json.dump(response, file)

            # update reports list
            with open(self.reports_list_file, "r+") as file:
                data = json.load(file)
                entry = {"report_id": len(data) + 1,
                         "timestamp": timestamp}
                data.append(entry)
                file.seek(0)
                json.dump(data, file)
        except Exception as ex:
            print("Exception, %s" % ex)


class ReportId(UFMResource):
    def __init__(self):
        super().__init__()
        try:
            with open(self.reports_list_file, "r") as file:
                self.data = json.load(file)
        except Exception as ex:
            print("Exception, %s" % ex)
            self.data = {}

    def get(self, report_id):
        try:
            for entry in self.data:
                if entry["report_id"] == int(report_id):
                    self.response_file = \
                        os.path.join(self.reports_dir,
                                     "report_{}.json".format(entry["timestamp"]))
        except Exception as ex:
            print("Exception, %s" % ex)
        finally:
            return super().get()


class Reports(UFMResource):
    def __init__(self):
        super().__init__()
        self.response_file = self.reports_list_file


class Ndts(UFMResource):
    def __init__(self):
        super().__init__()
        self.response_file = self.ndts_list_file
