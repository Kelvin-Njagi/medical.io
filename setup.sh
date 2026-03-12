#!/bin/bash

# Create directories
mkdir -p ~/.streamlit

# Streamlit config
echo "\
[server]\n\
headless = true\n\
enableCORS = false\n\
port = \$PORT\n\
" > ~/.streamlit/config.toml

# Install system dependencies
apt-get update
apt-get install -y build-essential python3-dev

# Upgrade pip and install setuptools first
pip install --upgrade pip setuptools wheel