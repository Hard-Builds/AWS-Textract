#!/bin/bash

# Variables
IMAGE_NAME="ocrImage"
CONTAINER_NAME="ocr_image_container"
PORT_MAPPING="8000:8000"  # Map host port 8000 to container port 8000, modify if needed
DOCKERFILE_PATH="./Dockerfile"  # Assuming Dockerfile is in the current directory
MAIN_FILE="main.py"  # The entry point for your Python application

# Function to check if Docker is installed
check_docker_installed() {
    if ! [ -x "$(command -v docker)" ]; then
        echo "Docker is not installed. Please install Docker first."
        exit 1
    fi
}

# Function to build the Docker image
build_docker_image() {
    echo "Building Docker image..."
    docker build -t $IMAGE_NAME -f $DOCKERFILE_PATH .

    if [ $? -ne 0 ]; then
        echo "Docker build failed. Exiting."
        exit 1
    fi
    echo "Docker image built successfully."
}

# Function to run the Docker container
run_docker_container() {
    # Stop and remove any existing container with the same name
    if [ "$(docker ps -a -q -f name=$CONTAINER_NAME)" ]; then
        echo "Stopping and removing existing container..."
        docker rm -f $CONTAINER_NAME
    fi

    # Run the new container
    echo "Running Docker container..."
    docker run --name $CONTAINER_NAME -p $PORT_MAPPING $IMAGE_NAME

    if [ $? -eq 0 ]; then
        echo "Docker container started successfully."
        echo "Application is running. You can access it at http://localhost:$PORT_MAPPING"
    else
        echo "Failed to start Docker container. Exiting."
        exit 1
    fi
}

# Main script
check_docker_installed
build_docker_image
run_docker_container
