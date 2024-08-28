"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Dec 2015
@author:    Aileen Henry
@summary:   Testset to deploy libvirt vcs functionality
"""

import os
from litp_generic_test import attr
import test_constants
import libvirt_test_data
from testset_libvirt_initial_setup import LibvirtGenericTest


class Libvirtupdate1(LibvirtGenericTest):
    """
    Description:
        This Test class is a combination of multiple user stories related
        to the libvirt module. The test stories that are covered in this
        file are described below
    """
    def setUp(self):
        """
        Setup is used to get site specific data, litp model information,
        network setup and VCS paths in the model
        """
        # 1. Call super class setup
        super(Libvirtupdate1, self).setUp()

        self.model = self.get_litp_model_information()
        self.management_server = self.model["ms"][0]["name"]

        self.srvc_path = self.model["libvirt"]["software_services_path"]
        self.clus_srvs = self.model["libvirt"]["cluster_services_path"]
        self.sw_image = self.model["libvirt"]["software_images_path"]

        self.up_dict1 = libvirt_test_data.UPDATED_SERVICE_GROUP_1_DATA
        self.up_dict2 = libvirt_test_data.UPDATED_SERVICE_GROUP_2_DATA
        self.up_dict3 = libvirt_test_data.UPDATED_SERVICE_GROUP_3_DATA
        self.up_dict4 = libvirt_test_data.UPDATED_SERVICE_GROUP_4_DATA
        self.up_dict5 = libvirt_test_data.UPDATED_SERVICE_GROUP_5_DATA
        self.up_dict6 = libvirt_test_data.VM_IMAGES
        self.up_dict7 = libvirt_test_data.UPDATED_SERVICE_GROUP_SLES_DATA
        self.disk1_dict = libvirt_test_data.DISK1_DATA
        self.up_ms_serv_dict = libvirt_test_data.UPDATE1_MS_VM1_DATA

        self.vm_service_urls = self.find(self.management_server,
                                         self.clus_srvs, "vm-service")
        self.stored_macs_dir = "/tmp/stored_mac_addresses/"
        self.vm_rule_coll_paths = self.find(self.management_server,
                                        '/software',
                                        'collection-of-vm-firewall-rule')
        self.rule_coll_path = [rule_coll_path for rule_coll_path in
        self.vm_rule_coll_paths if 'vm_service_1' in rule_coll_path][0]
        self.sles_rule_coll_path = [rule_coll_path for rule_coll_path in
                    self.vm_rule_coll_paths if self.up_dict7["VM_SERVICE"]
                                    ["service_name"] in rule_coll_path][0]

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Results:
            The super class prints out diagnostics and variables
        """
        super(Libvirtupdate1, self).tearDown()

    def _pre_plan_setup_story7848(self):
        """
        Description:
            Preplan setup steps for story LITPCDS-7848
        """
        # LITPCDS-7848
        # Get MAC addresses before node lock/unlock
        self._get_macs_and_interfaces_before_lock_unlock()
        self._create_network_interface_different_mac_prefix()

    def _get_running_vms(self):
        """
        Get all running VMs
        """
        vms = []
        for vm_service_url in self.vm_service_urls:
            cs_item_id = vm_service_url.rsplit('/', 3)[-3]

            # Select the first interface to ssh into node
            vm_ifaces = self.find(self.management_server, vm_service_url,
                                  'vm-network-interface',
                                  assert_not_empty=False)
            if not vm_ifaces:
                # VM has no interface on which we can ssh into it
                continue

            for iface in sorted(vm_ifaces):
                vm_ipaddrs = self.get_props_from_url(
                                        self.management_server,
                                        iface, 'ipaddresses').split(',')
                if vm_ipaddrs[0] != "dhcp":
                    break

            counter = 0
            for vm_ipaddr in vm_ipaddrs:
                vm_identifier = cs_item_id + '_' + str(counter)
                counter += 1
                vms.append(vm_identifier)
                self.add_vm_to_nodelist(
                    vm_identifier,
                    vm_ipaddr,
                    username=test_constants.LIBVIRT_VM_USERNAME,
                    password=test_constants.LIBVIRT_VM_PASSWORD)

        return vms

    def _get_mac_addresses_on_vm(self, v_m, include_ifaces=False):
        """
        Get list of all network interfaces and their MAC addresses from a VM

        Args:
            v_m: (object) The VM object which includes the IP address to be
                          used to ssh into the VM
            include_ifaces: (boolean) If False, just return the list of mac
                addresses on the VM. If True return dictionary with a key of
                interfaces a value of the list of mac addresses
        Returns:
            A dictionary that associates MAC address to each network interface
            or a list of MAC addresses
        """

        if "SLES" in v_m:
            os_vers, _, _ = self.run_command(v_m, "{0} {1}".format(
                test_constants.TAIL_PATH, test_constants.SLES_RELEASE_FILE),
                                         password=test_constants.
                                             LIBVIRT_SLES_VM_PASSWORD,
                                         add_to_cleanup=False,
                                         default_asserts=True)
            os_vers = os_vers[3]
        else:
            os_vers, _, _ = self.run_command(v_m, "{0} {1}".format(
                test_constants.TAIL_PATH, test_constants.RH_RELEASE_FILE),
                                         add_to_cleanup=False,
                                         default_asserts=True)
        if test_constants.RH_VERSION_6 in os_vers or \
                test_constants.RH_VERSION_6_10 in os_vers:
            cmd = " | ".join([
                r"/sbin/ifconfig -a",
                r"/bin/grep HWaddr",
                r"/bin/sed 's/^\(\S\+\).*HWaddr \(\S\+\)/\1 \2/g'"])
        elif test_constants.RH_VERSION_7 in os_vers or \
                test_constants.RH_VERSION_7_4 in os_vers:
            cmd = "ip -o link show | grep 'link/ether' |  " \
                      "awk '{print $2, $15}' | sed -e 's/://1'"
        elif test_constants.SLES_VERSION_15_4 in os_vers:
            cmd = "ip -o link show | grep 'link/ether' |  " \
                      "awk '{print $2, $17}' | sed -e 's/://1'"
        stdout, stderr, return_code = self.run_command(v_m, cmd,
                                                       execute_timeout=5)
        self.assertNotEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, return_code)

        macs = []
        macs_iface = {}
        for line in stdout:
            if_name, if_mac = line.rstrip().split(" ")
            macs_iface[if_name] = if_mac.upper()
            macs.append(if_mac.upper())

        if include_ifaces:
            return macs_iface

        return macs

    def _get_macs_and_interfaces_before_lock_unlock(self):
        """
        Description:
            Ensure that MAC addresses of all VMs are the same after a node lock
            Note: Store all MAC addresses in the filesystem. The check after
                node lock is made by method _check_macs_after_lock_unlock

        Steps:
            Execute command to obtain allow MAC addresses from each running VM
            Create a dictionary object with vms, interfaces, and mac addresses
            Write dictionary to local file system
        """
        all_vms = self._get_running_vms()
        all_macs_and_inferfaces_before = {}
        macs_if_file_location = (self.stored_macs_dir +
                                 "test7848_macs-iface-before-lock")
        for v_m in all_vms:
            all_macs_and_inferfaces_before[v_m] = \
                self._get_mac_addresses_on_vm(v_m, include_ifaces=True)
        # Dictionary object example:
        # {u'cs1_10.10.11.206': {'eth3': '52:54:00:6A:80:E6'}}

        cmd = "/bin/mkdir -p {0}".format(self.stored_macs_dir)
        stdout, stderr, r_code = self.run_command(self.management_server, cmd)
        self.assertEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, r_code)

        cmd = '/bin/echo "{0}" > {1}'.format(
            str(all_macs_and_inferfaces_before), macs_if_file_location)
        stdout, stderr, r_code = self.run_command(self.management_server, cmd)
        self.assertEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, r_code)

    def _create_network_interface_different_mac_prefix(self):
        """
        Retrieve a 2 node parallel VCS service group, and on that VCS
            service group, determine the vm-network-interfaces that the
            vm-service has
        Add a new vm-network-interface on that VCS service group that uses
            a mac_prefix. The device_name should be 1 greater that the
            highest eth, and the item_id is prefix_iface
        """
        if_data = libvirt_test_data\
            .UPDATED_SERVICE_GROUP_4_DATA["NETWORK_INTERFACES"]["IF_PREFIX"]
        stdout, stderr, r_code = self.execute_cli_create_cmd(
            self.management_server, self.srvc_path +
                        "vm_service_4/vm_network_interfaces/prefix_iface",
            "vm-network-interface",
            props="network_name='{0}' device_name='{1}' host_device='{2}'\
                 ipaddresses='{3}' mac_prefix='{4}'".format(
                if_data["network_name"],
                if_data["device_name"],
                if_data["host_device"],
                if_data["ipaddresses"],
                if_data["mac_prefix"]
            ),
            add_to_cleanup=False)

        self.assertEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, r_code)

    def setup_add_pkgs(self):
        """
        Description:
            - LITPCDS-7186 - As a LITP User I want to define
                            VM packages and repos
        Actions:
            1. Create folder and copy the RPMs to MS
            2. Using litp import all appropriate packages into
               appropriate directories
        Results:
            All packages are available in appropriate repos
        """
        # Create repo directories
        repo1_path = "/var/www/html/libvirt_repo1"
        repo2_path = "/var/www/html/libvirt_repo2"
        repo3_path = "/var/www/html/libvirt_repo3"
        repo4_path = "/var/www/html/ncm2"
        repo1_ms_path = "/var/www/html/libvirt_repo1_ms_srv"
        repo2_ms_path = "/var/www/html/libvirt_repo2_ms_srv"
        self.create_dir_on_node(self.management_server, repo1_path,
                                su_root=True, add_to_cleanup=False)
        self.create_dir_on_node(self.management_server, repo2_path,
                                su_root=True, add_to_cleanup=False)
        self.create_dir_on_node(self.management_server, repo3_path,
                                su_root=True, add_to_cleanup=False)
        self.create_dir_on_node(self.management_server, repo4_path,
                                su_root=True, add_to_cleanup=False)
        self.create_dir_on_node(self.management_server, repo1_ms_path,
                                su_root=True, add_to_cleanup=False)
        self.create_dir_on_node(self.management_server, repo2_ms_path,
                                su_root=True, add_to_cleanup=False)

        repo_dir = test_constants.PARENT_PKG_REPO_DIR
        lib1 = 'libvirt_repo1'
        lib2 = 'libvirt_repo2'
        lib3 = 'libvirt_repo3'
        lib4 = 'ncm2'
        lib_ms1 = 'libvirt_repo1_ms_srv'
        lib_ms2 = 'libvirt_repo2_ms_srv'
        list_of_repos = {
            lib1: ['empty_testrepo1_rpm1.rpm',
                   'empty_testrepo1_rpm2.rpm',
                   "empty_rpm2.rpm",
                    "empty_rpm3.rpm"],
            lib2: ['empty_testrepo2_rpm1.rpm',
                   'empty_testrepo2_rpm2.rpm'],
            lib3: ['empty_testrepo3_rpm1.rpm',
                   'empty_testrepo3_rpm2.rpm'],
            lib4: ["empty_rpm3.rpm", "empty_rpm9.rpm"],
            lib_ms1: ["empty_testrepo1_rpm3.rpm",
                     "empty_testrepo1_rpm4.rpm"],
            lib_ms2: ["empty_testrepo2_rpm3.rpm"]
        }

        for repo in list_of_repos:
            filelist = []
            for package in list_of_repos[repo]:
                # Copy RPMs to Management Server
                filelist.append(self.get_filelist_dict(
                    '{0}/{1}'.format(os.path.dirname(os.path.realpath(__file__)
                                        ) + "/rpms", package), "/tmp/"))

            self.copy_filelist_to(
                self.management_server,
                filelist,
                add_to_cleanup=False,
                root_copy=True)

            # Use LITP import to add to repo for each RPM
            for package in list_of_repos[repo]:
                self.execute_cli_import_cmd(
                    self.management_server,
                    '/tmp/{0}'.format(package),
                    repo_dir + repo)

    def update_network_cs_plan_1(self):
        """
        Description:
            Update properties of the five service groups.
        """
        #URL variables
        sg1_vm = self.clus_srvs + \
                            "/CS_VM1/applications/vm_service_1"
        sg2_vm = self.clus_srvs + \
                            "/CS_VM2/applications/vm_service_2"
        sg3_vm = self.clus_srvs + \
                            "/CS_VM3/applications/vm_service_3"
        sg4_vm = self.clus_srvs + \
                            "/CS_VM4/applications/vm_service_4"
        sg5_vm = self.clus_srvs + \
                            "/CS_VM5/applications/vm_service_5"

        vm_service_1_path = self.srvc_path + "vm_service_1"
        vm_service_2_path = self.srvc_path + "vm_service_2"
        vm_service_3_path = self.srvc_path + "vm_service_3"
        vm_service_4_path = self.srvc_path + "vm_service_4"
        vm_service_5_path = self.srvc_path + "vm_service_5"
        vm_service_sles_path = self.srvc_path + "sles"

        #Props variables
        prop_ali = "alias_names='{0}' address='{1}'"
        prop_net = "host_device='{0}' network_name='{1}' device_name='{2}'"

        #########################
        #                       #
        #  Service Group CS_VM1 #
        #                       #
        #########################
        #Dictionary variables for SG1
        dict1 = self.up_dict1
        net20 = dict1["NETWORK_INTERFACES"]["NET20"]
        net21 = dict1["NETWORK_INTERFACES"]["NET21"]
        dict_1_pkgs = dict1["PACKAGES"]
        dict_1_rpo = dict1["YUM_REPOS"]
        dict_1_vms = dict1["VM_SERVICE"]
        dict_1_ali = self.up_dict1["VM_ALIAS"]
        dict1_vm_ram_mount = dict1["VM_RAM_MOUNT"]

        #TORF-279479 & TORF-297880 - Create vm-firewall-rule(s) v4 & v6
        for rule in libvirt_test_data.VM_FIREWALL_RULES_1:
            item_path = '{0}/{1}'.format(self.rule_coll_path,
                                         rule["item_name"])

            self.execute_cli_create_cmd(self.management_server, item_path,
                                        'vm-firewall-rule',
                                        props=rule["props"],
                                        add_to_cleanup=False)

        #LITPCDS-7179 - Update vm hostnames
        self.execute_cli_update_cmd(self.management_server,
                                    sg1_vm,
                                    props="hostnames='{0}'"
                                    .format(dict_1_vms["hostnames"]))
        #LITPCDS-7179 - Create vm network interfaces
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_network_interfaces/net20",
                                    "vm-network-interface",
                                    props=prop_net.format(net20[
                                                          "host_device"],
                                                      net20[
                                                          "network_name"],
                                                      net20[
                                                          "device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_network_interfaces/net21",
                                    "vm-network-interface",
                                    props=prop_net.format(net21[
                                                          "host_device"],
                                                      net21[
                                                          "network_name"],
                                                      net21[
                                                          "device_name"]),
                                    add_to_cleanup=False)
        # Update ip addresses of inherited vm network interfaces
        self.execute_cli_update_cmd(self.management_server,
                                    sg1_vm + \
                                    "/vm_network_interfaces/net20",
                                    props="ipaddresses='{0}'".format(
                                    net20["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg1_vm + \
                                    "/vm_network_interfaces/net21",
                                    props="ipaddresses='{0}'".format(
                                    net21["ipaddresses"]))

        #LITPCDS-7184 - Create vm aliases
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_aliases/db20",
                                    "vm-alias",
                                    props=prop_ali.format(dict_1_ali["DB20"][
                                                          "alias_names"],
                                                     dict_1_ali["DB20"][
                                                         "address"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_aliases/db21",
                                    "vm-alias",
                                    props=prop_ali.format(dict_1_ali["DB21"][
                                                          "alias_names"],
                                                           dict_1_ali["DB21"][
                                                               "address"]),
                                    add_to_cleanup=False)

        # TORF-349676 - Create vm aliases with IPv6 address containing prefix
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_aliases/ipv6a",
                                    "vm-alias",
                                    props=prop_ali.format(dict_1_ali["IPV6a"][
                                                              "alias_names"],
                                                          dict_1_ali["IPV6a"][
                                                              "address"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_aliases/ipv6b",
                                    "vm-alias",
                                    props=prop_ali.format(dict_1_ali["IPV6b"][
                                                              "alias_names"],
                                                          dict_1_ali["IPV6b"][
                                                              "address"]),
                                    add_to_cleanup=False)

        #LITPCDS-7186 - Create vm packages
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_1_path + \
                                "/vm_packages/empty_testrepo1_rpm1",
                                "vm-package",
                                props="name='{0}'".format(dict_1_pkgs["PKG1"][
                                                      "name"]),
                                add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_1_path + \
                                "/vm_packages/empty_rpm3",
                                "vm-package",
                                props="name='{0}'".format(dict_1_pkgs["PKG2"][
                                                      "name"]),
                                add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_1_path + \
                                "/vm_packages/empty_testrepo2_rpm1",
                                "vm-package",
                                props="name='{0}'".format(dict_1_pkgs["PKG3"][
                                                      "name"]),
                                add_to_cleanup=False)
        #LITPCDS-7186 - Create vm repos
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_yum_repos/libvirt_repo1",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'".format(
                                        dict_1_rpo["libvirt_repo1"]["name"],
                                        dict_1_rpo[
                                            "libvirt_repo1"]["base_url"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + \
                                    "/vm_yum_repos/libvirt_repo2",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'".format(
                                        dict_1_rpo["libvirt_repo2"]["name"],
                                        dict_1_rpo[
                                            "libvirt_repo2"]["base_url"]),
                                    add_to_cleanup=False)
        #LITPCDS-585 - Update vm properties
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_1_path,
                                    props="cpus='{0}' ram='{1}'".format(
                                        dict_1_vms["cpus"], dict_1_vms["ram"]))

        #LITPCDS-7535 - Update internal status check
        self.execute_cli_update_cmd(self.management_server, vm_service_1_path,
                                    props="internal_status_check={0}"
                                    .format(
                                        dict_1_vms["internal_status_check"]
                                    ))
        # TORF-107476 - TC06 & TC15 - update vm_ram_mount RH7 to ramfs,
        # different mount point and mount options
        self.execute_cli_update_cmd(self.management_server, vm_service_1_path +
                                    "/vm_ram_mounts/vm_ram_mount_1",
                                    props="type='{0}' mount_point='{1}' "
                                          "mount_options='{2}'"
                                    .format(dict1_vm_ram_mount["type"],
                                            dict1_vm_ram_mount["mount_point"],
                                            dict1_vm_ram_mount["mount_options"]
                                            ))

        # TORF-107476 - TC06 & TC15 - update vm_ram_mount RH7 to ramfs,
        # different mount point and mount options
        self.execute_cli_update_cmd(self.management_server, vm_service_1_path +
                                    "/vm_ram_mounts/vm_ram_mount_1",
                                    props="type='{0}' mount_point='{1}' "
                                          "mount_options='{2}'"
                                    .format(dict1_vm_ram_mount["type"],
                                            dict1_vm_ram_mount["mount_point"],
                                            dict1_vm_ram_mount["mount_options"]
                                            ))

        # TORF-180365 - TC05
        # update vm custom script names
        self.execute_cli_update_cmd(self.management_server, vm_service_1_path +
                                    "/vm_custom_script/vm_custom_script_1",
                                    props="custom_script_names='{0}' "
                                    .format(
                                        dict1["VM_CUSTOM_SCRIPT"][
                                            "custom_script_names"]))

        # TORF-195147 - TC03
        # update status_timeout to be a valid timeout value
        self.execute_cli_update_cmd(self.management_server, self.clus_srvs +
                                    "/CS_VM1/ha_configs/service_config",
                                    props="status_timeout='{0}'".format(
                                        dict1["HA_CONFIG"]["status_timeout"]))

        #############################
        #                           #
        #  Service Group CS_SLES_VM #
        #                           #
        #############################
        #Dictionary variables for SLES
        dict7 = self.up_dict7
        dict7_cs = dict7["VM_CUSTOM_SCRIPT"]
        dict7_zp = dict7["ZYPPER_REPOS"]
        dict7_pk = dict7["PACKAGES"]
        sles_fw_path = vm_service_sles_path + "/vm_firewall_rules/"

        # TORF-406586 update vm custom script names
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_sles_path +
                                    "/vm_custom_script/vm_custom_script",
                                    props="custom_script_names='{0}' "
                                    .format(dict7_cs["custom_script_names"]))

        # TORF-404805 update vm zypper repo base_url
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_sles_path +
                                    "/vm_zypper_repos/repo_NCM",
                                    props="base_url='{0}' "
                                    .format(dict7_zp["NCM"]["base_url"]))

        # TORF-404805 update package under zypper repo
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_sles_path +
                                    "/vm_packages/pkg_empty_rpm",
                                    props="name='{0}' "
                                    .format(dict7_pk["PKG1"]["name"]))

        # TORF-422322 - Create IPv4 & IPv6 vm-firewall-rules for sles
        for rule in libvirt_test_data.VM_FIREWALL_RULES_SLES_1:
            self.execute_cli_create_cmd(self.management_server, sles_fw_path
                                        + rule["item_name"],
                                        'vm-firewall-rule',
                                        props=rule["props"],
                                        add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM2 #
        #                       #
        #########################
        #Dictionary variables for SG2
        dict2 = self.up_dict2
        net22 = dict2["NETWORK_INTERFACES"]["NET22"]
        net23_ip = net22["ipaddresses"]
        dict2_rpo = dict2["YUM_REPOS"]
        dict2_ali = dict2["VM_ALIAS"]
        dict2_vm_ram_mount = dict2["VM_RAM_MOUNT"]

        #LITPCDS-7179 - Update vm hostnames
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm,
                                    props="hostnames='{0}'"
                                    .format(dict2["VM_SERVICE"]["hostnames"]))
        #LITPCDS-7179 - Create vm network interfaces
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_2_path + \
                                    "/vm_network_interfaces/net22",
                                    "vm-network-interface",
                                    props=prop_net.format(net22[
                                                          "host_device"],
                                                      net22[
                                                          "network_name"],
                                                      net22[
                                                          "device_name"]),
                                    add_to_cleanup=False)
        #LITPCDS-7179 - Update network interface ip address
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm + \
                                    "/vm_network_interfaces/net22",
                                    props="ipaddresses='{0}'".format(net23_ip))
        #LITPCDS-7184 - Create vm aliases
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_2_path + \
                                    "/vm_aliases/db22",
                                    "vm-alias",
                                    props=prop_ali.format(dict2_ali["DB22"][
                                                          "alias_names"],
                                                           dict2_ali["DB22"][
                                                               "address"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_2_path + \
                                    "/vm_aliases/db23",
                                    "vm-alias",
                                    props=prop_ali.format(dict2_ali["DB23"][
                                                          "alias_names"],
                                                           dict2_ali["DB23"][
                                                               "address"]),
                                    add_to_cleanup=False)
        #LITPCDS-7186 - Create vm yum repos
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_2_path + \
                                    "/vm_yum_repos/libvirt_repo1",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'".format(
                                        dict2_rpo["libvirt_repo1"]["name"],
                                        dict2_rpo[
                                            "libvirt_repo1"]["base_url"]),
                                    add_to_cleanup=False)
        # TORF-107476 - TC05 & TC14 - update vm_ram_mount RH6 to ramfs,
        # different mount point and mount options
        self.execute_cli_update_cmd(self.management_server, vm_service_2_path +
                                    "/vm_ram_mounts/vm_ram_mount_2",
                                    props="type='{0}' mount_point='{1}' "
                                          "mount_options='{2}'"
                                    .format(dict2_vm_ram_mount["type"],
                                            dict2_vm_ram_mount["mount_point"],
                                            dict2_vm_ram_mount["mount_options"]
                                            ))

        #########################
        #                       #
        #  Service Group CS_VM3 #
        #                       #
        #########################

        #Dictionary variables for SG3
        dict3_net23 = self.up_dict3["NETWORK_INTERFACES"]["NET23"]
        dict3_net24 = self.up_dict3["NETWORK_INTERFACES"]["NET24"]
        d3_nt23_ip = dict3_net23["ipaddresses"]
        d3_nt24_ip = dict3_net24["ipaddresses"]
        dict3_mt16 = self.up_dict3["NFS_MOUNTS"]["VM_MOUNT16"]
        dict3_mt17 = self.up_dict3["NFS_MOUNTS"]["VM_MOUNT17"]
        dict3_mt18 = self.up_dict3["NFS_MOUNTS"]["VM_MOUNT18"]
        dict3_ali = self.up_dict3["VM_ALIAS"]

        #LITPCDS-7179 - Update vm hostnames
        self.execute_cli_update_cmd(self.management_server,
                                    sg3_vm,
                                    props="hostnames='{0}'".format(
                                    self.up_dict3["VM_SERVICE"]["hostnames"]))
        #LITPCDS-7179 - Create vm network interfaces
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_3_path + \
                                    "/vm_network_interfaces/net23",
                                    "vm-network-interface",
                                    props=prop_net.format(dict3_net23[
                                                          "host_device"],
                                                      dict3_net23[
                                                          "network_name"],
                                                      dict3_net23[
                                                          "device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_3_path + \
                                    "/vm_network_interfaces/net24",
                                    "vm-network-interface",
                                    props=prop_net.format(dict3_net24[
                                                          "host_device"],
                                                      dict3_net24[
                                                          "network_name"],
                                                      dict3_net24[
                                                          "device_name"]),
                                    add_to_cleanup=False)
        #LITPCDS-7179 - Update network interfaces
        self.execute_cli_update_cmd(self.management_server,
                                    sg3_vm + \
                                    "/vm_network_interfaces/net23",
                                    props="ipaddresses='{0}'"
                                    .format(d3_nt23_ip))
        self.execute_cli_update_cmd(self.management_server,
                                    sg3_vm + \
                                    "/vm_network_interfaces/net24",
                                    props="ipaddresses='{0}'"
                                    .format(d3_nt24_ip))
        #LITPCDS-12817 - Remove network interface
        self.execute_cli_remove_cmd(self.management_server, vm_service_3_path \
                                              + "/vm_network_interfaces/net33")
        #LITPCDS-12817 - Update network interface device_name to preserve
        #consecutiveness of device names
        self.execute_cli_update_cmd(self.management_server, vm_service_3_path \
                                    + "/vm_network_interfaces/net34",
                                    props="device_name='{0}'"
                                    .format(self.up_dict3["NETWORK_INTERFACES"]
                                                     ["NET34"]['device_name']))
        #LITPCDS-7184 - Create vm aliases
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_3_path + \
                                    "/vm_aliases/db24",
                                    "vm-alias",
                                    props=prop_ali.format(dict3_ali["DB24"][
                                                          "alias_names"],
                                                           dict3_ali["DB24"][
                                                               "address"]),
                                    add_to_cleanup=False)
        #LITPCDS-7815 - Create vm nfs mounts
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_3_path + \
                                    "/vm_nfs_mounts/vm_nfs_mount_16",\
                                    "vm-nfs-mount",\
                                    props="device_path='{0}' mount_point='{1}'"
                                    .format(dict3_mt16["device_path"],\
                                    dict3_mt16["mount_point"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_3_path + \
                                "/vm_nfs_mounts/vm_nfs_mount_17",
                                    "vm-nfs-mount",
                                props="device_path='{0}' mount_point='{1}' "
                                      "mount_options='{2}'".format(dict3_mt17[
                                                      "device_path"],
                                                  dict3_mt17[
                                                      "mount_point"],
                                                  dict3_mt17[
                                                      "mount_options"]),
                                add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_3_path + \
                                "/vm_nfs_mounts/vm_nfs_mount_18",
                                "vm-nfs-mount",
                                props="device_path='{0}' mount_point='{1}'"
                                    .format(dict3_mt18[
                                                      "device_path"],
                                                  dict3_mt18[
                                                      "mount_point"]),
                                add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM4 #
        #                       #
        #########################

        #Dictionary variables
        dict4_net25 = self.up_dict4["NETWORK_INTERFACES"]["NET25"]
        d4_nt25_ip = dict4_net25["ipaddresses"]
        dict4_pkgs = self.up_dict4["PACKAGES"]
        dict4_rpo = self.up_dict4["YUM_REPOS"]
        dict4_vms = self.up_dict4["VM_SERVICE"]
        dict4_ali = self.up_dict4["VM_ALIAS"]
        dict4_vm_custom_script = self.up_dict4["VM_CUSTOM_SCRIPT"]

        #LITPCDS-7179 - Update vm hostnames
        self.execute_cli_update_cmd(self.management_server,
                                    sg4_vm,
                                    props="hostnames='{0}'".format(
                                    self.up_dict4["VM_SERVICE"]["hostnames"]))
        #LITPCDS-7179 - Create vm network interfaces
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_4_path + \
                                    "/vm_network_interfaces/net25",
                                    "vm-network-interface",
                                    props=prop_net.format(dict4_net25[
                                                          "host_device"],
                                                      dict4_net25[
                                                          "network_name"],
                                                      dict4_net25[
                                                          "device_name"]),
                                    add_to_cleanup=False)
        #LITPCDS-7179 - Update net interface ip
        self.execute_cli_update_cmd(self.management_server,
                                    sg4_vm + \
                                    "/vm_network_interfaces/net25",
                                    props="ipaddresses='{0}'"
                                    .format(d4_nt25_ip))
        #LITPCDS-7184 - Create vm aliases
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_4_path + \
                                    "/vm_aliases/db25",
                                    "vm-alias",
                                    props=prop_ali.format(dict4_ali["DB25"][
                                                          "alias_names"],
                                                           dict4_ali["DB25"][
                                                               "address"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_4_path + \
                                    "/vm_aliases/db26",
                                    "vm-alias",
                                    props=prop_ali.format(dict4_ali["DB26"][
                                                          "alias_names"],
                                                           dict4_ali["DB26"][
                                                               "address"]),
                                    add_to_cleanup=False)
        #LITPCDS-7186 - Create vm packages
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_4_path + \
                                    "/vm_packages/empty_rpm1",\
                                    "vm-package",\
                                    props="name='{0}'"
                                    .format(dict4_pkgs["EMPTY_RPM1"]["name"]),
                                    add_to_cleanup=False)

        #LITPCDS-7188 - Update package names
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_4_path + \
                                    "/vm_packages/pkg_empty_rpm7",
                                    props="name='{0}'"
                                    .format(
                                        dict4_pkgs["PKG_EMPTY_RPM7"]["name"]))

        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_4_path + \
                                    "/vm_packages/pkg_empty_rpm6",
                                    props="name='{0}'"
                                    .format(
                                        dict4_pkgs["PKG_EMPTY_RPM6"]["name"]))
        #LITPCDS-7186 - Create vm yum repos
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_4_path + \
                                    "/vm_yum_repos/libvirt_repo1",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'"
                                    .format(dict4_rpo["libvirt_repo1"]["name"],
                                            dict4_rpo["libvirt_repo1"][
                                                "base_url"]),
                                    add_to_cleanup=False)
        #LITPCDS-585 - Update cpu and ram properties
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_4_path,
                                    props="cpus='{0}' ram='{1}'".format(
                                        dict4_vms["cpus"],
                                        dict4_vms["ram"]))

        # TORF-180365 - TC05, TORF - 180367 - TC22
        # update vm custom script names
        self.execute_cli_update_cmd(self.management_server, vm_service_4_path +
                                    "/vm_custom_script/vm_custom_script_1",
                                    props="custom_script_names='{0}' "
                                    .format(
                                        dict4_vm_custom_script[
                                            "custom_script_names"]))

        #########################
        #                       #
        #  Service Group CS_VM5 #
        #                       #
        #########################
        # Dictionary variables
        dict5 = self.up_dict5
        dict5_net26 = dict5["NETWORK_INTERFACES"]["NET26"]
        dict5_nt26_ip = dict5_net26["ipaddresses"]
        dict5_pkgs = dict5["PACKAGES"]
        dict5_rpo = dict5["YUM_REPOS"]
        dict5_vms = dict5["VM_SERVICE"]
        dict5_ali = dict5["VM_ALIAS"]
        dict5_vm_ram_mnt = dict5["VM_RAM_MOUNT"]
        dict5_vm_custom_script = dict5["VM_CUSTOM_SCRIPT"]

        # TORF-107476 - TC13 - Contract Service group and add VM_RAM_MOUNT
        self.execute_cli_update_cmd(self.management_server,
                                    self.clus_srvs + "/CS_VM5",
                                    props="active={0} standby={1} "
                                          "node_list={2}"
                                    .format(
                                        dict5["CLUSTER_SERVICE"]["active"],
                                        dict5["CLUSTER_SERVICE"]["standby"],
                                        dict5["CLUSTER_SERVICE"]["node_list"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg5_vm + "/vm_network_interfaces/net11",
                                    props="ipaddresses='{0}'".format(
                                        dict5["NETWORK_INTERFACES"]["NET11"]
                                        ["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg5_vm + "/vm_network_interfaces/net12",
                                    props="ipaddresses='{0}'".format(
                                        dict5["NETWORK_INTERFACES"]["NET12"]
                                        ["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg5_vm + "/vm_network_interfaces/net13",
                                    props="ipaddresses='{0}'".format(
                                        dict5["NETWORK_INTERFACES"]["NET13"]
                                        ["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg5_vm + "/vm_network_interfaces/net14",
                                    props="ipaddresses='{0}'".format(
                                        dict5["NETWORK_INTERFACES"]["NET14"]
                                        ["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg5_vm + "/vm_network_interfaces/net15",
                                    props="ipv6addresses='{0}'"
                                          " ipaddresses='{1}'".format(
                                        dict5["NETWORK_INTERFACES"]["NET15"]
                                        ["ipv6addresses"], dict5
                                        ["NETWORK_INTERFACES"]["NET15"]
                                        ["ipaddresses"]))

        #LITPCDS-7179 - Update vm hostnames
        self.execute_cli_update_cmd(self.management_server,
                                    sg5_vm,
                                    props="hostnames='{0}'"
                                    .format(dict5["VM_SERVICE"]["hostnames"]))
        #LITPCDS-7179 - Create vm network interface
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_network_interfaces/net26",
                                    "vm-network-interface",
                                    props=prop_net.format(dict5_net26[
                                                          "host_device"],
                                                      dict5_net26[
                                                          "network_name"],
                                                      dict5_net26[
                                                          "device_name"]),
                                    add_to_cleanup=False)
        #LITPCDS-7179 - Update ip of vm net interface
        self.execute_cli_update_cmd(self.management_server,
                                    sg5_vm + \
                                    "/vm_network_interfaces/net26",
                                    props="ipaddresses='{0}'"
                                    .format(dict5_nt26_ip))
        #LITPCDS-7184 - Create vm aliases
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_aliases/db27",
                                    "vm-alias",
                                    props=prop_ali.format(dict5_ali["DB27"][
                                                          "alias_names"],
                                                            dict5_ali["DB27"][
                                                               "address"]),
                                    add_to_cleanup=False)
        #LITPCDS-7186 - Create vm packages
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_packages/empty_testrepo1_rpm1",
                                    "vm-package",
                                    props="name='{0}'"
                                    .format(
                                        dict5_pkgs["EMPTY_TESTREPO1_RPM1"][
                                            "name"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_packages/empty_rpm3",
                                    "vm-package",
                                    props="name='{0}'"
                                    .format(dict5_pkgs["EMPTY_RPM3"]["name"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_packages/empty_rpm2",
                                    "vm-package",
                                    props="name='{0}'"
                                    .format(dict5_pkgs["EMPTY_RPM2"]["name"]),
                                    add_to_cleanup=False)

        #LITPCDS-7186 - Create vm yum repos
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_yum_repos/libvirt_repo1",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'"
                                    .format(
                                        dict5_rpo["libvirt_repo1"]["name"],
                                        dict5_rpo["libvirt_repo1"][
                                                "base_url"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_yum_repos/libvirt_repo2",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'"
                                    .format(
                                        dict5_rpo["libvirt_repo2"]["name"],
                                        dict5_rpo["libvirt_repo2"][
                                                "base_url"]),
                                    add_to_cleanup=False)
        # TORF-107476 - TC13 - Add VM_RAM_MOUNT to CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_5_path + \
                                    "/vm_ram_mounts/vm_ram_mount_5",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    .format(
                                      dict5_vm_ram_mnt["type"],
                                      dict5_vm_ram_mnt["mount_point"]),
                                    add_to_cleanup=False)

        #LITPCDS-585 - Update cpu no. and RAM
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_5_path,
                                    props="cpus='{0}' ram='{1}'".format(
                                        dict5_vms["cpus"], dict5_vms["ram"]))

        # TORF-113124: test_04_p_update_vm_image_on_vm_service: Update the
        # VM-Image used from VM-service-5 to vm_image_2
        self.execute_cli_update_cmd(self.management_server, vm_service_5_path,
                                    props="image_name={0}".format(
                                        self.up_dict5["VM_SERVICE"]
                                        ["image_name"]))

        # TORF-180365 - TC05
        # TORF-180367 - TC22, TC12
        # update vm custom script names
        self.execute_cli_update_cmd(self.management_server, vm_service_5_path +
                                    "/vm_custom_script/vm_custom_script_1",
                                    props="custom_script_names='{0}' "
                                    .format(
                                        dict5_vm_custom_script[
                                            "custom_script_names"]))

    def update_vm_software_images(self):
        """
        Description:
            - LITPCDS-7182 - As a LITP User I want to update my VM image
        Actions:
            1. Update the source uri of vm_image1
            2. Update the source uri of vm_image2
            3. Update the source uri of vm_image3
        """
        fmt1 = self.up_dict6["VM_IMAGE1"][
            "image_url"]
        fmt2 = self.up_dict6["VM_IMAGE2"][
            "image_url"]
        fmt3 = self.up_dict6["VM_IMAGE3"][
            "image_url"]
        prop = "source_uri='{0}'"
        self.execute_cli_update_cmd(self.management_server,
                                    self.sw_image + \
                                    "vm_image_1",
                                    props=prop.format(fmt1))
        self.execute_cli_update_cmd(self.management_server,
                                    self.sw_image + \
                                    "vm_image_2",
                                    props=prop.format(fmt2))
        self.execute_cli_update_cmd(self.management_server,
                                    self.sw_image + \
                                    "vm_image_3",
                                    props=prop.format(fmt3))

    def update_ms1_sg(self):
        """
        Description:
            LITPCDS-11387 - As a LITP user I want to specify additional
                            filesystems for my VM
        """
        # LITPCDS-11387 - Create path variables
        ms_vm_sg = "/ms/services/MS_VM1"
        fs2 = "/infrastructure/storage/storage_profiles/" \
              "sp11387/volume_groups/vg1/file_systems/fs2"
        disk1_dict = self.disk1_dict
        up_ms_serv_dict = self.up_ms_serv_dict

        #LITPCDS-11387 - Update mount_point property of vm disk
        self.execute_cli_update_cmd(self.management_server,
                                    ms_vm_sg + "/vm_disks/vmd1",
                                    props="mount_point='{0}'".
                                    format(
                                        up_ms_serv_dict["VM_DISK"][
                                            "VMD1"]["mount_point"]))

        #LITPCDS-11387 - Create file system
        self.execute_cli_create_cmd(self.management_server,
                                    fs2,
                                    "file-system",
                                    props="type='{0}' mount_point='{1}' " \
                                          "size='{2}'".
                                    format(
                                        disk1_dict["VOLUME_GROUP"][
                                            "VG1"]["file_system"]["fs2"][
                                            "type"],
                                        disk1_dict["VOLUME_GROUP"][
                                            "VG1"]["file_system"]["fs2"][
                                            "mount_point"],
                                        disk1_dict["VOLUME_GROUP"][
                                            "VG1"]["file_system"]["fs2"][
                                            "size"]),
                                    add_to_cleanup=False)

        #LITPCDS-11387 - Create additional vm-disk items
        self.execute_cli_create_cmd(self.management_server,
                                    ms_vm_sg + "/vm_disks/vmd2",
                                    "vm-disk",
                                    props="host_volume_group='{0}' " \
                                          "host_file_system='{1}' " \
                                          "mount_point='{2}'".
                                    format(
                                        up_ms_serv_dict["VM_DISK"]["VMD2"][
                                            "host_volume_group"],
                                        up_ms_serv_dict["VM_DISK"]["VMD2"][
                                            "host_file_system"],
                                        up_ms_serv_dict["VM_DISK"]["VMD2"][
                                            "mount_point"]),
                                    add_to_cleanup=False)

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

    def _confirm_vm_custom_script_on_node(self, node, service_name,
                                          vm_custom_script):
        """
        Description:
        TORF-180365: Test method to check vm custom scripts are present inside
        service_name userdata file on the node.
        :param node: node on which we run the check
        :param service_name: name of the vm-service that contains the scripts
        :param vm_custom_script: custom scripts
        """
        filename = '/var/lib/libvirt/instances/{0}/user-data'.format(
                                                              service_name)
        file_contents = self.get_file_contents(node, filename)
        return self.is_text_in_list(vm_custom_script, file_contents)

    def _confirm_vm_custom_script_ran(self, vm_hostname, vm_ip,
                                      vm_custom_script):

        """
        Description:
        TORF-180367: Test method to check vm custom scripts were run
        and logged in /var/log/messages file on the node.
        :param vm_hostname: hostname of vm the logs are checked
        :param vm_ip: ip of vm the logs are checked
        :param vm_custom_script: custom scripts
        """
        path_to_logs = test_constants.GEN_SYSTEM_LOG_PATH
        # for each script in the list doing the check if it's logged
        # adding the vm to node list so we can run commands from it
        if "sles" in vm_hostname:
            vm_password = test_constants.LIBVIRT_SLES_VM_PASSWORD
        else:
            vm_password = test_constants.LIBVIRT_VM_PASSWORD

        self.add_vm_to_node_list(vm_hostname, username=test_constants.
                                 LIBVIRT_VM_USERNAME, password=vm_password,
                                 ipv4=vm_ip)

        # for each script in the list check the log entry
        for script in vm_custom_script.split(","):
            run_cmd = 'cat {0} | grep "{1}"'.format(path_to_logs, script)
            output, _, _ = self.run_command(vm_hostname,
                                                run_cmd,
                                                username=test_constants.
                                                LIBVIRT_VM_USERNAME,
                                                password=vm_password)
            # If the script in list is supposed to fail, check that
            if script == 'csfname5.sh':
                self.assertTrue(self.is_text_in_list('[FAILED]', output))
            # If the script is too long, check that TIMEOUT is logged
            elif script == "csfname6.sh":
                # if there's timeout, the logs will not refer to
                # certain script but show the general TIMEOUT msg
                timeout_cmd = 'cat {0} | grep "customscriptmanager"'. \
                    format(path_to_logs)
                time_out, _, _ = self.run_command(vm_hostname, timeout_cmd,
                                                      username=test_constants.
                                                      LIBVIRT_VM_USERNAME,
                                                      password=vm_password)
                self.assertTrue(self.is_text_in_list('[TIMEOUT]', time_out))
                # if the script is timed out, no point in checking further
                break
            # For the rest of the scripts the result should be success
            else:
                self.assertTrue(self.is_text_in_list('[SUCCESS]', output))

    def _check_vm_custom_script(self, node):
        """
        Description:
            Confirm vm custom scripts were updated for TORF-180365
            Confirm scripts were run successfully for TORF-180367
        :param node: node on which check is run
        """

        # Checking one VM
        hostname_vm5 = self.up_dict5["VM_SERVICE"]["hostnames"].split(",")[0]
        ip_vm5 = self.up_dict5["NETWORK_INTERFACES"]["NET11"]["ipaddresses"].\
            split(",")[0]

        script_data1 = self.up_dict1["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-1',
                                       script_data1["custom_script_names"])

        self._confirm_vm_custom_script_ran(self.up_dict1["VM_SERVICE"]
                                           ["hostnames"],
                                           self.up_dict1["NETWORK_INTERFACES"]
                                           ["NET1"]["ipaddresses"],
                                           script_data1["custom_script_names"])

        script_data3 = self.up_dict3["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-3',
                                       script_data3["custom_script_names"])
        self._confirm_vm_custom_script_ran(self.up_dict3["VM_SERVICE"]
                                           ["hostnames"],
                                           self.up_dict3["NETWORK_INTERFACES"]
                                           ["NET23"]["ipaddresses"],
                                           script_data3["custom_script_names"])

        script_data4 = self.up_dict4["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-4',
                                       script_data4["custom_script_names"])
        self._confirm_vm_custom_script_ran(self.up_dict4["VM_SERVICE"]
                                           ["hostnames"],
                                           self.up_dict4["NETWORK_INTERFACES"]
                                           ["NET25"]["ipaddresses"],
                                           script_data4["custom_script_names"])

        script_data5 = self.up_dict5["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-5',
                                       script_data5["custom_script_names"])
        self._confirm_vm_custom_script_ran(hostname_vm5,
                                           ip_vm5,
                                           script_data5["custom_script_names"])

        # TORF-406586 verify custom scipts work on sles
        script_data7 = self.up_dict7["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node, 'sles',
                                           script_data7["custom_script_names"])
        self._confirm_vm_custom_script_ran(self.up_dict7["VM_SERVICE"]
                                           ["hostnames"],
                                           self.up_dict7["NETWORK_INTERFACES"]
                                           ["NET1"]["ipaddresses"],
                                           script_data7["custom_script_names"])

    @attr('all', 'non-revert', "libvirt_update1", "LITPCDS-7188",
          "LITPCDS-7184", "LITPCDS-7186", "LITPCDS-585", "TORF-107476",
          "TORF-113124", "TORF-180365", "TORF-180367", "TORF_279479",
          "TORF-297880", "TORF-349676", "TORF-404805", "TORF-406586",
          "TORF-422322", "TORF-419532")
    def test_p_libvirt_update_plan_1(self):
        """
        @tms_id: litpcds_libvirt_tc02
        @tms_requirements_id: LITPCDS-7188, LITPCDS-7184, LITPCDS-7186,
        LITPCDS-585, LITPCDS-7815, LITPCDS-7179, LITPCDS-7182, LITPCDS-11405,
        LITPCDS-11387, TORF-107476, TORF-113124, TORF-180365, TORF-180367,
        TORF-279479, TORF-297880, TORF-349676, TORF-404805, TORF-406586,
        TORF-422322, TORF-419532

        @tms_title: First update for the multiple cluster services running in
        the litp model
        @tms_description: Updates the following item configurations in the
            litp model.
            -VM-packages(litpcds_7188)
            -VM-aliases(litpcds_7184, TORF-349676)
            -Add vm-firewall-rule(s) (torf-279479 & TORF-297880, TORF-422322)
            -Add new packages and repos(litpcds_7186)
            -Update zypper repo and package (TORF-404805)
            -Update VM configuration i.e. vCPUs & RAM(litpcds_585)
            -NFS-mount filesystems(litpcds_7815)
            -Update hostnames(litpcds_7179)
            -Update IP addresses on vm-network-interfaces(litpcds_7179)
            -Update VM images(litpcds_7182)
            -VM services defined in MS service collection(litpcds_11405)
            -Add additonal filesystems to VM (litpcds_11387)
            -Add VM-RAM_MOUNT to VM(torf_107476)
            -Update VM-CUSTOM-SCRIPT (torf-180365 & TORF-406586)
            -Remove Unused files from /var/lib/libvirt/images on
             nodes(torf-113124)
            -MAC addresses updated with deterministic values(litpcds_7848)
             NOTE: this is a preplan step for a subsequent test case


        @tms_test_steps:
            @step: Create new zypper repo dir on ms
            @result: ncm2 is created on ms under repos folder

            @step: Import new empty_rpm packages
            @result: empty_rpm packages are imported successfully

            @step: Import empty_repo
            @result: empty_repos are imported successfully

            @step: Update VM images
            @result: VM images are updated

            @step: Update all VMs hostnames
            @result: All VMs hostnames are updated

            @step: Create and update VM-network-interfaces, VM-aliases
             for all VMs
            @result: All VMs have more VM-network-interfaces and VM-aliases

            @step: Update VM service-1, VM service-4, and VM-service-5
             with more RAM and CPU
            @result: VM-service-1, 4 and 5 have more RAM and CPU assigned

            @step: Remove vm-network-interface from CS_VM3
            @result: vm-network-interface is removed from CS_VM3

            @step: Create NFS-mounts for CS_VM3
            @result: CS_VM3 has new NFS mounts

            @step: Create VM-packages for CS_VM4
            @result: VM-packages are created for CS_VM4

            @step: Contract CS_VM5 to run on one node
            @result: CS_VM5 is a one node parallel service group

            @step: VM-RAM-Mounts on CS_VM1, CS_VM2 are updated
            @result: CS_VM1 and CS_VM2 RAM mount are updated

            @step: VM-RAM-Mount is created for CS_VM5
            @result: CS_VM5 has a VM-RAM-Mount

            @step: Update vm-image for vm-service-5
            @result: VM-service-5 images is updated to vm-image-2

            @step: Update a vm-custom-scripts on CS_SLES_VM
            @result: vm-custom-scripts are updated on CS_SLES_VM

            @step: Update a vm-zypper-repo and vm-package on CS_SLES_VM
            @result: vm-zypper-repo and vm-package are updated on CS_SLES_VM

            @step: Create IPv4 and IPv6 vm-firewall rules for CS_SLES_VM
            @result: IPv4 and IPv6 vm-firewall rules for CS_SLES_VM are created

            @step: Create new file system and vm-disk
            @result: New file system and vm-disk is created

            @step: Create and run plan
            @result: Wait for until plan completion

            @step: Assert VM-RAM-Mount are configured as expected
            @result: VM-RAM-Mount are validated against

            @step: TORF-113124 Verify unused image files are removed
            @result: Unused image file VM-Image-3 is removed from node 1

            @step: TORF-422322 Verify IPv4 and IPv6 vm-firewall rules are
                   applied on CS_SLES_VM
            @result: IPv4 and IPv6 vm-firewall rules are applied on CS_SLES_VM

            @step: TORF-180365, TORF-180367 & TORF-406586 Verify vm custom
                   script names were updated on CS_VM1, CS_VM4, CS_VM5 and
                   CS_SLES_VM
            @result: VM-CUSTOM-script were updated on CS_VM1, CS_VM4, CS_VM5
                     and CS_SLES_VM

            @step: TORF-180367 Verify custom scripts ran again on CS_VM3
                    due to the alias update(cscript hasn't changed) (TC18)
            @result: VM-CUSTOM-script was not updated, but alias was,
                    so scripts triggered again

            @step: TORF-349676 Create IPv6 vm-aliases with prefix and verify
                   hosts file on CS_VM1 is updated without the prefix
            @result: IPv6 vm-aliases without prefix are as expected in hosts
                     file on CS_VM1

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        # Setup the test case.
        primary_node = self.get_managed_node_filenames()[0]
        plan_timeout_mins = 60
        self._pre_plan_setup_story7848()
        self.setup_add_pkgs()
        self.update_vm_software_images()
        self.update_network_cs_plan_1()
        self.update_ms1_sg()

        # TORF-113124: test_04_p_update_vm_image_on_vm_service:  Verify
        # vm-image-3 exists in /var/lib/libvirt/images directory
        vm_image_3 = libvirt_test_data.VM_IMAGE_FILE_NAME['VM_IMAGE3']
        self.assertTrue(
            self._check_image_on_node(vm_image_3, primary_node))

        # Create and execute plan
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)

        # TORF-279479 & TORF-297880
        task = 'Copy VM cloud init userdata file to node "{0}" for '\
               'instance "test-vm-service-1" as part of VM update'.format(
                primary_node)

        task_err_msg = 'No task to update the userdata file for '\
                      '"test-vm-service-1"'

        self.log("info", "wait for the task updating the userdata file "
                 "(containing vm-firewall-rules) is successful")
        self.assertTrue(self.wait_for_task_state(self.management_server,
                                                 task,
                                                 test_constants.
                                                 PLAN_TASKS_SUCCESS,
                                                 False, timeout_mins=20),
                                                 task_err_msg)

        self.execute_cli_stopplan_cmd(self.management_server)

        self.assertTrue(self.wait_for_plan_state(
            self.management_server,
            test_constants.PLAN_STOPPED,
            plan_timeout_mins
        ))

        self.execute_cli_createplan_cmd(self.management_server)

        stdout, _, _ = self.execute_cli_showplan_cmd(self.management_server)
        self.assertNotEqual([], stdout)

        self.log("info", "Verify previously successful task not in "
                 "recreated plan")
        self.assertFalse(self.is_text_in_list(task, stdout),
                             'Previously Successful task "{0}" found in '
                             'recreated plan:\n\n"{1}"'.format(task, stdout))

        self.execute_cli_runplan_cmd(self.management_server)

        self.assertTrue(self.wait_for_plan_state(
            self.management_server,
            test_constants.PLAN_COMPLETE,
            plan_timeout_mins
        ))

        self.verify_vm_rules_applied(self.management_server,
                                     libvirt_test_data.VM_FIREWALL_RULES_1,
                                     self.up_dict1["EXP_IPTABLES_OUTPUT"],
                                     self.up_dict1["NETWORK_INTERFACES"]
                                     ["NET1"]["ipaddresses"],
                                     self.up_dict1["VM_SERVICE"]
                                     ["service_name"], self.rule_coll_path,
                                     args='-nL')

        # TORF-422322 Verify ipv4/ipv6 vm-firewall rules are applied on sles
        self.verify_vm_rules_applied(self.management_server,
                                libvirt_test_data.VM_FIREWALL_RULES_SLES_1,
                                self.up_dict7["EXP_IPTABLES_OUTPUT"],
                                self.up_dict7["NETWORK_INTERFACES"]["NET1"]
                                ["ipaddresses"], self.up_dict7["VM_SERVICE"]
                                ["service_name"], self.sles_rule_coll_path,
                                     args='-nL')

        # TORF - 180365 Test case 05 verification vm custom script updates
        # TORF-406586 TC04 Custom script functionality on sles
        self._check_vm_custom_script(primary_node)

        # TORF-107476: Verify mounts are as expected TC06 and TC15
        self._check_mount_conf(self.up_dict1["VM_SERVICE"]["hostnames"],
                               self.up_dict1["NETWORK_INTERFACES"]["NET1"]
                               ["ipaddresses"],
                               self.up_dict1["VM_RAM_MOUNT"]["type"],
                               self.up_dict1["VM_RAM_MOUNT"]["mount_point"])

        # TORF-107476: Verify mounts are as expected TC05 and TC14
        self._check_mount_conf(self.up_dict2["HOSTNAMES"]["hostnames"],
                               self.up_dict2["NETWORK_INTERFACES"]["NET22"]
                               ["ipaddresses"],
                               self.up_dict2["VM_RAM_MOUNT"]["type"],
                               self.up_dict2["VM_RAM_MOUNT"]["mount_point"])

        # TORF-107476: Verify mounts are as expected TC13
        self._check_mount_conf(self.up_dict5["VM_SERVICE"]["hostnames"],
                               self.up_dict5["NETWORK_INTERFACES"]["NET26"]
                               ["ipaddresses"],
                               self.up_dict5["VM_RAM_MOUNT"]["type"],
                               self.up_dict5["VM_RAM_MOUNT"]["mount_point"])

        # TORF-349676 check /etc/hosts file is updated on test-vm-service-1
        #  with IPV6 vm-alias
        vm_aliases = ["IPV6a", "IPV6b"]
        for vm_alias in vm_aliases:
            self.check_host_file_on_vm(
                self.up_dict1["VM_SERVICE"]["service_name"],
                self.up_dict1["NETWORK_INTERFACES"]["NET1"]["ipaddresses"],
                self.up_dict1["VM_ALIAS"][vm_alias]["alias_names"],
                self.up_dict1["VM_ALIAS"][vm_alias]["address"],
                "1")

        # TORF-113124: test_04_p_update_vm_image_on_vm_service: Verify unused
        # vm-image-3 is removed from /var/lib/libvirt/images directory
        self.assertFalse(
            self._check_image_on_node(vm_image_3, primary_node))
