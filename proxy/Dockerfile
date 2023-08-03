FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="g-leo.fun"

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./gunicorn_params /etc/nginx/gunicorn_params
COPY ./run.sh /run.sh

ENV APP_HOST=app
ENV APP_PORT=8000

USER root

RUN mkdir -p /vol/static && \
    chmod 755 /vol/static && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh

VOLUME /vol/static

CMD ["/run.sh"]
