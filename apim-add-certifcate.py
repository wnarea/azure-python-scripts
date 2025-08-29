import requests
import json
import elita_resources
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.keyvault.models import AccessPolicyEntry, Permissions

# Set up Azure credentials
credential = DefaultAzureCredential()
token = credential.get_token("https://management.azure.com/.default").token
api_version = "2020-06-01-preview"
env = "test"

kv_subscription_id = '71d00b98-02b3-47df-961f-b2516cbb33ca'

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {token}"
}

# Define permissions
permissions = Permissions(
    keys=["get", "list"],
    secrets=["get", "list"],
    certificates=["get", "list"]
)

# Define the REST API endpoint and headers
for resource in elita_resources.elita_apim_test:
    subscription_id = resource["subscriptionId"]
    resource_group_name = resource["resourceGroup"]
    service_name = resource["name"]
    region = resource["region"]
    certificate_id = "elita-function-apps"
    kv_subscription_id = resource["elita"]["subscriptionId"]
    kv_resource_group_name = resource["elita"]["resourceGroup"]

    endpoint = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.ApiManagement/service/{service_name}?api-version={api_version}"
    # Make the GET request
    response = requests.get(endpoint, headers=headers)
    if response.status_code == 200:

      principal_id = response.json()['identity']['principalId']
      tenant_id = response.json()['identity']['tenantId']
      print(f'Principal Id: {principal_id}')
      # print(f"{response.json()}")

      # Initialize KeyVaultManagementClient
      keyvault_client = KeyVaultManagementClient(credential, kv_subscription_id)
      key_vault_name = f"kv-elita-{env}-{region}"
      
      print(f"Resource Group:{resource_group_name}, KeyVault:{key_vault_name}")
      key_vault = keyvault_client.vaults.get(kv_resource_group_name, key_vault_name)

      # Create an access policy entry
      access_policy = AccessPolicyEntry(
          tenant_id=tenant_id,
          object_id=principal_id,
          permissions=permissions
      )

      key_vault.properties.access_policies.append(access_policy)
      # Apply the updated access policies
      poller = keyvault_client.vaults.begin_create_or_update(
          resource_group_name=resource_group_name,
          vault_name=key_vault_name,
          parameters=key_vault
      )

      # Wait for the operation to complete
      vault = poller.result()

      print(f"Access policy added to Key Vault '{key_vault_name}'.")
      
      json_body = {
        "properties": {
          "keyVault": {
            "secretIdentifier" :f"https://kv-elita-{env}-{region}.vault.azure.net/secrets/elita-function-apps"
          }
        }
      }

      endpoint = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.ApiManagement/service/{service_name}/certificates/{certificate_id}?api-version={api_version}"
      # Make the GET request
      response = requests.put(endpoint, json=json_body, headers=headers)

      # Handle the response
      if response.status_code == 200:
          print(f"{service_name} Success!")
          body = response.json()        
      else:
          print(f"{service_name}, Error: {response.status_code}")
          print(f"\t{response.text}")

    else:
        print(f"{service_name}, Error: {response.status_code}")
        print(f"\t{response.text}")