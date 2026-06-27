FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY mcp-server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем MCP-сервер
COPY mcp-server/ ./mcp-server/

# Копируем memory
COPY memory/ ./memory/

# Копируем team.py и departments
COPY team.py .
COPY departments/ ./departments/

# Порты
EXPOSE 8000

# По умолчанию — MCP-сервер
CMD ["python", "mcp-server/server.py"]
