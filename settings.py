import resolvers.cloudflare as cf
import resolvers.google as google
import resolvers.quad9 as quad9
import resolvers.dnssb as dnssb
import resolvers.securedns as securedns

NAMES_DATA = 'custom-names.json'

START_TIME = 0
DNS_ANSWERED = 0

RESOLVERS = {
    'cloudflare': cf,
    'google': google,
    'quad9': quad9,
    'dnssb': dnssb,
    'securedns': securedns,
}

LOCAL_ADDR = 'localhost'
LOCAL_PORT = 53

FALLBACK_DNS_ADDR = '8.8.8.8'
FALLBACK_DNS_PORT = 53