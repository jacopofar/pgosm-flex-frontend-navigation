#!/bin/zsh
./node_modules/.bin/prettier --write app.tsx
./node_modules/.bin/esbuild app.tsx --bundle --minify --sourcemap --outfile=bundle.js
python3 -m http.server