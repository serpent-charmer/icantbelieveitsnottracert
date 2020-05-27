import os, os.path, io, subprocess, re, json
from flask import Flask, flash, request, redirect, url_for, send_file, render_template
from urllib.request import urlopen
from collections import OrderedDict

REGEX = r'(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]){1,3}'
CACHE_DIR = 'cache'

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.debug = True

try:
    os.mkdir(CACHE_DIR)
except:
    pass
    
def filter_func_tuple(x):
    for _x in x.keys():
        if not _x: return
    return x
    
def get_json(data):
    data_dict = json.loads(data.decode())
    return data_dict

def get_traceroute(ip):
    ret = urlopen('http://lg.eltel.net/cgi-bin/LG.cgi?r=s&q=t&a=%s' % ip)
    text_r = ret.read().decode(errors='ignore')
    return text_r
    
def text2ips(text_r):
    matches = re.finditer(REGEX, text_r, re.MULTILINE)
    rt = [m.group() for m in matches][1::]
    return rt

@app.errorhandler(404)
def page_not_found(e):
    #return render_template('not_found.html'), 404
    return render_template('index.html'), 404

@app.route('/', methods=['GET', 'POST'])
def get_main_page():
    return render_template('main_page.html', files=os.listdir(CACHE_DIR))   
   
@app.route('/trace/<string:ip>', methods=['GET'])
def trace_route(ip):
    cached_ip = CACHE_DIR + '/' + ip
    
    if not os.path.isfile(cached_ip):
    
        if os.name != 'posix':
        
            return render_template('no_cache.html')
    
        with open(cached_ip, 'w+') as f:
        
            try:
                urls = [get_json(urlopen('http://ipinfo.io/%s/geo' % tr).read()) for tr in text2ips(get_traceroute(ip))]
            
                coords = list(filter(filter_func_tuple, [{url.get('loc') : [url.get('city'), url.get('region')]} for url in urls]))
            
                coord_dict = {}
                
                for c in coords:
                    coord_dict.update(c)
                    
                js_dict = json.dumps(coord_dict)
                
                f.write(js_dict)
            except:
                f.close()
                os.remove(cached_ip)
                return render_template('no_cache.html', message='Error while caching')
    
        return render_template('trace.html', cached=False, ip=ip)
        
    with open(cached_ip) as f:
    
        text_r = f.read()
        
        try:
            json_r = json.loads(text_r)
        except:
            f.close()
            os.remove(cached_ip)
            return render_template('no_cache.html', message='Error while reading cache')
            
        return render_template('trace.html', cached=True, ip=ip, coords=json_r)
            
    