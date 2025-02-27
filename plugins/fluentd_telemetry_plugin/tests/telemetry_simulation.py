import time
import http.server
import random
from datetime import datetime
import io
import csv
import argparse
from urllib.parse import urlparse
import threading

HEADER_DEFAULT = "generated_header"
PORT_HEADERS_AMOUNT = 6
PORT_HEADERS = ["timestamp",'source_id', 'tag', 'node_guid', 'port_guid', 'port_num']

class TelemetryData:
    def __init__(self, rows:int, columns:int, max_changes:int=None, path:str="", update_interval:float=1.0):
        self.rows = rows
        self.columns = columns
        self.update_interval = update_interval
        self.generate_headers(columns)
        if max_changes:
            self.max_changes = max_changes
        else:
            self.max_changes = len(columns)
        self.path = path
        self.data = [[random.randint(0,100) for _ in range(columns)] for _ in range(rows)]
        self.generate_ports(rows)
        self.last_update = datetime.now()
        self.running = False

    def update_date(self):
        current_time = datetime.now()
        current_timestamp = int(current_time.timestamp())
        if (current_time - self.last_update).total_seconds() > 1:
            for row in range(self.rows):
                self.data[row][0] = current_timestamp
                for col in range(self.columns):
                    if col >= self.max_changes:
                        break
                    self.data[row][col + PORT_HEADERS_AMOUNT] = random.randint(0,100)
            self.last_update = current_time

    def run_updates(self):
        if self.running:
            return # already running somewhere else
        self.running = True
        while self.running:
            self.update_date()
            time.sleep(self.update_interval)

    def stop_updates(self):
        self.running = False

    def generate_headers(self,num_of_columns:int):
        headers = [] + PORT_HEADERS
        random_index = random.randint(0,num_of_columns)
        for index in range(num_of_columns):
            headers.append(HEADER_DEFAULT + "_" + str(random_index + index * num_of_columns))
        self.headers = headers
    
    def generate_ports(self, rows_num: int):
        ports = []
        for row_index in range(rows_num):
            port_str = f'0x{random.randrange(16**16):016x}'
            # holds the prefix of each simulated csv rows , list of counters structures(will be filled further)
            self.data[row_index] = ["",port_str,"",port_str,port_str,"1"] + self.data[row_index]
        return ports
    
    def generate_csv(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.headers)
        writer.writerows(self.data)
        return output.getvalue()


class TelemetryRequestHandler(http.server.SimpleHTTPRequestHandler):

    telemetry_paths = {}

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path in self.telemetry_paths:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            telemetry_data = self.telemetry_paths[parsed_path.path]
            self.wfile.write(telemetry_data.generate_csv().encode())
        else:
            self.send_response(404)
            self.end_headers()
        
    
class TelemetryServer:
    def __init__(self, server_address:tuple, telemetry_path:list, rows:int, columns:int, max_changes:int, interval:float):
        self.server_address = server_address
        self.telemetry_data = {}
        for path in telemetry_path:
            self.telemetry_data[path] = TelemetryData(rows, columns, max_changes, path, interval)
        self.httpd = None
        self.update_thread = {}
    
    def start(self):
        print(f"Starting serving telemetry on port {self.server_address[1]}")
        for path,telemetry_data in self.telemetry_data.items():
            self.update_thread[path] = threading.Thread(target=telemetry_data.run_updates, daemon=True)
            self.update_thread[path].start()
            print(f"Serving at http://127.0.0.1:{self.server_address[1]}{path}")

        TelemetryRequestHandler.telemetry_paths = self.telemetry_data

        self.httpd = http.server.HTTPServer(self.server_address, TelemetryRequestHandler)
        self.httpd.serve_forever()

    def stop(self):
        if self.update_thread:
            for path, telemetry in self.telemetry_data.items():
                telemetry.stop_updates()
                self.update_thread[path].join()
            if self.httpd:
                self.httpd.shutdown()
                self.httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="Telemetry Server")
    parser.add_argument('--rows', type=int, default=10, help='')
    parser.add_argument('--columns', type=int, default=5, help='')
    parser.add_argument('--update_interval', type=float, default=1.0, help='')
    parser.add_argument('--max_changing', type=int, default=10, help='')
    parser.add_argument('--port', type=int, default=9007, help='')
    parser.add_argument('--paths', nargs='+', default=["/csv/metrics"], help='')

    args = parser.parse_args()
    server_address = ('', args.port)

    server = TelemetryServer(server_address, args.paths, args.rows, args.columns, args.max_changing, args.update_interval)
    try:
        server.start()
    except (KeyboardInterrupt,SystemExit):
        print("shutting down the server")
        server.stop()

if __name__ == "__main__":
    main()