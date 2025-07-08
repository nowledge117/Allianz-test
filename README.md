aws-eks-jenkins-automation/
├── main_setup.py               # Main Python script to orchestrate everything
├── main_teardown.py            # Python script to destroy all resources
├── requirements.txt            # Python dependencies
├── README.md                   # Instructions and explanation (like this document)
│
├── terraform/
│   ├── main.tf                 # Main Terraform configuration for EKS
│   ├── variables.tf            # Terraform variables
│   ├── outputs.tf              # Terraform outputs
│   └── versions.tf             # Pinned provider versions
│
├── kubernetes/
│   ├── jenkins/
│   │   └── values.yaml         # Custom configuration for the Jenkins Helm chart
│   └── app/
│       ├── deployment.yaml     # Template for the app deployment (Blue/Green)
│       ├── service-blue-green.yaml # The main service that switches traffic
│       └── service-green.yaml  # A "testing" service for the green deployment
│
├── sample-app/
│   ├── Dockerfile
│   ├── index.js
│   └── package.json
│
└── Jenkinsfile                 # The pipeline definition for the Blue/Green deployment