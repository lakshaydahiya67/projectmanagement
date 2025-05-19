#!/bin/bash

# Create a temporary nginx config file
cat > /tmp/updated_nginx_conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Frame-Options SAMEORIGIN;
    
    # Frontend static files
    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API proxy
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }
    
    # Admin site proxy
    location /admin/ {
        proxy_pass http://backend:8000/admin/;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }
    
    # Static files for frontend React app
    location /static/ {
        alias /usr/share/nginx/html/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }
    
    # Backend static files - serve directly from the mounted volume
    location /backend/static/ {
        alias /usr/share/nginx/html/backend/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
        try_files $uri $uri/ =404;
    }
    
    # Media files proxy for backend
    location /media/ {
        proxy_pass http://backend:8000/media/;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }
    
    # WebSocket proxy for Django Channels
    location /ws/ {
        proxy_pass http://backend:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_read_timeout 86400s;     # 24 hours to handle long-lived connections
        proxy_send_timeout 86400s;     # 24 hours
        proxy_buffering off;           # Disable proxy buffering for WebSockets
    }
}
EOF

# Copy the updated config to the frontend container
docker cp /tmp/updated_nginx_conf frontend:/etc/nginx/conf.d/default.conf

# Restart nginx in the frontend container
docker exec -it frontend nginx -s reload

echo "Nginx configuration updated and reloaded!"
