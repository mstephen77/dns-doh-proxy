import requests

DOMAIN = 'doh.dns.sb'
ENDPOINT = 'https://doh.dns.sb/dns-query'

def resolve(name, type):
    r = requests.get(ENDPOINT, params={
            'type': type,
            'name': name,
            'cd': 'false'
        })
    r.raise_for_status()
    query = r.json()
    if query['Status'] == 0: #NOERROR
        if 'Answer'in query:
            return query['Answer']
        else:
            return []
    elif query['Status'] == 3: #NXDOMAIN
        return []
    else:
        raise Exception('DNS resolve error, got status: {0}'.format(query['Status']))
