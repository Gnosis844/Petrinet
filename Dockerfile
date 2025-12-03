# --- Giai đoạn builder ---
FROM python:3.14-rc-slim AS builder

WORKDIR /app

# Cài các gói hệ thống cần thiết để build lxml hoặc các packages khác
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Sao chép requirements và cài đặt Python packages
COPY PetriNetBDDs/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Giai đoạn cuối cùng ---
FROM python:3.14-rc-slim

# Cài đặt các thư viện runtime cần thiết cho lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Sao chép các gói đã cài đặt từ builder
COPY --from=builder /usr/local/lib/python3.14/site-packages/ /usr/local/lib/python3.14/site-packages/

# Sao chép toàn bộ mã nguồn ứng dụng
COPY PetriNetBDDs/src/ ./src/

# Sao chép các file PNML ra cwd (không thay đổi script)
COPY PetriNetBDDs/src/*.pnml ./

# Lệnh mặc định để chạy ứng dụng
CMD ["python", "src/run_task3_experiments.py"]
