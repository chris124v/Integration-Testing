FROM nginx:1.27-alpine
# La plantilla usa ${PEDIDOS_URL}; la imagen oficial de nginx la sustituye al arrancar.
COPY templates/default.conf.template /etc/nginx/templates/default.conf.template
COPY public/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=3s --timeout=3s --retries=20 CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
