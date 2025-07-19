

```aiignore
// Jenkinsfile example
pipeline {
    agent any
    
    environment {
        GITHUB_APP_ID = credentials('github-app-id')
        GITHUB_APP_PRIVATE_KEY = credentials('github-app-private-key')
        GITHUB_APP_INSTALLATION_ID = credentials('github-app-installation-id')
    }
    
    stages {
        stage('Get GitHub Token') {
            steps {
                script {
                    // Get GitHub App token
                    def token = sh(
                        script: """
                            python3 jenkins_github_app_auth.py \
                                --app-id ${GITHUB_APP_ID} \
                                --private-key-path ${GITHUB_APP_PRIVATE_KEY} \
                                --installation-id ${GITHUB_APP_INSTALLATION_ID} \
                                --output-format token
                        """,
                        returnStdout: true
                    ).trim()
                    
                    // Use token for git operations
                    withEnv(["GITHUB_TOKEN=${token}"]) {
                        sh '''
                            git config --global url."https://x-access-token:${GITHUB_TOKEN}@github.com/".insteadOf "https://github.com/"
                            git clone https://github.com/your-org/your-repo.git
                        '''
                    }
                }
            }
        }
    }
}

```
