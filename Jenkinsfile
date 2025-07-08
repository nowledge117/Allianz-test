// IMPORTANT: Update with your AWS Account ID and region
def AWS_ACCOUNT_ID = '812073017047'
def ECR_REGISTRY = '812073017047.dkr.ecr.us-west-1.amazonaws.com/demo-app' // IMPORTANT: REPLACE with your ECR URL from the script output
def ECR_REPO_NAME = 'demo-app'
def AWS_REGION = 'us-west-1'

pipeline {
    agent {
        kubernetes {
            cloud 'kubernetes'
            yaml '''
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: aws-kubectl
    image: amazon/aws-cli-kubectl:latest
    command:
    - cat
    tty: true
  - name: docker
    image: docker:20.10.17
    command:
    - cat
    tty: true
    volumeMounts:
    - mountPath: /var/run/docker.sock
      name: docker-sock
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
'''
            defaultContainer 'aws-kubectl'
        }
    }

    environment {
        IMAGE_URI = "${ECR_REGISTRY}/${ECR_REPO_NAME}:${BUILD_NUMBER}"
    }

    stages {
        stage('Determine Deployment Colors') {
            steps {
                script {
                    def current_color_json = sh(returnStdout: true, script: "kubectl get svc demo-app-service -o jsonpath='{.spec.selector.color}'").trim()
                    
                    if (current_color_json == "blue") {
                        env.LIVE_COLOR = "blue"
                        env.INACTIVE_COLOR = "green"
                    } else {
                        env.LIVE_COLOR = "green"
                        env.INACTIVE_COLOR = "blue"
                    }
                    echo "Current Live Color: ${env.LIVE_COLOR}. Deploying to Inactive Color: ${env.INACTIVE_COLOR}"
                }
            }
        }

        stage('Confirm Image in ECR') {
            steps {
                echo "Verifying image ${env.IMAGE_URI} exists in ECR..."
                script {
                    def image_manifest = sh(
                        returnStdout: true,
                        script: """
                            aws ecr batch-get-image --repository-name ${ECR_REPO_NAME} --image-ids imageTag=${BUILD_NUMBER} --region ${AWS_REGION} --query 'images[].imageManifest' --output text
                        """
                    ).trim()

                    if (image_manifest == "") {
                        error("Failed to find image tag ${BUILD_NUMBER} in ECR after push.")
                    } else {
                        echo "Successfully verified image exists."
                    }
                }
            }
        }

        stage('Deploy to Inactive Environment') {
            steps {
                script {
                    echo "Deploying image ${env.IMAGE_URI} to color: ${env.INACTIVE_COLOR}"
                    def manifest = readFile 'kubernetes/app/deployment.yaml'
                    manifest = manifest.replace('{{COLOR}}', env.INACTIVE_COLOR)
                    manifest = manifest.replace('{{IMAGE_URI}}', env.IMAGE_URI)
                    
                    sh "echo '''${manifest}''' | kubectl apply -f -"
                    sh "kubectl rollout status deployment/demo-app-${env.INACTIVE_COLOR} --timeout=3m"
                }
            }
        }

        stage('Approval Gate') {
            steps {
                echo "The '${env.INACTIVE_COLOR}' deployment is ready for testing."
                echo "You can test it internally via the 'demo-app-service-green-internal' service."
                input "Promote '${env.INACTIVE_COLOR}' to live production?"
            }
        }

        stage('Promote to Live (Switch Traffic)') {
            steps {
                echo "Switching live traffic to ${env.INACTIVE_COLOR}"
                sh "kubectl patch service demo-app-service -p '{\"spec\":{\"selector\":{\"color\":\"${env.INACTIVE_COLOR}\"}}}'"
                echo "Traffic is now directed to the ${env.INACTIVE_COLOR} deployment."
            }
        }

        stage('Cleanup Old Deployment (Optional)') {
            steps {
                echo "You can now safely delete the old deployment: kubectl delete deployment demo-app-${env.LIVE_COLOR}"
            }
        }
    }
}