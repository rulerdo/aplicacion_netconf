import funciones as fn

def main():

    device_id,filter_id = fn.get_options_menu()
    device,netconf_filter = fn.get_device_filter(device_id,filter_id)
    xml_config = fn.get_config_filter(device,netconf_filter)
    config = fn.xml_to_json(xml_config)
    f_config = fn.config_format(config,filter_id)
    print('')
    [print(x) for x in f_config]

    configurar = input('Escribe "SI" si deseas modificar esta configuracion: ')

    if configurar == 'SI':

        new_config = fn.build_config_xml(filter_id)
        print('Aplicando configuracion...')
        response = fn.send_config(device,new_config)

    else:

        response = ('ADIOS!')

    print(response)


if __name__ == '__main__':

    main()