import backend.backend as backend
import time
import dnslib
import json
import requests
import threading
import settings
import random
from dnslib import server

print('DNS over HTTPS Server Proxy, Press Ctrl-C to exit.')
settings.START_TIME = round(time.time(), 0)

class CustomDNSResolver:
    def __init__(self):
        self.resolvers = []

        self.cache = {}
        self.custom_names = {}

        for k, mod in settings.RESOLVERS.items():
            self.resolvers.append({
                'name': k,
                'mod': mod,
                'count_query': 0,
                'count_answer': 0,
                'enabled': True,
            })
        
        self.load_custom_names()

    def update_ttl(self, time_passed: int):
        deletions = []
        for k, cache in self.cache.items():
            if 'TTL' in cache:
                cache['TTL'] = int(cache['TTL']) - time_passed
                if cache['TTL'] <= 0:
                    deletions.append(k)
            else:
                deletions.append(k)
        
        for deletion in deletions:
            del self.cache[deletion]

    def load_custom_names(self):
        self.custom_names = {}
        with open(settings.NAMES_DATA, 'r') as f:
            self.custom_names = json.load(f)
    
    def update_resolver_ip(self):
        updates = False

        for r in self.resolvers:
            domain = r['mod'].DOMAIN + '.'

            for i in range(len(self.resolvers)):
                update_r = False
                success_aaaa, answers_aaaa = self.fetch(domain, 'AAAA', log=False)
                success_a, answers_a = self.fetch(domain, 'A', log=False)

                if success_a and success_aaaa:
                    answers = [x for x in (answers_a + answers_aaaa) if dnslib.QTYPE[x['type']] == 'A' or dnslib.QTYPE[x['type']] == 'AAAA']
                    if len(answers) == 0:
                        continue

                    if domain not in self.custom_names or len(answers) != len(self.custom_names[domain]['answers']):
                        update_r = True
                    else:
                        for answer_i in answers:
                            exist = False
                            for answer_j in self.custom_names[domain]['answers']:
                                if answer_i['data'] == answer_j['data']:
                                    exist = True
                                    break
                            
                            if not exist:
                                update_r = True
                                break
                    
                    if update_r:
                        updates = True
                        self.custom_names[domain] = {
                            'resolver': True,
                            'locked': True,
                            'answers': answers
                        }
                        print('[DNS Server]: updated DNS records for resolver \'{0}\''.format(domain))

                    break
                
        if updates:
            with open(settings.NAMES_DATA, 'w') as f:
                json.dump(self.custom_names, f)

    def rr_resolver(self):
        random.shuffle(self.resolvers)
        self.resolvers.sort(key=lambda x: x['count_query'])
        self.resolvers[0]['count_query'] = self.resolvers[0]['count_query'] + 1
        return self.resolvers[0]
        
    def fetch(self, q_name, q_type, log=True):
        resolver = self.rr_resolver()
        success = False
        answers = []
        try:
            answers = resolver['mod'].resolve(q_name, q_type)

            if settings.ENABLE_DNS_CACHE:
                if q_name not in self.cache:
                    self.cache[q_name] = {}
                self.cache[q_name][q_type] = answers

            success = True
            if success: 
                resolver['count_answer'] = resolver['count_answer'] + 1

            if log:
                print('[DNS Server]: {0}::{1} - {2} query successful for \'{3}\''.format(resolver['name'], resolver['mod'].DOMAIN, q_type, q_name))
        except Exception:
            if log:
                print('[DNS Server]: {0}::{1} - error occured for \'{3}\''.format(resolver['name'], resolver['mod'].DOMAIN, q_type, q_name))

        return (success, answers)

    def resolve(self, request, handler):
        d = request.reply()
        q = request.get_q()
        q_type = str(dnslib.QTYPE[q.qtype])
        q_name = str(q.qname)

        if q_name in self.custom_names:
            custom_name = self.custom_names[q_name]
            if 'resolver' not in custom_name or not custom_name['resolver']:
                print('[DNS Server]: using custom record for {0} query \'{1}\''.format(q_type, q_name))

            for answer in custom_name['answers']:
                if dnslib.QTYPE[answer['type']] != q_type:
                    continue
                d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], 0, dnslib.QTYPE[answer['type']], answer['data'])))
            
            settings.DNS_ANSWERED = settings.DNS_ANSWERED + 1
            settings.DNS_ANSWER_FROM_CUSTOM = settings.DNS_ANSWER_FROM_CUSTOM + 1
            return d
        elif settings.ENABLE_DNS_CACHE and q_name in self.cache and q_type in self.cache[q_name]:
            print('[DNS Server]: using cached record for {0} query \'{1}\''.format(q_type, q_name))

            for answer in self.cache[q_name][q_type]:
                d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], 0, dnslib.QTYPE[answer['type']], answer['data'])))

            settings.DNS_ANSWERED = settings.DNS_ANSWERED + 1
            settings.DNS_ANSWER_BY_CACHE = settings.DNS_ANSWER_BY_CACHE + 1
            return d
        else:
            success = False
            for i in range(len(self.resolvers)):
                success, answers = self.fetch(q_name, q_type)
                if success:
                    for answer in answers:
                        d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], 0, dnslib.QTYPE[answer['type']], answer['data'])))

                    break

            if success:
                settings.DNS_ANSWERED = settings.DNS_ANSWERED + 1
                settings.DNS_ANSWER_BY_DOH = settings.DNS_ANSWER_BY_DOH + 1

                return d
            else:
                settings.DNS_FALLBACK = settings.DNS_FALLBACK + 1

                print('[DNS Server]: using fallback DNS for query \'{0}\''.format(q_name))
                a = dnslib.DNSRecord.parse(dnslib.DNSRecord.question(q_name).send(settings.FALLBACK_DNS_ADDR, settings.FALLBACK_DNS_PORT))
                for rr in a.rr:
                    d.add_answer(rr)

                return d

print('[DNS Server]: starting...')
r = CustomDNSResolver()
for bind in settings.BINDS:
    dns_server = 'server' in bind and bind['server'] or server.UDPServer
    s = server.DNSServer(r, port=bind['port'], address=bind['addr'], server=dns_server, logger=server.DNSLogger('-recv,-send,-request,-reply,-truncated,-data'))
    s.start_thread()

def scheduler(resolver):
    while True:
        resolver.update_resolver_ip()
        resolver.update_ttl(300)

        time.sleep(300) # 5 minutes

print('[Scheduler]: starting...')
scheduler_t = threading.Thread(target=scheduler, kwargs={'resolver': r})
scheduler_t.start()

print('[Backend]: starting...')
backend.start(r)