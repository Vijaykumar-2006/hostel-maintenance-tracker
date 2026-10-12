// Jenkins CI/CD pipeline for HostelCare - Hostel Maintenance Request Tracker
// Checkout -> Build (Docker) -> Test (Pytest in Docker) -> Deploy with Ansible

pipeline {
    agent any

    environment {
        IMAGE_NAME        = 'hostel-maintenance-ci'
        ANSIBLE_CONTAINER = 'ansible-docker-lab'
    }

    stages {
        stage('Checkout') {
            steps {
                echo '===== Stage 0: Checking out latest code from GitHub ====='
                // Uses the repository configured in the Jenkins job:
                // https://github.com/Vijaykumar-2006/hostel-maintenance-tracker.git
                checkout scm
            }
        }

        stage('Build') {
            steps {
                echo '===== Stage 1: Building Docker image ====='
                sh "docker build -t ${IMAGE_NAME} ."
                echo "Docker image '${IMAGE_NAME}' built successfully."
            }
        }

        stage('Test') {
            steps {
                echo '===== Stage 2: Running Pytest inside Docker ====='
                sh "docker run --rm ${IMAGE_NAME} python -m pytest test_app.py -v"
                echo 'All tests passed.'
            }
        }

        stage('Deploy with Ansible') {
            steps {
                echo '===== Stage 3: Deploying with Ansible ====='
                // Copy the latest playbook from the repo into the Ansible container
                sh "docker cp hostel-deploy.yml ${ANSIBLE_CONTAINER}:/hostel-deploy.yml"
                sh """
                    docker exec ${ANSIBLE_CONTAINER} \
                    ansible-playbook \
                    -i /inventory.ini \
                    /hostel-deploy.yml
                """
                echo 'Application deployed: http://localhost:5002'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: HostelCare CI/CD Pipeline Completed Successfully!'
        }
        failure {
            echo 'FAILURE: HostelCare CI/CD Pipeline Failed!'
        }
    }
}
