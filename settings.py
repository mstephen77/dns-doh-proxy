import resolvers.cloudflare as cf
import resolvers.google as google
import resolvers.quad9 as quad9
import resolvers.dnssb as dnssb
import resolvers.securedns as securedns
import resolvers.dohli as dohli
import resolvers.hostux as hostux
import resolvers.sebyio as sebyio
import dnslibext

SETTINGS_DATA = 'settings.json'
NAMES_DATA = 'custom-names.json'

START_TIME = 0
DNS_ANSWERED = 0
DNS_ANSWER_BY_CACHE = 0
DNS_ANSWER_BY_DOH = 0
DNS_ANSWER_FROM_CUSTOM = 0
DNS_FALLBACK = 0

ENABLE_DNS_CACHE = True
TIMEOUT = 3

RESOLVERS = {
    'cloudflare': cf,
    'google': google,
    'quad9': quad9,
    'dnssb': dnssb,
    'dohli': dohli,
    'hostux': hostux,
    'sebyio': sebyio,
    # 'securedns': securedns,
}

BINDS = [
    {
        'addr': '0.0.0.0',
        'port': 53,
    }, 
    {
        'addr': '::',
        'port': 53,
        'server': dnslibext.UDPServerIPv6,
    }
]

FALLBACK_DNS_ADDR = '8.8.8.8'
FALLBACK_DNS_PORT = 53