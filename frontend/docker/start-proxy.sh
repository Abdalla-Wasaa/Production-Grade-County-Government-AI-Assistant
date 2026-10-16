#!/bin/sh
set -eu
resolver=$(awk '$1 == "nameserver" {print $2; exit}' /etc/resolv.conf)
case "$resolver" in
  ""|*[!0-9a-fA-F:.]*) echo "Proxy DNS configuration unavailable." >&2; exit 1 ;;
esac
case "$resolver" in *:*) resolver="[$resolver]" ;; esac
sed "s/@RESOLVER@/$resolver/g" /etc/nginx/nginx.conf.template > /tmp/nginx.conf
exec nginx -c /tmp/nginx.conf -g 'daemon off;'
