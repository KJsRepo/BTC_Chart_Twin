import requests
import json
import re


def get_url(html_string):
    match = re.search('<input.*value="(.+?)".*id="myInput"', html_string)
    if match:
        return match.group(1)
    else:
        return None

def submit_file(file_path, server_url):
    try:
        with open(file_path, 'rb') as f:
            data = {'submit': 'Upload'}
            files = {'fileToUpload': f}
            response = requests.post(server_url, data=data, files=files)
            response.raise_for_status()
            return response
    except requests.exceptions.HTTPError as err:
        print(err)




response = submit_file('file.png', 'http://nostr.build/upload.php')
##url = '<input value="https://nostr.build/i/5281.png" id="myInput" style="width: 235px;">'

print(get_url(response.text))
print('---------------------------------------------------------')
print(response.text)