"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Jan 2017
@author:    Iacopo Isimbaldi
@summary:   Integration
            Agile: STORY-159934
"""

from litp_generic_test import GenericTest, attr
import copy
import libvirt_test_data
import test_constants
import os
import re


class Story159934(GenericTest):
    """
    TORF-159934: As a LITP user I want to be able to modify subnet definition
    in the model and have the Libvirt plugin act accordingly
    """

    def setUp(self):
        super(Story159934, self).setUp()

        # 2. Set up variables used in the test
        self.management_server = self.get_management_node_filename()
        self.vcs_cluster_url = self.find(self.management_server,
                                         '/deployments', 'vcs-cluster')[-1]
        self.nodes_urls = self.find(self.management_server,
                                    self.vcs_cluster_url,
                                    'node')
        self.networks_url = self.find(self.management_server,
                                      '/infrastructure',
                                      'collection-of-network')[-1]

        self.ms_props_mgmt = copy.deepcopy(libvirt_test_data.MGMT_MS_DATA)
        self.ms_props_ovlp = copy.deepcopy(libvirt_test_data.OVLP_MS_DATA)
        self.n_props = copy.deepcopy(libvirt_test_data.OVLP_N_DATA)
        self.vm_props = copy.deepcopy(libvirt_test_data.OVLP_VM_DATA)

    def tearDown(self):
        super(Story159934, self).tearDown()

        self.execute_and_wait_restore_snapshot(self.management_server)
        self.execute_and_wait_createsnapshot(self.management_server,
                                             add_to_cleanup=False,
                                             remove_snapshot=True)

    def _change_subnet(self, ms_props):
        """
        Expand subnet using ms server properties

        :param ms_props: ms properties
        :return: None
        """

        network_url = self.networks_url + \
                      '/{0}'.format(ms_props['network_name'])
        network_props = "subnet='{0}'".format(ms_props['subnet'])
        self.execute_cli_update_cmd(
            self.management_server,
            network_url,
            network_props)

    def _migrate_subnet_nodes(self, ms_props, n_props):
        """
        Migrate subnet to another address

        :param ms_props: ms properties
        :param n_props: nodes properties
        :return: None
        """

        self._change_subnet(ms_props)

        bond_url_ms = "/ms/network_interfaces/{0}".format(
            ms_props['bond_link'])
        bond_props_ms = "ipaddress='{0}'".format(ms_props['ip'])
        self.execute_cli_update_cmd(
            self.management_server,
            bond_url_ms,
            bond_props_ms)

        for node, i in zip(self.nodes_urls, xrange(0, len(self.nodes_urls))):
            bridge_url_n = node + \
                           "/network_interfaces/{0}".format(n_props['br_link'])
            bridge_props_n = "ipaddress={0}" \
                .format(n_props['ovlp_ips'][i])
            self.execute_cli_update_cmd(
                self.management_server, bridge_url_n, bridge_props_n)

    def _migrate_subnet_nodes_and_vm_service(
            self, ms_props, n_props, vm_props):
        """
        Migrate subnet and also update vm_services settings

        :param ms_props: ms properties
        :param n_props: nodes properties
        :param vm_props: vm_services properties
        :return: None
        """

        self._migrate_subnet_nodes(ms_props, n_props)

        ip_url_vm = self.vcs_cluster_url + "/services/{0}/applications/" \
                                           "{1}/vm_network_interfaces/{2}" \
            .format(vm_props["service_name"], vm_props["application_name"],
                    vm_props["ovlp_name"])
        ip_props_vm = "ipaddresses={0}".format(vm_props['ip'])
        self.execute_cli_update_cmd(
            self.management_server, ip_url_vm, ip_props_vm)

    def _migrate_vm_service_to_another_node(self, vm_props, node):
        """
        Migrate vm_service to another node

        :param vm_props: vm_service properties
        :param node:
        :return:
        """
        node_url_vm = self.vcs_cluster_url + "/services/{0}".format(
            vm_props[
                "service_name"])
        node_props_vm = "node_list={0}".format(node)

        self.execute_cli_update_cmd(
            self.management_server,
            node_url_vm,
            node_props_vm)

    def _ping_network(self, n_props, vm_props):
        """
        Ping networks

        :param n_props: nodes properties
        :param vm_props: vm_services properties
        :return: None
        """
        timeout = 10

        # Ping the nodes and vm_service
        for n_ip in n_props["mgmt_ips"]:
            p_result = self.wait_for_ping(n_ip, ping_success=True,
                                          timeout_mins=timeout,
                                          node=self.management_server)
            self.assertEquals(True, p_result)

        for n_ip in n_props["ovlp_ips"]:
            p_result = self.wait_for_ping(n_ip, ping_success=True,
                                          timeout_mins=timeout,
                                          node=self.management_server)
            self.assertEquals(True, p_result)

        p_result = self.wait_for_ping(vm_props["ip"], ping_success=True,
                                      timeout_mins=timeout,
                                      node=self.management_server)
        self.assertEquals(True, p_result)

    def _is_metadata_file_valid(self, vm_props):
        """
        Check metadata file on nodes

        :param vm_props: vm_services properties
        :return: None
        """
        n_url_vm = self.vcs_cluster_url + "/services/{0}" \
            .format(vm_props["service_name"])

        n_list_vm = self.get_props_from_url(self.management_server, n_url_vm,
                                            filter_prop="node_list").split(",")

        n_urlapp_vm = n_url_vm + "/applications/{0}".format(
            vm_props["application_name"])
        service_name = self.get_props_from_url(
            self.management_server, n_urlapp_vm, filter_prop="service_name")

        f_metadata_path = os.path.join(test_constants.LIBVIRT_INSTANCES_DIR,
                                       service_name, 'meta-data')

        for node in n_list_vm:
            n_urlname_vm = \
                [url for url in self.nodes_urls if url.endswith(node)][0]
            n_node = self.get_node_filename_from_url(
                self.management_server, n_urlname_vm)

            # Check mgmt is expanded to /15
            n_cmd_vm = "grep 192.168 -A4 {0} | grep netmask".format(
                f_metadata_path)

            results = self.run_command(n_node, n_cmd_vm, su_root=True,
                                       default_asserts=True)[0]
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

            for result in results:
                self.assertEquals(ansi_escape.sub('', result), "netmask "
                                                               "255.254.0.0")

            # Check ovlp is migrated but still /16
            n_cmd_vm = "grep 192.170 -A4 {0} | grep netmask".format(
                f_metadata_path)

            results = self.run_command(n_node, n_cmd_vm, su_root=True,
                                       default_asserts=True)[0]

            for result in results:
                self.assertEquals(ansi_escape.sub('', result), "netmask "
                                                               "255.255.0.0")

    # Test case 1 already covered by test case 2
    @attr('all', 'revert', 'story159934', 'story159934_tc02')
    def test_02_p_update_net_subnet_vm_running_expd_and_ovlp_network(self):
        """
        @tms_id: torf_159934_tc02
        @tms_requirements_id: TORF-159934
        @tms_title: Update network subnet while migrating another network with
                    a vm_service running on both networks and
                    performing an idempotency test
        @tms_description:
            Test to verify that a user can expand a network while the
            vm_service is using that network
        @tms_test_steps:
            @step: Update the litp management network to overlap ovlp network
                    and migrate ovlp to solve the problem. (The vm_service is
                    only on the litp management network)
            @result: Update networks subnet
            @step: Update ovlp ip of bridge interface on every nodes
            @result: Update ovlp ip of bridge
            @step: Update ovlp ip of bond interface on ms
            @result: Update ovlp ip of bond
            @step: Create/ Run Plan
            @result: Get a plan that expand mgmt network and migrate ovlp
                    network. This plan will also update all the relative ips
                    of the networks
            @step: After the plan succeed in unlock "node1" restart litpd and
                    recreate/rerun the plan
            @result: The plan should be restored and network
                    expansion/migration continued
            @step: Ensure network connectivity is restore after plan completes
                    and model/ nodes are updated
            @result: nodes and vm_services ips are "pingable"
            @step: Check the meta-data file of the vm_service is correct
            @result: Check the correct value for the subnet is present in
                    meta-data file of every node with vm_service
        @tms_test_precondition: Requires this scripts runned before:
                                testset_libvirt_initial_setup.py
                                testset_libvirt_update_1.py
                                testset_libvirt_update_2.py
                                testset_libvirt_update_3.py
                                testset_libvirt_update_4.py
                                testset_libvirt_update_5.py
        @tms_execution_type: Automated
        """

        timeout = 90

        # Expand litp management network
        self.ms_props_mgmt["subnet"] = "192.168.0.0/15"
        self._change_subnet(self.ms_props_mgmt)

        # Migrate ovlp network
        self.ms_props_ovlp["subnet"] = "192.170.0.0/16"
        self.ms_props_ovlp["ip"] = "192.170.0.42"
        self.n_props["ovlp_ips"] = ["192.170.0.43", "192.170.0.44"]
        self.vm_props["ip"] = "192.170.0.2"
        self._migrate_subnet_nodes_and_vm_service(
            self.ms_props_ovlp, self.n_props, self.vm_props)

        # Create and run the plan
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)

        # Idempotency
        task_desc = "Unlock VCS on node \"node1\""
        self.assertTrue(
            self.wait_for_task_state(self.management_server, task_desc,
                                     test_constants.PLAN_TASKS_SUCCESS,
                                     timeout_mins=timeout,
                                     ignore_variables=False),
            'Idempotent testing failed after Unlock VCS on node \"node1\"')
        self.restart_litpd_service(self.management_server)

        # Create and run the plan
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)
        self.assertTrue(
            self.wait_for_plan_state(self.management_server,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=timeout))

        # Ping the nodes and vm_service
        self._ping_network(self.n_props, self.vm_props)

        # Check meta-data file
        self._is_metadata_file_valid(self.vm_props)

    @attr('all', 'revert', 'story159934', 'story159934_tc04')
    def test_04_p_update_network_subnet_during_migration_vm_service(self):
        """
        @tms_id: torf_159934_tc04
        @tms_requirements_id: TORF-159934
        @tms_title: Update network subnet while migrating another network with
                    a vm_service running on both networks during a migration
        @tms_description:
            Test to verify that a user can expand a network while the
            vm_service is using both networks (mgmt and ovlp) while migrating
            the vm_service
        @tms_test_steps:
            @step: Update the litp management network to overlap ovlp network
                    and migrate ovlp to solve the problem.
                    (The vm_service is only on the litp management network)
            @result: Update networks subnet
            @step: Update ovlp ip of bridge interface on every nodes
            @result: Update ovlp ip of bridge
            @step: Update ovlp ip of bond interface on ms
            @result: Update ovlp ip of bond
            @step: Migrate the vm_service to another node
            @result: Migrate vm_service to another node
            @step: Create/ Run Plan
            @result: Get a plan that expand mgmt network and migrate ovlp
                    network while migrate the vm_service.
                    This plan will also update all the relative ips of the
                    networks
            @step: Ensure network connectivity is restore after plan completes
                    and model/ nodes are updated
            @result: nodes and vm_services ips are "pingable"
            @step: Check the meta-data file of the vm_service is correct
            @result: Check the correct value for the subnet is present in
                    meta-data file of every node with vm_service
        @tms_test_precondition: Requires this scripts runned before:
                                testset_libvirt_initial_setup.py
                                testset_libvirt_update_1.py
                                testset_libvirt_update_2.py
                                testset_libvirt_update_3.py
                                testset_libvirt_update_4.py
                                testset_libvirt_update_5.py
        @tms_execution_type: Automated
        """

        timeout = 90

        # Expand litp management network
        self.ms_props_mgmt["subnet"] = "192.168.0.0/15"
        self._change_subnet(self.ms_props_mgmt)

        # Migrate ovlp network
        self.ms_props_ovlp["subnet"] = "192.170.0.0/16"
        self.ms_props_ovlp["ip"] = "192.170.0.42"
        self.n_props["ovlp_ips"] = ["192.170.0.43", "192.170.0.44"]
        self.vm_props["ip"] = "192.170.0.2"
        self._migrate_subnet_nodes_and_vm_service(
            self.ms_props_ovlp, self.n_props, self.vm_props)

        # Migrate the service to another node
        self._migrate_vm_service_to_another_node(self.vm_props, "n1")

        # Create and run the plan
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)
        self.assertTrue(
            self.wait_for_plan_state(self.management_server,
                                     test_constants.PLAN_COMPLETE,
                                     timeout_mins=timeout))

        # Ping the nodes and vm_service
        self._ping_network(self.n_props, self.vm_props)

        # Check meta-data file
        self._is_metadata_file_valid(self.vm_props)
