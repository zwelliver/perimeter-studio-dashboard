#!/bin/bash
# Quick script to manually run the forecast pipeline checker

cd "$(dirname "$0")"
source venv/bin/activate
python3 check_forecast_pipeline.py
