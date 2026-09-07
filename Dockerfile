FROM python:3.9.18-slim

WORKDIR /workspace

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install pip==23.3.2 setuptools==65.5.0 wheel==0.38.4
RUN pip install gym==0.21.0 --no-build-isolation
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/jpmorganchase/abides-jpmc.git#subdirectory=abides-core
RUN pip install git+https://github.com/jpmorganchase/abides-jpmc.git#subdirectory=abides-markets
RUN pip install git+https://github.com/jpmorganchase/abides-jpmc.git#subdirectory=abides-gym

COPY . .

CMD ["bash"]