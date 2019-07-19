import resolvers.cloudflare as cf
import resolvers.google as google
import resolvers.quad9 as quad9

RESOLVERS = {
    'google': google,
    'cloudflare': cf,
    'quad9': quad9,
}

LOCAL_ADDR = 'localhost'
LOCAL_PORT = 53

FALLBACK_DNS_ADDR = '8.8.8.8'
FALLBACK_DNS_PORT = 53