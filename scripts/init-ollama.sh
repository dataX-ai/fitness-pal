#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Waiting for Ollama to start...${NC}"
sleep 10

echo -e "${YELLOW}Pulling Llama model...${NC}"
gcloud compute ssh fitness-prod-8v-16g --zone=us-central1-b --command="
    # Wait for Ollama to be ready
    while ! curl -s http://localhost:11434/api/version > /dev/null; do
        echo 'Waiting for Ollama API...'
        sleep 5
    done

    # Pull the model
    sudo docker exec kanishka_ateulerlabs_com_ollama_1 ollama run hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_L
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully pulled Llama model!${NC}"
else
    echo -e "${RED}Failed to pull Llama model${NC}"
    exit 1
fi 