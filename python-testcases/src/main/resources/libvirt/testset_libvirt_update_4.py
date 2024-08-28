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
from litp_generic_test import GenericTest, attr
from libvirt_utils import LibvirtUtils
import test_constants
import libvirt_test_data


class Libvirtupdate4(GenericTest):
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
        super(Libvirtupdate4, self).setUp()

        self.model = self.get_litp_model_information()
        self.management_server = self.model["ms"][0]["name"]

        self.srvc_path = self.model["libvirt"]["software_services_path"]
        self.clus_srvs = self.model["libvirt"]["cluster_services_path"]

        self.up_dict2 = libvirt_test_data.UPDATED4_SERVICE_GROUP_2_DATA
        self.up_dict4 = libvirt_test_data.UPDATED4_SERVICE_GROUP_4_DATA

        self.libvirt = LibvirtUtils()
        self.vcs_cluster_url = self.find(self.management_server,
                                         "/deployments", "vcs-cluster")[-1]

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Results:
            The super class prints out diagnostics and variables
        """
        super(Libvirtupdate4, self).tearDown()

    def update_timeout_values(self):
        """
        Description:
            This test involves the update of the timeout values for
            service groups 3, 4 and 5
        """
        # Variables
        vcs_sg3 = self.clus_srvs + \
                  "/CS_VM3"
        vcs_sg4 = self.clus_srvs + \
                  "/CS_VM4"
        vcs_sg5 = self.clus_srvs + \
                  "/CS_VM5"

        timeouts = libvirt_test_data.TIMEOUTS

        self.execute_cli_update_cmd(self.management_server, vcs_sg3,
                                    props="offline_timeout='{0}' "
                                          "online_timeout='{1}'".format(
                                        timeouts["OFFLINE"]["CS_VM3"],
                                        timeouts["ONLINE"]["CS_VM3"]))
        self.execute_cli_update_cmd(self.management_server, vcs_sg4,
                                    props="offline_timeout='{0}' "
                                          "online_timeout='{1}'".format(
                                        timeouts["OFFLINE"]["CS_VM4"],
                                        timeouts["ONLINE"]["CS_VM4"]))
        self.execute_cli_update_cmd(self.management_server, vcs_sg5,
                                    props="offline_timeout='{0}' "
                                          "online_timeout='{1}'".format(
                                        timeouts["OFFLINE"]["CS_VM5"],
                                        timeouts["ONLINE"]["CS_VM5"]))

    def update_network_cs_plan_1(self):
        """
        Description:
            This test involves the removal of service group 1, and updating
            service group 2.
        """
        # Set up the variables for the urls
        vcs_sg1 = self.clus_srvs + "/CS_VM1"
        vcs_sg2 = self.clus_srvs + "/CS_VM2"
        vcs_sg4 = self.clus_srvs + "/CS_VM4"
        sg2_vm = vcs_sg2 + "/applications/vm_service_2"
        sg4_vm = vcs_sg4 + "/applications/vm_service_4"

        #########################
        #                       #
        #  Service Group CS_VM1 #
        #                       #
        #########################
        #LITPCDS-11247 - Remove VCS clustered service group
        self.execute_cli_remove_cmd(self.management_server, vcs_sg1)

        #########################
        #                       #
        #  Service Group CS_VM2 #
        #                       #
        #########################
        # Dictionary variables
        fmt1 = self.up_dict2["CLUSTER_SERVICE"]
        fmt2 = self.up_dict2["NETWORK_INTERFACES"]["NET2"]["ipaddresses"]
        fmt3 = self.up_dict2["NETWORK_INTERFACES"]["NET3"]["ipaddresses"]
        fmt22 = self.up_dict2["NETWORK_INTERFACES"]["NET22"]["ipaddresses"]
        fmt30 = self.up_dict2["NETWORK_INTERFACES"]["NET30"]["ipaddresses"]
        fmt31 = self.up_dict2["NETWORK_INTERFACES"]["NET31"]["ipaddresses"]
        fmtd = self.up_dict2["NETWORK_INTERFACES"]["NET_DHCP"]["ipaddresses"]

        # LITPCDS-11750 - contract my parallel VCS Service Group
        # which is running VMs
        self.execute_cli_update_cmd(self.management_server,
                                    vcs_sg2,
                                    props="active='{0}' node_list='{1}'"
                                    .format(fmt1["active"],
                                            fmt1["node_list"]))

        # LITPCDS-7179 - Update the ip addresses of the vm network interfaces
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm + \
                                    "/vm_network_interfaces/net2",
                                    props="ipaddresses='{0}'".format(fmt2))
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm + \
                                    "/vm_network_interfaces/net3",
                                    props="ipaddresses='{0}'".format(fmt3))
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm + \
                                    "/vm_network_interfaces/net22",
                                    props="ipaddresses='{0}'".format(fmt22))
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm + \
                                    "/vm_network_interfaces/net30",
                                    props="ipaddresses='{0}'".format(fmt30))
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm + \
                                    "/vm_network_interfaces/net31",
                                    props="ipaddresses='{0}'".format(fmt31))
        # LITPCDS-8187 - Configure VM network interface with an IP allocated
        # from a DHCP server
        self.execute_cli_update_cmd(self.management_server,
                                    sg2_vm + \
                                    "/vm_network_interfaces/net_dhcp",
                                    props="ipaddresses='{0}'".format(fmtd))

        # TORF-107476 - TC12 -Remove VM-RAM-MOUNT from CS_VM2 on the software
        # level
        self.execute_cli_remove_cmd(self.management_server, self.srvc_path +
                                    'vm_service_2/vm_ram_mounts/'
                                    'vm_ram_mount_2')

        #########################
        #                       #
        #  Service Group CS_VM4 #
        #                       #
        #########################

        # TORF-107476 - TC19- Update CS_VM4 mount options to default value
        self.execute_cli_update_cmd(self.management_server, sg4_vm +
                                    '/vm_ram_mounts/vm_ram_mount_4',
                                    props='mount_options={0}'
                                    .format(self.up_dict4["VM_RAM_MOUNT"]
                                        ["mount_options"]))

    def _check_image_on_node(self, img_name, node):
        """
        TORF-113124: Test method to verify that any unused VM-Image is removed
        from /var/lib/libvirt/images directory on node
        :param img_name: name of image removed
        :param node: node to run command on
        :return: True/ False
        """
        file_contents, _, _ = \
            self.run_command(node, 'ls {0}/ -h'.format(test_constants
                                                       .LIBVIRT_IMAGE_DIR),
                             su_root=True)

        return self.is_text_in_list(img_name, file_contents)

    @attr('all', 'non-revert', "LITPCDS-11247", "LITPCDS-8187", "TORF-107476")
    def test_p_libvirt_update_plan_4(self):
        """
        @tms_id: litpcds_libvirt_tc05
        @tms_requirements_id: LITPCDS-11247, LITPCDS-8187, LITPCDS-7179,
        TORF-107476, TORF-113124, LITPCDS-11405

        @tms_title: Fourth Update for multiple cluster services running in the
        litp model
        @tms_description: Updates the following item configurations in the
        litp model
            - Remove a VCS Service Group running a VM(litpcds_11247)
            - Configure a VM network interface with an IP allocated from a
            DHCP server(litpcds_8187)
            - Update networking in my VM service(litpcds_7179)
            - Update vm-ram-mounts (torf_107476)
            - Verify VM-Image-2 is removed from relevant nodes after CS_VM1
                is removed (torf_113124)
            - Remove a running VM from the MS (litpcds-11405)

        @tms_test_steps:
            @step: Remove Clustered Service CS_VM1
            @result: CS_VM1 is removed

            @step: Contract service group CS_VM2
            @result: CS_VM2 is contracted to one node

            @step: Update CS_VM2 VM Network Interfaces IP addresses
            @result: IP addresses assigned to VM Network Interfaces are
            updated

            @step: Remove CS_VM2 VM RAM Mount
            @result: VM RAM Mount is removed from CS_VM2

            @step: Update VM RAM Mount on CS_VM4
            @result: CS_VM4 VM RAM Mount is updated with optional parameters

            @step: Update CS_VM3, CS_VM4 and CS_VM5 online and offline
            timeouts to default value '300'
            @result: Online and Offline timeouts are updated in CS_VM3, CS_VM4
            and CS_VM5

            @step: Validate VM-Image-2 exists on node
            @result: VM-Image-2 exists on node

            @step: Remove Clustered Service MS_VM1
            @result: MS_VM1 is removed

            @step: Create and run plan
            @result: Plan is created and run to completion

            @step: Validate CS_VM1 has been fully removed
            @result: CS_VM1 is removed

            @step: Validate CS_VM2 is contracted successfully
            @result: CS_VM2 is contracted to one node

            @step: Validate VM RAM Mount is updated
            @result: VM RAM Mount on CS_VM2 is updated

            @step: Validate VM-Image-2 is removed on node
            @result: VM-Image-2 doesnt exists on node

            @step: Validate MS_VM1 has been fully removed
            @result: MS_VM1 is removed

        @tms_test_precondition:
            - testset_libvirt_initial_setup, testset_libvirt_update_1,
              testset_libvirt_update_2, and testset_libvirt_update_3 have ran
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        # Setup the test case.
        plan_timeout_mins = 60
        self.update_network_cs_plan_1()
        self.update_timeout_values()
        primary_node = self.get_managed_node_filenames()[0]
        secondary_node = self.get_managed_node_filenames()[1]
        image_filenames = libvirt_test_data.VM_IMAGE_FILE_NAME

        # TORF-113124: test_08_p_vm_image_removed_after_CS_VM_removed
        # Assert VM-image 2 exists on node 1 and node 2 before plan is run
        for node in [primary_node, secondary_node]:
            self.assertTrue(
                self._check_image_on_node(image_filenames["VM_IMAGE2"], node))

        # LITPCDS-11405 - Remove a service group from MS
        ms_vm = "/ms/services/MS_VM1"
        self.execute_cli_remove_cmd(self.management_server, ms_vm,
                                    add_to_cleanup=False)

        # Create and execute plan, expect it to succeed
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)

        self.assertTrue(self.wait_for_plan_state(
            self.management_server,
            test_constants.PLAN_COMPLETE,
            plan_timeout_mins
        ))

        self._check_story11247()
        self._check_story_11750()

        # TORF-107476 - TC19 Verify mount options are default value
        # May need to add functionality to mount method when ready
        self._check_mount_conf(self.up_dict4["HOSTNAMES"]["hostnames"],
                               self.up_dict4["NETWORK_INTERFACES"]["NET8"]
                               ["ipaddresses"],
                               self.up_dict4["VM_RAM_MOUNT"]["type"],
                               self.up_dict4["VM_RAM_MOUNT"]["mount_point"])

        # TORF-113124: test_08_p_vm_image_removed_after_CS_VM_removed
        # Assert VM-image-2 doesnt exist on nodes under
        # /var/lib/libvirt/images
        for node in [primary_node, secondary_node]:
            self.assertFalse(
                self._check_image_on_node(image_filenames["VM_IMAGE2"], node))

        # LITPCDS-11405 - verify MS service group is fully removed
        self._check_story11405()

    def _check_mount_conf(self, hostname, ipaddr, mnt_type, mnt_point,
                          mount_options=''):
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
            MNT_OPTIONS: mount options to be checked against
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

        if mount_options != '':
            if mnt_pnt_flag:
                self.assertTrue(self.is_text_in_list(mnt_type and
                                                     mount_options, actual))
            else:
                self.log('info', 'VM_RAM_MOUNT not found in hostname {0}'
                         .format(hostname))
                self.assertFalse(self.is_text_in_list(mnt_type and
                                                      mount_options, actual))
        else:
            if mnt_pnt_flag:
                self.assertTrue(self.is_text_in_list(mnt_type, actual))
            else:
                self.log('info', 'VM_RAM_MOUNT not found in hostname {0}'
                         .format(hostname))
                self.assertFalse(self.is_text_in_list(mnt_type, actual))

    def _check_story11247(self):
        """
        Description:
        Test to verify that removed VCS Service Group VMs were
        correctly removed

        Steps:
        1. Verify the VMs are no longer running through virsh commands and
            instance directories.
        2. Ensure images and config files are also removed.
        """
        service_name = (libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA
                        ['VM_SERVICE']['service_name'])
        path_to_instance_dir = (test_constants.LIBVIRT_INSTANCES_DIR +
                                service_name)
        path_to_etc_init_file = ('/etc/init.d/' + service_name)

        node_urls = self.find(self.management_server, '/deployments', 'node')
        for url in node_urls:
            node_to_exe = self.get_node_filename_from_url(
                self.management_server, url)
            # Step 1
            std_out, _, rc = \
                self.run_command(node_to_exe,
                                 self.libvirt.get_virsh_dominfo_cmd(
                                     service_name),
                                 su_root=True)
            self.assertEqual(1, rc)
            self.assertEqual('error: Domain not found: no domain with'
                             ' matching name \'{0}\''.
                             format(service_name),
                             std_out[-1])
            # Step 2
            self.assertFalse(self.remote_path_exists(node_to_exe,
                                                     path_to_instance_dir,
                                                     expect_file=False),
                             'Instance directory is still present')
            self.assertFalse(self.
                             remote_path_exists(node_to_exe,
                                                path_to_etc_init_file),
                             '/etc/init.d script is still present')

    def _check_story_11750(self):
        """
        Description:
        Test to validate that when the node list is contracted with a parallel
        VCS SG that any files associated with the service are removed from
        the disassociated node, along with any VMs that were running
        are stopped and LSB scripts are removed

        Steps

        1. Create two node parallel VCS CS.
        2. Update node list to be one node parallel.
        3. Verify any files associated with the service is removed from
            the node (i.e. Instance image files & Configuration files).
        4. Any VMs are not running on removed node.
        5. Verify LSB script is removed.
        """
        conf = self.libvirt.generate_conf_plan2()
        path_to_instance_dir = (test_constants.LIBVIRT_INSTANCES_DIR + conf
                                ['lsb_app_properties']
                                ['vm_service_2']['service_name'])
        path_to_etc_init_file = ('/etc/init.d/' + conf
                                 ['lsb_app_properties']['vm_service_2']
                                 ['service_name'])
        # Step 1, 2
        # get cs conf path
        cs_name = 'CS_VM2'
        cs_url = self.get_cs_conf_url(self.management_server,
                                      cs_name,
                                      self.vcs_cluster_url)
        if cs_url is not None:
            path_to_node_image_file = self._get_vm_image_filename(cs_url)

            contracted_node = self._get_contracted_node()
            not_contracted_node = self._get_non_contracted_node()
            # Step 3
            self.assertFalse(self.remote_path_exists(contracted_node,
                                                     path_to_instance_dir,
                                                     expect_file=False),
                             'Instance directory is still present')
            self.assertFalse(self.
                             remote_path_exists(contracted_node,
                                                path_to_node_image_file,
                                                su_root=True),
                             'Main image file is still present')
            self.assertFalse(self.
                             remote_path_exists(contracted_node,
                                                path_to_node_image_file +
                                                '_checksum.md5',
                                                su_root=True),
                             'Main image checksum file is still present')
            # Check image is not removed in not contracted node
            self.assertTrue(self.
                            remote_path_exists(not_contracted_node,
                                               path_to_node_image_file,
                                               su_root=True),
                            'Main image file is removed')
            self.assertTrue(self.
                            remote_path_exists(not_contracted_node,
                                               path_to_node_image_file +
                                               '_checksum.md5',
                                               su_root=True),
                            'Main image checksum file is removed')
            # Step 4
            std_out, _, rc = \
                self.run_command(contracted_node, self.libvirt.
                                 get_virsh_dominfo_cmd(conf
                                                       ['lsb_app_properties']
                                                       ['vm_service_2']
                                                       ['service_name']),
                                 su_root=True)
            self.assertEqual(1, rc)
            self.assertEqual('error: Domain not found: no domain with'
                             ' matching name \'{0}\''.
                             format(conf['lsb_app_properties']
                                             ['vm_service_2']
                                             ['service_name']),
                             std_out[-1])
            std_out, _, rc = \
                self.run_command(not_contracted_node, self.libvirt.
                                 get_virsh_dominfo_cmd(conf
                                                       ['lsb_app_properties']
                                                       ['vm_service_2']
                                                       ['service_name']) +
                                 " | awk 'NR == 2 {{print}}'",
                                 su_root=True)
            self.assertEqual(0, rc)
            self.assertEqual(conf['lsb_app_properties']
                                      ['vm_service_2']
                                      ['service_name'],
                             std_out[0].rsplit(' ')[-1])
            # Step 5
            self.assertFalse(self.
                             remote_path_exists(contracted_node,
                                                path_to_etc_init_file),
                             '/etc/init.d script is still present')
        else:
            raise ValueError('Runtime VCS service "CS_VM2" is not present')

    def _check_story11405(self):
        """
        Description:
        Test to verify that removed VCS Service Group VM is correctly removed

        Steps:
        1. Verify the VM is no longer running on MS
        2. Ensure vm image and config files are also removed
        """
        service_name = \
            libvirt_test_data.MS_VM1_DATA['VM_SERVICE']['service_name']
        path_to_instance_dir = (test_constants.LIBVIRT_INSTANCES_DIR +
                                service_name)
        # Step 1
        std_out, _, rc = \
            self.run_command(self.management_server,
                             self.libvirt.get_virsh_dominfo_cmd(service_name),
                             su_root=True)
        self.assertEqual(1, rc)
        self.assertEqual('error: Domain not found: no domain with matching '
                         'name \'{0}\''.format(service_name), std_out[-1])
        # Step 2
        self.assertFalse(self.remote_path_exists(self.management_server,
                                                 path_to_instance_dir,
                                                 expect_file=False),
                         'Instance directory is still present')
        self.assertFalse(self._check_image_on_node(
                            libvirt_test_data.VM_IMAGE_FILE_NAME["VM_IMAGE2"],
                            self.management_server),
                        'Image file is still present')

    def _get_vm_image_filename(self, cs_url):
        """

        :param cs_url:
        :return:
        """
        vm_service_url = self.find(self.management_server,
                                   cs_url + '/applications',
                                   'reference-to-vm-service')
        image_name = self.get_props_from_url(self.management_server,
                                             vm_service_url[0],
                                             'image_name')
        image_urls = self.find(self.management_server,
                               '/software/images', 'vm-image')
        for image_url in image_urls:
            ref_image_name = self.get_props_from_url(
                self.management_server, image_url, 'name')
            if ref_image_name == image_name:
                image_file = \
                    self.get_props_from_url(self.management_server,
                                            image_url,
                                            'source_uri').rsplit('/')[-1]
                break
        path_to_node_image_file = test_constants.LIBVIRT_IMAGE_DIR + '/' + \
                                  image_file
        return path_to_node_image_file

    def _get_contracted_node(self):
        """
        Get the hostname of the contracted node
        :return: The hostname of the contracted node
        """
        data = \
            libvirt_test_data.UPDATED4_SERVICE_GROUP_2_DATA["CLUSTER_SERVICE"]
        return self.get_props_from_url(self.management_server,
                                       '{0}/nodes/{1}'.
                                       format(self.
                                              vcs_cluster_url,
                                              data["inactive_nodes"].
                                              partition(',')[0]),
                                       'hostname')

    def _get_non_contracted_node(self):
        """
        Get the hostname of the active node
        :return: The hostname of the active node
        """
        data = \
            libvirt_test_data.UPDATED4_SERVICE_GROUP_2_DATA["CLUSTER_SERVICE"]
        return self.get_props_from_url(self.management_server,
                                       '{0}/nodes/{1}'.
                                       format(self.vcs_cluster_url,
                                              data["node_list"].
                                              partition(',')[0]),
                                       'hostname')
