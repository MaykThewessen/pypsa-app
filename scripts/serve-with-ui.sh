#!/bin/bash
# Automated script to build frontends and serve pypsa-app with full UI
# Usage: pypsa-app-ui [--rebuild] [pypsa-app serve options...]

set -e

PYPSA_APP_SOURCE="/Users/mayk/pypsa-app"
PYPSA_APP_INSTALLED="/Users/mayk/.local/share/uv/tools/pypsa-app/lib/python3.13/site-packages/pypsa_app"
STATIC_DIR="$PYPSA_APP_INSTALLED/backend/static"

# Check for --rebuild flag
REBUILD=false
ARGS=()
for arg in "$@"; do
    if [ "$arg" = "--rebuild" ]; then
        REBUILD=true
    else
        ARGS+=("$arg")
    fi
done

# Check if static files exist
if [ -d "$STATIC_DIR/app" ] && [ -d "$STATIC_DIR/map" ] && [ "$REBUILD" = false ]; then
    echo "==> Frontend already built, skipping build (use --rebuild to force)"
else
    echo "==> Building app frontend..."
    cd "$PYPSA_APP_SOURCE/frontend/app"
    npm ci --silent
    npm run build

    echo "==> Building map frontend..."
    cd "$PYPSA_APP_SOURCE/frontend/map"
    npm ci --silent
    npm run build

    echo "==> Copying static files to installed location..."
    mkdir -p "$STATIC_DIR"
    cp -r "$PYPSA_APP_SOURCE/src/pypsa_app/backend/static/"* "$STATIC_DIR/"
fi

echo "==> Starting pypsa-app server..."
echo "    App: http://localhost:8000"
echo "    API: http://localhost:8000/api/docs"
pypsa-app serve "${ARGS[@]}"
