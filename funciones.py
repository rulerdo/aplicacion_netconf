from ncclient import manager
from ncclient import xml_
from ncclient.operations import RPCError
import xmltodict
import json
import devices as d
import filters as f


def get_config_filter(device,netconf_filter):
    
    with manager.connect(
        host=device['address'],
        port=device['port'],
        username=device['username'],
        password=device['password'],
        hostkey_verify=False) as m:

        if float(device['version']) >= 17.3:
            config = m.get_config('running',filter=('subtree',netconf_filter)).xml
        else:
            updated_filter = '<filter>' + netconf_filter + '</filter>'
            config = m.get_config('running',updated_filter).xml

    return config


def xml_to_json(xml_data):

    od_config = xmltodict.parse(xml_data)
    json_config = json.loads(json.dumps(od_config))
    config = json_config['rpc-reply']['data']['native']

    return config


def get_options_menu():

    menu = True

    while menu:
        device_id = input('''
1) ISR 4331
2) Catalyst 8000v
Selecciona el equipo al que te quieres conectar: ''')

        filter_id = input('''
1) Hostname
2) Usuarios
3) Rutas
4) Interfaz Loopback 10
Selecciona la configuracion que quieres obtener: ''')

        if device_id in ['1','2'] and filter_id in ['1','2','3','4']:
            menu = False
        else:
            print('Opcion incorrecta, usa los numeros para seleccionar equipo y configuracion')

    return device_id,filter_id


def get_device_filter(device_id,filter_id):

    dicc_filtros = {
        '1': f.hostname,
        '2': f.usernames,
        '3': f.routes,
        '4': f.loopback10
    }

    dicc_equipos = {
        '1': d.lab_4331,
        '2': d.lab_c8000v
    }

    device = dicc_equipos[device_id]
    netconf_filter = dicc_filtros[filter_id]

    return device,netconf_filter


def config_format(config,filter_id):

    f_config = list()

    if filter_id == '1':
        h_response = f'hostname: {config["hostname"]}'
        f_config.append(h_response)

    elif filter_id == '2':
        if type(config["username"]) == list:
            list_config = config["username"]
        else:
            list_config = [config["username"]]
        for user in list_config:
            n = user["name"]
            p = user["privilege"]
            s = user["secret"]["secret"]
            c = user["secret"]["encryption"]
            u_response = f'usuario: {n}\nprivilegio: {p}\nsecreto: {s}\ncifrado: {c}\n'
            f_config.append(u_response)

    elif filter_id == '3':
        if type(config["ip"]["route"]["ip-route-interface-forwarding-list"]) == list:
            list_config = config["ip"]["route"]["ip-route-interface-forwarding-list"]
        else:
            list_config = [config["ip"]["route"]["ip-route-interface-forwarding-list"]]

        for route in list_config:
            p = route["prefix"]
            m = route["mask"]
            n = route["fwd-list"]["fwd"]
            r_response = f'prefix: {p}\nmask: {m}\nnext-hop: {n}\n'
            f_config.append(r_response)

    elif filter_id == '4':
        name = 'Loopback 10'
        ip = config["interface"]["Loopback"]["ip"]["address"]["primary"]["address"]
        mask = config["interface"]["Loopback"]["ip"]["address"]["primary"]["mask"]
        l_response = f'{name}\nip: {ip}\nmascara: {mask}\n'
        f_config.append(l_response)

    else:
        print('Formato no disponible aun')
        f_config.append(config)

    return f_config


def apply_config_xml(device,new_config):
    
    if new_config == None:
        netconf_reply = 'Configuracion no soportada'

    else:

        with manager.connect(
            host=device['address'],
            port=device['port'],
            username=device['username'],
            password=device['password'],
            hostkey_verify=False) as m:

            if device['commit']:
                netconf_reply = m.edit_config(config=new_config,target='candidate')
                m.commit()
            else:
                netconf_reply = m.edit_config(config=new_config,target='running')
                netconf_save = '<cisco-ia:save-config xmlns:cisco-ia="http://cisco.com/yang/cisco-ia"/>'
                m.dispatch(xml_.to_ele(netconf_save))

    return netconf_reply


def build_config_xml(filter_id):

    if filter_id == '1':

        h = input('Escribe el nuevo hostname: ')

        new_config = f'''
        <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">  
            <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                <hostname>{h}</hostname>
            </native>
        </config>'''
    
    elif filter_id == '2':

        print('NOTA: modificar el usuario admin no esta permitido')
        u = input('Escribe el nuevo usuario: ')

        if u == 'admin':
            new_config = None

        else:
            p = input('Escribe el nuevo privilegio: ')
            s = input('Escribe el nuevo password: ')

            new_config = f'''
            <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"> 
                <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                    <username>
                        <name>{u}</name>
                        <privilege>{p}</privilege>
                        <secret>
                            <encryption>0</encryption>
                            <secret>{s}</secret>
                        </secret>
                    </username>
                </native>
            </config>'''

    elif filter_id == '3':

        print('NOTA: modificar la ruta 0.0.0.0 no esta permitido')
        p = input('Escribe el nuevo prefijo: ')
        
        if p == '0.0.0.0':
            new_config = None
        
        else:
            m = input('Escribe la nueva mascara: ')
            n = input('Escribe el nuevo next-hop: ')

            new_config = f'''
                <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"> 
                    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                        <ip>
                            <route>
                                <ip-route-interface-forwarding-list>
                                    <prefix>{p}</prefix>
                                    <mask>{m}</mask>
                                    <fwd-list>
                                        <fwd>{n}</fwd>
                                    </fwd-list>
                                </ip-route-interface-forwarding-list>
                            </route>
                        </ip>
                    </native>
                </config>'''

    elif filter_id == '4':

        i = input('Escribe la nueva IP: ')
        m = input('Escribe la nueva mascara: ')

        new_config = f'''
                <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"> 
                    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
                        <interface>
                            <Loopback>
                                <name
                                    xmlns:nc='urn:ietf:params:xml:ns:netconf:base:1.0'>10
                                </name>
                                <ip>
                                    <address>
                                        <primary>
                                            <address>{i}</address>
                                            <mask>{m}</mask>
                                        </primary>
                                    </address>
                                </ip>
                            </Loopback>
                        </interface>
                    </native>
                </config>'''

    else:
        new_config = None

    return new_config


def send_config(device,new_config):

    try:
        apply_config_xml(device,new_config)
        response = ('Configuracion aplicada')

    except RPCError as error:
        response = ('Problemas con la configuracion\nError: ',error._message)

    return response
