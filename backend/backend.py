import ipaddress
import json
import settings
import time
from dnslib import QTYPE
from flask import Flask, abort, session, render_template, request, jsonify

app = Flask(__name__)

def create_custom_ns_entry(domain, records):
    answers = []

    for record in records:
        record = record.split(',')
        if len(record) != 2:
            continue

        record[1] = int(record[1])
        try:
            if record[1] == 1:
                ipaddress.IPv4Address(record[0])
            else:
                ipaddress.IPv6Address(record[0])

            answers.append({
                'name': domain,
                'type': record[1],
                'TTL': 3600,
                'data': record[0]
            })
        except ipaddress.AddressValueError:
            pass

    return {
        'resolver': False,
        'locked': False,
        'answers': answers
    }

@app.route('/')
def view_dashboard():
    now = round(time.time(), 0)
    seconds = now - settings.START_TIME
    minutes = int(round(seconds / 60, 0))
    hours = int(round(minutes / 60, 0))

    return render_template('pages/dashboard.html', data={
        'hours': hours,
        'minutes': minutes % 60,
        'dns_answered': settings.DNS_ANSWERED
    })
@app.route('/resolvers')
def view_resolvers():
    resolvers = settings.RESOLVERS
    priorities = {}
    p = 0
    for k, _ in resolvers.items():
        p = p + 1
        priorities[k] = p

    return render_template('pages/resolvers.html', data={
        'resolvers': resolvers,
        'priorities': priorities
    })
@app.route('/domains', methods=['GET', 'POST'])
def view_domains():
    if request.method == 'POST':
        with open(settings.NAMESERVER_DATA, 'r') as f:
            custom_ns = json.load(f)
        
        create_new = request.form.get('create_new')
        domain = request.form.get('domain')
        records = request.form.getlist('records[]')
        if create_new is not None and domain is not None:
            create_new = int(create_new) == 1
            domain = domain + '.'
            ns_entry = create_custom_ns_entry(domain, records)
            if (create_new and domain not in custom_ns) or (not create_new and domain in custom_ns):
                custom_ns[domain] = ns_entry

                print('{0} custom domain \'{1}\'!'.format((create_new and 'Adding' or 'Updating'), domain))

        with open(settings.NAMESERVER_DATA, 'w') as f:
            json.dump(custom_ns, f)

    with open(settings.NAMESERVER_DATA, 'r') as f:
        custom_ns = json.load(f)
    
    return render_template('pages/domains.html', data={
        'name_servers': custom_ns.items()
    })
@app.route('/api/domains/<domain>')
def api_domains_domain(domain):
    with open(settings.NAMESERVER_DATA, 'r') as f:
        custom_ns = json.load(f)

    if domain not in custom_ns and (domain + '.') not in custom_ns:
        abort(404)

    if (domain + '.') in custom_ns:
        domain = domain + '.'

    return jsonify(custom_ns[domain])

def start(host='127.0.0.1', port=5000):
    app.run(host=host, port=port)