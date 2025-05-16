FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY tests/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the simulator code and protobuf files
COPY tests/gnmi_simulator.py .
COPY tests/gnmi/gnmi_pb2.py gnmi/
COPY tests/gnmi/gnmi_pb2_grpc.py gnmi/
COPY tests/gnmi_ext gnmi_ext/

# Expose the gNMI port
EXPOSE 9339

# Set entrypoint
ENTRYPOINT ["python", "gnmi_simulator.py"]