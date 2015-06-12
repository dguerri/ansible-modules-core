#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# Copyright (c) 2013, Benno Joy <benno@ansible.com>
#
# Author: Davide Guerri <davide.guerri@gmail.com>
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.

try:
    # noinspection PyUnresolvedReferences
    import shade

    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_port
short_description: Creates/Removes ports from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
description:
   - Add or Remove port from OpenStack.
options:
   name:
     description:
        - Name to be assigned to the port.
     required: true
   admin_state_up:
     description:
        - Whether the state should be marked as up or down.
     required: false
     default: true
   state:
     description:
        - Indicate desired state of the resource.
     choices: ['present', 'absent']
     required: false
     default: present
requirements: ["shade"]
'''

EXAMPLES = '''
- os_port:
    name=t1port
    state=present
    cloud=dguerri
'''

create_attributes = ('name', 'admin_state_up', 'mac_address', 'fixed_ips',
                     'subnet_id', 'ip_address', 'security_groups',
                     'allowed_address_pairs', 'extra_dhcp_opts',
                     'device_owner', 'device_id')
update_attributes = ('name', 'admin_state_up', 'fixed_ips',
                     'security_groups', 'allowed_address_pairs',
                     'extra_dhcp_opts', 'device_owner')


def main():
    argument_spec = openstack_full_argument_spec(
        port_id=dict(required=False),
        network_id=dict(required=False),
        name=dict(required=False),
        admin_state_up=dict(required=False, type='bool'),
        mac_address=dict(required=False),
        fixed_ips=dict(required=False, type='list'),
        subnet_id=dict(required=False),
        ip_address=dict(required=False),
        security_groups=dict(required=False, type='list'),
        allowed_address_pairs=dict(required=False, type='list'),
        extra_dhcp_opts=dict(required=False, type='list'),
        device_owner=dict(required=False),
        device_id=dict(required=False),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module_kwargs = openstack_module_kwargs(
        required_one_of=[('port_id', 'name')]
    )
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    port_id = module.params['port_id']
    port_name = module.params['name']
    network_id = module.params['network_id']
    state = module.params['state']

    check_mode = module.check_mode

    try:
        cloud = shade.openstack_cloud(**module.params)
        port = cloud.get_port(name_or_id=port_id or port_name)

        if state == 'present':
            if port is None:

                if module.check_mode:
                    module.exit_json(changed=True)

                # Build the argument list
                new_kwargs = dict()
                for arg in create_attributes:
                    if module.params.get(arg) is not None:
                        new_kwargs[arg] = module.params[arg]

                new_port = cloud.create_port(
                    network_id=network_id, **new_kwargs)
                module.exit_json(
                    changed=True, result="Created", port=new_port)
            else:
                changed = False
                for arg in update_attributes:
                    if port[arg] != module.params[arg]:
                        changed = True
                        break

                if check_mode:
                    module.exit_json(changed=changed, port=port)

                if changed:
                    # Build the argument list
                    update_kwargs = dict()
                    for arg in update_attributes:
                        if module.params.get(arg) is not None:
                            update_kwargs[arg] = module.params[arg]

                    updated_port = cloud.update_port(
                        name_or_id=port_id or port_name, **update_kwargs)
                    module.exit_json(
                        changed=True, result="Updated", port=updated_port)

        elif state == 'absent':
            if port is None:
                module.exit_json(changed=False)
            else:
                if check_mode:
                    module.exit_json(changed=True)

                cloud.delete_port(name_or_id=port['id'])
                module.exit_json(changed=True, result="Deleted")

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=e.message)


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *

main()
