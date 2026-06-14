#
# Copyright © 2009-2026 NVIDIA CORPORATION & AFFILIATES. ALL RIGHTS RESERVED.
#
# This software product is a proprietary product of Nvidia Corporation and its affiliates
# (the "Company") and all right, title, and interest in and to the software
# product, including all associated intellectual property rights, are and
# shall remain exclusively with the Company.
#
# This software product is governed by the End User License Agreement
# provided with the software product.
#
# ufm-state-mirror: the StateMirror init container (Redis -> emptyDir restore)
# and runtime sidecar (emptyDir -> Redis mirror). The same image runs both;
# the role is selected by the container command:
#   restore (init):  python -m state_mirror.restore
#   mirror (sidecar): python -m state_mirror.mirror

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY state_mirror /app/state_mirror

# Non-root: the sidecar only needs read/write on the shared emptyDir, which is
# mounted with appropriate ownership by the pod spec.
RUN useradd --create-home --uid 10001 statemirror
USER 10001

# Liveness/readiness/metrics endpoint.
EXPOSE 9180

# Default to the sidecar; the init container overrides command to run restore.
ENTRYPOINT ["python", "-m"]
CMD ["state_mirror.mirror"]
