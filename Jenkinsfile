// Needs Python 3 + git on the Jenkins agent PATH. Docker stage is optional (UNSTABLE if docker is missing).
// Auto-trigger: SCM polling. For instant builds add a GitHub webhook to http://<jenkins>/github-webhook/

def run(String cmd) {
    if (isUnix()) { sh cmd } else { bat cmd }
}

pipeline {
    agent any

    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        timestamps()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        IMAGE_NAME = 'devops-automation-hub'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                script {
                    env.SHORT_SHA = (env.GIT_COMMIT ?: 'local').take(7)
                    env.IMAGE_TAG = "1.0.${env.BUILD_NUMBER}-${env.SHORT_SHA}"
                    echo "Version tag: ${env.IMAGE_TAG}"
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    run('python -m pip install --upgrade pip')
                    run('python -m pip install -r requirements.txt pytest')
                }
            }
        }

        stage('Test') {
            steps { script { run('python -m pytest tests -q --junitxml=test-results.xml') } }
            post {
                always { junit allowEmptyResults: true, testResults: 'test-results.xml' }
            }
        }

        stage('Package') {
            steps {
                script {
                    run('mkdir dist')
                    run("git archive --format=zip -o dist/devops-automation-hub-${env.IMAGE_TAG}.zip HEAD")
                }
            }
        }

        stage('Archive Artifact') {
            steps { archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true }
        }

        stage('Docker Build') {
            steps {
                catchError(buildResult: 'SUCCESS', stageResult: 'UNSTABLE') {
                    script { run("docker build -t ${env.IMAGE_NAME}:${env.IMAGE_TAG} .") }
                }
            }
        }
    }

    post {
        success { echo "Build ${env.BUILD_NUMBER} OK - artifact archived, tag ${env.IMAGE_TAG}" }
        failure { echo 'Build failed - check the console output.' }
    }
}