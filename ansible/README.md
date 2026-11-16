# Ansible Deployment

This folder contains Ansible automation files for DevOps Automation Hub.

- inventory.ini: Defines the target host.
- deploy.yml: Builds the Docker image and starts the application container.

## Run

ansible-playbook -i inventory.ini deploy.yml

Prerequisites:
- Ansible installed
- Docker installed and running
- Application Dockerfile configured for port 5000

This example targets localhost for demonstration.
