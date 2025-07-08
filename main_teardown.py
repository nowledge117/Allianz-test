import os
import subprocess

# --- Configuration ---
TERRAFORM_DIR = "terraform"
CLUSTER_NAME = "my-eks-demo-cluster"
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-west-1")

def run_command(command, cwd="."):
    """Runs a command and handles errors."""
    print(f"\n\033[94mRunning command: {' '.join(command)}\033[0m")
    result = subprocess.run(command, cwd=cwd)
    if result.returncode != 0:
        print(f"\033[91mCommand failed with exit code {result.returncode}\033[0m")
        # Don't exit, try to continue cleanup
    return result.returncode

def destroy_infrastructure():
    """Destroys all infrastructure created by Terraform."""
    print("\n--- Tearing down all AWS resources ---")
    # Terraform destroy can be very slow, so we don't stream output here.
    # It provides its own progress updates.
    run_command([
        "terraform", "destroy", 
        "-auto-approve", 
        f"-var=cluster_name={CLUSTER_NAME}",
        f"-var=aws_region={AWS_REGION}"
    ], cwd=TERRAFORM_DIR)
    print("\033[92mInfrastructure teardown complete.\033[0m")

if __name__ == "__main__":
    print("\033[91mWARNING: This will destroy all AWS resources created by this project (EKS Cluster, VPC, etc.).\033[0m")
    confirm = input("Are you sure you want to continue? (yes/no): ")
    if confirm.lower() == "yes":
        destroy_infrastructure()
    else:
        print("Teardown cancelled.")