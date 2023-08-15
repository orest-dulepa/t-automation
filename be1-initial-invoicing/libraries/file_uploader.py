import requests
import json


def upload_file(invoice_id, file_path, credentials):
    data = {'grant_type': "client_credentials",
            'resource': "https://graph.microsoft.com",
            'client_id': credentials['client_id'],
            'client_secret': credentials['client_secret']}
    url = "https://login.windows.net/" + credentials['tenant_id'] + "/oauth2/token?api-version=1.0"

    r = requests.post(url=url, data=data)
    j = json.loads(r.text)

    token = j["access_token"]

    url = "https://graph.microsoft.com/v1.0/users/de2ea14e-ebf7-4d73-af3c-653214c17e18/drive/root:"
    headers = {'Authorization': "Bearer " + token}

    r = requests.get(url, headers=headers)
    j = json.loads(r.text)

    file_handle = open(file_path, 'rb')
    r = requests.put(url + "/" + invoice_id + ".pdf" + ":/content", data=file_handle, headers=headers)
    file_handle.close()
    if r.status_code == 200 or r.status_code == 201:
        return "Script completed"
    return "Something went wrong"
