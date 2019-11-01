import requests
from typing import Dict
import os
import dateutil.parser
from datetime import datetime, timezone


def main() -> None:
    token = None

    def query_api(endpoint: str, data: Dict = None, delete: bool = False
                  ) -> requests.Request:
        headers = {}
        #headers = {'Content-Type': 'application/json'}
        if token:
            headers['Authorization'] = f'JWT {token}'

        url = f'https://hub.docker.com/v2/{endpoint}'
        print(f'Fetching {url}')
        if data:
            resp = requests.post(url, data=data, headers=headers)
        elif delete:
            resp = requests.delete(url, headers=headers)
        else:
            resp = requests.get(url, headers=headers)

        if not resp.ok:
            raise Exception(
                f"Error querying docker api ({resp.status_code}): {resp.text}")

        return resp

    token_req_data = {
        'username': 'camas',
        'password': os.environ.get('DOCKER_PASSWORD'),
    }
    token_resp = query_api('users/login/', token_req_data)
    token = token_resp.json()['token']

    images_resp = query_api(f'repositories/camas/aur-ci/tags/?page_size=100')
    images = images_resp.json()['results']
    for image in images:
        name = image['name']
        last_updated = dateutil.parser.parse(image['last_updated'])
        diff = datetime.now(timezone.utc) - \
            last_updated.replace(tzinfo=timezone.utc)

        if name == 'latest':
            continue

        if diff.total_seconds() / (60 * 60) < 25:
            continue

        print(f"Deleting tag {name}")
        query_api(f"repositories/camas/aur-ci/tags/{name}/", delete=True)


if __name__ == '__main__':
    main()
