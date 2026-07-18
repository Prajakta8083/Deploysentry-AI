// Jenkinsfile — defines the CI/CD pipeline for a sample application.
// The key part for this project is the "DeploySentry Check" stage:
// it runs BEFORE deployment and can stop the pipeline automatically.

pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Pulling latest code...'
                // checkout scm   <- uncomment when connected to a real repo
            }
        }

        stage('Build & Test') {
            steps {
                echo 'Running build and tests...'
                // sh 'pytest'   <- your normal test suite would run here
            }
        }

        stage('DeploySentry Check') {
            steps {
                script {
                    // This calls jenkins_check.py with details about the change.
                    // In a real pipeline, these values come from git diff / PR metadata
                    // instead of being hardcoded like this example.
                    def exitCode = sh(
                        script: '''
                            python3 jenkins_check.py \
                                --files "auth/login.py" \
                                --lines 40 \
                                --branch feature/fix-login \
                                --pr true
                        ''',
                        returnStatus: true
                    )

                    if (exitCode == 0) {
                        echo "✅ APPROVED — proceeding with deployment"
                    } else if (exitCode == 2) {
                        echo "⚠️ FLAGGED FOR REVIEW — pausing for manual approval"
                        input message: "DeploySentry flagged this change. Approve manually to continue?"
                    } else {
                        error "⛔ BLOCKED by DeploySentry policy — halting pipeline"
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying to production...'
                // kubectl apply -f k8s/deployment.yaml   <- real deploy step
            }
        }
    }
}
