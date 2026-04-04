FROM zauberzeug/nicegui:latest
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --break-system-packages
COPY . .
EXPOSE 8080
CMD ["python", "main.py"]