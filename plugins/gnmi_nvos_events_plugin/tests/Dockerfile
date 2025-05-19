FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY tests/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tests/gnmi_simulator.py .
COPY tests/gnmi/gnmi_pb2.py gnmi/
COPY tests/gnmi/gnmi_pb2_grpc.py gnmi/
COPY tests/gnmi_ext gnmi_ext/

ENTRYPOINT ["python", "gnmi_simulator.py"]