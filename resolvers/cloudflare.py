import requests

DOMAIN = 'cloudflare-dns.com'
ENDPOINT = 'https://cloudflare-dns.com/dns-query'

def resolve(name, type):
    r = requests.get(ENDPOINT, params={
            'type': type,
            'name': name,
            'ct': 'application/dns-json',
            'cd': 'true'
        })
    r.raise_for_status()
    query = r.json()
    if query['Status'] == 0 and 'Answer' in query:
        return query['Answer']
    else:
        raise Exception('DNS resolve error, got status: {0}'.format(query['Status']))
