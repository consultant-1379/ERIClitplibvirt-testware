#!/usr/bin/env python
'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Dec 2014
@author:    David Gibbons
@summary:   Agile: LITPCDS-7848
'''
import test_constants
from litp_generic_test import GenericTest, attr


class Story7848(GenericTest):
    """
    As a LITP User I want my VM network interfaces to be configured with a
    determistic MAC address so that VM MACs can be persisted over VM
    re-initialisations
    """

    def setUp(self):
        """
        Description:
            Runs before every single test
        Results:
            Class variables that are required to execute tests
        """
        super(Story7848, self).setUp()

        self.model = self.get_litp_model_information()
        self.management_server = self.model["ms"][0]["name"]
        self.clus_srvs = self.model["libvirt"]["cluster_services_path"]

        # LITPCDS-7848 setup
        self.vm_service_urls = self.find(self.management_server,
                                         self.clus_srvs, "vm-service")
        self.stored_macs_dir = "/tmp/stored_mac_addresses/"
        self.macs_if_file_location = (self.stored_macs_dir +
                                      "test7848_macs-iface-before-lock")
        self.given_mac_prefix = "AA:BB:CC"
        self.all_vms = self._get_running_vms()

    def tearDown(self):
        super(Story7848, self).tearDown()

    @attr('all', 'non-revert', 'story7848', 'story7848_b')
    def test_post_plan_check_story7848(self):
        """
        @tms_id: litpcds_7848_tc01
        @tms_requirements_id: LITPCDS-7848
        @tms_title: Verify after update 1 the MAC addresses are correct

        @tms_description: Test to verify after the first update in Libvirt KGB
        the MAC address assignments are correct

        @tms_test_steps:
            @step: Ensure that MAC addresses of all VMs are the same after a
            node lock
            @result: Mac addresses are the same after a node lock

            @step: Ensure that when a vm-service is deployed with a new
            vm-network-interface (with a different mac_prefix) that the MAC
            address deployed uses that mac_prefix
            @result: The mac_prefix is used with the VM-Network-Interface

            @step: For each network interface in each running VM, ensure its
            MAC address starts with 52:54:00
            @result: MAC address starts with 52:54:00

            @step: For each network interface in each running VM, ensure its
            MAC address is unique within the cluster
            @result: MAC address are unique within the cluster

            @step: Ensure that the MAC address of a failover service group is
            persisted even after a failover onto the second node
            @result: MAC address of the failover service group is persisted
            after a failover onto a second node

        @tms_test_precondition:
            - testset_libvirt_initial_setup and testset_libvirt_update_1
             has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        self._check_macs_after_lock_unlock()
        self._check_mac_prefix()
        self._check_macs_format()
        self._check_mac_uniqueness()
        self._check_macs_failover()

    def _check_macs_after_lock_unlock(self):
        """
        Description:
            Ensure that MAC addresses of all VMs are the same after a node lock
            Note: The MAC addresses before the lock are stored in a file
            created in the method _get_macs_and_interfaces_before_lock_unlock

        Steps:
            Read the contents of the tmp file from before the node lock from
                file system and parse into a python dictionary
            Execute command to obtain allow MAC addresses from each running VM
            Create a dictionary object with vms, interfaces, and mac addresses
            Assert that the two dictionary objects are the same
        """
        file_contents = self.get_file_contents(
                            self.management_server,
                            self.macs_if_file_location)[0]
        all_macs_and_inferfaces_before = eval(file_contents)

        all_macs_and_inferfaces_after = {}
        for v_m in self.all_vms:
            all_macs_and_inferfaces_after[v_m] = \
                self._get_mac_addresses_on_vm(v_m, include_ifaces=True)
        for running_vm in all_macs_and_inferfaces_before.keys():
            # Exclude CS_VM1 as it was removed and CS_VM4 as
            # it was used for testing _check_mac_prefix
            if running_vm.startswith(("CS_VM1_", "CS_VM4_", "CS_VM5_1")):
                continue
            for device, mac in \
                    all_macs_and_inferfaces_after[running_vm].iteritems():
                if device in all_macs_and_inferfaces_before[running_vm]:
                    self.assertEqual(
                        all_macs_and_inferfaces_before[running_vm][device],
                        mac)

    def _check_macs_format(self):
        """
        Description:
            For each network interface in each running VM, ensure its MAC
            address starts with 52:54:00

        Steps:
            Execute command to obtain allow MAC addresses from each running VM
            Assert that all MAC addresses start with constant
                "mac_address_start"
        """
        mac_address_start = "52:54:00"

        all_macs = []
        for v_m in self.all_vms:
            # Exclude CS_VM4 as it was used for testing _check_mac_prefix
            if v_m.startswith("CS_VM4_"):
                continue
            all_macs.extend(self._get_mac_addresses_on_vm(v_m))

        for mac in all_macs:
            self.assertEqual(mac[:8], mac_address_start)

    def _check_mac_uniqueness(self):
        """
        Description:
            For each network interface in each running VM, ensure its MAC
            address is unique within the cluster

        Steps:
            Execute command to obtain allow MAC addresses from each running VM
            Assert that the length list of MAC addresses is the same as the set
                (no duplicates) of MAC addresses
        """
        all_macs = []
        for v_m in self.all_vms:
            all_macs.extend(self._get_mac_addresses_on_vm(v_m))

        self.assertEqual(len(all_macs), len(set(all_macs)))

    def _check_macs_failover(self):
        """
        Description:
            Ensure that the MAC address of a failover service group is
                persisted even after a failover onto the second node

        Steps:
            Retrieve the MAC address for a failover service group
            Initiate a failover of that service group using the
                "hagrp -switch <group> -any" command
            Retrieve the MAC address for the same service group and ensure that
                it is the same. Note that the test relies on that fact that the
                IP of a failed over service group is the same
        """
        primary_node = self.get_managed_node_filenames()[0]
        all_macs_and_inferfaces_before = {}
        for v_m in self.all_vms:
            all_macs_and_inferfaces_before[v_m] =\
                self._get_mac_addresses_on_vm(v_m, include_ifaces=True)

        failover_sg_name = self._get_a_failover_sg_name()

        cmd = "/opt/VRTSvcs/bin/hagrp -switch " + failover_sg_name + " -any"
        stdout, stderr, return_code = self.run_command(primary_node, cmd,
                                                       su_root=True)
        self.assertEqual([], stdout)
        self.assertEqual([], stderr)
        self.assertEqual(0, return_code)

        self.wait_for_vcs_service_group_online(primary_node,
            failover_sg_name, 1, wait_time_mins=10)

        all_vms = self._get_running_vms()
        all_macs_and_inferfaces_after = {}
        for v_m in all_vms:
            all_macs_and_inferfaces_after[v_m] = self._get_mac_addresses_on_vm(
                                                      v_m, include_ifaces=True)

        self.assertEqual(all_macs_and_inferfaces_before,
                         all_macs_and_inferfaces_after)

    def _check_mac_prefix(self):
        """
        LITPCDS-7848
        Description:
            Ensure that when a vm-service is deployed with a new
            vm-network-interface (with a different mac_prefix) that the MAC
            address deployed uses that mac_prefix
        Steps:
            Retrieve the MAC addresses from before the creation
            of ht new interface
            Retrieve the current MAC addresses
            Check the new MAC addresses use the different prefix
        """
        all_macs_after = []
        for v_m in self.all_vms:
            if v_m.startswith("CS_VM4_"):
                all_macs_after.extend(self._get_mac_addresses_on_vm(v_m))
        macs_with_prefix = [mac for mac in all_macs_after \
                            if mac[:8] == self.given_mac_prefix]
        self.assertEqual(1, len(macs_with_prefix))

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

            for iface in vm_ifaces:
                ip_list = self.get_props_from_url(self.management_server,
                                                  iface, 'ipaddresses')
                if not ip_list:
                    continue
                vm_ipaddrs = ip_list.split(',')
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

    def _get_a_failover_sg_name(self):
        """
        Get the VCS Group Name of the first VCS failover group found which
        is a vm-service and has at least one interface
        If there are no failover groups return None
        """
        for vm_service_url in self.vm_service_urls:
            vm_ifaces = self.find(self.management_server, vm_service_url,
                        'vm-network-interface', assert_not_empty=False)
            if not vm_ifaces:
                # No interfaces means no MAC addresses. Assumed that each iface
                # has a MAC address
                continue

            cs_item_url = vm_service_url.rsplit('/', 2)[0]

            vm_active_num = self.get_props_from_url(self.management_server,
                                                    cs_item_url, 'active')
            vm_standby_num = self.get_props_from_url(self.management_server,
                                                     cs_item_url, 'standby')
            if vm_active_num == "1" and vm_standby_num == "1":
                cs_item_id = vm_service_url.rsplit('/', 3)[-3]
                cluster_item_id = vm_service_url.rsplit('/', 5)[-5]
                return "Grp_CS_" + cluster_item_id + "_" + cs_item_id
