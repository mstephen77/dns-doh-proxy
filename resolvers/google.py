import requests

DOMAIN = 'dns.google'
ENDPOINT = 'https://dns.google/resolve'

def resolve(name, type):
    r = requests.get(ENDPOINT, params={
            'type': type,
            'name': name,
            'cd': 'true'
        })
    r.raise_for_status()
    query = r.json()
    if query['Status'] == 0:
        if 'Answer'in query:
            return query['Answer']
        else:
            return []
    else:
        raise Exception('DNS resolve error, got status: {0}'.format(query['Status']))
