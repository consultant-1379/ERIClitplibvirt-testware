"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Dec 2015
@author:    Kevin O Sullivan
@summary:   Testset to update libvirt vcs functionality
"""
import os
from litp_generic_test import attr
from testset_libvirt_initial_setup import LibvirtGenericTest
import test_constants
import libvirt_test_data


class Libvirtupdate2(LibvirtGenericTest):
    """
    Description:
        This Test class is a combination of multiple user stories
        related to the libvirt module. The test stories that are
        covered in this file are described below
    """
    def setUp(self):
        """
        Setup is used to get site specific data, litp model
        information, network setup and VCS paths in the model
        """
        # 1. Call super class setup
        super(Libvirtupdate2, self).setUp()

        self.model = self.get_litp_model_information()
        self.ms_node = self.model["ms"][0]["name"]
        self.srvc_path = self.model["libvirt"]["software_services_path"]
        self.clus_srvs = self.model["libvirt"]["cluster_services_path"]
        self.srvc_urls = self.find(self.ms_node, '/software/', "vm-service")
        self.srvc_urls.extend(
            self.find(self.ms_node, '/deployments/', "vm-service"))
        self.up_dict1 = libvirt_test_data.UPDATED2_SERVICE_GROUP_1_DATA
        self.up_dict2 = libvirt_test_data.UPDATED2_SERVICE_GROUP_2_DATA
        self.up_dict3 = libvirt_test_data.UPDATED2_SERVICE_GROUP_3_DATA
        self.up_dict4 = libvirt_test_data.UPDATED2_SERVICE_GROUP_4_DATA
        self.up_dict5 = libvirt_test_data.UPDATED2_SERVICE_GROUP_5_DATA
        self.up_sg6_dict = libvirt_test_data.UPDATED_SERVICE_GROUP_6_DATA
        self.up_dict7 = libvirt_test_data.UPDATED2_SERVICE_GROUP_SLES_DATA

        self.sg1_path = "{0}/CS_VM1".format(self.clus_srvs)
        self.sg6_path = "{0}/CS_VM6".format(self.clus_srvs)
        self.sg6_net_ifs_path = self.find(self.ms_node, self.sg6_path,
                                    'collection-of-vm-network-interface')[0]

        self.vm_rule_coll_paths = self.find(self.ms_node,
                                        '/software',
                                        'collection-of-vm-firewall-rule')

        self.vm1_rule_coll_path = [rule_coll_path for rule_coll_path in
                self.vm_rule_coll_paths if 'vm_service_1' in rule_coll_path][0]

        self.sles_rule_coll_path = [rule_coll_path for rule_coll_path in
                self.vm_rule_coll_paths if 'sles' in rule_coll_path][0]
        self.vm1_firewall_rules = libvirt_test_data.VM_FIREWALL_RULES_2
        self.vm_image_2 = libvirt_test_data.VM_IMAGE_FILE_NAME["VM_IMAGE2"]

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Results:
            The super class prints out diagnostics and variables
        """
        super(Libvirtupdate2, self).tearDown()

    @attr('all', 'non-revert', 'story7188', "LITPCDS-7188")
    def test_story7188_tc18_p_pkg_update(self):
        """
        @tms_id: litpcds_7188_tc18
        @tms_requirements_id: LITPCDS-7188

        @tms_title: Update VM packages and repos so that modifications can
        be made to a VM if required
        @tms_description: Check package on CS_VM1, CS_VM3, CS_VM5 after update

        @tms_test_steps:
            @step: Log onto each VM in the SGs mentioned above and ensure the
            correct packages are installed
            @result: Each VM has the correct packages installed

        @tms_test_precondition:
            - testset_libvirt_initial_setup and testset_libvirt_update_1
              have ran
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """

        updates = {
            'CS_VM1': {
                'item_id': 'pkg_empty_rpm1',
                'old': 'empty_rpm1',
                'new': 'empty_rpm2',
            },
            'CS_VM3': {
                'item_id': 'pkg_empty_rpm4',
                'old': 'empty_rpm4',
                'new': 'empty_rpm6',
            },
            'CS_VM5': {
                'item_id': 'empty_rpm3',
                'old': 'empty_rpm3',
                'new': 'empty_rpm5',
            },
        }
        vm_ip = self.get_ip_for_vms(self.ms_node)
        for app_name, pkg_name in updates.items():
            for ipaddress in vm_ip[app_name]:
                node_name = "{0}-node".format(app_name)
                self.add_vm_to_nodelist(node_name, ipaddress,
                                username=test_constants.LIBVIRT_VM_USERNAME,
                                password=test_constants.LIBVIRT_VM_PASSWORD)
                self.wait_for_node_up(node_name)
                # Ensure the new package is installed on the node
                self.assertTrue(self.check_pkgs_installed(
                    node_name, [pkg_name['new']], su_root=False))
                # Ensure the old package is NOT installed on the node
                self.assertFalse(self.check_pkgs_installed(
                    node_name, [pkg_name['old']], su_root=False))

    def update_vm_hostnames(self):
        """
        Description:
            - Update remove vm-services hostnames property using -d option.
            - CS_VM expected starting configuration
                CS_VM1 -> vm-service-1 -> smo-vm-1
                CS_VM2 -> vm-service-2 -> smo-vm-2
                CS_VM3 -> vm-service-3 -> smo-vm-3
                CS_VM4 -> vm-service-4 -> smo-vm-4
                CS_VM5 -> vm-service-5 -> smo-vm-5-n1,smo-vm-5-n2

        Actions:
            1. Update remove vm-services hostnames property with -d option.

            - CS_VM expected ending hostnames configuration should have
            default values.
                test-vm-service-1 -> test-vm-service-1-n1
                test-vm-service-2 -> test-vm-service-2-n2
                test-vm-service-3 -> test-vm-service-3
                test-vm-service-4 -> test-vm-service-4
                test-vm-service-5 -> test-vm-service-5-n1,test-vm-service-5-n2
        """

        # REMOVE HOSTNAMES FROM VM SERVICES USING -d OPTION
        for srvc_url in self.srvc_urls:
            stdout, stderr, returnc = \
                self.execute_cli_update_cmd(self.ms_node,
                                            srvc_url,
                                            "hostnames",
                                            action_del=True)

            self.assertEqual(0, returnc)
            self.assertEqual([], stdout)
            self.assertEqual([], stderr)

    def update_network_cs_plan(self):
        """
        Description:
            Update properties of the five service groups.
        """
        # Set up the variables for the service group urls

        sg2_path = self.clus_srvs + "/CS_VM2"
        sg3_path = self.clus_srvs + "/CS_VM3"
        sg4_path = self.clus_srvs + "/CS_VM4"
        sg5_path = self.clus_srvs + "/CS_VM5"
        vm_srvc_1_path = self.srvc_path + "vm_service_1"
        vm_srvc_2_path = self.srvc_path + "vm_service_2"
        vm_srvc_3_path = self.srvc_path + "vm_service_3"
        vm_srvc_4_path = self.srvc_path + "vm_service_4"
        vm_srvc_5_path = self.srvc_path + "vm_service_5"
        vm_srvc_sles_path = self.srvc_path + "sles"

        #########################
        #                       #
        #  Service Group CS_VM1 #
        #                       #
        #########################
        update_rules = libvirt_test_data.VM_FIREWALL_RULES_TO_UPDATE

        #TORF-279479 & TORF-297880 - Update vm-firewall-rule v4 & v6
        for rule in update_rules:
            self.execute_cli_update_cmd(self.ms_node, '{0}/{1}'.format(
                                        self.vm1_rule_coll_path,
                                        rule["item_name"]),
                                        props=rule["props"])

        #TORF-279479 & TORF-297880 - Remove vm-firewall-rule v4 & v6
        remove_rules = libvirt_test_data.VM_FIREWALL_RULES_TO_REMOVE
        for rule in remove_rules:
            self.execute_cli_remove_cmd(self.ms_node, '{0}/{1}'.format(
                                        self.vm1_rule_coll_path,
                                        rule["item_name"]))

        #LITPCDS-7179 - Update ips of vm network interfaces
        self.execute_cli_update_cmd(self.ms_node, self.sg1_path + \
            "/applications/vm_service_1/vm_network_interfaces/net1",\
            props='ipaddresses={0}'.format(self.up_dict1
                                ["NETWORK_INTERFACES"]["NET1"]["ipaddresses"]))

        #Update alias names
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_1_path + \
            "/vm_aliases/db1", props='alias_names={0}'.format(self.up_dict1
                                        ["VM_ALIAS"]["DB1"]["alias_names"]))

        self.execute_cli_update_cmd(self.ms_node, vm_srvc_1_path + \
            "/vm_aliases/db20", props='alias_names={0}'.format(
            self.up_dict1["VM_ALIAS"]["DB20"]["alias_names"]))

        #Update alias addresses
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_1_path + \
            "/vm_aliases/db2", props='address={0}'.format(
            self.up_dict1["VM_ALIAS"]["DB2"]["address"]))

        self.execute_cli_update_cmd(self.ms_node, vm_srvc_1_path + \
            "/vm_aliases/db21", props='address={0}'.format(
            self.up_dict1["VM_ALIAS"]["DB21"]["address"]))

        # TORF-349676 - update vm aliases with IPv6 address containing prefix
        self.execute_cli_update_cmd(self.ms_node,
                                    vm_srvc_1_path + "/vm_aliases/ipv6a",
                                    props='address={0}'.format
                            (self.up_dict1["VM_ALIAS"]["IPV6a"]["address"]))

        self.execute_cli_update_cmd(self.ms_node,
                                    vm_srvc_1_path + "/vm_aliases/ipv6b",
                                    props='address={0}'.format
                            (self.up_dict1["VM_ALIAS"]["IPV6b"]["address"]))

        #LITPCDS-585 - Update vm service properties; no. of cpu, ram
        rep29 = self.up_dict1["VM_SERVICE"]["cpus"]
        self.execute_cli_update_cmd(self.ms_node, self.sg1_path + \
            "/applications/vm_service_1", props='cpus={0}'.format(rep29))

        #TORF-219762 - Update cpuset
        rep30 = self.up_dict1["VM_SERVICE"]["cpuset"]
        self.execute_cli_update_cmd(self.ms_node, self.sg1_path +
            "/applications/vm_service_1", props='cpuset={0}'.format(rep30))

        rep32 = self.up_dict1["VM_SERVICE"]["ram"]
        self.execute_cli_update_cmd(self.ms_node, self.sg1_path + \
            "/applications/vm_service_1", props='ram={0}'.format(rep32))

        #LITPCDS-7188 - Update package name
        rep35 = self.up_dict1["PACKAGES"]["PKG_EMPTY_RPM1"]["name"]
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_1_path + \
            "/vm_packages/pkg_empty_rpm1", props='name={0}'.format(rep35))

        #LITPCDS-7815 - Update device path of vm nfs mount
        rep38 = self.up_dict1["NFS_MOUNTS"]["VM_MOUNT1"]["device_path"]
        self.execute_cli_update_cmd(self.ms_node,\
            vm_srvc_1_path + "/vm_nfs_mounts/vm_nfs_mount_1",\
            props='device_path={0}'.format(rep38))

        #LITPCDS-7182 - Update vm image name
        # TORF-113124 test_06_p_update_multiple_vm_images_during_idemp
        rep39 = self.up_dict1["VM_SERVICE"]["image_name"]
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_1_path,\
            props='image_name={0}'.format(rep39))

        # TORF-107476 - TC21 - Remove vm-ram-mount item from CS RH7
        self.execute_cli_remove_cmd(self.ms_node, self.sg1_path +
                                    '/applications/vm_service_1/vm_ram_mounts/'
                                    'vm_ram_mount_1')

        #############################
        #                           #
        #  Service Group CS_SLES_VM #
        #                           #
        #############################
        # TORF-279479 & TORF-297880 - Create IPv4 & IPv6 vm-firewall-rules
        sles_fw_path = vm_srvc_sles_path + "/vm_firewall_rules/"
        for rule in libvirt_test_data.VM_FIREWALL_RULES_SLES_2:
            self.execute_cli_update_cmd(self.ms_node, sles_fw_path
                                        + rule["item_name"],
                                        props=rule["props"])

        # TORF-404805
        # description: Configure zypper repos
        # test_steps:
        #   step: Create a second zypper repo for CS_SLES_VM
        #   result: Zypper repo is created for CS_SLES_VM
        self.execute_cli_create_cmd(self.ms_node,
                            vm_srvc_sles_path + "/vm_zypper_repos/repo_NCM2",
                            "vm-zypper-repo",
                            props="name='{0}' base_url='{1}'".format(
                                self.up_dict7["ZYPPER_REPOS"]["NCM"]["name"],
                                self.up_dict7["ZYPPER_REPOS"]["NCM"][
                                        "base_url"]), add_to_cleanup=False)

        # description: Configure vm packages
        # test_steps:
        #   step: Configure vm packages for CS_SLES_VM
        #   result: VM packages are configured for CS_SLES_VM
        self.execute_cli_create_cmd(self.ms_node, vm_srvc_sles_path +
                        "/vm_packages/pkg_empty_rpm9", "vm-package",
                                props="name='{0}'".format(self.up_dict7
                        ["PACKAGES"]["PKG1"]["name"]), add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM2 #
        #                       #
        #########################
        #LITPCDS-7179 - Create 2 new vm network interfaces
        rep42 = self.up_dict2["NETWORK_INTERFACES"]["NET30"]
        self.execute_cli_create_cmd(self.ms_node, vm_srvc_2_path + \
             "/vm_network_interfaces/net30", "vm-network-interface",
             props="host_device='{0}' network_name='{1}' device_name='{2}'"
                                    .format(rep42["host_device"],
                                            rep42["network_name"],
                                            rep42["device_name"]),
                                    add_to_cleanup=False)

        rep43 = self.up_dict2["NETWORK_INTERFACES"]["NET31"]
        self.execute_cli_create_cmd(self.ms_node, vm_srvc_2_path + \
             "/vm_network_interfaces/net31",\
             "vm-network-interface",
             props="host_device='{0}' network_name='{1}' device_name='{2}'"
                                    .format(rep43["host_device"],
                                            rep43["network_name"],
                                            rep43["device_name"]),
                                    add_to_cleanup=False)

        #LITPCDS-7179 - Update the ip addresses of 4 vm network interfaces
        self.execute_cli_update_cmd(self.ms_node, sg2_path + \
            "/applications/vm_service_2/vm_network_interfaces/net30",\
            props='ipaddresses={0}'.format(rep42["ipaddresses"]))

        self.execute_cli_update_cmd(self.ms_node, sg2_path + \
            "/applications/vm_service_2/vm_network_interfaces/net31",\
            props='ipaddresses={0}'.format(rep43["ipaddresses"]))

        rep6 = self.up_dict2["NETWORK_INTERFACES"]["NET2"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg2_path + \
            "/applications/vm_service_2/vm_network_interfaces/net2",\
            props='ipaddresses={0}'.format(rep6))

        rep7 = self.up_dict2["NETWORK_INTERFACES"]["NET3"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg2_path + \
            "/applications/vm_service_2/vm_network_interfaces/net3",\
            props='ipaddresses={0}'.format(rep7))

        #Update the alias names and address of 2 vm aliases
        rep8a = self.up_dict2["VM_ALIAS"]["DB1"]["alias_names"]
        rep8b = self.up_dict2["VM_ALIAS"]["DB1"]["address"]
        self.execute_cli_update_cmd(self.ms_node,\
            vm_srvc_2_path + "/vm_aliases/db1",\
            props='alias_names={0} address={1}'.format(rep8a, rep8b))

        rep9a = self.up_dict2["VM_ALIAS"]["DB22"]["alias_names"]
        rep9b = self.up_dict2["VM_ALIAS"]["DB22"]["address"]
        self.execute_cli_update_cmd(self.ms_node,\
            sg2_path + "/applications/vm_service_2/vm_aliases/db22",\
            props='alias_names={0} address={1}'.format(rep9a, rep9b))

        #LITPCDS-7815 - Create 3 new vm nfs mounts
        rep44 = self.up_dict2["NFS_MOUNTS"]["VM_MOUNT13"]
        self.execute_cli_create_cmd(self.ms_node,
            vm_srvc_2_path + "/vm_nfs_mounts/vm_nfs_mount_13",\
            "vm-nfs-mount",\
            props="device_path='{0}' mount_point='{1}'"
                                    .format(rep44["device_path"],\
                                            rep44["mount_point"]),
                                    add_to_cleanup=False)

        rep45 = self.up_dict2["NFS_MOUNTS"]["VM_MOUNT14"]
        self.execute_cli_create_cmd(self.ms_node,
            vm_srvc_2_path + "/vm_nfs_mounts/vm_nfs_mount_14",
            "vm-nfs-mount",
            props="device_path='{0}' mount_point='{1}'"
                                    .format(rep45["device_path"],\
                                            rep45["mount_point"]),
                                    add_to_cleanup=False)

        rep46 = self.up_dict2["NFS_MOUNTS"]["VM_MOUNT15"]
        self.execute_cli_create_cmd(self.ms_node,
            vm_srvc_2_path + "/vm_nfs_mounts/vm_nfs_mount_15",
            "vm-nfs-mount",
            props="device_path='{0}' mount_point='{1}'"
                                    .format(rep46["device_path"],
                                            rep46["mount_point"]),
                                    add_to_cleanup=False)
        #LITPCDS-7182 - Update the vm image
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_2_path,\
            props='image_name={0}'.format(
                self.up_dict2["VM_SERVICE"]["image_name"]))

        #TORF-219762 - Update cpuset
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_2_path,\
            props='cpuset={0}'.format(self.up_dict2["VM_SERVICE"]["cpuset"]))

        # TORF-107476 - TC20 - Remove vm-ram-mount item from CS RH6
        self.execute_cli_remove_cmd(self.ms_node, sg2_path +
                                    '/applications/vm_service_2/vm_ram_mounts/'
                                    'vm_ram_mount_2')

        #########################
        #                       #
        #  Service Group CS_VM3 #
        #                       #
        #########################

        sg3_nets = self.up_dict3["NETWORK_INTERFACES"]

        # TORF-107476: TC10 -  remove a vm-ram-mount during fo to parallel
        self.execute_cli_remove_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/vm_ram_mounts/'
                                    'vm_ram_mount_3')

        self.execute_cli_update_cmd(self.ms_node, sg3_path,
                                    props='active={0} standby={1} '
                                          'node_list={2}'
                                    .format(
                                        self.up_dict3["CLUSTER_SERVICE"]
                                        ["active"], self.up_dict3
                                        ["CLUSTER_SERVICE"]["standby"],
                                        self.up_dict3["CLUSTER_SERVICE"]
                                        ["node_list"]))

        self.execute_cli_update_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/'
                                    'vm_network_interfaces/net4',
                                    props="ipaddresses={0}".format(
                                        sg3_nets["NET4"]["ipaddresses"]))
        # LITPCDS-7179 - Update ip address of network interface
        self.execute_cli_update_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/'
                                    'vm_network_interfaces/net5',
                                    props="ipaddresses={0}".format(
                                        sg3_nets["NET5"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/'
                                    'vm_network_interfaces/net6',
                                    props="ipaddresses={0}".format(
                                        sg3_nets["NET6"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/'
                                    'vm_network_interfaces/net_dhcp',
                                    props="ipv6addresses={0}".format(
                                        sg3_nets["NET_DHCP"]["ipv6addresses"]
                                    ))
        self.execute_cli_update_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/'
                                    'vm_network_interfaces/net32',
                                    props="ipaddresses={0} ipv6addresses={1}"
                                    .format(sg3_nets["NET32"]["ipaddresses"],
                                            sg3_nets["NET32"]["ipv6addresses"]
                                    ))
        self.execute_cli_update_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/'
                                    'vm_network_interfaces/net23',
                                    props="ipaddresses={0}"
                                    .format(sg3_nets["NET23"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.ms_node, sg3_path +
                                    '/applications/vm_service_3/'
                                    'vm_network_interfaces/net24',
                                    props="ipaddresses={0}"
                                    .format(sg3_nets["NET24"]["ipaddresses"]))

        # LITPCDS-12817 - update device names to preserve consecutiveness
        self.execute_cli_update_cmd(self.ms_node,
                            vm_srvc_3_path + "/vm_network_interfaces/net23",
                            props="device_name={0}"
                            .format(sg3_nets["NET23"]['device_name']))
        self.execute_cli_update_cmd(self.ms_node,
                            vm_srvc_3_path + "/vm_network_interfaces/net24",
                            props="device_name={0}"
                            .format(sg3_nets["NET24"]['device_name']))

        #LITPCDS-12817 - remove vm network interface
        self.execute_cli_remove_cmd(self.ms_node,
                            vm_srvc_3_path + "/vm_network_interfaces/net34")

        #Update properties of vm aliases
        rep11 = self.up_dict3["VM_ALIAS"]["DB1"]["alias_names"]
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_3_path + \
            "/vm_aliases/db1", props='alias_names={0}'.format(rep11))

        rep12 = self.up_dict3["VM_ALIAS"]["DB2"]["address"]
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_3_path + \
            "/vm_aliases/db2", props='address={0}'.format(rep12))

        rep13 = self.up_dict3["VM_ALIAS"]["DB3"]["alias_names"]
        self.execute_cli_update_cmd(self.ms_node,\
            sg3_path + "/applications/vm_service_3/vm_aliases/db3",\
            props='alias_names={0}'.format(rep13))

        rep14 = self.up_dict3["VM_ALIAS"]["DB4"]["address"]
        self.execute_cli_update_cmd(self.ms_node,\
            sg3_path + "/applications/vm_service_3/vm_aliases/db4",\
            props='address={0}'.format(rep14))

        #LITPCDS-7188 - Update package name
        rep36 = self.up_dict3["PACKAGES"]["pkg_empty_rpm4"]["name"]
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_3_path + \
            "/vm_packages/pkg_empty_rpm4", props='name={0}'.format(rep36))

        #LITPCDS-7182 - Update vm image name
        rep40 = self.up_dict3["VM_SERVICE"]["image_name"]
        self.execute_cli_update_cmd(self.ms_node,\
            vm_srvc_3_path, props='image_name={0}'.format(rep40))

        # TORF-291089 - Unset cpunodebind
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_3_path,
                                    'cpunodebind', action_del=True)

        #########################
        #                       #
        #  Service Group CS_VM4 #
        #                       #
        #########################

        #LITPCDS-7179 - Update the ip addresses of 3 vm network interfaces
        rep15 = self.up_dict4["NETWORK_INTERFACES"]["NET8"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg4_path + \
            "/applications/vm_service_4/vm_network_interfaces/net8",\
            props='ipaddresses={0}'.format(rep15))

        rep16 = self.up_dict4["NETWORK_INTERFACES"]["NET9"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg4_path + \
            "/applications/vm_service_4/vm_network_interfaces/net9",\
            props='ipaddresses={0}'.format(rep16))

        rep17 = self.up_dict4["NETWORK_INTERFACES"]["NET10"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg4_path + \
            "/applications/vm_service_4/vm_network_interfaces/net10",\
            props='ipaddresses={0}'.format(rep17))

        #Update the alias names and address of 2 vm aliases
        rep18a = self.up_dict4["VM_ALIAS"]["DB25"]["alias_names"]
        rep18b = self.up_dict4["VM_ALIAS"]["DB25"]["address"]
        self.execute_cli_update_cmd(self.ms_node,\
            vm_srvc_4_path + "/vm_aliases/db25",\
            props='alias_names={0} address={1}'.format(rep18a, rep18b))

        rep19a = self.up_dict4["VM_ALIAS"]["DB26"]["alias_names"]
        rep19b = self.up_dict4["VM_ALIAS"]["DB26"]["address"]
        self.execute_cli_update_cmd(self.ms_node,\
            sg4_path + "/applications/vm_service_4/vm_aliases/db26",\
            props='alias_names={0} address={1}'.format(rep19a, rep19b))

        #LITPCDS-585 - Update vm service properties; cpu no. and ram
        rep30 = self.up_dict4["VM_SERVICE"]["cpus"]
        self.execute_cli_update_cmd(self.ms_node, sg4_path + \
            "/applications/vm_service_4", props='cpus={0}'.format(rep30))

        rep33 = self.up_dict4["VM_SERVICE"]["ram"]
        self.execute_cli_update_cmd(self.ms_node, sg4_path + \
            "/applications/vm_service_4", props='ram={0}'.format(rep33))

        # TORF-113124 test_06_p_update_multiple_vm_images_during_idemp
        rep36 = self.up_dict4["VM_SERVICE"]["image_name"]
        self.execute_cli_update_cmd(self.ms_node, sg4_path + \
            "/applications/vm_service_4", props='image_name={0}'.format(rep36))

        ########################
        #                      #
        # Service Group CS_VM5 #
        #                      #
        ########################

        #LITPCDS-7179 - Update the ipaddresses of 2 vm network interfaces
        rep20 = self.up_dict5["NETWORK_INTERFACES"]["NET11"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg5_path + \
            "/applications/vm_service_5/vm_network_interfaces/net11",\
            props='ipaddresses={0}'.format(rep20))

        rep21 = self.up_dict5["NETWORK_INTERFACES"]["NET13"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg5_path + \
            "/applications/vm_service_5/vm_network_interfaces/net13",\
            props='ipaddresses={0}'.format(rep21))

        #LITPCDS-7179 - Delete the ipv6addresses, and gateway,
        # of vm network interface
        self.execute_cli_update_cmd(self.ms_node, sg5_path + \
            "/applications/vm_service_5/vm_network_interfaces/net15",\
            'ipv6addresses', action_del=True)

        self.execute_cli_update_cmd(self.ms_node, vm_srvc_5_path + \
            "/vm_network_interfaces/net15", 'gateway6', action_del=True)

        #LITPCDS-7179 - Update the ip addresses of the same network interface
        rep24 = self.up_dict5["NETWORK_INTERFACES"]["NET15"]["ipaddresses"]
        self.execute_cli_update_cmd(self.ms_node, sg5_path + \
            "/applications/vm_service_5/vm_network_interfaces/net15",\
            props='ipaddresses={0}'.format(rep24))

        #Update the alias names and addresses of vm aliases
        rep25 = self.up_dict5["VM_ALIAS"]["DB1"]["alias_names"]
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_5_path + \
            "/vm_aliases/db1", props='alias_names={0}'.format(rep25))

        rep26 = self.up_dict5["VM_ALIAS"]["DB2"]["address"]
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_5_path + \
            "/vm_aliases/db2", props='address={0}'.format(rep26))

        rep27 = self.up_dict5["VM_ALIAS"]["DB4"]["alias_names"]
        self.execute_cli_update_cmd(self.ms_node,\
            sg5_path + "/applications/vm_service_5/vm_aliases/db4",\
            props='alias_names={0}'.format(rep27))

        rep28 = self.up_dict5["VM_ALIAS"]["DB27"]["address"]
        self.execute_cli_update_cmd(self.ms_node,\
            sg5_path + "/applications/vm_service_5/vm_aliases/db27",\
            props='address={0}'.format(rep28))

        #LITPCDS-585 - Update vm service properties; cpu and ram
        rep31 = self.up_dict5["VM_SERVICE"]["cpus"]
        self.execute_cli_update_cmd(self.ms_node, sg5_path + \
            "/applications/vm_service_5", props='cpus={0}'.format(rep31))

        self.execute_cli_update_cmd(self.ms_node, sg5_path + \
            "/applications/vm_service_5", props='ram={0}'.format(
                self.up_dict5["VM_SERVICE"]["ram"]))

        #LITPCDS-7188 - Update package name
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_5_path + \
            "/vm_packages/empty_rpm3", props='name={0}'.format(
            self.up_dict5["PACKAGES"]["pkg_empty_rpm3"]["name"]))

        # LITPCDS-7182 - Update vm image name
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_5_path,\
        props='image_name={0}'.format(
            self.up_dict5["VM_SERVICE"]["image_name"]))

        # TORF-219762 - Unset cpuset
        self.execute_cli_update_cmd(self.ms_node, vm_srvc_5_path,
                                    'cpuset', action_del=True)

        #LITPCDS-12817 - Add vm-network-interfaces for removal in next update
        for vm_net_id in self.up_dict5["NETWORK_INTERFACES"]:
            if vm_net_id in ["NET35", "NET36", "NET37"]:
                vm_net = self.up_dict5["NETWORK_INTERFACES"][vm_net_id]
                self.execute_cli_create_cmd(self.ms_node, vm_srvc_5_path + \
                            "/vm_network_interfaces/" + vm_net_id.lower(),
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' "
                               "device_name='{2}' ipaddresses='{3}' "
                               "ipv6addresses='{4}'".format(
                               vm_net["host_device"], vm_net["network_name"],
                               vm_net["device_name"], vm_net["ipaddresses"],
                               vm_net["ipv6addresses"]),
                                        add_to_cleanup=False)

        # TORF-271798 - update vm service based on a rhel7.4 image
        #########################
        #                       #
        #  Service Group CS_VM6 #
        #                       #
        #########################
        # TORF-271798 TC_06: update vcs clustered service from FO to PL
        self.execute_cli_update_cmd(
            self.ms_node, self.sg6_path, props='active={0} standby={1}'.format(
                self.up_sg6_dict["CLUSTER_SERVICE"]["active"],
                self.up_sg6_dict["CLUSTER_SERVICE"]["standby"]))

        # TORF-271798 TC_11: update IPv4 addresses of vm network interface
        self.execute_cli_update_cmd(
            self.ms_node, "{0}/net1".format(self.sg6_net_ifs_path),
            props='ipaddresses={0}'.format(
                self.up_sg6_dict["NETWORK_INTERFACES"]["NET1"]["ipaddresses"]))

        # TORF-271798 TC_12: update IPv6 addresses of vm network interface
        self.execute_cli_update_cmd(
            self.ms_node, "{0}/net2".format(self.sg6_net_ifs_path),
            props='ipv6addresses={0}'.format(
            self.up_sg6_dict["NETWORK_INTERFACES"]["NET2"]["ipv6addresses"]))

        # TORF-271798 TC_13: create new vm network interface
        self.execute_cli_create_cmd(self.ms_node,
                '{0}vm_service_6/vm_network_interfaces/net3'.format(
                    self.srvc_path),
                class_type="vm-network-interface",
                props="host_device={0} network_name={1} device_name={2}".format
                (self.up_sg6_dict["NETWORK_INTERFACES"]["NET3"]["host_device"],
                self.up_sg6_dict["NETWORK_INTERFACES"]["NET3"]["network_name"],
                self.up_sg6_dict["NETWORK_INTERFACES"]["NET3"]["device_name"]),
                add_to_cleanup=False)

        # TORF-271798 TC_08: deploy vm service with IPv6
        self.execute_cli_update_cmd(
            self.ms_node, "{0}/net3".format(self.sg6_net_ifs_path),
            props='ipv6addresses={0} ipaddresses={1}'.format(
            self.up_sg6_dict["NETWORK_INTERFACES"]["NET3"]["ipv6addresses"],
            self.up_sg6_dict["NETWORK_INTERFACES"]["NET3"]["ipaddresses"]))

        self.execute_cli_update_cmd(self.ms_node,
                url=self.srvc_path + 'vm_service_6/vm_network_interfaces/net3',
                props="gateway6={0}".format(
                self.up_sg6_dict["NETWORK_INTERFACES"]["NET3"]["gateway6"]))

        # TORF-271798 TC_14: update vm service properties: ram, hostnames,
        # internal_status_check
        self.execute_cli_update_cmd(
            self.ms_node, "{0}vm_service_6".format(self.srvc_path),
            props='ram={0} hostnames={1} internal_status_check={2}'.format(
                self.up_sg6_dict["VM_SERVICE"]["ram"],
                self.up_sg6_dict["VM_SERVICE"]["hostnames"],
                self.up_sg6_dict["VM_SERVICE"]["internal_status_check"]))

        # TORF-271798 TC_18: create vm firewall rules
        for fw_rule in self.up_sg6_dict["VM_FIREWALL_RULES"]:
            item_path = '{0}/{1}'.format(
                self.srvc_path + "vm_service_6/vm_firewall_rules",
                fw_rule["item_name"])
            self.execute_cli_create_cmd(self.ms_node, item_path,
                                        class_type='vm-firewall-rule',
                                        props=fw_rule["props"],
                                        add_to_cleanup=False)

    def setup_add_pkgs(self):
        """
        Description:
            -LITPCDS-7186 -As a LITP User I want to define VM packages
             and repos
        Actions:
            1. Copy the RPMs to MS
            2. Using litp import all appropriate packages into
               appropriate directories
        Results:
            All packages are available in appropriate repos
        """
        repo_dir = test_constants.PARENT_PKG_REPO_DIR
        rpm_src_dir = os.path.dirname(os.path.realpath(__file__)) + "/rpms"
        list_of_repos = {
            'libvirt_repo1': ['empty_testrepo1_rpm3.rpm', "empty_rpm5.rpm"],
            'libvirt_repo2': ['empty_testrepo2_rpm3.rpm'],
            'libvirt_repo3': ['empty_testrepo3_rpm3.rpm'],
        }

        for repo in list_of_repos:
            filelist = []
            for package in list_of_repos[repo]:
                # Copy RPMs to Management Server
                filelist.append(self.get_filelist_dict(
                    '{0}/{1}'.format(rpm_src_dir, package), "/tmp/"))

            self.copy_filelist_to(
                self.ms_node,
                filelist,
                add_to_cleanup=False,
                root_copy=True)

            # Use LITP import to add to repo for each RPM
            for package in list_of_repos[repo]:
                self.execute_cli_import_cmd(
                    self.ms_node,
                    '/tmp/{0}'.format(package),
                    repo_dir + repo)

    def update_ms_vm(self):
        """
        Description:
            Update the ms vm service for story LITPCDS-12817
        :return:
        """
        ms_vm1 = "/ms/services/MS_VM1"
        ms_vm1_data = libvirt_test_data.UPDATE2_MS_VM1_DATA

        # Add new vm_network_interfaces for story 12817
        vm_net_id = None
        vm_net = None
        for vm_net_id, vm_net in ms_vm1_data["NETWORK_INTERFACE"].iteritems():
            self.execute_cli_create_cmd(self.ms_node, ms_vm1
                              + "/vm_network_interfaces/" + vm_net_id.lower(),
                              "vm-network-interface",
                              "host_device='{0}' network_name='{1}' " \
                              "device_name='{2}' ipaddresses='{3}'".format(
                                                      vm_net["host_device"],
                                                      vm_net["network_name"],
                                                      vm_net["device_name"],
                                                      vm_net["ipaddresses"]),
                              add_to_cleanup=False)
        self.execute_cli_update_cmd(self.ms_node, ms_vm1
                            + "/vm_network_interfaces/" + vm_net_id.lower(),
                            "ipaddresses={0}".format(vm_net["ipaddresses"]))

    def _check_mount_conf(self, hostname, ipaddr, mnt_type, mnt_point):
        """
        Description:
            Method that will determine if a filesystem mount exists on a VM,
            specifically in /etc/fstab. True if filesystem exists,
            fails otherwise
        Objects:
            HOSTNAME: The hostname assigned to the VM configuration, i.e.
                tmo-vm-2 (used in libvirt KGB)

            IPADDR: ip address used to ssh into the VM i.e. 192.168.0.2

            MNT_TYPE: type of mount point that will be greped in the fstab
                file
            MNT_POINT: directory the mount is pointing to
        Returns: Nothing
        """

        target_cmd = 'findmnt -s -l -n -T {0}'.format(mnt_point)

        self.add_vm_to_node_list(hostname,
                                 username=test_constants.LIBVIRT_VM_USERNAME,
                                 password=test_constants.LIBVIRT_VM_PASSWORD,
                                 ipv4=ipaddr)

        actual, _, _ = self.run_command(hostname, target_cmd,
                                        username=test_constants.
                                        LIBVIRT_VM_USERNAME,
                                        password=test_constants.
                                        LIBVIRT_VM_PASSWORD,
                                        execute_timeout=60)
        mnt_pnt_flag = self.is_text_in_list(mnt_point, actual)

        if mnt_pnt_flag:
            self.assertTrue(self.is_text_in_list(mnt_type, actual))
        else:
            self.log('info', 'VM_RAM_MOUNT not found in hostname {0}'
                     .format(hostname))
            self.assertFalse(self.is_text_in_list(mnt_type, actual))

    def _check_image_on_node(self, img_name, node):
        """
        TORF-113124: Test method to verify that any unused VM-Image is removed
        from /var/lib/libvirt/images directory on node
        :param img_name: name of image removed
        :param node: node to run command on
        :return: True/ False
        """
        file_contents, _, _ = \
            self.run_command(node, 'ls {0}/ -h'.format(test_constants.
                                                      LIBVIRT_IMAGE_DIR),
                             su_root=True)

        return self.is_text_in_list(img_name, file_contents)

    def reboot_vm_rules_persist(self, ipaddr, service_name, rules_to_check,
                                exp_fw_rules, rule_coll_path):
        """
        Description: Reboot VM and verify the vm-firewall-rules
                     persist.
        Args:
            ipaddr (str): ipaddress of the VM
            service_name (str): Name of the VM
            rules_to_check (dict): Rules to check if they are in the
                            ip(6)tables for a vm.
                            Each value contains a list of lists with
                            each sublist corresponding to a rule in
                            the ip(6)tables.
                    (e.g.
                        {iptables : [[100 icmp ipv4', 'ACCEPT']],
                         ip6ables : [['OUTPUT', 'udp', '1995 ntp out']]}
                    )
            exp_fw_rules (dict): EXP_IPTABLES_OUTPUT from test data
            rule_coll_path (dict): Path to collection of firewall rules
        """

        timeout_err_msg = 'The VM "{0}" did not come back up after a reboot '
        'within the time limit, which is 10 mins by default'

        if "sles" == service_name:
            vm_password = test_constants.LIBVIRT_SLES_VM_PASSWORD
            cmd = '{0}'.format(test_constants.REBOOT_PATH)
        else:
            vm_password = test_constants.LIBVIRT_VM_PASSWORD
            cmd = '{0} -r now'.format(test_constants.SHUTDOWN_PATH)

        self.add_vm_to_node_list(service_name,
                                 username=test_constants.LIBVIRT_VM_USERNAME,
                                 password=vm_password,
                                 ipv4=ipaddr)

        self.run_command(service_name, cmd,
                        username=test_constants.
                        LIBVIRT_VM_USERNAME,
                        password=vm_password,
                        execute_timeout=60)

        if "sles" == service_name:
            status = self.wait_for_node_up(service_name)
            if not status:
                self.start_service(self.get_managed_node_filenames()[0],
                                   service_name)
            else:
                self.assertTrue(self.wait_for_node_up(service_name),
                                timeout_err_msg.format(service_name))
        else:
            self.assertTrue(self.wait_for_node_up(service_name),
                            timeout_err_msg.format(service_name))

        self.verify_vm_rules_applied(self.ms_node, exp_fw_rules,
                                     rules_to_check, ipaddr, service_name,
                                     rule_coll_path, args='-nL')

    @attr('all', 'non-revert', 'libvirt_update2', "LITPCDS-585",
          "LITPCDS-7182", "LITPCDS-7188", "TORF-107476", "TORF-219762",
          "TORF-279479", "TORF-297880", "TORF-271798", "TORF-343548",
          "TORF-349676", "TORF-404805", "TORF-406586", "TORF-422322",
          "TORF-419532")
    def test_p_libvirt_update_plan_2(self):
        """
        @tms_id: litpcds_libvirt_tc03
        @tms_requirements_id: LITPCDS-585, LITPCDS-7182, LITPCDS-7188,
        LITPCDS-7815, LITPCDS-7179, LITPCDS-11405, TORF-107476, TORF-113124,
        TORF-219762, TORF-279479, TORF-297880, TORF-271798, TORF-343548,
        TORF-349676, TORF-404805, TORF-406586, TORF-422322, TORF-419532

        @tms_title: Second update for multiple cluster services running in the
        litp model
        @tms_description: Updates the following item configurations in the
            litp model
            - Update vm-firewall-rule(s) ) (torf-279479, TORF-297880 &
              TORF-422322)
            - Update VM hostnames(litpcds_7179)
            - Update VM configuration i.e. vCPUs & RAM size(litpcds_585)
            - Update VM images (litpcds_7182)
            - Update VM packages and repos (litpcds_7188)
            - Update VM packages and zypper repos (TORF-404805)
            - Update VM network interfaces (litpcds_7179)
            - Update VM service under MS service(litpcds_11405)
            - Update VM-RAM-MOUNTs (torf_107476)
            - Remove Unused files from /var/lib/libvirt/images on
              nodes(torf-113124)
            - Update VM cpuset property (torf-219762)
            - Unset VM cpu cpunodebind (torf-291089)
            - Update VM aliases IPv6 address

        @tms_test_steps:
            @step: Remove hostnames from software/services and VM deployments
            @result: Hostnames are removed from both instances

            @step: Update CS_VM1, VM-network-interfaces, VM-aliases, vCPU,
            RAM, VM-packages, VM-nfs-mount, VM-image, cpuset
            @result: VM-network-interfaces, VM-aliases, vCPU, RAM,
            VM-packages, VM-nfs-mounts, VM-images and cpuset are updated

            @step: CS_VM1, VM-RAM_Mount is removed
            @result: VM-RAM-Mount is removed

            @step: Create two new VM-Network-Interfaces for CS_VM2
            @result: Two new VM-network-interfaces are created for CS_VM2

            @step: Create three VM-NFS-Mounts for CS_VM2
            @result: Three VM-NFS-Mounts are created for CS_VM2

            @step: Update CS_VM2, VM-network-interfaces, VM-aliases,
            VM-image, cpuset
            @result: VM-network-interfaces, VM-aliases, VM-image, cpuset
            are updated in CS_VM2

            @step: CS_VM2, VM-RAM_Mount is removed
            @result: VM-RAM-Mount is removed

            @step: Update CS_VM3, Cluster-service is parallel,
            VM-network-interfaces, VM-alises, VM-packages, VM-image
            @result: CS becomes [2,0], VM-network-interfaces, VM-aliases,
            VM-packages and VM-images are updated in CS_VM3

            @step: Remove VM-Network-Interface from CS_VM3
            @result: VM-Network-Interface is removed from CS_VM3

            @step: Unset the cpunodebind property of CS_VM3
            @result: No libvirt domain vcpu cpuset property defined for CS_VM3

            @step: Remove VM-RAM-Mount from CS_VM3
            @result: VM-RAM-Mount is removed from CS_VM3

            @step: Update CS_VM4, VM-network-interfaces, VM-aliases, vCPU, RAM
            size
            @result: VM-network-interfaces, VM-aliases vCPU, RAM are updated
            for CS_VM4

            @step: Update CS_VM5, VM-network-interfaces, VM-aliases, vCPU, RAM
            size, VM-packages, VM-image, delete cpuset
            @result: VM-network-interfaces, VM-aliases vCPU, RAM, VM-packages,
            VM-image, cpuset is deleted for CS_VM5

            @step: VM-network-interfaces are created for CS_VM5
            @result: CS_VM5 has newly created VM-network-interfaces

            @step: Update CS_VM6 based on a rhel7.4 image: cluster-service is
            parallel, VM-network-interfaces, VM-hostnames, RAM,
            internal-status-check, vm-firewall-rules
            @result: CS becomes [2,0],VM-network-interfaces, VM-hostnames, RAM,
            internal-status-check, vm-firewall-rules are updated in CS_VM6

            @step: Update CS_SLES_VM, VM-firewall-rules, VM-zypper-repos and
                   VM-packages
            @result: VM-firewall-rules, VM-zypper-repos and VM-packages are
                   updated for CS_SLES_VM

            @step: VM-network-interfaces are created for CS_VM5
            @result: CS_VM5 has newly created VM-network-interfaces

            @step: Verify network-config V1 file is created
            @result: network-config V1 file is located in
            /var/lib/libvirt/instances/<vm-service> directory

            @step: Import new empty package
            @result: Package is imported successfully

            @step: Update MS_VM1 service with new VM-network-interfaces
            @result: VM-network-interfaces are created for MS_VM1

            @step: Update vm-image for CS_VM1, CS_VM2, CS_VM3 and CS_VM4 to use
                   vm-image-3 and update CS_VM5 to use vm-image-1
            @result: CS_VM1 to CS_VM4 updated to use vm-image-3 and CS_VM5
                     updated to use vm-image-1

            @step: Verify vm-image-2 in directory /var/lib/libvirt/images/
                   on both node 1 and node 2
            @result: vm-image-2 file in /var/lib/libvirt/images/ on both nodes

            @step: Create and Run plan
            @result: Plan is created and is running

            @step: Restart litpd while plan is running when task to remove
                   unused images on node2 is complete then create and run plan
            @result: Plan is created and run successfully

            @step: Verify vm-firewall-rules are in ip(6)tables
            @result: Rules are present

            @step: Verify vm-firewall-rule was removed from ip6tables
            @result: Rule not present in ip6tables

            @step: Reboot test-vm-service-1 and sles and verify
                   vm-firewall-rule(s) persist
            @result: Rules Persist

            @step: VM-RAM_Mounts are validated to be removed after plan
            @result: Result for VM-RAM_Mounts comes back with False (1)

            @step: TORF-113124 Verify vm-image-2 has been removed from
                   /var/lib/libvirt/images/ on both node 1 and node 2
            @result: vm-image-2 file has been removed from directory
                     /var/lib/libvirt/images/ on both nodes.

            @step: Verify CS_VM1 has access to vcpu-0 and vcpu-1.
            @result: Validate CM_VM1 has access to vcpu-0 and vcpu-1.

            @step: Verify CS_VM2 has access to vcpu-1 only.
            @result: Validate CM_VM2 has access to vcpu-1 only.

            @step: Verify CS_VM5 has access to vcpu-0 and vcpu-1.
            @result: Validate CM_VM5 csuset is deleted and has access to
                     vcpu-0 and vcpu-1.

            @step: Verify that CS_VM3 has no vcpu element attribute cpuset
             defined.
            @result: Libvirt domain definition for CS_VM3 has no cpuset
             attribute in the vcpu element.

             @step: Verify CS_VM6 service is ONLINE on all active nodes
             @result: CS_VM6 service is ONLINE on node1 and node2

             @step: Verify test-vm-service-6 is running on all active nodes
             @result: test-vm-service-6 is running on node1 and node2

             @step: Verify test-vm-service-6 is pingable (ipv4 and ipv6)
             from MS
             @result: Ping and ping6 commands are successful for
             test-vm-service-6

             @step: TORF-349676 Update IPv6 vm-aliases with prefix and verify
                    hosts file on CS_VM1 is updated without the prefix
             @result: IPv6 vm-aliases without prefix are as expected in hosts
                      file on CS_VM1

        @tms_test_precondition:
            - testset_libvirt_initial_setup and testset_libvirt_update_1
              have ran
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        # Maximum duration of running plan
        # Code to be uncommented once Story code for TORF-113124 in rpm.
        primary_node = self.get_managed_node_filenames()[0]
        secondary_node = self.get_managed_node_filenames()[1]
        plan_timeout_mins = 60
        self.update_vm_hostnames()
        self.update_network_cs_plan()
        self.setup_add_pkgs()
        self.update_ms_vm()

        # TORF-113124: test_06_p_update_multiple_vm_images_during_idemp
        # Verify used vm-image-2 is in /var/lib/libvirt/images directory on
        # nodes 1 and 2.
        self.assertTrue(
            self._check_image_on_node(self.vm_image_2, primary_node))
        self.assertTrue(
            self._check_image_on_node(self.vm_image_2, secondary_node))

        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        task_desc = 'Remove unused VM image files on node "node2"'

        self.assertTrue(self.wait_for_task_state(self.ms_node,
                                                 task_desc,
                                                 test_constants.
                                                 PLAN_TASKS_SUCCESS,
                                                 False, timeout_mins=20),
                          'No task to remove unused image files')

        self.execute_cli_showplan_cmd(self.ms_node)

        self.restart_litpd_service(self.ms_node)

        # Create and execute plan again and expect it to succeed
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        self.assertTrue(self.wait_for_plan_state(
            self.ms_node,
            test_constants.PLAN_COMPLETE,
            plan_timeout_mins
        ))

        #TORF-279479 & TORF-297880 - verify rules applied
        self.log("info", "Verify expected rules are applied.")
        self.verify_vm_rules_applied(self.ms_node, self.vm1_firewall_rules,
                        self.up_dict1["EXP_IPTABLES_OUTPUT"],
                        self.up_dict1["NETWORK_INTERFACES"]["NET1"]
                        ["ipaddresses"], "test-vm-service-1-n1",
                        self.vm1_rule_coll_path, args='-nL')

        # TORF-271798 TC_18: verify firewall rules work as expected for
        # rhel7.4 based vm service
        upd_vm6 = libvirt_test_data.UPDATED_SERVICE_GROUP_6_DATA
        vm6_cs = upd_vm6["CLUSTER_SERVICE"]
        vm6_service_name = upd_vm6["VM_SERVICE"]["service_name"]
        vm6_ips = self.get_ip_for_vms(self.ms_node)[vm6_cs['name']]
        vm6_fw_rules_path = \
            "{0}vm_service_6/vm_firewall_rules".format(self.srvc_path)
        self.verify_vm_rules_applied(self.ms_node,
                                     upd_vm6["VM_FIREWALL_RULES"],
                                     upd_vm6["EXP_IPTABLES_OUTPUT"],
                                     vm6_ips[0],
                                     vm6_service_name,
                                     vm6_fw_rules_path,
                                     args='-nL')

        self.log("info", "Verify sles fw rules are updated as expected")
        sles_firewall_rules = libvirt_test_data.VM_FIREWALL_RULES_SLES_2
        self.verify_vm_rules_applied(self.ms_node,
                                     sles_firewall_rules,
                                    self.up_dict7["EXP_IPTABLES_OUTPUT"],
                                    self.up_dict7["NETWORK_INTERFACES"]
                                    ["NET1"]["ipaddresses"],
                                    self.up_dict7["VM_SERVICE"]
                                    ["service_name"], self.sles_rule_coll_path,
                                    args='-nL')

        #TORF-279479 & TORF-297880 - verify rule is removed from iptables
        self.log("info", "Verify rule '413 vm_test_rule2' is not "
                 "found in iptables")

        self.verify_vm_rules_applied(self.ms_node,
                                    self.vm1_firewall_rules,
                                    self.up_dict1["RULE_REMOVED"],
                                    self.up_dict1["NETWORK_INTERFACES"]
                                    ["NET1"]["ipaddresses"],
                                    "test-vm-service-1-n1",
                                    self.vm1_rule_coll_path,
                                     expect_present=False,
                                    args='-nL')

        #TORF-279479, TORF-297880, TORF-343548, TORF-422322 tc4- Verify that a
        #vm-firewall-rule item remains as expected after a VM reboot.
        #TORF-474543 added a "service sles start" for the case that sles does
        # not come back up in the specified time
        self.log("info", "Verify that a vm-firewall-rule item remains "
                          "as expected after a VM reboot.")
        self.reboot_vm_rules_persist(self.up_dict1["NETWORK_INTERFACES"]
                                     ["NET1"]["ipaddresses"],
            "test-vm-service-1-n1", self.up_dict1["EXP_IPTABLES_OUTPUT"],
                                     self.vm1_firewall_rules,
                                     self.vm1_rule_coll_path)

        self.reboot_vm_rules_persist(self.up_dict7["NETWORK_INTERFACES"]
                                     ["NET1"]["ipaddresses"],
                                     self.up_dict7["VM_SERVICE"]
                                     ["service_name"], self.up_dict7
                                     ["EXP_IPTABLES_OUTPUT"],
                                     sles_firewall_rules,
                                     self.sles_rule_coll_path)

        # TORF-107476: Verify mounts dont exist
        self._check_mount_conf(self.up_dict3["VM_SERVICE"]["hostnames"],
                               self.up_dict3["NETWORK_INTERFACES"]["NET4"]
                               ["ipaddresses"].split(',')[0],
                               self.up_dict3["VM_RAM_MOUNT"]["type"],
                               self.up_dict3["VM_RAM_MOUNT"]["mount_point"])
        self._check_mount_conf(self.up_dict2["HOSTNAMES"]["hostnames"],
                               self.up_dict2["NETWORK_INTERFACES"]["NET2"]
                               ["ipaddresses"],
                               self.up_dict2["VM_RAM_MOUNT"]["type"],
                               self.up_dict2["VM_RAM_MOUNT"]["mount_point"])
        self._check_mount_conf(self.up_dict1["HOSTNAMES"]["hostnames"],
                               self.up_dict1["NETWORK_INTERFACES"]["NET1"]
                               ["ipaddresses"],
                               self.up_dict1["VM_RAM_MOUNT"]["type"],
                               self.up_dict1["VM_RAM_MOUNT"]["mount_point"])

        # TORF-113124: test_06_p_update_multiple_vm_images_during_idemp
        # Verify unused vm-image-2 has been removed from
        # /var/lib/libvirt/images directory on nodes 1 and 2.
        self.assertFalse(
            self._check_image_on_node(self.vm_image_2, primary_node))
        self.assertFalse(
            self._check_image_on_node(self.vm_image_2, secondary_node))

        lvtd_vm1 = libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA
        lvtd_vm2 = libvirt_test_data.INITIAL_SERVICE_GROUP_2_DATA
        lvtd_vm3 = libvirt_test_data.INITIAL_SERVICE_GROUP_3_DATA
        lvtd_vm5 = libvirt_test_data.UPDATED_SERVICE_GROUP_5_DATA

        # TORF-219762: Verify vm cpu affinity with update cpuset property
        # (from unset value)
        lvtd_vm1_nodelist = lvtd_vm1['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_vm_cpu_affinity(self.model['nodes'],
                                    lvtd_vm1['VM_SERVICE']['service_name'],
                                    lvtd_vm1_nodelist, 'yy')

        # TORF-219762: Verify vm cpu affinity with cpuset update from one
        # value to another
        lvtd_vm2_nodelist = lvtd_vm2['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_vm_cpu_affinity(self.model['nodes'],
                                    lvtd_vm2['VM_SERVICE']['service_name'],
                                    lvtd_vm2_nodelist, '-y')

        # TORF-219762: Verify vm cpu affinity with cpuset property deleted
        lvtd_vm5_nodelist = lvtd_vm5['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_vm_cpu_affinity(self.model['nodes'],
                                    lvtd_vm5['VM_SERVICE']['service_name'],
                                    lvtd_vm5_nodelist, 'yy')

        # TORF-291089: Verify vm cpu affinity with unset cpunodebind property
        # has no cpuset attribute in its vcpu element
        lvtd_vm3_nodelist = lvtd_vm3['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_domain_vcpuset(
                self.model['nodes'],
                lvtd_vm3['VM_SERVICE']['service_name'],
                lvtd_vm3_nodelist, None,
                standby=int(lvtd_vm3['CLUSTER_SERVICE']['standby']),
                vcs_name='Grp_CS_c1_{0}'.format(lvtd_vm3['CLUSTER_SERVICE'][
                                                    'name']))

        # TORF-271798 TC_6: Verify meta-data and network-config files are both
        # present for a rhel7.4 based vm-service deployed under a PL SG
        peer_nodes = {}
        for node in self.model['nodes']:
            peer_nodes[node['url'].split('/')[-1]] = node['name']

        upd_vm6_nodelist = vm6_cs['node_list'].split(',')
        for node in upd_vm6_nodelist:
            node_hostname = peer_nodes[node]
            self.confirm_vm_config_files_on_node(node_hostname,
                                                 vm6_service_name)

        # TORF-271798: verify updated vm service based on rhel7.4 image is up
        # and running with all configurations applied
        sg6_name = 'Grp_CS_c1_CS_VM6'
        sg6_states = self.run_vcs_hagrp_display_command(primary_node,
                                                        sg6_name,
                                                        "State")
        online_nodes = [sg_state['SYSTEM'] for sg_state in
                        sg6_states['State']
                        if "|ONLINE|" in sg_state['VALUE']]
        self.assertEqual(len(online_nodes), int(vm6_cs['active']),
                         'Service Group {0} is not ONLINE on all active nodes'.
                         format(sg6_name))
        for node in online_nodes:
            self.get_service_status_cmd(node, vm6_service_name,
                                        assert_running=True)

        # TORF-271798: ping rhel7.4 based vm-service and make sure reachable
        for ip_addr in vm6_ips:
            self.assertTrue(self.is_ip_pingable(self.ms_node, ip_addr,
                                                timeout_secs=30),
                            "VM ip {0} cannot be pinged".format(ip_addr))

        net_props = upd_vm6["NETWORK_INTERFACES"].values()
        vm_ipv6 = []
        for network in net_props:
            if "ipv6addresses" in network:
                vm_ips = network["ipv6addresses"].split(",")
                for vm_ip in vm_ips:
                    vm_ipv6.append(vm_ip.split("/")[0])
        for ip6_addr in vm_ipv6:
            self.assertTrue(
                self.is_ip_pingable(self.ms_node, ip6_addr.split("/")[0],
                                    ipv4=False, timeout_secs=30),
                "VM ipv6 {0} cannot be pinged".format(ip6_addr.split("/")[0]))

        # TORF-349676 check /etc/hosts file is updated on test-vm-service-1
        vm_aliases = ["IPV6a", "IPV6b"]
        for vm_alias in vm_aliases:
            self.check_host_file_on_vm(
                "test-vm-service-1",
                self.up_dict1["NETWORK_INTERFACES"]["NET1"]["ipaddresses"],
                self.up_dict1["VM_ALIAS"][vm_alias]["alias_names"],
                self.up_dict1["VM_ALIAS"][vm_alias]["address"],
                "1")
