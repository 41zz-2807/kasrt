FROM node:22-alpine AS css
WORKDIR /build
COPY package*.json tailwind.config.js ./
COPY app/templates app/templates
COPY app/static/src app/static/src
RUN npm ci && npx tailwindcss -i app/static/src/input.css -o app/static/dist/app.css --minify

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 TZ=Asia/Jakarta
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY --from=css /build/app/static/dist app/static/dist
RUN useradd -m appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8000", "--access-logfile", "-", "wsgi:app"]
