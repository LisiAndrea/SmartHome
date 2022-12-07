#!/bin/bash

## Delete .ev files in each folder
echo "Deleting files"
rm .env
rm Consumer/.env
rm Manager/.env
rm Orchestrator/.env

## Create an empty env file
echo "Creating files"
touch .env
touch Consumer/.env
touch Manager/.env
touch Orchestrator/.env

## parse .env.default
while IFS= read -r l
do
    [ -z "$l" ] && continue
    if ! [[ "$l" == *"###"* ]]; then
        if [[ "$l" == "CONSUMER"* ]]; then
            echo $l >> Consumer/.env
        elif [[ "$l" == "MANAGER"* ]]; then
            echo $l >> Manager/.env
        elif [[ "$l" == "ORCHESTRATOR"* ]]; then
            echo $l >> Orchestrator/.env
        else
            echo $l >> .env
            echo "Error!"
        fi
    fi
done < .env.default
echo "Done!"

#docker-compose up -d --build