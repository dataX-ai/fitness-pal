#!/bin/bash

# Default values
REGISTRY="c.tsapp.dev"
USERNAME="kanishka"
IMAGE_NAME="fitness-tracker"
TAG="latest"

# Full image name
FULL_IMAGE_NAME="$REGISTRY/$USERNAME/$IMAGE_NAME:$TAG"

echo "Building image: $FULL_IMAGE_NAME"
docker build -t $FULL_IMAGE_NAME .

if [ $? -eq 0 ]; then
    echo "Build successful. Pushing to registry..."
    docker push $FULL_IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        echo "Successfully pushed image to registry"
        echo "You can now run: docker-compose -f docker-compose.local.yml up"
    else
        echo "Failed to push image. Make sure you're logged in:"
        echo "docker login $REGISTRY"
    fi
else
    echo "Build failed"
    exit 1
fi 