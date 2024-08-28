"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Nov 2015
@author:    Aileen Henry
@summary:   Testset to deploy libvirt vcs functionality
"""

from litp_generic_test import GenericTest, attr
from libvirt_utils import LibvirtUtils
import libvirt_test_data
import time


class LibvirtFailover(GenericTest):
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
        super(LibvirtFailover, self).setUp()

        self.model = self.get_model_names_and_urls()
        self.management_server = self.model["ms"][0]["name"]

        self.managed_nodes = [n["name"] for n in self.model["nodes"]]
        self.libvirt = LibvirtUtils()
        self.sg3_name = "Grp_CS_c1_CS_VM3"
        self.sg4_name = "Grp_CS_c1_CS_VM4"
        self.sg5_name = "Grp_CS_c1_CS_VM5"

        self.cs3 = libvirt_test_data.INITIAL_SERVICE_GROUP_3_DATA[
            "CLUSTER_SERVICE"]
        self.cs4 = libvirt_test_data.INITIAL_SERVICE_GROUP_4_DATA[
            "CLUSTER_SERVICE"]
        self.cs5 = libvirt_test_data.INITIAL_SERVICE_GROUP_5_DATA[
            "CLUSTER_SERVICE"]

        self.cs3_online_timeout_mins = int(self.cs3["online_timeout"]) / 60
        self.cs4_online_timeout_mins = int(self.cs4["online_timeout"]) / 60
        self.cs5_online_timeout_mins = int(self.cs5["online_timeout"]) / 60

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Results:
            The super class prints out diagnostics and variables
        """
        super(LibvirtFailover, self).tearDown()

    @staticmethod
    def filter_by_state(vcs_info, state):
        """
        :param vcs_info: A list of hastatus dictionaries
        :param state: All dictionaries with the subkey "STATE"
                    matching this argument are returned as a list
        :return: A list of nodenames that match the provided state
        """
        matching_node_dictionaries = [x for x in vcs_info
                                        if x["STATE"] == state]
        return [n["SYSTEM"] for n in matching_node_dictionaries]

    def get_virsh_vm_state(self, vm_name, node):
        """
        Description:
            Retrieve the state of the specified vm as output in virsh console
        :param vm_name: The vm which you wish to check the state of
        :param node: The node which the vm is running on
        :return: The state of the vm
        """
        # Use dominfo command to get the vm state
        dominfo_cmd = self.libvirt.get_virsh_dominfo_cmd(vm_name)
        stdout, _, _ = self.run_command(node, dominfo_cmd, su_root=True)
        # Parse the stdout to get the vm state
        for line in stdout:
            if "State" in line:
                data1 = line.split()
                state = data1[1]
        return state

    def get_sg_vcs_info(self, target_node, target_sg_name):
        """
        Description:
            This is a convenience method to return a list of nodes for
                a named service group
        :param target_node: The node on which to run the vcs hastatus command
        :param target_sg_name: The name of the service group to filter for
        :return: A list of dictionaries representing the nodes for vcs service
            groups. This is a filtered run_vcs_hastatus_sum_command list
        """
        node1_hastatus = self.run_vcs_hastatus_sum_command(
            target_node)
        test_sg_info = [sg for sg in node1_hastatus["SERVICE_GROUPS"]
                        if sg["GROUP"] == target_sg_name]
        return test_sg_info

    def check_node_status(self, node, query_node, target_sg_name,
                          expected_status, timeout_mins=5):
        """
        Description:
            Repeatedly checks for a node to enter a status.
        :param node: The node on which to execute the hastatus command
        :param query_node: The node to query for online/offline
        :param target_sg_name: The service group to query
        :param expected_status: The expected response to wait for
        :param timeout_mins: Timeout in minutes before breaking
        :return: True or false depending on success
        """
        status_cmd = self.vcs.get_hastatus_sum_cmd() + \
                     " | grep ^B | grep {0} " \
                     "| grep {1} | tr -s ' ' " \
                     "| cut -d ' ' -f 6"
        return self.wait_for_cmd(node,
                                 status_cmd.format(target_sg_name,
                                                   query_node), 0,
                                 expected_stdout=expected_status,
                                 timeout_mins=timeout_mins,
                                 su_root=True)

    def run_destroy_command(self, target_node, vm_to_destroy):
        """
        Description:
            Runs virsh destroy command to destroy vm on specified node
        :param target_node: The node on which the vm sg is running
        :param vm_to_destroy: The name of the vm to destroy
        :return: The standard output following the virsh destroy command
        """
        destroy_cmd = self.libvirt.get_virsh_destroy_cmd(vm_to_destroy)
        stdout, _, _ = self.run_command(target_node, destroy_cmd,
                                              su_root=True)
        return stdout[0]

    def run_multiple_destroy_cmd(self, target_node, target_vm, sg_name):
        """
        Description:
            Runs virsh destroy command on specified node until
            the service group is no longer running on the node.
            A loop is used to repeat the virsh destroy command
            if the vm is brought back up on the same node.
        :param target_node: The node on which the vm sg is running
        :param target_vm: The name of the vm as it appears in virsh console
        :param sg_name: The service group name
        """
        # Run destroy command to kill vm on specified node
        self.run_destroy_command(target_node, target_vm)
        seconds = libvirt_test_data.SLEEP
        time.sleep(seconds)
        # Check if service group is online
        status_cmd = self.vcs.get_hagrp_value_cmd(sg_name, 'State',
                                                  target_node)
        stdout, _, _ = self.run_command(target_node, status_cmd, su_root=True)
        # While the target node is listed as Online
        while stdout[0] == "|ONLINE|":
            # Run virsh destroy on the node again
            self.run_destroy_command(target_node, target_vm)
            time.sleep(seconds)
            # Check status of the target node
            stdout, _, _ = self.run_command(target_node, status_cmd,
                                            su_root=True)
        # Check the virsh list to ensure vm is no longer running
        vm5_state = self.get_virsh_vm_state(target_vm, target_node)
        self.assertNotEqual(vm5_state, "running")

    def get_sg_nodes_in_state(self, node, sg_name, state):
        """
        :param node: The node to query
        :param sg_name: The service group to query
        :param state: The state to filter on ONLINE or OFFLINE
        :return: A list of node-names that match the provided state
        """
        sg4_info = self.get_sg_vcs_info(node, sg_name)
        sg4_nodes = self.filter_by_state(sg4_info, state)
        return sg4_nodes

    def clean_node(self, faulted_node, sg_name, bring_online):
        """
        Description:
            Clean the faulted node and bring the service group online
        :param faulted_node: The node on which the vm sg is running
        :param sg_name: The name of the sg to clear
        :param bring_online: boolean value specifying if the sg needs to be
                             brought online
        :return: Nothing
        """
        # Clean the faulted node
        clear_cmd = self.vcs.get_hagrp_cs_clear_cmd(sg_name, faulted_node)
        self.run_command(faulted_node, clear_cmd, su_root=True)

        sg_online_times = {self.sg3_name: self.cs3_online_timeout_mins,
                           self.sg4_name: self.cs4_online_timeout_mins,
                           self.sg5_name: self.cs5_online_timeout_mins}

        # Bring service group online
        if bring_online:
            bring_on_cmd = self.vcs.get_hagrp_cs_online_cmd(sg_name,
                                                            faulted_node)
            self.run_command(faulted_node, bring_on_cmd, su_root=True)
            # Wait for sg to come online
            node_status = self.check_node_status(self.managed_nodes[0],
                                                 faulted_node,
                                                 sg_name,
                                                 "ONLINE",
                                                 sg_online_times[sg_name])
            self.assertTrue(node_status)

    def run_switch_command(self, from_node, to_node, sg_name):
        """
        Description: Run the command to trigger a cluster handover
        :param from_node: The node on which to execute the command
        :param to_node: The node to make active
        :param sg_name: The service group to switch
        """

        command = self.vcs.get_hagrp_cmd("-switch {0} -to {1}"
                                         .format(sg_name, to_node))
        self.run_command(from_node,
                         command,
                         su_root=True)

    @attr('all', 'non-revert', 'libvirt_handover')
    def test_01_libvirt_handover(self):
        """
        @tms_id: litpcds_libvirt_vcs_failovers_tc01
        @tms_requirements_id: LITPCDS-7180
        @tms_title: Libvirt Handover during service group handover

        @tms_description: This test checks for service group handover

        @tms_test_steps:
            @step: Obtain the hastatus -sum information for the target SG
            @result: SG information is gathered

            @step: Gather the names of both active/standby nodes on the SG
            @result: Active/Standby Node information is obtained

            @step: Execute a hagrp -switch command
            @result: hagrp -switch command is used to cause handover to
            inactive node

            @step: Wait for the formerly offline node to come online
            @result: Previous standby node is now active node

            @step: Obtain the hastatus -sum information for the target SG
            @result: SG information is gathered

            @step: Verify the SG has switched its active and standby node
            @result: SG is Validated against with active and standby
            configuration

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """

        # 1. Obtain the hastatus -sum info for the target sg
        vcs_info = self.get_sg_vcs_info(self.managed_nodes[0], self.sg3_name)

        # 2. Get the names of the online and offline nodes
        initial_online_node = self.filter_by_state(vcs_info, 'ONLINE')[0]
        initial_offline_node = self.filter_by_state(vcs_info, 'OFFLINE')[0]

        # 3. Execute the switch command to cause handover to the inactive node
        self.run_switch_command(initial_online_node, initial_offline_node,
                                self.sg3_name)

        # 4. Wait for the formerly offline node becomes online
        self.assertTrue(self.check_node_status(self.managed_nodes[0],
                                               initial_offline_node,
                                               self.sg3_name, "ONLINE",
                                               self.cs3_online_timeout_mins),
                        '{0} is not ONLINE on {1}'.format(self.sg3_name,
                                                          initial_offline_node)
                        )
        self.assertTrue(self.check_node_status(self.managed_nodes[0],
                                               initial_online_node,
                                               self.sg3_name, "OFFLINE",
                                               self.cs3_online_timeout_mins),
                        '{0} is not OFFLINE on {1}'.format(self.sg3_name,
                                                           initial_online_node)
                        )

        # 5. Obtain the currently active node by querying hastatus -sum
        after_switch_vcs_info = self.get_sg_vcs_info(initial_offline_node,
                                                     self.sg3_name)
        after_switch_online_node = \
            self.filter_by_state(after_switch_vcs_info, "ONLINE")[0]
        after_switch_offline_node = \
            self.filter_by_state(after_switch_vcs_info, "OFFLINE")[0]

        # 6. Verify that the initial offline and current online
        #   node are the same
        self.assertEqual(initial_offline_node, after_switch_online_node)
        self.assertEqual(initial_online_node, after_switch_offline_node)

    @attr('all', 'non-revert', 'libvirt_sg_failover')
    def test_02_libvirt_sg_failover(self):
        """
        @tms_id: litpcds_libvirt_sg_failover_tc02
        @tms_requirements_id: LITPCDS-7180
        @tms_title: Libvirt service group failover

        @tms_description: This test checks for service group failover

        @tms_test_steps:
            @step: Obtain the hastatus -sum information for the target SG
            @result: SG information is gathered

            @step: Gather the names of both active/standby nodes on the SG
            @result: Active/Standby Node information is obtained

            @step: Execute a virsh destroy command to destroy the VM on the
            node thats active
            @result: VM destroyed by virsh command

            @step: Wait for the formerly offline node to come online
            @result: Previous standby node is now active node with running VM

            @step: Verify VM is now running on node that was previously in
            standby state, using virsh command
            @result: VM is now running on previously offline node

            @step: Clear and restore faulted node
            @result: Faulted node is cleared

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """

        # 1. Obtain the hastatus -sum info for the target sg
        vcs_info = self.get_sg_vcs_info(self.managed_nodes[0], self.sg3_name)

        # 2. Find out which node VM3 is running on
        initial_online_node = self.filter_by_state(vcs_info, 'ONLINE')[0]
        initial_offline_node = self.filter_by_state(vcs_info, 'OFFLINE')[0]

        # 3. Destroy the vm on the node on which it's running
        target_vm_name = "test-vm-service-3"
        destroy_output = self.run_destroy_command(initial_online_node,
                                                  target_vm_name)
        # Assert vm was destroyed
        exp_destroy_output = "Domain " + target_vm_name + " destroyed"
        self.assertEqual(destroy_output, exp_destroy_output)

        # 4. Wait for failover from initial online node to initial offline
        #    node
        node_status = self.check_node_status(self.managed_nodes[0],
                                             initial_online_node,
                                             self.sg3_name,
                                             "OFFLINE|FAULTED",
                                             self.cs3_online_timeout_mins)
        self.assertTrue(node_status)
        node_status = self.check_node_status(self.managed_nodes[0],
                                             initial_offline_node,
                                             self.sg3_name, "ONLINE",
                                             self.cs3_online_timeout_mins)
        self.assertTrue(node_status)

        # 5. Verify that vm3 is running state on final online node
        final_vm_state = self.get_virsh_vm_state(target_vm_name,
                                                 initial_offline_node)
        self.assertEqual(final_vm_state, "running")

        # 6. Restore faulted node
        self.clean_node(initial_online_node, self.sg3_name, False)

    @attr('all', 'non-revert', 'libvirt_parallel_failure')
    def test_03_libvirt_parallel_failure(self):
        """
        @tms_id: litpcds_libvirt_parallel_failure_tc03
        @tms_requirements_id: LITPCDS-7180
        @tms_title: Libvirt service group parallel failure

        @tms_description: Testing parallel service group failure

        @tms_test_steps:
            @step: Obtain the hastatus -sum information for the target SG
            @result: SG information is gathered

            @step: Gather the names of both active nodes on the SG
            @result: Active Node information is obtained

            @step: Offline one of the nodes in the parallel SG
            @result: SG will be active on only one node

            @step: Wait for one of the nodes to offline
            @result: One node is fully offline

            @step: Clear the fault on the SG nodes
            @result: Fault is cleared on offline node

            @step: Wait for node to come online
            @result: Faulted node comes online

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
            - VM5 is configured as a 2-0 vcs service group
        @tms_execution_type: Automated
        """

        # 1. Obtain the hastatus -sum info for the target sg
        vcs_info = self.get_sg_vcs_info(self.managed_nodes[0], self.sg5_name)

        # 2. Get list of the online nodes
        initial_online_nodes = self.filter_by_state(vcs_info, 'ONLINE')
        online_node_1 = initial_online_nodes[0]
        online_node_2 = initial_online_nodes[1]

        # 3. Virsh destroy vm5 on one node
        target_vm_name = "test-vm-service-5"
        self.run_multiple_destroy_cmd(online_node_1, target_vm_name,
                                      self.sg5_name)

        # 4. Wait for the node to go offline on which the vm was destroyed
        node_status = self.check_node_status(self.managed_nodes[0],
                                             online_node_1,
                                             self.sg5_name,
                                             "OFFLINE|FAULTED",
                                             self.cs5_online_timeout_mins)
        self.assertTrue(node_status)

        # 5. Check that vm5 is still running on other online node virsh console
        node_2_vm5_state = self.get_virsh_vm_state(target_vm_name,
                                                   online_node_2)
        self.assertEqual(node_2_vm5_state, "running")

        # 6. Restore faulted node and bring up vm
        self.clean_node(online_node_1, self.sg5_name, True)

    @attr('all', 'non-revert', 'libvirt_failover_reboot')
    def test_04_libvirt_failover_reboot(self):
        """
        @tms_id: litpcds_libvirt_failover_reboot_tc04
        @tms_requirements_id: LITPCDS-7180
        @tms_title: Libvirt service group failover reboot

        @tms_description: This test checks for service group handover during
        reboot

        @tms_test_steps:
            @step: Check CS_VM4 is active on one node
            @result: CS_VM4 is active on one node

            @step: Check CS_VM5 is active on both nodes
            @result: CS_VM5 is active on both nodes

            @step: Check CS_VM3 is active 1 and standby 1
            @result: CS_VM3 is active on one node

            @step: Issue reboot on active node
            @result: Active node will reboot

            @step: CS_VM3 will fail over to standby node
            @result: CS_VM3 fails over to standby node

            @step: CS_VM5 should be active on the failover node
            @result: CS_VM5 is online on the failover node

            @step: After reboot CS_VM5 should be active on both nodes
            @result: CS_VM5 is active on both nodes

            @step: CS_VM3 should be active on failover node and offline on
            the previously active node
            @result: CS_VM3 is still online on failed over node

            @step: CS_VM4 should be active on one node
            @result: CS_VM4 is active on one node

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
            - VM3 is configured as a 1-1 vcs service group
        @tms_execution_type: Automated
        """

        # Grp_CS_c1_CS_VM3: fail-over service group based on a RHEL7.2 vm image
        # Grp_CS_c1_CS_VM4: fail-over service group based on a RHEL6.10 vm
        # image and dependant on CS_VM3
        # Grp_CS_c1_CS_VM5: two nodes parallel service group based on a
        # RHEL6.10 vm image

        # Check CS_VM4 is online on one node
        sg4_nodes = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                               self.sg4_name, "ONLINE")
        self.assertEqual(len(sg4_nodes), 1)

        # Check CS_VM5 is active on both nodes
        sg5_nodes = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                               self.sg5_name, "ONLINE")
        self.assertEqual(len(sg5_nodes), 2)

        # Check CS_VM3 is online on one node - so find that node.
        sg3_nodes = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                               self.sg3_name, "ONLINE")
        self.assertEqual(len(sg3_nodes), 1)
        active_node = sg3_nodes[0]
        failover_node = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                                   self.sg3_name, "OFFLINE")[0]

        # Issue the reboot command on active_node
        self.run_command(active_node, "/usr/sbin/reboot", su_root=True)

        # Wait for indication that failover has occurred:
        #   CS_VM3 should fail over to standby node
        #   CS_VM5 should be active on the failover node
        for sg_name in [self.sg3_name, self.sg5_name]:
            if sg_name in self.sg3_name:
                timeout = self.cs3_online_timeout_mins
            else:
                timeout = self.cs5_online_timeout_mins
            self.assertTrue(self.check_node_status(failover_node,
                                                   failover_node,
                                                   sg_name, "ONLINE", timeout),
                            '{0} is not ONLINE on {1}'.format(sg_name,
                                                              failover_node))

        # Wait for the first node to restart
        self.wait_for_node_up(active_node)

        # Wait for services to come back up and ensure they resume correct
        # participation in clusters Note: active node is node 1
        self.assertTrue(self.check_node_status(active_node, active_node,
                                               self.sg5_name, "ONLINE",
                                               self.cs5_online_timeout_mins),
                        '{0} is not ONLINE on {1}'.format(self.sg5_name,
                                                          active_node))
        self.assertTrue(self.check_node_status(active_node, failover_node,
                                               self.sg5_name, "ONLINE",
                                               self.cs5_online_timeout_mins),
                        '{0} is not ONLINE on {1}'.format(self.sg5_name,
                                                          failover_node))
        sg4_nodes = \
            self.get_sg_nodes_in_state(active_node, self.sg4_name, "ONLINE")
        sg5_nodes = \
            self.get_sg_nodes_in_state(active_node, self.sg5_name, "ONLINE")
        self.assertEqual(len(sg4_nodes), 1)
        self.assertEqual(len(sg5_nodes), 2)

        current_active = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                                    self.sg3_name, "ONLINE")[0]
        current_inactive = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                                      self.sg3_name,
                                                      "OFFLINE")[0]
        self.assertEqual(current_active, failover_node)
        self.assertEqual(current_inactive, active_node)

    @attr('all', 'non-revert', 'libvirt_failover_hard_reboot')
    def test_05_libvirt_failover_hard_reboot(self):
        """
        @tms_id: litpcds_libvirt_failover_hard_reboot_tc05
        @tms_requirements_id: LITPCDS-7180
        @tms_title: Libvirt service group failover hard reboot

        @tms_description: This test checks for service group handover during
        hard reboot

        @tms_test_steps:
            @step: Check CS_VM4 is active 1 and standby 1
            @result: CS_VM4 is active on one node

            @step: Check CS_VM5 is active on both nodes
            @result: CS_VM5 is active on both nodes

            @step: Check CS_VM3 is active 1 and standby 1
            @result: CS_VM3 will be active on one node

            @step: Power off an active node
            @result: Active node is powered off

            @step: CS_VM3 and CS_VM4 will fail over to standby node
            @result: CS_VM3 and CS_VM4 fail over to standby node

            @step: CS_VM5 should be active on the failover node
            @result: CS_VM5 is online on the failover node

            @step: Power on an active node
            @result: Active node is up

            @step: After power on CS_VM5 should be active on both nodes
            @result: CS_VM5 is active on both nodes

            @step: CS_VM3 and CS_VM4 should be active on failover node and
            offline on the previously active node
            @result: CS_VM3 and CS_VM4 are still online on failed over node

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
            - VM3 is configured as a 1-1 vcs service group
        @tms_execution_type: Automated
        """

        # Grp_CS_c1_CS_VM3: fail-over service group based on a RHEL7.2 vm image
        # Grp_CS_c1_CS_VM4: fail-over service group based on a RHEL6.10 vm
        # image and dependant on CS_VM3
        # Grp_CS_c1_CS_VM5: two nodes parallel service group based on a
        # RHEL6.10 vm image

        # Check CS_VM4 is online on one node
        sg4_nodes = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                               self.sg4_name, "ONLINE")
        self.assertEqual(len(sg4_nodes), 1)

        # Check CS_VM5 is active on both nodes
        sg5_nodes = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                               self.sg5_name, "ONLINE")
        self.assertEqual(len(sg5_nodes), 2)

        # Check CS_VM3 is online on one node - so find that node.
        sg3_nodes = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                               self.sg3_name, "ONLINE")
        self.assertEqual(len(sg3_nodes), 1)
        initial_active_node = sg3_nodes[0]
        failover_node = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                                   self.sg3_name, "OFFLINE")[0]

        # Issue the power off command on active_node
        self.poweroff_peer_node(self.management_server, initial_active_node)

        # Wait for indication that failover has occurred:
        #   CS_VM3 and CS_VM4 should fail over to standby node
        #   CS_VM5 should be active on the failover node
        for sg_name in [self.sg3_name, self.sg4_name, self.sg5_name]:
            if sg_name in self.sg3_name:
                timeout = self.cs3_online_timeout_mins
            elif sg_name in self.sg4_name:
                timeout = self.cs4_online_timeout_mins
            else:
                timeout = self.cs5_online_timeout_mins

            self.assertTrue(self.check_node_status(failover_node,
                                                   failover_node,
                                                   sg_name, "ONLINE", timeout),
                            '{0} is not ONLINE on {1}'.format(sg_name,
                                                              failover_node))

        # Check that there is one node active in each service group
        sg4_nodes = self.get_sg_nodes_in_state(failover_node, self.sg4_name,
                                               "ONLINE")
        sg5_nodes = self.get_sg_nodes_in_state(failover_node, self.sg5_name,
                                               "ONLINE")
        sg3_nodes = self.get_sg_nodes_in_state(failover_node, self.sg3_name,
                                               "ONLINE")

        self.assertEqual(len(sg3_nodes), 1)
        self.assertEqual(len(sg4_nodes), 1)
        self.assertEqual(len(sg5_nodes), 1)

        # Power on the first node and wait until it's up
        self.poweron_peer_node(self.management_server, initial_active_node)
        self.wait_for_node_up(initial_active_node)

        # Wait for services to come back up and ensure they resume correct
        # participation in clusters
        # CS_VM5 should be active on both nodes
        self.assertTrue(self.check_node_status(initial_active_node,
                                               initial_active_node,
                                               self.sg5_name, "ONLINE",
                                               self.cs5_online_timeout_mins),
                        '{0} is not ONLINE on {1}'.format(self.sg5_name,
                                                          initial_active_node))
        sg5_nodes = self.get_sg_nodes_in_state(initial_active_node,
                                               self.sg5_name, "ONLINE")
        self.assertEqual(len(sg5_nodes), 2)

        # CS_VM3 and CS_VM4 should be active on failover node and offline on
        #  the previously active node
        sg3_nodes = self.get_sg_nodes_in_state(initial_active_node,
                                               self.sg3_name, "ONLINE")
        self.assertEqual(len(sg3_nodes), 1)
        current_active = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                                    self.sg3_name, "ONLINE")[0]
        current_inactive = self.get_sg_nodes_in_state(self.managed_nodes[0],
                                                      self.sg3_name,
                                                      "OFFLINE")[0]
        self.assertEqual(current_active, failover_node)
        self.assertEqual(current_inactive, initial_active_node)

        self.assertTrue(self.check_node_status(initial_active_node,
                                               failover_node, self.sg4_name,
                                               "ONLINE",
                                               self.cs4_online_timeout_mins),
                        '{0} is not ONLINE on {1}'.format(self.sg4_name,
                                                          failover_node))
        sg4_nodes = self.get_sg_nodes_in_state(initial_active_node,
                                               self.sg4_name, "ONLINE")
        self.assertEqual(len(sg4_nodes), 1)
