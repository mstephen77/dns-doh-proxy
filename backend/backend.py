import ipaddress
import json
import settings
import time
from dnslib import QTYPE
from flask import Flask, abort, session, render_template, request, jsonify
from flask.logging import default_handler
from gevent.pywsgi import WSGIServer

app = Flask(__name__)
app.logger.removeHandler(default_handler)

resolver = None

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
                'TTL': 30,
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
        'dns_answered': settings.DNS_ANSWERED,
        'dns_answer_cache': settings.DNS_ANSWER_BY_CACHE,
        'dns_answer_doh': settings.DNS_ANSWER_BY_DOH,
        'dns_answer_custom': settings.DNS_ANSWER_FROM_CUSTOM,
        'dns_answer_fallback': settings.DNS_FALLBACK,
    })
@app.route('/resolvers')
def view_resolvers():
    global resolver
    return render_template('pages/resolvers.html', data={
        'resolvers': resolver.resolvers,
    })
@app.route('/domains', methods=['GET', 'POST'])
def view_domains():
    if request.method == 'POST':
        with open(settings.NAMES_DATA, 'r') as f:
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

                print('[Backend]: {0} custom domain \'{1}\'!'.format((create_new and 'Adding' or 'Updating'), domain))

        with open(settings.NAMES_DATA, 'w') as f:
            json.dump(custom_ns, f)
        
        resolver.load_custom_names()

    with open(settings.NAMES_DATA, 'r') as f:
        custom_ns = json.load(f)
    
    return render_template('pages/domains.html', data={
        'name_servers': custom_ns.items()
    })
@app.route('/api/domains/<domain>')
def api_domains_domain(domain):
    with open(settings.NAMES_DATA, 'r') as f:
        custom_ns = json.load(f)

    if domain not in custom_ns and (domain + '.') not in custom_ns:
        abort(404)

    if (domain + '.') in custom_ns:
        domain = domain + '.'

    return jsonify(custom_ns[domain])
@app.route('/dns-cache')
def view_dns_cache():
    global resolver
    return render_template('pages/dns-cache.html', data={
        'dns_cache': resolver.cache.items()
    })

def start(_resolver, host='0.0.0.0', port=5000):
    global resolver
    resolver = _resolver
    # app.run(host=host, port=port, threaded=True)
    http_server = WSGIServer((host, port), app)
    http_server.serve_forever()