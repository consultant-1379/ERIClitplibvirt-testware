"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     August 2016
@author:    James Langan, Ciaran Reilly
@summary:   Testset to deploy libvirt update 1 to KGB Expansion suite
"""

import time
import test_constants
from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
import libvirt_test_data


class Libvirtexpansionupdate1(GenericTest):
    """
    Description:
        This Test class is a combination of multiple user stories related
        to the libvirt module. The test stories that are covered in this
        file are described below
    """
    def setUp(self):
        """
        Description:
            Runs before every single test
        Actions:
            Determine
                management server,
                primary vcs node(first node in array
                                 returned from test framework)
                list of all managed nodes
        Results:
            Class variables that are required to execute tests
        """

        # 1. Call super class setup
        super(Libvirtexpansionupdate1, self).setUp()
        self.management_server = self.get_management_node_filename()
        self.rhcmd = RHCmdUtils()

        self.vcs_cluster_url = self.find(self.management_server,
                                         '/deployments', 'vcs-cluster')[-1]
        self.cluster_id = self.vcs_cluster_url.split('/')[-1]
        self.nodes_urls = self.find(self.management_server,
                                    self.vcs_cluster_url,
                                    'node')
        self.nodes_to_expand = list()

        self.model = self.get_litp_model_information()
        self.srvc_path = self.model["libvirt"]["software_services_path"]
        self.clus_srvs = self.model["libvirt"]["cluster_services_path"]

        node_exe = self.get_managed_node_filenames()

        self.node1 = node_exe[0]
        self.node2 = ''
        self.node3 = ''
        self.node4 = ''

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Actions:
            -
        Results:
            The super class prints out diagnostics and variables
        """
        super(Libvirtexpansionupdate1, self).tearDown()

    def reboot_node(self, node):
        """ Reboot a node and wait for it to come up. """
        cmd = "/sbin/reboot now"
        out, err, ret_code = self.run_command(node, cmd, su_root=True)
        self.assertTrue(self.is_text_in_list("The system is going down", out))

        self.assertEqual([], err)
        self.assertEqual(0, ret_code)

        self.assertTrue(self.wait_for_node_up(node, timeout_mins=20,
                                              wait_for_litp=True))
        time.sleep(5)

    def _execute_prepare_restore(self, expect_error=None):
        """
        Description:
            Run the litp prepare_restore cli command and wait for plan
            to complete
        Args:
            expect_error (str): Expected error type
        """
        if expect_error is None:
            self.execute_cli_prepare_restore_cmd(self.management_server)
        else:
            _, stderr, _ = self.execute_cli_prepare_restore_cmd(
                            self.management_server, expect_positive=False)
            self.assertTrue(self.is_text_in_list(expect_error, stderr),
                            'Expected error {0} not found in {1}'
                            .format(expect_error, stderr))

        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)
        self.wait_for_plan_state(self.management_server,
                                 test_constants.PLAN_COMPLETE)

    def _expand_model(self):
        """
        This Method is used to expand the LITP model using UTIL scripts
        supplied
        :return: Nothing
        """
        self.nodes_to_expand.append("node2")
        self.nodes_to_expand.append("node3")
        self.nodes_to_expand.append("node4")
        self.execute_expand_script(self.management_server,
                                   'expand_cloud_c1_mn2.sh',
                                    cluster_filename='192.168.0.42_4node.sh')
        self.execute_expand_script(self.management_server,
                                   'expand_cloud_c1_mn3.sh',
                                   cluster_filename='192.168.0.42_4node.sh')
        self.execute_expand_script(self.management_server,
                                   'expand_cloud_c1_mn4.sh',
                                   cluster_filename='192.168.0.42_4node.sh')

    def _perform_cleanup(self):
        """
        Method that restores model back to one node after expansion has
        succeeded
        """
        # If the expansion has succeeded we restore_snapshot to bring us
        # back to a one node state again. Note we set the poweroff_nodes value
        # as expanded nodes should be powered off before restoring back.
        self.nodes_to_expand.append("node2")
        self.nodes_to_expand.append("node3")
        self.nodes_to_expand.append("node4")
        self.execute_and_wait_restore_snapshot(
            self.management_server, poweroff_nodes=self.nodes_to_expand)

        # Create a new snapshot for the next test to have a restore_point
        self.execute_and_wait_createsnapshot(self.management_server,
                                             add_to_cleanup=False)

        # Reset Passwords for next test case
        self.assertTrue(self.set_pws_new_node(self.management_server,
                                              self.node1),
                        'Passwords Not Set')
        stdout, _, _ = self.run_command(self.node1, 'hostname')
        self.assertEqual('node1', stdout[0])

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

    def libvirt_update_1(self, contraction=False):
        """
        Description:
        (litpcds_8851) Extend a vcs-clustered-service that
        contains a vm-service from one node parallel to three nodes parallel
        with nodes priority order present and contract back to one node
        parallel again.

        (torf_124980) Migrate a vcs-clustered-service that has a vm-service
        running, to a new set of nodes (migration + expansion) when the
        cluster is expanding with new nodes

        :param contraction: (bool) indicates the expansion/contraction update
                to run
        :return: Nothing
        """

        # Variables for the model paths
        sg1_path = self.clus_srvs + "/CS_VM1"
        sg2_path = self.clus_srvs + "/CS_VM2"
        vm_srvc_1_path = self.srvc_path + "vm_service_1"
        vm_serv_path_1 = sg1_path + "/applications/vm_service_1"
        vm_serv_path_2 = sg2_path + "/applications/vm_service_2"

        vm_image_3_path = self.model["libvirt"][
                              "software_images_path"] + "vm_image_3"

        exp_lvtd_vm1 = libvirt_test_data.EXPANDED_SERVICE_GROUP_1_DATA
        exp_lvtd_vm2 = libvirt_test_data.EXPANDED_SERVICE_GROUP_2_DATA
        con_lvtd_vm1 = libvirt_test_data.CONTRACT_SERVICE_GROUP_1_DATA

        vm_images = libvirt_test_data.VM_IMAGES

        if not contraction:
            self.execute_cli_create_cmd(
                self.management_server, vm_image_3_path, "vm-image",
                props="source_uri={0} name={1}".format(
                    vm_images["VM_IMAGE3"]["image_url"],
                    vm_images["VM_IMAGE3"]["image_name"]),
                add_to_cleanup=False)

            # Update the service to use vm-image-2
            image_props = 'image_name={0}'\
                .format(exp_lvtd_vm1["VM_SERVICE"]["image_name"])
            self.execute_cli_update_cmd(self.management_server, vm_srvc_1_path,
                                        image_props)

            # Update the node list to include 3 active nodes instead of '1'
            node_props = 'active={0} node_list={1}'.format(
                        exp_lvtd_vm1["CLUSTER_SERVICE"]["active"],
                        exp_lvtd_vm1["CLUSTER_SERVICE"]["node_list"])
            self.execute_cli_update_cmd(self.management_server,
                                        sg1_path, node_props)

            vm_serv_props = 'hostnames={0}'.format(
                                exp_lvtd_vm1["VM_SERVICE"]["hostnames"])
            self.execute_cli_update_cmd(self.management_server,
                                        vm_serv_path_1, vm_serv_props)

            vm_net_props = "ipaddresses={0}".format(
                exp_lvtd_vm1["NETWORK_INTERFACES"]["NET1"]["ipaddresses"])
            self.execute_cli_update_cmd(self.management_server,
                                vm_serv_path_1 + "/vm_network_interfaces/net1",
                                vm_net_props)

            ###############################################################
            # TORF-128940-  Update the node list to include 3 active nodes
            # during migration
            ###############################################################
            node_props = 'active={0} node_list={1}'.format(
                        exp_lvtd_vm2["CLUSTER_SERVICE"]["active"],
                        exp_lvtd_vm2["CLUSTER_SERVICE"]["node_list"])
            self.execute_cli_update_cmd(self.management_server,
                                        sg2_path, node_props)

            vm_serv_props = 'hostnames={0}'.format(exp_lvtd_vm2["VM_SERVICE"]
                                                   ["hostnames"])
            self.execute_cli_update_cmd(self.management_server,
                                        vm_serv_path_2, vm_serv_props)
            vm_net_props = "ipaddresses={0}".format(
                exp_lvtd_vm2["NETWORK_INTERFACES"]["NET2"]["ipaddresses"])
            self.execute_cli_update_cmd(self.management_server,
                                vm_serv_path_2 + "/vm_network_interfaces/net2",
                                vm_net_props)
            vm_net_props = "ipaddresses={0}".format(
                exp_lvtd_vm2["NETWORK_INTERFACES"]["NET3"]["ipaddresses"])
            self.execute_cli_update_cmd(self.management_server,
                                vm_serv_path_2 + "/vm_network_interfaces/net3",
                                vm_net_props)
        else:
            # Update the service to use vm-image-3
            image_props = 'image_name={0}'\
                .format(con_lvtd_vm1["VM_SERVICE"]["image_name"])
            self.execute_cli_update_cmd(self.management_server, vm_srvc_1_path,
                                        image_props)

            # Contract service to 1 node from 3 nodes.
            node_props = 'active={0} node_list={1}'.format(
                        con_lvtd_vm1["CLUSTER_SERVICE"]["active"],
                        con_lvtd_vm1["CLUSTER_SERVICE"]["node_list"])
            self.execute_cli_update_cmd(self.management_server, sg1_path,
                                        node_props)

            vm_serv_props = 'hostnames={0}'.format(
                                con_lvtd_vm1["VM_SERVICE"]["hostnames"])
            self.execute_cli_update_cmd(self.management_server,
                                        vm_serv_path_1, vm_serv_props)

            vm_net_props = "ipaddresses={0}".format(
                con_lvtd_vm1["NETWORK_INTERFACES"]["NET1"]["ipaddresses"])
            self.execute_cli_update_cmd(self.management_server,
                                vm_serv_path_1 + "/vm_network_interfaces/net1",
                                vm_net_props)

    def libvirt_update_2(self):
        """
        Description:
        (torf_159091) Migrate a vcs-clustered-service that has a vm-service
        running, to a new set of nodes (migration + expansion) when the
        cluster is expanding with new nodes

        :return: Nothing
        """

        # Variables for the model paths
        sg1_path = self.clus_srvs + "/CS_VM1"
        sg2_path = self.clus_srvs + "/CS_VM2"
        vm_serv_path_1 = sg1_path + "/applications/vm_service_1"
        vm_serv_path_2 = sg2_path + "/applications/vm_service_2"

        exp_lvtd_2_vm1 = \
            libvirt_test_data.EXPANDED_SERVICE_GROUP_1_UPDATE_3_DATA
        exp_lvtd_2_vm2 = \
            libvirt_test_data.EXPANDED_SERVICE_GROUP_2_UPDATE_3_DATA

        #########################################################
        # TORF-159091 - Update CS_VM1 to be on nodes 1 & 2 ######
        #########################################################
        # Update the node list to include 2 active nodes instead of '3'
        node_props = 'active={0} node_list={1}'.format(
            exp_lvtd_2_vm1["CLUSTER_SERVICE"]["active"],
            exp_lvtd_2_vm1["CLUSTER_SERVICE"]["node_list"])
        self.execute_cli_update_cmd(self.management_server, sg1_path,
                                    node_props)

        vm_serv_props = 'hostnames={0}'.format(
            exp_lvtd_2_vm1["VM_SERVICE"]["hostnames"])
        self.execute_cli_update_cmd(self.management_server, vm_serv_path_1,
                                    vm_serv_props)

        vm_net_props = "ipaddresses={0}".format(
            exp_lvtd_2_vm1["NETWORK_INTERFACES"]["NET1"]["ipaddresses"])
        self.execute_cli_update_cmd(self.management_server,
                                    vm_serv_path_1 +
                                    "/vm_network_interfaces/net1",
                                    vm_net_props)

        #########################################################
        # TORF-159091 - Update CS_VM2 to be on nodes 3 & 4 ######
        #########################################################
        node_props = 'active={0} node_list={1}'.format(
                        exp_lvtd_2_vm2["CLUSTER_SERVICE"]["active"],
                        exp_lvtd_2_vm2["CLUSTER_SERVICE"]["node_list"])
        self.execute_cli_update_cmd(self.management_server, sg2_path,
                                    node_props)

        vm_serv_props = 'hostnames={0}'.format(exp_lvtd_2_vm2["VM_SERVICE"]
                                               ["hostnames"])
        self.execute_cli_update_cmd(self.management_server,
                                    vm_serv_path_2, vm_serv_props)
        vm_net_props = "ipaddresses={0}".format(exp_lvtd_2_vm2
                                                ["NETWORK_INTERFACES"]["NET2"]
                                                ["ipaddresses"])
        self.execute_cli_update_cmd(self.management_server,
                                    vm_serv_path_2 +
                                    "/vm_network_interfaces/net2",
                                    vm_net_props)
        vm_net_props = "ipaddresses={0}".format(exp_lvtd_2_vm2
                                                ["NETWORK_INTERFACES"]
                                                ["NET3"]["ipaddresses"])
        self.execute_cli_update_cmd(self.management_server,
                                    vm_serv_path_2 +
                                    "/vm_network_interfaces/net3",
                                    vm_net_props)

    @attr('expansion', 'revert', "libvirt_expansion_update1",
          'story8851_tc06', 'story113124', 'story113124_tc03',
          'story124980_tc11')
    def test_p_libvirt_expansion_update_plan_1(self):
        """
        @tms_id: litpcds_libvirt_expansion_tc02
        @tms_requirements_id: LITPCDS-8851, TORF-113124, TORF-124980

        @tms_title: First update for multiple cluster services running in
        the litp model during cluster expansion
        @tms_description: Updates the following item configurations in the
            litp model.
            -Expands the number of VMs running on a cluster to deal with
            increased capacity demands(litpcds_8851)
            -Migrate service groups to new nodes with running VMs, so that i
            can optimise an expanded cluster(torf_124980)

        @tms_test_steps:
            @step: Expand the litp model to run on three nodes
            @result: litp model successfully expanded to three nodes

            @step: Assert node list prior to update
            @result: Node list should only consist of one node

            @step: Execute a litp update command to update the CS_VM1
                   to use vm-image-2.
            @result: Command executes successfully

            @step: Execute a litp update command to update the node list to
                   include two new nodes and update the active property from
                   a value of '1' to '3' for clustered service CS_VM1
            @result: Command executes successfully

            @step: Execute a litp update command to update the hostnames to
                   include two hostnames and rename existing hostname for
                   clustered service CS_VM1
            @result: Command executes successfully

            @step: Execute a litp update command to update the ipaddresses
                   to include two new ipaddresses for clustered service CS_VM1
            @result: Command executes successfully

            @step: Update CS_VM2 node_list to be migrated to multiple nodes
            n4,n2,n3
            @result: CS_VM2 will be migrated to different nodes

            @step: Update Network IP addresses and hostnames as part of
            expansion for CS_VM2
            @result: Hostnames and IP addresses are all acceptable

            @step: Verify used vm-image-1 is in /var/lib/libvirt/images
                   directory on node 1 and unused vm-image-2 is not.
            @result: /var/lib/libvirt/images directory on node 1 contains
                     vm-image-1, but not vm-image-2.

            @step: Create and run plan
            @result: Plan is created and run successfully

            @step: Set passwords on newly expanded node2, node3 and node4
            @result: Passwords configured node2, node3 and node4

            @step: Verify used vm-image-2 is in /var/lib/libvirt/images
                   directory on nodes 1, 2 and 3 and unused vm-image-1 is not
                   in directory.
            @result: /var/lib/libvirt/images directory on nodes 1, 2 and 3
                     contains vm-image-2, but not vm-image-1.

            @step: Assert node list after to update for CS_VM2 migration
            @result: Node list should consist of 3 different nodes

            @step: Execute a litp update command to contract the node list to
                   n1 only and update the active property from a value of '3'
                   to '1' for clustered service CS_VM1
            @result: Command executes successfully

            @step: Execute a litp update command to update the hostnames to
                   include only one hostname for clustered service CS_VM1
            @result: Command executes successfully

            @step: Execute a litp update command to update the ipaddresses
                   to include only one ipaddress for clustered service CS_VM1
            @result: Command executes successfully

            @step: Create and run plan
            @result: Plan is created and run successfully

            @step: Verify used vm-image-3 is in /var/lib/libvirt/images
                   directory on node 1 and unused vm-image-2 is not
                   in directory.
            @result: /var/lib/libvirt/images directory on node 1 contains
                     vm-image-3, but not vm-image-2.

        @tms_test_precondition:
            - testset_libvirt_initial_setup_expansion
            - A 1 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        sg1_path = self.clus_srvs + "/CS_VM1"
        sg2_path = self.clus_srvs + "/CS_VM2"
        # Expand the litp model to run on three nodes
        self._expand_model()

        node_exe = self.get_managed_node_filenames()

        self.node1 = node_exe[0]
        self.node2 = node_exe[1]
        self.node3 = node_exe[2]
        self.node4 = node_exe[3]

        vm_images = libvirt_test_data.VM_IMAGES
        vm_image1_url = vm_images["VM_IMAGE1"]['image_url'].split('/')[-1]
        vm_image2_url = vm_images["VM_IMAGE2"]['image_url'].split('/')[-1]
        vm_image3_url = vm_images["VM_IMAGE3"]['image_url'].split('/')[-1]

        ##################################################################
        #TORF-124980: Assert Node list prior update for CS_VM2
        node_list = self.get_props_from_url(self.management_server,
                                            sg2_path,
                                            filter_prop='node_list')
        self.assertEqual(node_list, 'n1')
        ##################################################################

        self.libvirt_update_1()

        # TORF-113124: test_03_p_expansion_contraction_vm_image_update
        # Verify used vm-image-1 is in /var/lib/libvirt/images directory on
        # node 1, but vm-image-2 is not in directory.
        self.assertTrue(self._check_image_on_node(vm_image1_url, self.node1))
        self.assertTrue(self._check_image_on_node(vm_image2_url, self.node1))

        # Create/ Run plan
        plan_timeout_mins = 90
        self.run_and_check_plan(self.management_server,
                                test_constants.PLAN_COMPLETE,
                                plan_timeout_mins,
                                add_to_cleanup=False)

        self.set_pws_new_node(self.management_server, self.node2)
        self.set_pws_new_node(self.management_server, self.node3)
        self.set_pws_new_node(self.management_server, self.node4)

        # TORF-113124: test_03_p_expansion_contraction_vm_image_update
        # Verify unused vm-image-1 has been removed from directory
        # /var/lib/libvirt/images directory on all peer nodes.
        self.assertFalse(
            self._check_image_on_node(vm_image1_url,
                                      self.node1))
        self.assertFalse(
            self._check_image_on_node(vm_image1_url,
                                      self.node2))
        self.assertFalse(
            self._check_image_on_node(vm_image1_url,
                                      self.node3))

        # TORF-113124: test_03_p_expansion_contraction_vm_image_update
        # Verify used vm-image-2 is in directory /var/lib/libvirt/images
        # on all peer nodes.
        self.assertTrue(self._check_image_on_node(vm_image2_url, self.node1))
        self.assertTrue(self._check_image_on_node(vm_image2_url, self.node2))
        self.assertTrue(self._check_image_on_node(vm_image2_url, self.node3))

        node_list = self.get_props_from_url(self.management_server,
                                            sg1_path,
                                            filter_prop='node_list')
        self.assertEqual(node_list, 'n1,n2,n3')

        ##################################################################
        # TORF-124980: Assert Node list after migration update for CS_VM2
        node_list = self.get_props_from_url(self.management_server,
                                            sg2_path,
                                            filter_prop='node_list')
        self.assertEqual(node_list, 'n2,n3,n4')
        ##################################################################

        # LITPCDS - 8851: Contract SG with VM configured
        self.libvirt_update_1(contraction=True)
        self.run_and_check_plan(self.management_server,
                                test_constants.PLAN_COMPLETE,
                                plan_timeout_mins,
                                add_to_cleanup=False)

        # TORF-113124: test_03_p_expansion_contraction_vm_image_update
        # Verify used vm-image-3 is in directory /var/lib/libvirt/images
        # on node 1.
        self.assertTrue(self._check_image_on_node(vm_image3_url, self.node1))

        # TORF-113124: test_03_p_expansion_contraction_vm_image_update
        # Verify unused vm-image-2 is removed from directory
        # /var/lib/libvirt/images on node 1.
        self.assertFalse(self._check_image_on_node(vm_image2_url, self.node1))

    @attr('expansion', 'revert', "libvirt_expansion_update2", 'story159091',
          'story159091_tc08')
    def test_p_libvirt_expansion_update_plan_2(self):
        """
        @tms_id: litpcds_libvirt_expansion_tc03
        @tms_requirements_id: TORF-159091

        @tms_title: Second update for multiple cluster services running in
        the litp model during cluster expansion
        @tms_description: Updates the following item configurations in the
            litp model.
            -Expand/Contract service groups by updating the node_list to not
            interrupt service on nodes that remain in the node_list property
            (torf_159091)

        @tms_test_steps:
            @step: Ensure the node list for CS_VM1 and CS_VM2 are 3 nodes
            @result: Nodes in CS_VM1 and 2 have 3 nodes
            @step: Update SGs node list to keep 1 node, remove and add 1 node
            @result: CS_VM1 = n1,n2 and CS_VM2 =n3,n4
            @step: Create/ Run plan
            @result: Plan is created and run
            @step: Ensure the node list for CS_VM1 and CS_VM2 are 2 nodes
            @result: Nodes in CS_VM1 =n1,n2 and CS_VM2 =n3,n4
            @step: During plan ensure CS_VM2 is still ONLINE on node n3
            @result: CS_VM are online on overlapping nodes

            @step: Assert node list prior to update
            @result: Node list should only consist of one node

        @tms_test_precondition:
            - testset_libvirt_initial_setup_expansion
            - test_p_libvirt_expansion_update_plan_1
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        # Timeout being set to 25 to account for delay seen in CIS-66850
        plan_timeout_mins = 25
        sg1_path = self.clus_srvs + "/CS_VM1"
        sg2_path = self.clus_srvs + "/CS_VM2"

        ##################################################################
        # TORF-159091: Assert Node list before update for CS_VM1 and CS_VM2
        node_list = self.get_props_from_url(self.management_server,
                                            sg1_path,
                                            filter_prop='node_list')
        self.assertEqual(node_list, 'n1')

        node_list = self.get_props_from_url(self.management_server,
                                            sg2_path,
                                            filter_prop='node_list')
        self.assertEqual(node_list, 'n2,n3,n4')
        ##################################################################

        # Update SGs node list for torf-159091
        self.libvirt_update_2()

        # Create/ Run plan
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)

        task_list = self.get_full_list_of_tasks(self.management_server)
        self.assertFalse('Lock VCS on node "node3"' in task_list)

        csvm2_name = self.vcs.generate_clustered_service_name('CS_VM2',
                                                              self.cluster_id)
        self.wait_for_vcs_service_group_online(self.node1, csvm2_name,
                                               online_count=2,
                                               wait_time_mins=15)

        self.assertTrue(self.wait_for_plan_state(
            self.management_server,
            test_constants.PLAN_COMPLETE,
            plan_timeout_mins
        ))

        ##################################################################
        # TORF-159091: Assert Node list before update for CS_VM1 and CS_VM2
        node_list = self.get_props_from_url(self.management_server,
                                            sg1_path,
                                            filter_prop='node_list')
        self.assertEqual(node_list, 'n1,n2')

        node_list = self.get_props_from_url(self.management_server,
                                            sg2_path,
                                            filter_prop='node_list')
        self.assertEqual(node_list, 'n3,n1')
        ##################################################################

        # Bring litp model back to one node after expansion test is complete
        self._perform_cleanup()
