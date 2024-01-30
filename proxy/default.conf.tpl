upstream django_app{
    server ${APP_HOST}:${APP_PORT};
}

server {
    listen 8000;
    listen [::]:8000;

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
