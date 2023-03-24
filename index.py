import requests
import yaml
import time
from copy import deepcopy

from urllib.parse import parse_qs, urlparse

HELLO_WORLD = b"Hello world!"
CLASHURL = "<http订阅链接>"
V2RAYURL = "<http订阅链接>"
SSRURL = "<http订阅链接>"
shadowrocketURL = "<http订阅链接>"
TOKEN = "123456"
protocol_list = ['clash','v2ray','ssr','shadowrocket']
now_str_time = time.asctime( time.localtime(time.time()) )
new_proxy_group = {
    "name":"亚洲负载均衡",
    "type":"url-test",
    "interval":600,
    "url":"http://www.gstatic.com/generate_204",
    "proxies":[]
}
filter_conditions={
    "require_list":['IPLC'],
    "option_list":['广港','广台','广新','广日']
}

chatgpt_group={
    "name":"chatgpt",
    "type":"select",
    "proxies":[]
}
chatgpt_rules=[
    str('DOMAIN-SUFFIX,openai.com,chatgpt'),
    str('DOMAIN-SUFFIX,chat.openai.com,chatgpt'),
    str('DOMAIN-SUFFIX,challenges.cloudflare.com,chatgpt'),
    str('DOMAIN-SUFFIX,auth0.openai.com,chatgpt'),
    str('DOMAIN-SUFFIX,platform.openai.com,chatgpt'),
    str('DOMAIN-SUFFIX,ai.com,chatgpt')
]

def get_subscribe_metadata(protocol):
    sub_response={
        "headers":[],
        "responseText":""
    }
    if protocol=="clash":
        resp = requests.get(CLASHURL)
        if resp.headers.get("Subscription-UserInfo"):
            sub_response["headers"].append(("Subscription-UserInfo",resp.headers['Subscription-UserInfo']))
            sub_response["responseText"]=resp.text
    elif protocol=="v2ray":
        resp = requests.get(V2RAYURL)
        sub_response["responseText"]=resp.text
    elif protocol=="ssr":
        resp = requests.get(SSRURL)
        sub_response["responseText"]=resp.text
    elif protocol=="shadowrocket":
        resp = requests.get(shadowrocketURL)

    return sub_response

def process_clash_dingyue(yamlstr):
    json_data = yaml.safe_load(yamlstr)
    for index,proxy_item in enumerate(json_data['proxies']):
        for require_item in filter_conditions['require_list']:
            if require_item in proxy_item['name']:
                for option_item in  filter_conditions['option_list']:
                    if option_item in proxy_item['name']:
                        new_proxy_group['proxies'].append(proxy_item['name'])
                        continue

    json_data['proxy-groups'][0]['proxies'].insert(0,new_proxy_group['name'])
    json_data['proxy-groups'].insert(-1,new_proxy_group)
    # add chatgpt grou
    chatgpt_list = [item['name'] for item in json_data['proxies']]
    chatgpt_group['proxies'] = chatgpt_list
    json_data['proxy-groups'].insert(-1,chatgpt_group)
    # add rules
    json_data['rules'] = chatgpt_rules+json_data['rules']
    json_data['updateTime'] = now_str_time
    print(json_data['rules'][-20:])
    return yaml.safe_dump(json_data)

def parser_params(params_str):
    item_dict={}
    param_dict_tmp = parse_qs(params_str)
    for key,value in param_dict_tmp.items():
        if len(value)==0:
            continue
        else :
            item_dict[key]=value[0]
    return item_dict




# handler部分

def handler(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    params_dict=parser_params(environ['QUERY_STRING'])
    if params_dict.get('token') !=  TOKEN:
        start_response(status, response_headers)
        return [b'error token']
    if params_dict.get('protocol') not in protocol_list:
        start_response(status, response_headers)
        return [b'error protocol']
    resp_item = get_subscribe_metadata(params_dict['protocol'] )
    if params_dict.get('protocol')=="clash":
        resp_item["responseText"] = process_clash_dingyue(resp_item["responseText"])
    for item in resp_item['headers']:
        response_headers.append(item)
    start_response(status, response_headers)
    return [resp_item['responseText'].encode('utf-8')]