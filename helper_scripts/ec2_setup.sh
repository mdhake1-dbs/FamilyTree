#!/bin/bash
set -euo pipefail

TERRAFORM_DIR="./terraform"
ANSIBLE_INVENTORY_TEMPLATE="./ansible/hosts.ini"   
ANSIBLE_INVENTORY_FILE="./ansible/hosts.tmp"       
ANSIBLE_PLAYBOOK_FILE="./ansible/playbook.yml"
PRIVATE_KEY="${HOME}/.ssh/id_rsa"

export ANSIBLE_HOST_KEY_CHECKING=False

# Cleanup temp inventory when script exits (success or failure)
cleanup() {
  if [[ -f "$ANSIBLE_INVENTORY_FILE" ]]; then
    rm -f "$ANSIBLE_INVENTORY_FILE"
    echo "[INFO] Removed temporary inventory: $ANSIBLE_INVENTORY_FILE"
  fi
}
trap cleanup EXIT

echo "--- Running Terraform Apply ---"
terraform -chdir="$TERRAFORM_DIR" init
terraform -chdir="$TERRAFORM_DIR" apply -auto-approve

echo "--- Capturing Instance IP ---"
if ! command -v jq &>/dev/null; then
  echo "ERROR: 'jq' is not installed. Please install it and re-run."
  exit 1
fi

INSTANCE_IP=$(terraform -chdir="$TERRAFORM_DIR" output -json instance_public_ip | jq -r)
if [[ -z "$INSTANCE_IP" || "$INSTANCE_IP" == "null" ]]; then
  echo "ERROR: Failed to capture instance IP from Terraform output. Check output name and terraform state."
  exit 1
fi

echo "New EC2 Instance IP: $INSTANCE_IP"
echo "Access Application @ http://$INSTANCE_IP"

echo "--- Generating temporary Ansible inventory ---"
# If your template contains the token YOUR_INSTANCE_IP replace it; otherwise append a new web host entry
if grep -q "YOUR_INSTANCE_IP" "$ANSIBLE_INVENTORY_TEMPLATE" 2>/dev/null; then
  sed "s/YOUR_INSTANCE_IP/${INSTANCE_IP}/g" "$ANSIBLE_INVENTORY_TEMPLATE" > "$ANSIBLE_INVENTORY_FILE"
else
  # create a basic inventory from scratch (fallback)
  cat > "$ANSIBLE_INVENTORY_FILE" <<EOF
[web]
${INSTANCE_IP} ansible_user=ubuntu ansible_ssh_private_key_file=${PRIVATE_KEY}
EOF
fi
echo "[INFO] Temporary inventory written to $ANSIBLE_INVENTORY_FILE"

echo "--- Running Ansible Provisioning ---"
ansible-playbook -i "$ANSIBLE_INVENTORY_FILE" "$ANSIBLE_PLAYBOOK_FILE" --private-key "$PRIVATE_KEY"

echo "--- Ansible finished ---"
echo "App available at: http://$INSTANCE_IP"
# temp inventory will be removed by trap on exit

