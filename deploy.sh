#!/usr/bin/env sh

# Environment
SERVER_PROJECT_ROOT=/home/bot/projects/misis-admission-bot

# Pull all changes from src_bots repo
cd ./src_bots && git pull origin main && cd ..

# Send files to the production server
rsync -av --delete ./ misis-bot:${SERVER_PROJECT_ROOT}

# SSH into the server and redeploy using Docker Compose
# shellcheck disable=SC2029
ssh misis-bot "cd ${SERVER_PROJECT_ROOT} && docker compose up -d --build"

# Get logs from Docker Compose and display them here
# shellcheck disable=SC2029
ssh misis-bot "cd ${SERVER_PROJECT_ROOT} && docker compose logs -f"
