#!/usr/bin/env bash

# **demo.sh**
# Prior to running this script check the following:
# 1. Set the name and path of the keystone_admin file in demo.conf OPENSTACK_ENV_FILE var
# 2. The script assumes two users with the names: admin and demo
# 3. The script requires three tenants to be present, their names are set in
#    demo.conf as the following variables:
#    ADMIN_TENANT_NAME, HR_TENANT_NAME, FINANCE_TENANT_NAME
# Usage:
# ./clean.sh

source demo.conf
source functions-common

function unset_prs_for_groups {
    local xtrace=$(set +o | grep xtrace)
    set +o xtrace
    uuids="$(echo $(gbp group-list | get_field 1) | sed 's/id //g')"
    for id in $uuids
    do
        set -o xtrace
        gbp group-update $id --provided-policy-rule-sets ""
        gbp group-update $id --consumed-policy-rule-sets ""
        set +o xtrace
    done
    $xtrace
}

function unset_prs_and_external_segments_for_external_policies {
    local xtrace=$(set +o | grep xtrace)
    set +o xtrace
    uuids="$(echo $(gbp external-policy-list | get_field 1) | sed 's/id //g')"
    for id in $uuids
    do
        set -o xtrace
        gbp external-policy-update $id --provided-policy-rule-sets ""
        gbp external-policy-update $id --consumed-policy-rule-sets ""
        gbp external-policy-update $id --external-segments ""
        set +o xtrace
    done
    $xtrace
}

function unset_external_segment_for_l3_policies {
    local xtrace=$(set +o | grep xtrace)
    set +o xtrace
    uuids="$(echo $(gbp l3policy-list | get_field 1) | sed 's/id //g')"
    for id in $uuids
    do
        set -o xtrace
        gbp l3policy-update $id --external-segment ""
        set +o xtrace
    done
    $xtrace
}

function delete_external_segments {
    local xtrace=$(set +o | grep xtrace)
    set +o xtrace
    uuids="$(echo $(gbp external-segment-list | get_field 1) | sed 's/id //g')"
    for id in $uuids
    do
        set -o xtrace
        gbp external-segment-delete $id
        set +o xtrace
    done
    $xtrace
}

# This script exits on an error so that errors don't compound and you see
# only the first error that occurred.
#set -o errexit

# Settings
# ========

set -o xtrace
source $OPENSTACK_ENV_FILE

if [ -z "$ADMIN_PASSWORD" ]; then
    ADMIN_PASSWORD=$OS_PASSWORD
fi
if [ -z "$NON_ADMIN_PASSWORD" ]; then
    NON_ADMIN_PASSWORD=$OS_PASSWORD
fi

set_user_password_tenant $ADMIN_USERNAME $ADMIN_PASSWORD $ADMIN_TENANT_NAME
unset_prs_and_external_segments_for_external_policies
unset_external_segment_for_l3_policies
delete_external_segments

set_user_password_tenant $NON_ADMIN_USERNAME $NON_ADMIN_PASSWORD $HR_TENANT_NAME
unset_prs_for_groups
if [ -n "`heat stack-show $HR_STACK | grep 'id'`" ]; then
    heat stack-delete "$HR_STACK"
    confirm_resource_deleted "heat stack-show" "$HR_STACK" "DELETE_COMPLETE"
fi

set_user_password_tenant $NON_ADMIN_USERNAME $NON_ADMIN_PASSWORD $ENG_TENANT_NAME
unset_prs_for_groups
if [ -n "`heat stack-show $ENG_STACK | grep 'id'`" ]; then
    heat stack-delete "$ENG_STACK"
    confirm_resource_deleted "heat stack-show" "$ENG_STACK" "DELETE_COMPLETE"
fi

set_user_password_tenant $ADMIN_USERNAME $ADMIN_PASSWORD $ADMIN_TENANT_NAME
unset_prs_for_groups
if [ -n "`heat stack-show $ADMIN_STACK | grep 'id'`" ]; then
    heat stack-delete "$ADMIN_STACK"
    confirm_resource_deleted "heat stack-show" "$ADMIN_STACK" "DELETE_COMPLETE"
fi
if [ -n "`heat stack-show $CONTRACTS_STACK | grep 'id'`" ]; then
    heat stack-delete "$CONTRACTS_STACK"
    confirm_resource_deleted "heat stack-show" "$CONTRACTS_STACK" "DELETE_COMPLETE"
fi
delete_external_segments

echo "*********************************************************************"
echo "SUCCESS: End $0"
echo "*********************************************************************"
