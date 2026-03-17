
# docker build -t e3 -f Dockerfile .
# docker run -d --name e3 -p 443:443 e3
# docker logs -f e3
# docker rm e3 --force


# docker run -d \
#   --name e3 \
#   -v /home/miguel/freedom/e3/backend:/app/backend \
#   -p 443:443 \
#   e3

# https://us-west-1.console.aws.amazon.com/ecr/private-registry/repositories?region=us-west-1

# 509499992346.dkr.ecr.us-west-1.amazonaws.com/uw1-infopioneer-e3

# docker tag e3:latest 509499992346.dkr.ecr.us-west-1.amazonaws.com/uw1-infopioneer-e3
# aws ecr get-login-password --region us-west-1 | docker login --username AWS --password-stdin 509499992346.dkr.ecr.us-west-1.amazonaws.com

# docker push 509499992346.dkr.ecr.us-west-1.amazonaws.com/uw1-infopioneer-e3:latest

# ssh -i ~/.ssh/11222024.pem ubuntu@54.219.221.33

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# OS deps: openssl for self-signed cert, libcap2-bin for setcap, and CA bundle
RUN apt-get update && apt-get install -y --no-install-recommends \
      openssl libcap2-bin ca-certificates vim \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -d /app -s /usr/sbin/nologin e3

# Install Python deps first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY scripts/data-prep.sh .
COPY scripts/deploy-e3.sh .
COPY . .
COPY backend/storage/database/ backend/storage/database/
# Prepare any local data your script needs
RUN chmod +x data-prep.sh && ./data-prep.sh

# --- Generate self-signed TLS cert (CN=localhost + SAN for modern browsers)
# Keys live in standard locations; owned by appuser so Uvicorn can read them.
RUN mkdir -p /etc/ssl/private /etc/ssl/certs

COPY backend/security/private.server.key /etc/ssl/private/server.key
COPY backend/security/server.crt /etc/ssl/certs/server.crt

RUN mkdir -p /etc/ssl/private /etc/ssl/certs
RUN chown -R e3:e3 /etc/ssl/
RUN chown e3:e3 /etc/ssl/private/server.key /etc/ssl/certs/server.crt && \
    chmod 400 /etc/ssl/private/server.key


# Provide perms for user resource
RUN chown e3:e3 -R backend/storage/
RUN chmod 777 -R backend/storage/
RUN chmod 777 -R backend/storage/serve/uploaded_images/
RUN chmod 777 -R backend/storage/database/
RUN chmod 777 -R backend/storage/serve/


# Allow binding to privileged ports (e.g., 443) as non-root
# (Python console scripts point to the interpreter; grant the cap to python binary)
RUN setcap 'cap_net_bind_service=+ep' /usr/local/bin/python3.12 || true && \
    setcap 'cap_net_bind_service=+ep' /usr/local/bin/python || true


# Drop privileges
USER e3

EXPOSE 443

# Run Uvicorn on 443 with TLS
CMD ["uvicorn", "backend.main:app", \
     "--host", "0.0.0.0", "--port", "443", \
     "--ssl-keyfile", "/etc/ssl/private/server.key", \
     "--ssl-certfile", "/etc/ssl/certs/server.crt"]

# Keep the container running
# CMD ["tail", "-f", "/dev/null"]

# curl -k -X POST "https://e3.ldmg.org/e3/ai_agent" \
#   -H "Content-Type: application/json" \
#   -d '{"message":"Hello world","user":"Miguel"}'


# uvicorn backend.main:app --host 0.0.0.0 --port 443 --ssl-keyfile backend/security/private.server.key --ssl-certfile backend/security/server.crt
