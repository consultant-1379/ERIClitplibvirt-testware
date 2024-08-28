#!/usr/bin/env python
"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Nov 2014
@author:    Danny McDonald
@summary:   Afile: LITPCDS-7535
"""

import re
from time import sleep
import test_constants
from litp_generic_test import GenericTest, attr
from test_constants import RH_RELEASE_FILE, RH_VERSION_6, RH_VERSION_6_10,\
    RH_VERSION_7, RH_VERSION_7_4

import libvirt_test_data


class Story7535(GenericTest):
    """
    As a LITP User I want the libvirt adaptor to check the internal
    status of the VM so that application faults can be detected
    """

    def setUp(self):
        """
        Description:
            Runs before every single test
        Actions:
            Determine
                management server,
                list of ips used by vm-service items
        Results:
            Class variables that are required to execute tests
        """
        super(Story7535, self).setUp()

        self.management_server = self.get_management_node_filename()
        self.list_managed_nodes = self.get_managed_node_filenames()
        self.primary_node = self.list_managed_nodes[0]
        self.max_vm_startup_time = 600
        self.vcs_cluster_url = self.find(self.management_server,
                                         "/deployments", "vcs-cluster")[-1]

        self.vm_ip = self.get_ip_for_vms(self.management_server)

        self.init_nodes()

    def tearDown(self):
        super(Story7535, self).tearDown()

    def init_nodes(self):
        """
        Add each of the nested vms in the deployment to this testcase
        using `add_vm_to_nodelist`.
        """
        for ipaddresses in self.vm_ip.values():
            for ipaddress in ipaddresses:
                # Hostname not needed so substitute IP address.
                self.add_vm_to_nodelist(
                    ipaddress,
                    ipaddress,
                    username=test_constants.LIBVIRT_VM_USERNAME,
                    password=test_constants.LIBVIRT_VM_PASSWORD)

    def _verify_ssh_is_accessable(self, ip_addr):
        """
        Run nc command to poll the ssh port on the given ip address
        to try to confirm that the ssh deamon is running, and return a
        boolean result

        Args:
            - ip_addr: IP address to be checked
        Returns: -
            - True/False depending on return code from command
        """
        cmd = '/usr/bin/nc -w 1 {0} -z 22'.format(ip_addr)
        _, _, return_code = self.run_command(self.management_server,
                                             cmd)
        return self._return_code_as_bool(return_code)

    def check_all_ips_ssh_accessible(self, ip_list):
        """
        Takes list of all IPs assigned in the model and verifies
        that for each one, the ssh deamon is active. It will retry
        up until a maximum time.

        Args:
            ip_list: list of IP address to be checked

        Returns: -
        True or False. True if all IPs can be accessed via ssh
        """
        time_to_wait = self.max_vm_startup_time
        ok_list = set()
        while time_to_wait > 0:
            for ip_addr in ip_list:
                if ip_addr not in ok_list:
                    if self._verify_ssh_is_accessable(ip_addr):
                        ok_list.add(ip_addr)
            if not set(ip_list).difference(ok_list):
                return True
            sleep(5)
            time_to_wait -= 5
        return False

    def _kill_the_ocf_check_service(self, ip_addr):
        """
        Run a chkconfig command on the vm-service to stop ocf_checkd
        from starting

        Args:
            - ip_addr: IP address of the VM service
        Returns: -
            - True/False depending on return code from command
        """

        rh_vers, _, _ = self.run_command(ip_addr, 'tail ' + RH_RELEASE_FILE,
                                         add_to_cleanup=False,
                                         default_asserts=True)
        if RH_VERSION_6 in rh_vers or RH_VERSION_6_10 in rh_vers:
            cmd = "chkconfig --del ocf_checkd"
        elif RH_VERSION_7 in rh_vers or RH_VERSION_7_4 in rh_vers:
            cmd = "chkconfig --del vmmonitord"

        _, _, return_code = self.run_command(ip_addr, cmd)
        self.assertEqual(0, return_code)

    def _verify_group_is_online(self, cs_name, expected):
        """
        Execute the hagrp command and verify that the clusters-
        service is online
        args:
            cs_name (str): clustered-service name
            expected (int): the number of times this clustered-service is
                            expected to be listed as ONLINE
        return:
               -
        """
        cluster_id = self.vcs_cluster_url.split("/")[-1]
        cs_grp_name = self.vcs.generate_clustered_service_name(cs_name,
                                                               cluster_id)
        cmd = self.vcs.get_hagrp_state_cmd()
        hagrp_output, stderr, return_code = self.run_command(
            self.primary_node,
            cmd,
            su_root=True)
        self.assertEqual(0, return_code)
        self.assertEqual([], stderr)

        # Search in the output from hagrp and count
        # the number of times that it is online
        reg_ex = cs_grp_name + r'\s+State\s+\w+\s+\|ONLINE\|$'
        online_cnt = 0
        for line in hagrp_output:
            if re.search(reg_ex, line):
                online_cnt = online_cnt + 1
        # Is group online the correct number of times
        self.assertEqual(expected,
                         online_cnt)

    @staticmethod
    def _return_code_as_bool(return_code):
        """
        Return `True` if return_code is 0 else `False`.
        """
        return return_code == 0

    @attr('all', 'non-revert', 'story7535', 'story7535_tc1')
    def test_01_p_confirm_internal_status_check_off(self):
        """
        @tms_id: litpcds_7535_tc01
        @tms_requirements_id: LITPCDS-7535
        @tms_title: Confirm internal status check is off

        @tms_description: In a previously executed plan the internal status
        check for CS_VM1 was turned off. This test verifies that the
        internal_status_check flag for CS_VM1 has been turned off deployed
        vm-service, CS_VM1. The test will log into the vm and switch off the
        http server so it does not respond. After waiting sufficient time,
        it verifies the service is still ONLINE.

        @tms_test_steps:
            @step: Wait until ssh access to the nested VM is possible
            @result: SSH access becomes possible to the nested VM

            @step: Kill the HTTP server on the node
            @result: HTTP server on the node is killed

            @step: Wait for more than 3 times the monitoring interval and
            Verify the service is still ONLINE in VCS
            @result: 3 times the monitoring interval is passes and SG is
            still ONLINE

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        conf_data = libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA
        expected_active = int(conf_data["CLUSTER_SERVICE"]["active"])
        service_name = conf_data["VM_SERVICE"]["service_name"]
        cs_name = conf_data["CLUSTER_SERVICE"]["name"]
        service_urls = self.find(self.management_server,
                                 "/software", "vm-service")
        service_url = None
        for url in service_urls:
            if service_name in url:
                service_url = url
                break
        # STEP 1
        ip_list = self.vm_ip[cs_name]
        result = self.check_all_ips_ssh_accessible(ip_list)
        self.assertTrue(result)
        # STEP 2
        ip_addr = ip_list[0]
        self._kill_the_ocf_check_service(ip_addr)

        # STEP 3
        status_interval = self.get_props_from_url(
            self.management_server,
            service_url,
            'status_interval')
        if not status_interval:
            status_interval = 60
        restart_limit = self.get_props_from_url(
            self.management_server,
            service_url,
            'restart_limit')
        if not restart_limit:
            restart_limit = 1
        time_to_sleep = status_interval * restart_limit

        sleep(time_to_sleep)

        # STEP 4
        self._verify_group_is_online(cs_name, expected_active)
