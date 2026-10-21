#!/bin/sh
# Install the complete, checksum-pinned official npm bundle before npm executes.
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$script_dir/npm-toolchain.env"
node_binary=$(readlink -f "$(command -v node)")
install_prefix=${1:-$(dirname "$(dirname "$node_binary")")}
test -x "$install_prefix/bin/node"
test -d "$install_prefix/lib/node_modules/npm"
work_dir=$(mktemp -d)
trap 'rm -rf "$work_dir"' EXIT HUP INT TERM
archive=${2:-$work_dir/npm.tgz}
if [ "$#" -lt 2 ]; then
    curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' "$NPM_ARCHIVE_URL" --output "$archive"
fi
printf '%s  %s\n' "$NPM_ARCHIVE_SHA256" "$archive" | sha256sum --check --status
tar -xzf "$archive" -C "$work_dir"
test -f "$work_dir/package/bin/npm-cli.js"
# Replace the entire bundle, leaving no vulnerable files from the previous npm.
rm -rf "$install_prefix/lib/node_modules/npm"
mv "$work_dir/package" "$install_prefix/lib/node_modules/npm"
ln -sf ../lib/node_modules/npm/bin/npm-cli.js "$install_prefix/bin/npm"
ln -sf ../lib/node_modules/npm/bin/npx-cli.js "$install_prefix/bin/npx"
