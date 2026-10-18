FROM node:24.22.0-bookworm-slim@sha256:a5f4366e834695d5f363b920c104953a535d3a9864d1bdf74566a0ebe01daee5 AS dependencies
WORKDIR /app
RUN chown node:node /app
USER node
COPY --chown=node:node package.json package-lock.json .npmrc ./
RUN npm ci
FROM dependencies AS test
COPY --chown=node:node . .
CMD ["npm", "test"]
FROM test AS build
RUN npm run build
FROM nginxinc/nginx-unprivileged:stable-alpine-slim@sha256:4ac59c85c8c46d9e91eaabd2122cda4923ba380cf11f4138e389f069bcdc77a3 AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf.template /etc/nginx/nginx.conf.template
COPY docker/start-proxy.sh /opt/start-proxy.sh
USER 101:101
ENTRYPOINT ["/bin/sh", "/opt/start-proxy.sh"]
