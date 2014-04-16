#!/bin/bash

set -e

NUM_NETS=${1:-2}
NUM_VMS_PER_NET=${2:-2}
USER_NAME=admin
TENANT_NAME=demo
FLAVOR=m1.tiny
ROUTER=router1

. ~/devstack/openrc "${USER_NAME}" "${TENANT_NAME}"
IMAGE=$(nova image-list | awk '/cirros-0.3.1-x86_64-uec\ / {print $2}' | head -1)

if ! [ "$NUM_NETS" -eq "$NUM_NETS" ] 2>/dev/null ; then
  echo "USAGE: $0 [ <number of nets> [ <number of VMs per net>]]" 1>&2
  echo "The number of networks must be an integer (argument supplied: '$NUM_NETS')" 1>&2
  exit 1
fi

if ! [ "$NUM_VMS_PER_NET" -eq "$NUM_VMS_PER_NET" ] 2>/dev/null ; then
  echo "USAGE: $0 [ <number of nets> [ <number of VMs per net>]]" 1>&2
  echo "The number of VMs per network must be an integer (argument supplied: '$NUM_VMS_PER_NET')" 1>&2
  exit 2
fi

if neutron net-list | grep net1\  1>/dev/null
then
  echo "Test already running? net1 exists" 1>&2
  neutron net-list 1>&2
  exit 3
fi

echo "Tenant:       ${USER_NAME}"
echo "Networks:     ${NUM_NETS}"
echo "VMs/network:  ${NUM_VMS_PER_NET}"
echo ""

TENANT=$(keystone tenant-list | awk "/${TENANT_NAME}/ {print \$2}" | head -1)
neutron router-create --tenant-id "$TENANT" "$ROUTER"

RULEID=$(neutron security-group-list -c id -c tenant_id |  awk "/$TENANT/ {print \$2}" | head -1)
neutron security-group-rule-create --protocol icmp --direction ingress "$RULEID"
neutron security-group-rule-create --protocol tcp --port-range-min 22 --port-range-max 22 --direction ingress "$RULEID"
sleep 30

if [ "$NUM_NETS" -gt 0 ]
then
  for netnum in `seq 1 $NUM_NETS`
  do
    neutron net-create --tenant-id "$TENANT" "net$netnum"
    neutron subnet-create --tenant-id "$TENANT" --name "subnet$netnum" "net$netnum" "10.10.${netnum}.0/24"
    neutron router-interface-add "$ROUTER" "subnet$netnum"
    sleep 5

    if [ "$NUM_VMS_PER_NET" -gt 0 ]
    then
      NETID=$(neutron net-list | awk "/net${netnum}/ {print \$2}")
      for vmnum in `seq 1 $NUM_VMS_PER_NET`
      do
        nova boot --image "$IMAGE" --flavor "$FLAVOR" --nic net-id="$NETID" "vm-net${netnum}-${vmnum}"
        sleep 10
      done
    fi
  done
fi

# list all routers, networks and VMs
neutron net-list
neutron router-list
neutron router-port-list "$ROUTER"
nova list
