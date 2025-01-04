#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Print section header
print_header() {
    echo -e "\n${BLUE}${BOLD}=== $1 ===${NC}\n"
}

# Print success message
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Print error message
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Print warning message
print_warning() {
    echo -e "${YELLOW}! $1${NC}"
}

# GCP Configuration
PROJECT="valid-flow-446606-m2"
ZONE="us-central1-a"
INSTANCE="fitness-prod-4-8g"

# Default to asking for build preference
SKIP_BUILD=

# --------------------------- Argument Input Handling ------------------------------------------------------------------------------------------

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-build) SKIP_BUILD=true ;;
        *) echo -e "${RED}Unknown parameter: $1${NC}"; exit 1 ;;
    esac
    shift
done

# --------------------------- Review Deployment Information -------------------------------------------------------------------------------------


# Get the parent directory of the scripts folder
PARENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Print deployment information
print_header "Deployment Information"
echo -e "Project: ${BOLD}$PROJECT${NC}"
echo -e "Zone: ${BOLD}$ZONE${NC}"
echo -e "Instance: ${BOLD}$INSTANCE${NC}"
echo -e "Directory: ${BOLD}$PARENT_DIR${NC}"

# Ask for confirmation
echo -e "\n${YELLOW}${BOLD}Do you want to proceed with the deployment? (y/N)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy]$ ]]; then
    print_warning "Deployment cancelled by user"
    exit 0
fi

# Ask about building if not specified
if [ -z "$SKIP_BUILD" ]; then
    echo -e "\n${YELLOW}${BOLD}Do you want to build and push a new image? (Y/n)${NC}"
    read -r build_response
    if [[ "$build_response" =~ ^[Nn]$ ]]; then
        SKIP_BUILD=true
    else
        SKIP_BUILD=false
    fi
fi

# --------------------------- GCloud Authentication ----------------------------------------------------------------------------------------------

# Check GCloud Authentication
print_header "Authentication Check"
if ! gcloud auth list --filter=status:ACTIVE --format="get(account)" 2>/dev/null | grep -q '^'; then
    print_warning "Not authenticated with GCloud. Running login..."
    gcloud auth login
    if [ $? -ne 0 ]; then
        print_error "GCloud authentication failed"
        exit 1
    fi
fi
print_success "GCloud authentication verified"

# Set GCloud project
print_header "Project Configuration"
echo "Setting GCloud project..."
gcloud config set project $PROJECT
print_success "Project set to $PROJECT"

# --------------------------- Env Check ------------------------------------------------------------------------------------------

# Load environment variables from .env file
if [ -f "$PARENT_DIR/.env" ]; then
    print_success "Loading environment variables from .env file"
    export $(cat "$PARENT_DIR/.env" | grep -v '^#' | xargs)
else
    print_warning "Warning: .env file not found in project root"
fi

# Check for TreeScale credentials
if [ -z "$TSCALE_USERNAME" ] || [ -z "$TSCALE_TOKEN" ]; then
    print_error "TreeScale credentials not found in environment variables"
    echo "Please set TSCALE_USERNAME and TSCALE_TOKEN in your .env file"
    exit 1
fi
print_success "TreeScale credentials verified"

# --------------------------- Docker Build ------------------------------------------------------------------------------------------

# Build and push if not skipped
if [ "$SKIP_BUILD" = false ]; then
    print_header "Building and Pushing Image"
    ./scripts/push_image.sh
    if [ $? -ne 0 ]; then
        print_error "Failed to build and push image"
        exit 1
    fi
    print_success "Image built and pushed successfully"
else
    print_warning "Skipping image build and push"
fi

# --------------------------- File Transfer To VM ------------------------------------------------------------------------------------------

# Files to copy
print_header "File Transfer"
FILES_TO_COPY=(
    "$PARENT_DIR/docker-compose.prod.yml"
    "$PARENT_DIR/.env.prod"
    "$PARENT_DIR/nginx.conf"
    "$PARENT_DIR/start.sh"
    "$PARENT_DIR/healthcheck.sh"
)

# Copy necessary files to VM
for file in "${FILES_TO_COPY[@]}"; do
    echo "Copying $(basename $file) to VM..."
    gcloud compute scp $file $INSTANCE:~/ --zone=$ZONE --project=$PROJECT
    if [ $? -eq 0 ]; then
        print_success "Copied $(basename $file)"
    else
        print_error "Failed to copy $(basename $file)"
        exit 1
    fi
done

# --------------------------- Deploy Image to VM ------------------------------------------------------------------------------------------

# Create a temporary file for docker login
echo "$TSCALE_TOKEN" > /tmp/docker_pass.txt

# Deploy to VM
print_header "Deployment"
echo "Connecting to VM and starting deployment..."
gcloud compute ssh $INSTANCE --zone=$ZONE --project=$PROJECT --command="
    # Install Docker if not installed
    if ! command -v docker &> /dev/null; then
        echo 'Installing Docker...'
        sudo apt-get update
        sudo apt-get install -y docker.io docker-compose
        sudo systemctl start docker
        sudo systemctl enable docker
    fi

    # Login to TreeScale registry
    echo 'Logging into TreeScale registry...'
    echo $TSCALE_TOKEN | sudo docker login c.tsapp.dev -u $TSCALE_USERNAME --password-stdin

    # Fix line endings and permissions
    echo 'Fixing script permissions...'
    sudo dos2unix start.sh healthcheck.sh
    sudo chmod +x start.sh healthcheck.sh

    # Pull new images first while old containers are still running
    echo 'Pulling new images...'
    sudo docker-compose -f docker-compose.prod.yml pull

    # Recreate containers one at a time
    echo 'Updating containers...'
    sudo docker-compose -f docker-compose.prod.yml up -d --remove-orphans --no-build --force-recreate

    # Clean up old images
    echo 'Cleaning up old images...'
    sudo docker image prune -f

    # Verify deployment
    echo 'Verifying deployment...'
    sudo docker-compose -f docker-compose.prod.yml ps
"

# --------------------------- Clean Up ------------------------------------------------------------------------------------------

# Clean up
rm -f /tmp/docker_pass.txt

print_header "Deployment Complete"
print_success "Your application has been deployed successfully!"
echo -e "\n${BOLD}You can access your application at:${NC}"
echo -e "https://api.getaktive.fit"