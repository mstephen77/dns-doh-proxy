import backend.backend as backend
import time
import dnslib
import json
import requests
import threading
import settings
from dnslib import server

class SpecialResolver:
    def resolve(self, request, handler):
        d = request.reply()
        q = request.get_q()
        q_type = str(dnslib.QTYPE[q.qtype])
        q_name = str(q.qname)
        custom_ns = {}

        with open('custom-ns.json', 'r') as f:
            custom_ns = json.load(f)

        if q_name in custom_ns:
            print('Using custom nameserver for query \'{0}\'!'.format(q_name))
            for answer in custom_ns[q_name]['answers']:
                if dnslib.QTYPE[answer['type']] != q_type:
                    continue
                d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], answer['TTL'], dnslib.QTYPE[answer['type']], answer['data'])))
            
            return d
        else:
            success = False
            for k, mod in settings.RESOLVERS.items():
                try:
                    answers = mod.resolve(q_name, q_type)                    
                    for answer in answers:
                        d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], answer['TTL'], dnslib.QTYPE[answer['type']], answer['data'])))

                    success = True
                    print('[{0}] - DNS query successful for \'{1}\'!'.format(k, q_name))
                except Exception:
                    print('[{0}] - An error occured for \'{1}\'!'.format(k, q_name))

                if success:
                    break

            if success:
                return d
            else:
                print('Using fallback DNS for query \'{0}\'!'.format(q_name))
                a = dnslib.DNSRecord.parse(dnslib.DNSRecord.question(q_name).send(settings.FALLBACK_DNS_ADDR, settings.FALLBACK_DNS_PORT))
                for rr in a.rr:
                    d.add_answer(rr)

                return d


def update_resolver_ns():
    while True:
        with open('custom-ns.json', 'r') as f:
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
                        print('[Scheduler] - updated DNS records for resolver {0}'.format(domain))

                    success = True
                except Exception as e:
                    print('[{0}] - An error occured for \'{1}\'!'.format(k, domain))

                if success:
                    break
                
        if updates:
            with open('custom-ns.json', 'w') as f:
                json.dump(custom_ns, f)

        time.sleep(300) # default ttl value for resolvers (5 min)

print('Initializing System, Press Ctrl-C to exit.')

print('Starting DNS Proxy...')
r = SpecialResolver()
s = server.DNSServer(r, port=settings.LOCAL_PORT, address=settings.LOCAL_ADDR)
s.start_thread()

print('Scheduling resolver update...')
update_resolver_t = threading.Thread(target=update_resolver_ns)
update_resolver_t.start()

print('Starting web service...')
backend.start()