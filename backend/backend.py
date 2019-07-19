import json
import settings
from dnslib import QTYPE
from flask import Flask, session, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def view_dashboard():
    return render_template('pages/dashboard.html')
@app.route('/resolvers')
def view_resolvers():
    resolvers = settings.RESOLVERS
    priorities = {}
    p = 0
    for k, resolver in resolvers.items():
        p = p + 1
        priorities[k] = p

    return render_template('pages/resolvers.html', data={
        'resolvers': resolvers,
        'priorities': priorities
    })
@app.route('/domains', methods=['GET', 'POST'])
def view_domains():
    with open('custom-ns.json', 'r') as f:
        custom_ns = json.load(f)
    
    return render_template('pages/domains.html', data={
        'name_servers': custom_ns.items()
    })

def start(host='127.0.0.1', port=5000):
    app.run(host=host, port=port)