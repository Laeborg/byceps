#!/bin/bash
docker-compose down
git pull
docker-compose up -d --force-recreate --build