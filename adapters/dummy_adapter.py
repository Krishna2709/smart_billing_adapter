import requests

class DUMMYAdapter:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.dummybilling.com'

    def create_customer(self, data: dict) -> str:
        # Prepare the headers with API key
        headers = {'X-API-Key': self.api_key, 'Content-Type': 'application/json'}
        # Make the API call to create a customer
        response = requests.post(f'{self.base_url}/customers', json=data, headers=headers)
        # Assuming the response contains the created customer data
        if response.status_code == 201:
            return response.json()['id']  # Return the provider id
        else:
            response.raise_for_status()

    def get_invoice(self, inv_id: str) -> dict:
        # Prepare the headers with API key
        headers = {'X-API-Key': self.api_key}
        # Make the API call to get an invoice
        response = requests.get(f'{self.base_url}/invoices/{inv_id}', headers=headers)
        # Assuming the response contains the invoice data
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()