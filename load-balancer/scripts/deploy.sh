#!/bin/bash
# Deployment script for Visey Recommender Load Balancer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-development}
LOAD_BALANCER=${2:-nginx}  # nginx or haproxy
REPLICAS=${3:-3}

echo -e "${GREEN}🚀 Deploying Visey Recommender with Load Balancer${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Load Balancer: ${YELLOW}$LOAD_BALANCER${NC}"
echo -e "Replicas: ${YELLOW}$REPLICAS${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Generate SSL certificates
generate_ssl_certs() {
    echo -e "${YELLOW}🔐 Generating SSL certificates...${NC}"
    
    mkdir -p ssl
    
    if [ ! -f "ssl/visey-recommender.crt" ]; then
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/visey-recommender.key \
            -out ssl/visey-recommender.crt \
            -subj "/C=US/ST=CA/L=San Francisco/O=Visey/CN=visey-recommender.com"
        
        # Create PEM file for HAProxy
        cat ssl/visey-recommender.crt ssl/visey-recommender.key > ssl/visey-recommender.pem
        
        echo -e "${GREEN}✅ SSL certificates generated${NC}"
    else
        echo -e "${GREEN}✅ SSL certificates already exist${NC}"
    fi
}

# Setup environment file
setup_environment() {
    echo -e "${YELLOW}⚙️  Setting up environment...${NC}"
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# WordPress Configuration
WP_BASE_URL=https://your-wordpress-site.com
WP_AUTH_TYPE=basic
WP_USERNAME=your_username
WP_PASSWORD=your_password

# Environment
ENVIRONMENT=$ENVIRONMENT
REPLICAS=$REPLICAS

# Load Balancer
LOAD_BALANCER=$LOAD_BALANCER

# Redis
REDIS_PASSWORD=changeme123

# Monitoring
GRAFANA_PASSWORD=admin123
EOF
        echo -e "${YELLOW}⚠️  Please update .env file with your WordPress credentials${NC}"
    fi
}

# Build application image
build_app() {
    echo -e "${YELLOW}🏗️  Building application image...${NC}"
    
    cd ..
    docker build -t visey-recommender:latest .
    cd load-balancer
    
    echo -e "${GREEN}✅ Application image built${NC}"
}

# Deploy with Docker Compose
deploy_docker_compose() {
    echo -e "${YELLOW}🚀 Deploying with Docker Compose...${NC}"
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Start services
    if [ "$LOAD_BALANCER" = "nginx" ]; then
        docker-compose up -d nginx-lb visey-app-1 visey-app-2 visey-app-3 redis prometheus grafana
    else
        docker-compose up -d haproxy-lb visey-app-1 visey-app-2 visey-app-3 redis prometheus grafana
    fi
    
    echo -e "${GREEN}✅ Services deployed${NC}"
}

# Deploy to Kubernetes
deploy_kubernetes() {
    echo -e "${YELLOW}☸️  Deploying to Kubernetes...${NC}"
    
    # Create namespace
    kubectl create namespace visey --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    kubectl apply -f kubernetes/redis.yaml
    kubectl apply -f kubernetes/deployment.yaml
    
    # Wait for deployment
    kubectl rollout status deployment/visey-recommender -n visey --timeout=300s
    
    echo -e "${GREEN}✅ Kubernetes deployment completed${NC}"
}

# Health check
health_check() {
    echo -e "${YELLOW}🏥 Performing health checks...${NC}"
    
    sleep 10  # Wait for services to start
    
    if [ "$LOAD_BALANCER" = "nginx" ]; then
        LB_PORT=8080
        LB_HEALTH_PATH="/nginx_health"
    else
        LB_PORT=8405
        LB_HEALTH_PATH="/health"
    fi
    
    # Check load balancer health
    if curl -f "http://localhost:$LB_PORT$LB_HEALTH_PATH" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Load balancer is healthy${NC}"
    else
        echo -e "${RED}❌ Load balancer health check failed${NC}"
        exit 1
    fi
    
    # Check application health through load balancer
    if curl -f "http://localhost/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Application is healthy through load balancer${NC}"
    else
        echo -e "${RED}❌ Application health check failed${NC}"
        exit 1
    fi
}

# Show deployment info
show_info() {
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}📊 Access URLs:${NC}"
    
    if [ "$LOAD_BALANCER" = "nginx" ]; then
        echo -e "Load Balancer: ${GREEN}http://localhost${NC}"
        echo -e "Status Page: ${GREEN}http://localhost:8080/nginx_status${NC}"
    else
        echo -e "Load Balancer: ${GREEN}http://localhost:8081${NC}"
        echo -e "Stats Page: ${GREEN}http://localhost:8404/stats${NC}"
    fi
    
    echo -e "Prometheus: ${GREEN}http://localhost:9090${NC}"
    echo -e "Grafana: ${GREEN}http://localhost:3000${NC} (admin/admin123)"
    echo ""
    echo -e "${YELLOW}📋 Useful commands:${NC}"
    echo -e "View logs: ${GREEN}docker-compose logs -f${NC}"
    echo -e "Scale app: ${GREEN}docker-compose up -d --scale visey-app-1=2${NC}"
    echo -e "Stop all: ${GREEN}docker-compose down${NC}"
}

# Main deployment flow
main() {
    check_prerequisites
    generate_ssl_certs
    setup_environment
    build_app
    
    if [ "$ENVIRONMENT" = "kubernetes" ]; then
        deploy_kubernetes
    else
        deploy_docker_compose
        health_check
    fi
    
    show_info
}

# Run main function
main