#!/usr/bin/env bash
set -e
PYTHONPATH=src uvicorn apps.api.main:app --reload --port 8000
