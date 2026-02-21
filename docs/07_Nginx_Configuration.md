# Nginx Reverse Proxy Configuration

This guide explains the Nginx reverse proxy setup for the Card Approval Prediction project.

## Overview

Nginx acts as a reverse proxy and load balancer, providing:
- Single entry point (port 80)
- Rate limiting
- Security headers
- Request routing
- SSL termination (optional)
- Access logs

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Client                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Nginx (Port 80)                           │
│                  Reverse Proxy + Rate Limiting               │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─► /                    → API (8000)
             ├─► /api/v1/predict     → API (8000) [5 req/s]
             ├─► /mlflow/            → MLflow (5000)
             ├─► /airflow/           → Airflow (8080)
             ├─► /grafana/           → Grafana (3000)
             ├─► /prometheus/        → Prometheus (9090)
             ├─► /health             → API Health
             └─► /metrics            → API Metrics
```

## Access URLs

With Nginx running, access all services through port 80:

| Service | Direct URL | Nginx URL |
|---------|-----------|-----------|
| API Docs | http://localhost:8000/docs | http://localhost/docs |
| API Predict | http://localhost:8000/api/v1/predict | http://localhost/api/v1/predict |
| MLflow | http://localhost:5000 | http://localhost/mlflow/ |
| Airflow | http://localhost:8080 | http://localhost/airflow/ |
| Grafana | http://localhost:3000 | http://localhost/grafana/ |
| Prometheus | http://localhost:9090 | http://localhost/prometheus/ |
| Health Check | http://localhost:8000/health | http://localhost/health |
| Metrics | http://localhost:8000/metrics | http://localhost/metrics |

## Rate Limiting

Nginx implements rate limiting to protect the API:

### General API Endpoints
- **Rate**: 10 requests/second per IP
- **Burst**: 20 requests
- **Applies to**: All API endpoints

### Prediction Endpoint
- **Rate**: 5 requests/second per IP
- **Burst**: 10 requests
- **Applies to**: `/api/v1/predict`

**Example:**
```bash
# This will be rate limited after 5 requests/second
for i in {1..20}; do
  curl http://localhost/api/v1/predict -X POST -H "Content-Type: application/json" -d @test_payload.json
done
```

**Response when rate limited:**
```
HTTP/1.1 503 Service Temporarily Unavailable
<html>
<head><title>503 Service Temporarily Unavailable</title></head>
<body>
<center><h1>503 Service Temporarily Unavailable</h1></center>
<hr><center>nginx</center>
</body>
</html>
```

## Security Headers

Nginx adds security headers to all responses:

```
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: no-referrer-when-downgrade
```

## Configuration

The Nginx configuration is located at `nginx/nginx.conf`.

### Key Settings

**Worker Processes:**
```nginx
worker_processes auto;  # Uses all available CPU cores
```

**Gzip Compression:**
```nginx
gzip on;
gzip_comp_level 6;
gzip_types text/plain text/css application/json application/javascript;
```

**Timeouts:**
```nginx
proxy_connect_timeout 60s;
proxy_send_timeout 60s;
proxy_read_timeout 60s;
keepalive_timeout 65;
```

## Testing Nginx

### Test Configuration Syntax

```bash
# Test config without restarting
docker exec nginx nginx -t
```

### Reload Configuration

```bash
# Reload without downtime
docker exec nginx nginx -s reload
```

### View Access Logs

```bash
# Real-time access logs
docker exec nginx tail -f /var/log/nginx/access.log

# Error logs
docker exec nginx tail -f /var/log/nginx/error.log
```

### Check Nginx Status

```bash
# Nginx status (from inside Docker network)
docker exec nginx wget -qO- http://localhost/nginx_status
```

## Testing Through Nginx

### Test API Health

```bash
# Direct
curl http://localhost:8000/health

# Through Nginx
curl http://localhost/health
```

### Test Prediction

```bash
# Through Nginx
curl -X POST http://localhost/api/v1/predict \
  -H "Content-Type: application/json" \
  -d @test_payload.json
```

### Test Rate Limiting

```bash
# Send 20 requests rapidly
for i in {1..20}; do
  echo "Request $i:"
  curl -s -o /dev/null -w "%{http_code}\n" http://localhost/health
  sleep 0.05
done
```

## SSL/TLS Configuration (Optional)

To enable HTTPS, update `nginx/nginx.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # ... rest of configuration
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

Mount SSL certificates in `docker-compose.yml`:

```yaml
nginx:
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    - ./nginx/ssl:/etc/nginx/ssl:ro
```

## Load Balancing (Optional)

To add multiple API instances:

```yaml
# docker-compose.yml
api-1:
  # ... same as api service
  container_name: card-approval-api-1

api-2:
  # ... same as api service
  container_name: card-approval-api-2
```

Update `nginx/nginx.conf`:

```nginx
upstream api {
    least_conn;  # Load balancing method
    server api-1:8000;
    server api-2:8000;
}
```

## Monitoring Nginx

### Prometheus Metrics

Install nginx-prometheus-exporter:

```yaml
# docker-compose.yml
nginx-exporter:
  image: nginx/nginx-prometheus-exporter:latest
  command:
    - '-nginx.scrape-uri=http://nginx/nginx_status'
  ports:
    - "9113:9113"
  depends_on:
    - nginx
```

Add to `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
```

### Access Logs Analysis

```bash
# Top 10 IPs
docker exec nginx awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# Top 10 endpoints
docker exec nginx awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# Response codes
docker exec nginx awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# Average response time (if logged)
docker exec nginx awk '{sum+=$10; count++} END {print sum/count}' /var/log/nginx/access.log
```

## Troubleshooting

### Nginx Not Starting

```bash
# Check logs
docker logs nginx

# Test configuration
docker exec nginx nginx -t

# Common issues:
# - Port 80 already in use
# - Invalid nginx.conf syntax
# - Missing upstream services
```

### 502 Bad Gateway

```bash
# Check if backend services are running
docker ps | grep -E "api|mlflow|airflow|grafana|prometheus"

# Check backend service logs
docker logs api
docker logs mlflow

# Check Nginx error logs
docker logs nginx
```

### 503 Service Unavailable

This is usually rate limiting. Check:

```bash
# View error logs
docker logs nginx | grep "limiting requests"

# Adjust rate limits in nginx.conf if needed
```

### WebSocket Connection Issues

Ensure WebSocket headers are set:

```nginx
proxy_http_version 1.1;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection "upgrade";
```

## Best Practices

1. **Use Nginx in production** - Single entry point, better security
2. **Enable rate limiting** - Protect against abuse
3. **Monitor access logs** - Track usage patterns
4. **Use SSL/TLS** - Encrypt traffic in production
5. **Set appropriate timeouts** - Prevent hanging connections
6. **Enable gzip** - Reduce bandwidth usage
7. **Add health checks** - Monitor Nginx availability

## Performance Tuning

### Worker Connections

```nginx
events {
    worker_connections 2048;  # Increase for high traffic
}
```

### Caching (Optional)

```nginx
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=1g inactive=60m;

location /api/v1/model-info {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_pass http://api;
}
```

### Buffer Sizes

```nginx
proxy_buffer_size 4k;
proxy_buffers 8 4k;
proxy_busy_buffers_size 8k;
```

## Next Steps

- Configure SSL/TLS for production
- Set up load balancing for multiple API instances
- Add Nginx metrics to Grafana
- Implement custom error pages
- Configure log rotation

## References

- [Nginx Documentation](https://nginx.org/en/docs/)
- [Nginx Rate Limiting](https://www.nginx.com/blog/rate-limiting-nginx/)
- [Nginx Security Headers](https://www.nginx.com/blog/hardening-nginx-ssl-tls/)
