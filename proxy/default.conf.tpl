upstream django_app{
    server ${APP_HOST}:${APP_PORT};
}
server {
    listen 80;
    listen [::]:80;

    server_tokens off;

     location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }

    set $domain "https://${DOMAIN}";

	location / {
            return 301 $domain$request_uri;
        }
}

server {
    listen 443 default_server ssl;
    listen [::]:443 ssl;
    
    set $domain "${DOMAIN}";

    ssl_certificate /etc/nginx/ssl/live/$domain/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/$domain/privkey.pem;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static {
        alias /vol/static;
    }

    location / {
        include                 /etc/nginx/gunicorn_params;
        proxy_pass              http://django_app;
        client_max_body_size    200M;
    }
}
