#!/bin/bash
set -e

CONTAINER=sql2019
SA_PASSWORD='Pass@word123'
PORT=1433

echo "Connect using: Server=localhost,$PORT User=SA Password=$SA_PASSWORD"