pipeline {
    agent any

    stages {
        stage('Run transfer validation tests') {
            steps {
                bat 'if not exist reports mkdir reports'
                bat 'py -m pytest -v --junitxml=reports\\pytest-results.xml'
            }
        }
    }

    post {
        always {
            junit testResults: 'reports/pytest-results.xml',
                  allowEmptyResults: true

            archiveArtifacts artifacts: 'reports/pytest-results.xml',
                             allowEmptyArchive: true

            echo 'Post-build test report published.'
        }
    }
}
