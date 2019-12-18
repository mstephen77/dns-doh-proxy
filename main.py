import backend.backend as backend
import time
import dnslib
import json
import requests
import threading
import settings
from dnslib import server

print('DNS over HTTPS Server Proxy, Press Ctrl-C to exit.')
settings.START_TIME = round(time.time(), 0)

class CustomDNSResolver:
    def __init__(self):
        self.resolvers = []
        self.cache = {}

        for k, mod in settings.RESOLVERS.items():
            print('[DNS Server]: adding resolver {0}::{1}'.format(k, mod.DOMAIN))
            self.resolvers.append({
                'name': k,
                'mod': mod,
                'count': 0,
            })

    def update_ttl(self, time_passed: int):
        for cache in self.cache:
            if 'TTL' in cache:
                cache['TTL'] = int(cache['TTL']) - time_passed
                if cache['TTL'] <= 0:
                    del cache
            else:
                del cache

    def rr_resolver(self):
        self.resolvers.sort(key=lambda x: x['count'])
        self.resolvers[0]['count'] = self.resolvers[0]['count'] + 1
        return self.resolvers[0]
        
    def resolve(self, request, handler):
        d = request.reply()
        q = request.get_q()
        q_type = str(dnslib.QTYPE[q.qtype])
        q_name = str(q.qname)
        custom_names = {}

        with open(settings.NAMES_DATA, 'r') as f:
            custom_names = json.load(f)

        if q_name in custom_names:
            print('[DNS Server]: using custom record for query \'{0}\''.format(q_name))
            for answer in custom_names[q_name]['answers']:
                if dnslib.QTYPE[answer['type']] != q_type:
                    continue
                d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], 0, dnslib.QTYPE[answer['type']], answer['data'])))
            
            settings.DNS_ANSWERED = settings.DNS_ANSWERED + 1
            settings.DNS_ANSWER_FROM_CUSTOM = settings.DNS_ANSWER_FROM_CUSTOM + 1
            return d
        elif q_name in self.cache:
            print('[DNS Server]: using cached record for query \'{0}\''.format(q_name))

            for answer in self.cache[q_name]:
                d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], 0, dnslib.QTYPE[answer['type']], answer['data'])))

            settings.DNS_ANSWERED = settings.DNS_ANSWERED + 1
            settings.DNS_ANSWER_BY_CACHE = settings.DNS_ANSWER_BY_CACHE + 1
            return d
        else:
            success = False
            for i in range(len(self.resolvers)):
                resolver = self.rr_resolver()
                try:
                    answers = resolver['mod'].resolve(q_name, q_type)
                    self.cache[q_name] = answers
                    for answer in answers:
                        d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], 0, dnslib.QTYPE[answer['type']], answer['data'])))

                    success = True
                    print('[DNS Server]: {0}::{1} - query successful for \'{2}\''.format(resolver['name'], resolver['mod'].DOMAIN, q_name))
                except Exception:
                    print('[DNS Server]: {0}::{1} - error occured for \'{2}\''.format(resolver['name'], resolver['mod'].DOMAIN, q_name))

                if success:
                    break

            if success:
                settings.DNS_ANSWERED = settings.DNS_ANSWERED + 1
                settings.DNS_ANSWER_BY_CACHE = settings.DNS_ANSWER_BY_CACHE + 1
                return d
            else:
                print('[DNS Server]: using fallback DNS for query \'{0}\''.format(q_name))
                a = dnslib.DNSRecord.parse(dnslib.DNSRecord.question(q_name).send(settings.FALLBACK_DNS_ADDR, settings.FALLBACK_DNS_PORT))
                for rr in a.rr:
                    d.add_answer(rr)

                settings.DNS_FALLBACK = settings.DNS_FALLBACK + 1
                return d

print('[DNS Server]: starting...')
r = CustomDNSResolver()
for bind in settings.BINDS:
    dns_server = 'server' in bind and bind['server'] or server.UDPServer
    s = server.DNSServer(r, port=bind['port'], address=bind['addr'], server=dns_server, logger=server.DNSLogger('-recv,-send,-request,-reply,-truncated,-data'))
    s.start_thread()

def update_resolver_ns():
    while True:
        with open(settings.NAMES_DATA, 'r') as f:
            custom_ns = json.load(f)

        updates = False
        for domain, data in custom_ns.items():
            if not data['resolver']:
                continue

            success = False
            for k, mod in settings.RESOLVERS.items():
                update_r = False
                try:
                    answers_a = mod.resolve(domain, 'A')
                    answers_aaaa = mod.resolve(domain, 'AAAA')
                    answers = answers_aaaa + answers_a
                    if len(answers) != len(data['answers']):
                        update_r = True

                    for answer_i in answers:
                        exist = False
                        for answer_j in data['answers']:
                            if answer_i['data'] == answer_j['data']:
                                exist = True
                                break
                        
                        if not exist:
                            update_r = True
                            break

                    if update_r:
                        updates = True
                        data['answers'] = answers
                        print('[Scheduler]: updated DNS records for resolver {0}'.format(domain))

                    success = True
                except Exception:
                    print('[Scheduler]: error occured at {0} for \'{1}\'!'.format(k, domain))

                if success:
                    break
                
        if updates:
            with open(settings.NAMES_DATA, 'w') as f:
                json.dump(custom_ns, f)

        time.sleep(300) # 5 minutes

def check_cache_ttl(resolver: CustomDNSResolver):
    while True:
        resolver.update_ttl(60)
        time.sleep(60)

print('[Scheduler]: starting...')
update_resolver_t = threading.Thread(target=update_resolver_ns)
update_resolver_t.start()
check_cache_ttl_t = threading.Thread(target=check_cache_ttl, kwargs={'resolver': r})
check_cache_ttl_t.start()

print('[Backend]: starting...')
backend.start(r)