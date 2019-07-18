import time
import dnslib
import json
import requests
import resolvers.cloudflare as cf
import resolvers.google as google
import resolvers.quad9 as quad9
from dnslib import server

RESOLVERS = {
    'google': google,
    'cloudflare': cf
    'quad9': quad9,
}

LOCAL_ADDR = 'localhost'
LOCAL_PORT = 53

FALLBACK_DNS_ADDR = '1.1.1.1'
FALLBACK_DNS_PORT = 53

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
            for answer in custom_ns[q_name]['answers']:
                if answer['type'] != q_type:
                    continue
                d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], answer['TTL'], dnslib.QTYPE[answer['type']], answer['data'])))
        else:
            success = False
            for k, mod in RESOLVERS.items():
                try:
                    answers = mod.resolve(q_name, q_type)                    
                    for answer in answers:
                        d.add_answer(*dnslib.RR.fromZone('{0} {1} {2} {3}'.format(answer['name'], answer['TTL'], dnslib.QTYPE[answer['type']], answer['data'])))

                    success = True
                except Exception as e:
                    print('[{0}] - An error occured! Details: {1}'.format(k, e))

                if success:
                    break

            if not success:
                a = dnslib.DNSRecord.parse(dnslib.DNSRecord.question(q_name).send(FALLBACK_DNS_ADDR, FALLBACK_DNS_PORT))
                for rr in a.rr:
                    d.add_answer(rr)


        return d

r = SpecialResolver()
s = server.DNSServer(r, port=LOCAL_PORT, address=LOCAL_ADDR)

s.start_thread()

print('Starting DNS Proxy, Press Ctrl-C to exit.')
while True:
    now = round(time.time())
    with open('custom-ns.json', 'r') as f:
        custom_ns = json.load(f)

    updates = False
    for domain, data in custom_ns.items():
        if not data['resolver']:
            continue

        success = False
        for k, mod in RESOLVERS.items():
            update_r = False
            try:
                answers = mod.resolve(domain, 'A')
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
                print('[{0}] - An error occured! Details: {1}'.format(k, e))

            if success:
                break
            
    if updates:
        with open('custom-ns.json', 'w') as f:
            json.dump(custom_ns, f)

    time.sleep(300) # default ttl value for resolvers (5 min)
