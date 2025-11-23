#!/bin/bash
set -e # Exit immediately if any command fails

# Define the relative paths to subdirectories
TERRAFORM_DIR="./terraform"
ANSIBLE_INVENTORY_FILE="./ansible/hosts.ini"
ANSIBLE_PLAYBOOK_FILE="./ansible/playbook.yml"
export ANSIBLE_HOST_KEY_CHECKING=False

# 1. Run Terraform Apply and Capture the IP
echo "--- Running Terraform Apply ---"

terraform -chdir="$TERRAFORM_DIR" init
#terraform -chdir="$TERRAFORM_DIR" apply
terraform -chdir="$TERRAFORM_DIR" apply -auto-approve

echo "--- Capturing Instance IP ---"
if ! command -v jq &> /dev/null; then
    echo "ERROR: 'jq' is not installed. Please install it to use the robust JSON parsing."
    exit 1
fi

INSTANCE_IP=$(terraform -chdir="$TERRAFORM_DIR" output -json instance_public_ip | jq -r)

if [ -z "$INSTANCE_IP" ]; then
    echo "ERROR: Failed to capture instance IP from Terraform output. Check the output name (web_instance_ip)."
    exit 1
fi
echo "New EC2 Instance IP: $INSTANCE_IP"
echo "Access Application @ http://$INSTANCE_IP "

# 2. Update Ansible Inventory
echo "--- Updating Ansible Inventory (hosts.ini) ---"
sed -i "s/YOUR_INSTANCE_IP/$INSTANCE_IP/g" "$ANSIBLE_INVENTORY_FILE"

# 3. Run Ansible Provisioning
echo "--- Running Ansible Provisioning (Docker Install) ---"
ansible-playbook -i "$ANSIBLE_INVENTORY_FILE" "$ANSIBLE_PLAYBOOK_FILE" --private-key ~/.ssh/id_rsa

# 4. Cleanup
echo "--- Cleaning up Inventory placeholder ---"
# Revert the IP to the placeholder for the next run
sed -i "s/$INSTANCE_IP/YOUR_INSTANCE_IP/g" "$ANSIBLE_INVENTORY_FILE"

echo "--- Infrastructure Provisioned. Ready for CI/CD Deployment. ---"
echo "New EC2 Instance IP: $INSTANCE_IP"
echo "Access Application @ http://$INSTANCE_IP "
