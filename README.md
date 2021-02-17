# Overview

A subordinate charm to deploy Netdata and provide Netdata metrics
to an existing Prometheus deployment using promreg. 

# Usage

Use this charm with any other charm:

    juju deploy netadata --config ~/netdata.yaml
    juju add-relation netdata:netdata-host other-charm:juju-info

netdata.yaml:

    netdata:
      netdata_nginx_port: 19998
      netdata_nginx_listen_subnet: "10.0.0.0/24"
      netdata_nginx_allowed_subnet: "10.0.0.0/24"   
      promreg_authtoken: ****
      promreg_url: https://promreg_url:12321      
      prometheus_main_label: "pref_label_n1,pref_label_n2,pref_label_n3"