FROM node:24.22.0-bookworm-slim@sha256:91acba91b842bec0bf7ea6f5e09c644c7ccad72c4996ed9616d861d1c7cd60d4 AS dependencies
COPY docker/bootstrap-npm.sh docker/npm-toolchain.env /opt/npm-toolchain/
ADD --checksum=sha256:dd77c48eb845f4856c2cdba347cfb52bd877a2655a1ea48ff0c4796e3df9dd7b https://registry.npmjs.org/npm/-/npm-11.21.1.tgz /tmp/npm-toolchain.tgz
RUN sh /opt/npm-toolchain/bootstrap-npm.sh /usr/local /tmp/npm-toolchain.tgz && rm /tmp/npm-toolchain.tgz
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
