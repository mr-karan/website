+++
title = "Setting up Kong API Gateway - Part 1/2"
date = 2019-03-23T10:57:55+05:30
type = "post"
description = "Ansible Playbook for Deploying Kong Cluster - part 1"
in_search_index = true
[taxonomies]
tags = ["devops","ansible","kong"]
+++

# Kong

[Kong](https://konghq.com/) is an API Gateway, which basically reverse proxies every incoming request to the upstream URL. It is pretty useful if you have a lot of internal services which need to talk to each other (through HTTP) but you don't want to keep managing the authentication layer, rate limiting, hosts whitelisting and other such things in every service. Kong acts as a central entrypoint to all other services' API endpoints and all the common fluff is heavylifted by Kong's API layer.

Kong follows a [plugin](https://docs.konghq.com/hub/) approach, which makes it extensible and you can even [make your own plugins](https://docs.konghq.com/1.0.x/plugin-development/). Using plugins, it is possible to modify the request,
add authentication layer at the Kong layer, forward user meta information headers to the upstream.

Amongst other API Gateway solutions, Kong is pretty straightforward to get started with and has a nice community support as well. All of the actions to configure your API endpoints and manage them can be done through a RESTful Admin API.

The following setup guide describes how the infra is setup for **High Availability** of a cluster of Kong nodes.

## Infra Setup

Each individual Kong node is stateless, since it is always connected to an external datastore. In this tutorial, we will provision 2 nodes for Kong. The instances are frontended by Amazon's ELB which routes the traffic internally to either of a Kong node using internal DNS. Kong requires a datastore to fetch the information about upstream APIs, consumers, routing mechanisms, plugins, so each of the Kong node must be in sync with the other Kong node. We will achieve the same by using Cassandra as our database for Kong, which is being run in a clustering mode. Cassandra uses it's gossip mechanism to ensure the other Cassandra node is upto-date with any new changes to the data.

### Scaling Kong

To scale Kong in future, we can keep on adding multiple Kong nodes horizontally and attaching them to one of the Cassandra node. This way we can have multiple Kong nodes in one cluster each pointing to one central Cassandra datastore.

## Setting up the cluster

We will use Ansible to automate the task of setting up Kong+Cassandra in each of 2 nodes. You can refer to the [playbook](https://github.com/mr-karan/kong-ansible) which will do the job.

```yml
---
# https://github.com/mr-karan/kong-ansible
# Playbook to install the Cassandra and Kong

- hosts: "{{control_host}}"
  remote_user: "{{control_user}}"
  become: yes
  roles:
    - role: java
    - role: cassandra
- role: kong
```

After you run the playbook, there are a couple of important things which needs to be configured in order to have an HA setup. This setup guide
assumes the playbook is run individually on 2 servers: `srvr A` and `srvr B`.

### Important Directory Paths

| Local location                           | Description                                                                                                                 |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `/usr/local/bin/kong`                    | Kong executable binary                                                                                                      |
| `/usr/local/kong`                        | All the settings and logs are available under a namespaced directory, which will be called as `PREFIX` in further sections. |
| `/etc/systemd/service/kong.service`      | Managing Kong as systemd service                                                                                            |
| `/etc/systemd/service/cassandra.service` | Managing Cassandra db as systemd service                                                                                    |
| `/etc/cassandra/cassandra.yaml`          | Config for Cassandra                                                                                                        |
| `/etc/kong/kong.conf`                    | Config for Kong                                                                                                             |

### First Steps

#### Setting up Cassandra

Let's setup Cassandra first and run in clustering mode. Do these steps in both of the servers.

1.  Stop any running cassandra node:

    ```bash
    sudo service cassandra stop
    ```

2.  Edit the cassandra config file and update the following values:

        cluster_name: 'KongAPICluster'
        seed_provider:
        - class_name: org.apache.cassandra.locator.SimpleSeedProvider
            parameters:
                - seeds: "<private_ip_srvrA>,<private_ip_srvrB>"
        listen_address: <private_ip_srvr>
            start_rpc: true

3.  Start cassandra on both the servers and check the status:

    ```bash
    sudo serice cassandra start
    ```

4.  Verify Cassandra clustering:

    ```bash
    sudo nodetool status # Give it a couple of seconds (30-45) for both nodes to warm up and discover each other.
    ```

    The output of above command should look like:

    ```bash
    $ sudo nodetool status
    Datacenter: datacenter1
    =======================
    Status=Up/Down
    |/ State=Normal/Leaving/Joining/Moving
    --  Address        Load       Tokens       Owns (effective)  Host ID   Rack
    UN  <REDACTED>  467.26 KiB  256          100.0%            <REDACTED>  rack1
    UN  <REDACTED>  496.36 KiB  256          100.0%            <REDACTED>  rack1
    ```

5.  Troubleshooting Cassandra:

    - **cqlsh unable to connect to `cassandra` server:**
      `cqlsh` has a known bug in some versions with Python2.7 where it cannot connect to the cassandra server. Do the following steps to fix:

      ```bash
      sudo pip install cassandra-driver
      export CQLSH_NO_BUNDLED=TRUE
      ```

    - **Unable to discover the other cassandra cluster:**
      This usally happens because of network connectivity issues. Verify both nodes are able to talk to each other by running Cassandra in single cluster mode and then issue the following commands:

      ```bash
      # in srvrA
      netstat -lntvp | grep cassandra # should be present (port 9042 usually)
      # in srvrB, check similarly...
      # in srvrA
      telnet private_ip_srvrB 9042 # should connect
      # in srvrB, check similarly...
      ```

#### Setting up Kong

Let's setup each Kong node in the cluster as following.

1. Stop any running kong instance:

   ```bash
   sudo service kong stop
   ```

2. Edit the kong config file and update the following values:

   ```bash
   ...
   admin_listen = <private_ip_srvrA>:8001, <private_ip_srvrA>:8444 ssl
   database = cassandra
   db_update_propagation = 10 #seconds
   ...
   ```

3. Start kong on both the servers and check the status:

   ```bash
   sudo serice kong start
   ```

4. Verify if Kong is running:

   ```bash
   sudo service kong status
   ```

5. Run Kong Migrations:

   Run the migrations on _only_ one cluster. Since the datastores will be in sync(_eventual consistency_ thanks to Cassandra), we don't have to run migrations on the second cluster.

   ```bash
   kong migrations -c /etc/path/to/config
   ```

6. Troubleshooting Kong:

   - Check if Kong is actually running by `sudo service kong status`. You can check for logs in `$PREFIX/logs/error.log`.
   - If Kong is not running, you can try running `kong check` for checking if the config file is correct. Kong additionally provides a health check command, which can be executed using `kong health`.

## Managing Kong

Kong comes with [Admin API](https://docs.konghq.com/1.0.x/admin-api/) to manage all aspects of Kong. There is also an unofficial project which is aN UI on top of Kong's API and it comes pretty handy to configure upstream endpoints, adding plugins etc.

To read more about it, you can continue reading the second part of the series [here](/posts/setting-up-kong-part-2)
