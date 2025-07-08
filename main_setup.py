# main_setup.py (Significant Updates)

import os
import subprocess
import sys
import time
import json

# --- Configuration ---
TERRAFORM_DIR = "terraform"
KUBERNETES_DIR = "kubernetes"
CLUSTER_NAME = "my-demo-cluster"
HELM_CHART_NAME = "jenkins"
HELM_RELEASE_NAME = "jenkins"
JENKINS_NAMESPACE = "jenkins"
JENKINS_SERVICE_ACCOUNT = "jenkins" # As defined in our values.yaml
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-west-1") # Match your terraform var

# --- Helper Functions ---
def run_command(command, cwd=".", check=True, capture_output=False):
    """Runs a command, streams output, and can capture it."""
    print(f"\n\033[94mRunning command: {' '.join(command)} in {cwd}\033[0m")
    try:
        if capture_output:
            result = subprocess.run(
                command,
                cwd=cwd,
                check=check,
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print(f"\033[93mSTDERR:\n{result.stderr}\033[0m")
            return result.stdout.strip()

        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )
        for line in process.stdout:
            print(line, end="")
        process.wait()
        if check and process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        return process.returncode
    except FileNotFoundError:
        print(f"\033[91mError: Command '{command[0]}' not found. Is it installed and in your PATH?\033[0m")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\033[91mCommand failed with exit code {e.returncode}\033[0m")
        sys.exit(1)

def setup_infrastructure():
    """Initializes and applies Terraform configuration."""
    print("\n--- Step 1: Setting up EKS, ECR, and IAM with Terraform ---")
    run_command(["terraform", "init", "-upgrade"], cwd=TERRAFORM_DIR)
    run_command([
        "terraform", "apply", "-auto-approve",
        f"-var=cluster_name={CLUSTER_NAME}",
        f"-var=aws_region={AWS_REGION}"
    ], cwd=TERRAFORM_DIR)
    print("\033[92mTerraform apply completed successfully.\033[0m")

def get_terraform_outputs():
    """Gets key values from terraform output."""
    print("\n--- Step 2: Retrieving outputs from Terraform ---")
    output_json = run_command(
        ["terraform", "output", "-json"],
        cwd=TERRAFORM_DIR,
        capture_output=True
    )
    return json.loads(output_json)

def configure_kubectl():
    """Configures kubectl to connect to the new EKS cluster."""
    print("\n--- Step 3: Configuring kubectl ---")
    run_command([
        "aws", "eks", "update-kubeconfig",
        "--name", CLUSTER_NAME,
        "--region", AWS_REGION
    ])
    print("\033[92m`kubectl` is now configured to connect to the EKS cluster.\033[0m")

# In main_setup.py

def deploy_jenkins_and_configure_iam(jenkins_role_arn):
    """Deploys Jenkins and annotates its service account for IRSA."""
    print("\n--- Step 4: Deploying Jenkins and Configuring IAM Role ---")
    run_command(["kubectl", "create", "namespace", JENKINS_NAMESPACE], check=False)
    
    print("\nAdding Jenkins Helm repo...")
    # CORRECT REPO NAME: jenkinsci
    run_command(["helm", "repo", "add", "jenkinsci", "https://charts.jenkins.io"])
    run_command(["helm", "repo", "update"])
    
    print(f"\nDeploying Jenkins release '{HELM_RELEASE_NAME}'...")
    run_command([
        "helm", "upgrade", "--install", HELM_RELEASE_NAME,
        # CORRECT CHART REFERENCE: jenkinsci/jenkins
        "jenkinsci/jenkins",
        "--namespace", JENKINS_NAMESPACE,
        "-f", f"{KUBERNETES_DIR}/jenkins/values.yaml"
    ])
    # ... rest of the function is the same ...
    
    print("\nWaiting for Jenkins service account to be created by Helm...")
    time.sleep(15) # Give Helm a moment to create the resources

    print(f"Annotating service account '{JENKINS_SERVICE_ACCOUNT}' with IAM Role: {jenkins_role_arn}")
    run_command([
        "kubectl", "annotate", "serviceaccount",
        "-n", JENKINS_NAMESPACE,
        JENKINS_SERVICE_ACCOUNT,
        f"eks.amazonaws.com/role-arn={jenkins_role_arn}",
        "--overwrite" # Use overwrite in case we are re-running the script
    ])
    print("\033[92mJenkins service account annotated for ECR access.\033[0m")
    
    print("\nRestarting Jenkins pod to apply the IAM role annotation...")
    run_command(["kubectl", "rollout", "restart", "statefulset/jenkins", "-n", JENKINS_NAMESPACE])


def show_final_instructions(tf_outputs):
    """Prints the final steps for the user."""
    # ... (This function remains mostly the same, but can now show the ECR URL)
    print("\n\n--- Setup Complete! ---")
    # ... (get jenkins url, password, etc) ...
    print(f"\n\n\033[1mECR Repository URL (for your Jenkinsfile):\033[0m {tf_outputs['ecr_repository_url']['value']}")
    print("\n\033[1mNext Steps:\033[0m")
    print("1. The `Jenkinsfile` in this project is now configured to use this ECR repo.")
    print("2. Log in to Jenkins, create a 'Pipeline' job, point it to your Git repo, and run it!")


if __name__ == "__main__":
    setup_infrastructure()
    outputs = get_terraform_outputs()
    configure_kubectl()
    deploy_jenkins_and_configure_iam(outputs['jenkins_iam_role_arn']['value'])
    show_final_instructions(outputs)