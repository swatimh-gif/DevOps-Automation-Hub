# DevOps notes
App: Flask (app.py, port 5000, /health, tests in tests/).

- Git: git log --oneline --graph --all
- Tests: python -m pytest tests -q
- Jenkins: Pipeline job, SCM = this repo, Script Path Jenkinsfile
- Ansible (WSL/Linux): cd ansible && ansible-playbook -i inventory playbook.yml --ask-become-pass
- Docker: docker build -t devops-automation-hub:1.0.0 .  then  docker run -d -p 5000:5000 devops-automation-hub:1.0.0
- Kubernetes: kubectl apply -f k8s/  then  kubectl get deployments,services,pods -o wide
- Scale: kubectl scale deployment devops-hub --replicas=5 ; kubectl get pods ; kubectl scale deployment devops-hub --replicas=3
- Rollback: kubectl set image deployment/devops-hub devops-hub=devops-automation-hub:broken ; kubectl rollout undo deployment/devops-hub