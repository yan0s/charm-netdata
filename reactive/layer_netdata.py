import subprocess

from charms.netdata_installation import (
    configure_nginx_netdata_vhost,
    remove_config,
    fix_rootfs_netdata_systemd_conf
)

import charms.promreg as promreg

import charms.apt

from charms.reactive import (
    when,
    when_not,
    set_flag,
    hook,
    clear_flag,
)

from charmhelpers.core import (
    hookenv,
)


def get_all_units_in_labels():

    result = subprocess.check_output(["/bin/systemctl", "--no-pager"])\
        .splitlines()

    juju_label_list = ""

    for line in result:
        str_line = line.decode("utf-8")
        if "jujud-unit-" in str_line:
            start = str_line.find("jujud-unit-") + "jujud-unit-".__len__()
            end = str_line.find(".service")
            if juju_label_list != "":
                juju_label_list += ","
            juju_label_list += str_line[start:end]
            print(str_line[start:end])

    return juju_label_list


@when_not('apt_packages_installed')
def install_packages():
    hookenv.log("*** NETDATA CHARM | Installing APT packages ***",
                "DEBUG")

    message = "APT packages installed!"
    hookenv.status_set('maintenance', message)

    set_flag('apt_packages_installed')

    message = "APT packages installed!"
    hookenv.status_set('active', message)


@when('apt.installed.nginx')
@when('apt.installed.netdata')
@when_not('netdata.configured')
def configure_netdata_systemd():
    message = "Modifying Netdata systemd configuration"
    hookenv.status_set('maintenance', message)

    fix_rootfs_netdata_systemd_conf()

    set_flag('netdata.configured')

    message = "Netdata service successfully configured!"
    hookenv.status_set('active', message)


@when('apt.installed.nginx')
@when('apt.installed.netdata')
@when('netdata.configured')
@when_not('nginx.configured')
def configure_nginx():
    configure_nginx_netdata_vhost()
    config = hookenv.config()

    message = "Netdata agent configured via nginx at port {}"\
        .format(config['netdata_nginx_port'])
    hookenv.status_set('active', message)
    set_flag('nginx.configured')


@when('nginx.configured')
@when_not('netdata_agent_to_prometheus.registered')
def register_netdata_agent_to_prometheus():
    config = hookenv.config()
    if config["promreg_url"] != "":
        main_label_names_str = config['prometheus_main_label']
        main_label_names_list = main_label_names_str.split(",")

        all_units_str = get_all_units_in_labels()
        all_units_list = all_units_str.split(",")

        main_unit_name = None

        for unit in all_units_list:
            for main_label_name in main_label_names_list:
                if unit[:(main_label_name + "-").__len__()] \
                   == main_label_name + "-":
                    main_unit_name = unit
                    break

        if main_unit_name is not None:
            print(main_unit_name)
        else:
            print(all_units_list[0])

        custom_labels = {
            "juju_unit_list": all_units_str,
            "juju_main_unit": main_unit_name
        }
        promreg.register(None, config['netdata_nginx_port'], custom_labels)
        message = "Netdata target registered to Prometheus"
        hookenv.status_set('active', message)
        set_flag('netdata_agent_to_prometheus.registered')
    else:
        message = "Netdata ready"
        hookenv.status_set('active', message)
        set_flag('netdata_agent_to_prometheus.registered')


@hook("stop")
def remove_netdata():
    hookenv.log("*** NETDATA CHARM | Removing netdata and "
                "Nginx Netdata vhost ***", "DEBUG")
    charms.apt.purge(['netdata'])
    remove_config()
    config = hookenv.config()
    promreg.deregister(None, config['netdata_nginx_port'])


@hook('upgrade-charm')
def upgrade_charm():
    clear_flag('netdata.configured')
    clear_flag('nginx.configured')
    clear_flag('netdata_agent_to_prometheus.registered')


@when('config.changed')
def handle_config_changes():
    clear_flag('netdata.configured')
    clear_flag('nginx.configured')
    clear_flag('netdata_agent_to_prometheus.registered')
