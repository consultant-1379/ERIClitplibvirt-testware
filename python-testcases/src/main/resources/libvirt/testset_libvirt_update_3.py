"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Nov 2015
@author:    John Dolan
@summary:   Testset to deploy libvirt vcs functionality
"""

from litp_generic_test import attr
from testset_libvirt_initial_setup import LibvirtGenericTest
import os
import test_constants
import libvirt_test_data


class Libvirtupdate3(LibvirtGenericTest):
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
        super(Libvirtupdate3, self).setUp()

        self.model = self.get_model_names_and_urls()
        self.management_server = self.model["ms"][0]["name"]

        # Location where the rpms to be installed are stored
        self.rpm_src_dir = \
            os.path.dirname(os.path.realpath(__file__)) + "/rpms"

        self.libvirt_info = self.get_litp_model_information()
        self.vm_ip = self.get_ip_for_vms(self.management_server)
        self.ms_hostname = self.get_node_att(self.management_server,
                                             "hostname")

        # LITPCDS-7848 setup
        self.clus_srvs = self.libvirt_info["libvirt"]["cluster_services_path"]
        self.vm_service_urls = self.find(self.management_server,
                                         self.clus_srvs, "vm-service")

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Results:
            The super class prints out diagnostics and variables
        """
        super(Libvirtupdate3, self).tearDown()

    def copy_rpms(self):
        """
        Description:
            - LITPCDS-7186 - As a LITP User I want to define VM packages
             and repos
        """
        repo_dir = test_constants.PARENT_PKG_REPO_DIR
        repo_3pp = test_constants.PP_REPO_DIR_NAME
        repos = {
            repo_3pp: [
                "empty_rpm1.rpm",
                "empty_rpm2.rpm",
                "empty_rpm3.rpm",
                "empty_rpm4.rpm",
                "empty_rpm5.rpm",
                "empty_rpm6.rpm",
                "empty_rpm7.rpm",
                "empty_rpm8.rpm",
                "empty_rpm9.rpm"]
        }

        for repo, packages in repos.iteritems():
            # Generate a filelist from package names
            filelist = []
            for package in packages:
                filelist.append(self.get_filelist_dict(
                    '{0}/{1}'.format(self.rpm_src_dir, package), "/tmp/"))

            # Copy rpms to ms
            self.copy_filelist_to(
                self.management_server,
                filelist,
                add_to_cleanup=False,
                root_copy=True)

            # Use LITP import to add to repo for each RPM
            for package in packages:
                self.execute_cli_import_cmd(
                    self.management_server,
                    '/tmp/{0}'.format(package),
                    repo_dir + repo)

    @attr('all', 'non-revert', 'story7188_tc_09', "LITPCDS-7188")
    def test_story7188_tc_09_p_deploy_pkg_repo(self):
        """
        @tms_id: litpcds_7188_tc09
        @tms_requirements_id: LITPCDS-7188

        @tms_title: Verify CS_VM1 has been updated with new repo and package
        @tms_description: Check new package and repo on CS_VM1

        @tms_test_steps:
            @step: Log onto each VM in the SGs mentioned above and ensure the
            correct packages are installed
            @result: libvirt_repo2, and empty_testrepo2 package is installed
             on CS_VM1

        @tms_test_precondition:
            - testset_libvirt_initial_setup, testset_libvirt_update_1,
              testset_libvirt_update_2, testset_libvirt_update_3 has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """

        # Values for cli:
        updates = {
            'repo': {
                'name': 'libvirt_repo2',
                'base_url': 'http://%s/libvirt_repo2' % self.ms_hostname},
            'package': {
                'name': 'empty_testrepo2_rpm1',
            }
        }
        # Validate the updates have suceeded.
        for ipaddress in self.vm_ip['CS_VM1']:
            node_name = "{0}-node".format('CS_VM1')
            self.add_vm_to_nodelist(node_name, ipaddress,
                                username=test_constants.LIBVIRT_VM_USERNAME,
                                password=test_constants.LIBVIRT_VM_PASSWORD)
            self.wait_for_node_up(node_name)
            self.assertTrue(
                self.check_repos_on_node(
                    node_name, [updates['repo']['name']], su_root=False))
            self.assertTrue(
                self.check_pkgs_installed(
                    node_name, [updates['package']['name']], su_root=False))

    @attr('all', 'non-revert', 'story7188_tc_20', "LITPCDS-7188")
    def test_story7188_tc_20_p_pkg_update(self):
        """
        @tms_id: LITPCDS_7188_tc20
        @tms_requirements_id: LITPCDS-7188

        @tms_title: Verify CS_VM1, CS_VM3 and CS_VM5 have broken inheritance
        by having a different package
        @tms_description: Check package on CS_VM1, CS_VM3, CS_VM5 after update

        @tms_test_steps:
            @step: Log onto each VM in the SGs mentioned above and ensure the
            correct packages are installed
            @result: Each VM has the correct packages installed

        @tms_test_precondition:
            - testset_libvirt_initial_setup, testset_libvirt_update_1,
              testset_libvirt_update_2, testset_libvirt_update_3 has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """

        updates = {
            'CS_VM1': {
                'item_id': 'pkg_empty_rpm1',
                'old': 'empty_rpm2',
                'new': 'empty_rpm4',
            },
            'CS_VM3': {
                'item_id': 'pkg_empty_rpm4',
                'old': 'empty_rpm6',
                'new': 'empty_rpm7',
            },
            'CS_VM5': {
                'item_id': 'empty_rpm3',
                'old': 'empty_rpm5',
                'new': 'empty_rpm8',
            },
        }

        for app_name, pkg_name in updates.items():
            for ipaddress in self.vm_ip[app_name]:
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

    def update_services(self):
        """
        Description:
            This test involves updates to all service groups.
        """
        sg1 = self.libvirt_info["libvirt"][
                                "software_services_path"] + "vm_service_1"
        sg2 = self.libvirt_info["libvirt"][
                                "software_services_path"] + "vm_service_2"
        sg3 = self.libvirt_info["libvirt"][
                                "software_services_path"] + "vm_service_3"
        sg4 = self.libvirt_info["libvirt"][
                                "software_services_path"] + "vm_service_4"
        sg5 = self.libvirt_info["libvirt"][
                                "software_services_path"] + "vm_service_5"
        sg7 = self.libvirt_info["libvirt"][
                                "software_services_path"] + "sles"

        cs_vm1 = self.libvirt_info["libvirt"][
                       "cluster_services_path"] + "/CS_VM1"
        cs_vm2 = self.libvirt_info["libvirt"][
                       "cluster_services_path"] + "/CS_VM2"
        cs_vm3 = self.libvirt_info["libvirt"][
                       "cluster_services_path"] + "/CS_VM3"
        cs_vm4 = self.libvirt_info["libvirt"][
                       "cluster_services_path"] + "/CS_VM4"
        cs_vm5 = self.libvirt_info["libvirt"][
                       "cluster_services_path"] + "/CS_VM5"
        cs1 = cs_vm1 + "/applications/vm_service_1"
        cs2 = cs_vm2 + "/applications/vm_service_2"
        cs3 = cs_vm3 + "/applications/vm_service_3"
        cs4 = cs_vm4 + "/applications/vm_service_4"
        cs5 = cs_vm5 + "/applications/vm_service_5"
        vm_image_4 = self.libvirt_info["libvirt"]["software_images_path"] + \
                     "vm_image_4"

        update3_sg1 = libvirt_test_data.UPDATE3_SERVICE_GROUP_1_DATA
        update3_sg2 = libvirt_test_data.UPDATE3_SERVICE_GROUP_2_DATA
        update3_sg3 = libvirt_test_data.UPDATE3_SERVICE_GROUP_3_DATA
        update3_sg4 = libvirt_test_data.UPDATE3_SERVICE_GROUP_4_DATA
        update3_sg5 = libvirt_test_data.UPDATE3_SERVICE_GROUP_5_DATA
        vm_images = libvirt_test_data.VM_IMAGES

        #########################
        #                       #
        #  Service Group CS_VM1 #
        #                       #
        #########################
        #Update VM Aliases
        self.execute_cli_update_cmd(self.management_server,
                                    sg1 + "/vm_aliases/db1",
                                    "alias_names='{0}'".format(
                                        update3_sg1["VM_ALIAS"]["DB1"][
                                            "alias_names"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg1 + "/vm_aliases/db2",
                                    "address='{0}'".format(
                                        update3_sg1["VM_ALIAS"]["DB2"][
                                            "address"]))
        #LITPCDS-7188 - Update VM packages
        self.execute_cli_update_cmd(self.management_server,
                                    cs1 + "/vm_packages/pkg_empty_rpm1",
                                    "name='{0}'".format(
                                        update3_sg1["VM_PACKAGE"][
                                            "PKG_EMPTY_1"]["name"]))
        #LITPCDS-12817 - Remove vm aliases
        self.execute_cli_remove_cmd(self.management_server,
                                    sg1 + "/vm_aliases/db21")

        # TORF-349676 - remove vm aliases with IPv6 address containing prefix
        self.execute_cli_remove_cmd(self.management_server,
                                    sg1 + "/vm_aliases/ipv6a")
        self.execute_cli_remove_cmd(self.management_server,
                                    sg1 + "/vm_aliases/ipv6b")

        # TORF-107476 -  Test case 11
        self.execute_cli_update_cmd(self.management_server,
                                    cs1 + "/vm_network_interfaces/net1",
                                    "ipaddresses={0}".format(
                                        update3_sg1["NETWORK_INTERFACES"][
                                            "NET1"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs1 + "/vm_network_interfaces/net20",
                                    "ipaddresses={0}".format(
                                        update3_sg1["NETWORK_INTERFACES"][
                                            "NET20"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs1 + "/vm_network_interfaces/net21",
                                    "ipaddresses={0}".format(
                                        update3_sg1["NETWORK_INTERFACES"][
                                            "NET21"]["ipaddresses"]))
        # Update cluster service
        self.execute_cli_update_cmd(self.management_server, cs_vm1,
                                    "active={0} standby={1} node_list={2}".
                                    format(update3_sg1
                                           ["CLUSTER_SERVICE"]["active"],
                                           update3_sg1["CLUSTER_SERVICE"]
                                           ["standby"],
                                           update3_sg1["CLUSTER_SERVICE"]
                                           ["node_list"]))
        self.execute_cli_remove_cmd(self.management_server, sg1 +
                                    '/vm_ram_mounts/vm_ram_mount_1')
        # TORF-180365 - Remove vm custom script
        self.execute_cli_remove_cmd(self.management_server, sg1 +
                                    '/vm_custom_script/vm_custom_script_1')

        #############################
        #                           #
        #  Service Group CS_SLES_VM #
        #                           #
        #############################
        # TORF-404805 remove zypper repo and package
        self.execute_cli_remove_cmd(self.management_server, sg7 +
                                    '/vm_packages/pkg_empty_rpm')
        self.execute_cli_remove_cmd(self.management_server, sg7 +
                                    '/vm_zypper_repos/repo_NCM')

        # TORF-422322 remove vm-firewall-rule(s) for sles v4 & v6
        for rule in libvirt_test_data.VM_FIREWALL_RULES_SLES_1:
            self.execute_cli_remove_cmd(self.management_server, sg7 +
                                    '/vm_firewall_rules/' + rule["item_name"])

        # TORF-406586 remove vm custom scripts
        self.execute_cli_remove_cmd(self.management_server, sg7 +
                                    '/vm_custom_script/vm_custom_script')

        #########################
        #                       #
        #  Service Group CS_VM2 #
        #                       #
        #########################
        # Update VM aliases
        self.execute_cli_update_cmd(self.management_server,
                                    sg2 + "/vm_aliases/db1",
                                    "alias_names='{0}' address='{1}'".format(
                                        update3_sg2["VM_ALIAS"]["DB1"][
                                            "alias_names"],
                                        update3_sg2["VM_ALIAS"]["DB1"][
                                            "address"]))

        # LITPCDS-8851 Update the number of nodes and interfaces
        # for a clustered service
        self.execute_cli_update_cmd(self.management_server,
                                    cs2 + "/vm_network_interfaces/net31",
                                    "ipaddresses={0}".format(
                                        update3_sg2["NETWORK_INTERFACE"][
                                            "NET31"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs2 + "/vm_network_interfaces/net22",
                                    "ipaddresses={0}".format(
                                        update3_sg2["NETWORK_INTERFACE"][
                                            "NET22"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs2 + "/vm_network_interfaces/net2",
                                    "ipaddresses={0}".format(
                                        update3_sg2["NETWORK_INTERFACE"][
                                            "NET2"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs2 + "/vm_network_interfaces/net3",
                                    "ipaddresses={0}".format(
                                        update3_sg2["NETWORK_INTERFACE"][
                                            "NET3"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs2 + "/vm_network_interfaces/net30",
                                    "ipaddresses={0}".format(
                                        update3_sg2["NETWORK_INTERFACE"][
                                            "NET30"]["ipaddresses"]))
        #Update cluster service
        self.execute_cli_update_cmd(self.management_server, cs_vm2,
                                "active={0} standby={1} node_list={2}".format(
                                    update3_sg2["CLUSTER_SERVICE"][
                                        "active"],
                                    update3_sg2["CLUSTER_SERVICE"][
                                        "standby"],
                                    update3_sg2["CLUSTER_SERVICE"][
                                        "node_list"]))
        #LITPCDS-12817 - Remove vm aliases
        self.execute_cli_remove_cmd(self.management_server,
                                    sg2 + "/vm_aliases/db22")
        self.execute_cli_remove_cmd(self.management_server,
                                    sg2 + "/vm_aliases/db23")
        # TORF-107476 -  Test case 9 & 18
        self.execute_cli_update_cmd(self.management_server, sg2 +
                                    "/vm_ram_mounts/vm_ram_mount_2",
                                    props="type='{0}' mount_point='{1}' "
                                    "mount_options='{2}'"
                                    .format(
                                      update3_sg2["VM_RAM_MOUNT"]["type"],
                                      update3_sg2["VM_RAM_MOUNT"]
                                      ["mount_point"],
                                      update3_sg2["VM_RAM_MOUNT"]
                                      ["mount_options"]
                                      ))

        #########################
        #                       #
        #  Service Group CS_VM3 #
        #                       #
        #########################

        # Update vm aliases
        self.execute_cli_update_cmd(self.management_server,
                                    sg3 + "/vm_aliases/db1",
                                    "alias_names='{0}'".format(
                                        update3_sg3["VM_ALIAS"]["DB1"][
                                            "alias_names"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg3 + "/vm_aliases/db2",
                                    "address='{0}'".format(
                                        update3_sg3["VM_ALIAS"]["DB2"][
                                            "address"]))
        #LITPCDS-7188 - Update vm packages
        self.execute_cli_update_cmd(self.management_server,
                                    cs3 + "/vm_packages/pkg_empty_rpm4",
                                    "name='{0}'".format(
                                        update3_sg3["VM_PACKAGE"][
                                            "PKG_EMPTY_4"]["name"]))
        #LITPCDS-7815 - Update NFS mount
        self.execute_cli_update_cmd(self.management_server,
                                sg3 + "/vm_nfs_mounts/vm_nfs_mount_16",
                                "device_path='{0}' mount_point='{1}'".format(
                                    update3_sg3["NFS_MOUNT"]["MOUNT_16"][
                                        "device_path"],
                                    update3_sg3["NFS_MOUNT"]["MOUNT_16"][
                                        "mount_point"]))
        #LITPCDS-12817 - Add back vm network interface
        net33 = update3_sg3["NETWORK_INTERFACE"]["NET33"]
        self.execute_cli_create_cmd(self.management_server,
                                sg3 + "/vm_network_interfaces/net33",
                                "vm-network-interface",
                                props="host_device='{0}' network_name='{1}' "
                                   "device_name='{2}' ipaddresses='{3}' "
                                   "ipv6addresses='{4}'".format(
                                   net33["host_device"], net33["network_name"],
                                   net33["device_name"], net33["ipaddresses"],
                                   net33["ipv6addresses"]),
                                    add_to_cleanup=False)

        #LITPCDS-13197 - Remove vm ssh key
        self.execute_cli_remove_cmd(self.management_server,
                                    sg3 + "/vm_ssh_keys/ssh_key_rsa_14")
        #LITPCDS-13197 - Remove vm package
        self.execute_cli_remove_cmd(self.management_server,
                                    sg3 + "/vm_packages/pkg_empty_rpm5")
        #LITPCDS-13197 - Remove vm nfs mount
        self.execute_cli_remove_cmd(self.management_server,
                                    sg3 + "/vm_nfs_mounts/vm_nfs_mount_18")
        #LITPCDS-13197 - Remove vm yum repo
        self.execute_cli_remove_cmd(self.management_server,
                                    sg3 + "/vm_yum_repos/repo_LITP ")
        # TORF-180365 - Remove vm custom script
        self.execute_cli_remove_cmd(self.management_server, sg3 +
                                    '/vm_custom_script/vm_custom_script_1')

        #########################
        #                       #
        #  Service Group CS_VM4 #
        #                       #
        #########################

        # Update vm aliases
        self.execute_cli_update_cmd(self.management_server,
                                    sg4 + "/vm_aliases/db25",
                                    "alias_names='{0}' address='{1}'".format(
                                        update3_sg4["VM_ALIAS"]["DB25"][
                                            "alias_names"],
                                        update3_sg4["VM_ALIAS"]["DB25"][
                                            "address"]))
        #LITPCDS-7179 - Configure network interfaces
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/net10",
                                    "ipaddresses={0}".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "NET10"]["ipaddresses"]))
        # LITPCDS-7516 Configure vm with ipv6 addresses
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/net_dhcp",
                                    "ipv6addresses='{0}'".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "DHCP"]["ipv6addresses"]))
        # LITPCDS-8968 Configure network interfaces for parallel CS
        self.execute_cli_update_cmd(self.management_server,
                                    sg4 + "/vm_network_interfaces/net_dhcp",
                                    "gateway6='{0}'".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "DHCP"]["gateway6"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/net9",
                                    "ipaddresses={0}".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "NET9"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/net8",
                                    "ipaddresses={0}".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "NET8"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/net7",
                                    "ipaddresses={0}".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "NET7"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/net25",
                                    "ipaddresses={0}".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "NET25"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/"
                                          "prefix_iface",
                                    "ipaddresses={0}".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "IF_PREFIX"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                                    cs4 + "/vm_network_interfaces/net_dhcp",
                                    "ipv6addresses='{0}'".format(
                                        update3_sg4["NETWORK_INTERFACE"][
                                            "DHCP"]["ipv6addresses"]))
        # LITPCDS-8968 Convert CS from failover to parallel
        self.execute_cli_update_cmd(self.management_server, cs_vm4,
                                    "active={0} standby={1}".format(
                                        update3_sg4["CLUSTER_SERVICE"][
                                            "active"],
                                        update3_sg4["CLUSTER_SERVICE"][
                                            "standby"]))
        # TORF-107476 - Test Case 07 - Create a tmpfs on VM4
        self.execute_cli_create_cmd(self.management_server, sg4 +
                                    "/vm_ram_mounts/vm_ram_mount_4",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    "mount_options='{2}' "
                                    .format(
                                      update3_sg4["VM_RAM_MOUNT"]["type"],
                                      update3_sg4["VM_RAM_MOUNT"]
                                      ["mount_point"],
                                      update3_sg4["VM_RAM_MOUNT"]
                                      ["mount_options"]
                                      ),
                                    add_to_cleanup=False)
        # TORF-180365 - Remove vm custom script
        self.execute_cli_remove_cmd(self.management_server, sg4 +
                                    '/vm_custom_script/vm_custom_script_1')

        #########################
        #                       #
        #  Service Group CS_VM5 #
        #                       #
        #########################

        # Update vm aliases
        self.execute_cli_update_cmd(self.management_server,
                                    sg5 + "/vm_aliases/db1",
                                    "alias_names='{0}'".format(
                                        update3_sg5["VM_ALIAS"]["DB1"][
                                            "alias_names"]))
        self.execute_cli_update_cmd(self.management_server,
                                    sg5 + "/vm_aliases/db2",
                                    "address='{0}'".format(
                                        update3_sg5["VM_ALIAS"]["DB2"][
                                            "address"]))
        # LITPCDS-7188 - Update vm packages
        self.execute_cli_update_cmd(self.management_server,
                                    cs5 + "/vm_packages/empty_rpm3",
                                    "name='{0}'".format(
                                        update3_sg5["VM_PACKAGE"]["PKG_3"][
                                            "name"]))
        # LITPCDS-7815 - Update NFS mounts
        self.execute_cli_update_cmd(self.management_server,
                                    sg5 + "/vm_nfs_mounts/vm_nfs_mount_10",
                                    "mount_options='{0}'".format(
                                        update3_sg5["NFS_MOUNT"]["MOUNT_10"][
                                            "mount_options"]))
        # LITPCDS-12817 - Remove vm-network-interfaces from software path
        self.execute_cli_remove_cmd(self.management_server,
                                sg5 + "/vm_network_interfaces/net35")
        self.execute_cli_remove_cmd(self.management_server,
                                sg5 + "/vm_network_interfaces/net36")
        self.execute_cli_remove_cmd(self.management_server,
                                sg5 + "/vm_network_interfaces/net37")
        # TORF-180365 - Remove vm custom script
        self.execute_cli_remove_cmd(self.management_server, sg5 +
                                    '/vm_custom_script/vm_custom_script_1')

        #################################
        # IMAGE update for LITPCDS-7182 #
        #################################
        # Add a new image to the litp model and switch a service to use it
        # LITPCDS-7182 - changing images on inherited service
        self.execute_cli_create_cmd(self.management_server, vm_image_4,
                                    "vm-image",
                                    "name={0} source_uri={1}".format(
                                        vm_images["VM_IMAGE4"]["image_name"],
                                        vm_images["VM_IMAGE4"]["image_url"]),
                                    add_to_cleanup=False)
        self.execute_cli_update_cmd(self.management_server, cs1,
                                    "image_name={0}".format(
                                        update3_sg1["CLUSTER_SERVICE"]
                                        ["image_name"]))
        self.execute_cli_update_cmd(self.management_server, cs3,
                                    "image_name={0}".format(
                                        update3_sg3["CLUSTER_SERVICE"][
                                            "image_name"]))
        self.execute_cli_update_cmd(self.management_server, cs5,
                                    "image_name={0}".format(
                                        update3_sg5["CLUSTER_SERVICE"][
                                            "image_name"]))
        ####################################
        # IMAGE update for TORF-113124     #
        ####################################
        # test_05_p_update_vm_image_under_deployments breaking the inheritence
        self.execute_cli_update_cmd(self.management_server, cs4,
                                    "image_name={0}".format(
                                        update3_sg4["CLUSTER_SERVICE"][
                                            "image_name"]))

    def ms_srv_update(self):
        """
        Description:
            Update the ms server as part of story LITPCDS-11405
        """
        # LITPCDS-11405 - Create path variables
        ms_vm1 = "/ms/services/MS_VM1"
        update1_ms_vm1_data = libvirt_test_data.UPDATE1_MS_VM1_DATA
        ms_vm1_data = libvirt_test_data.MS_VM1_DATA
        # LITPCDS-11405 - Update image name
        self.execute_cli_update_cmd(self.management_server, ms_vm1,
                                    "image_name={0}".format(
                                        update1_ms_vm1_data["VM_IMAGE"]))
        # LITPCDS-11405 - Update ip addresses on network interface
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_network_interfaces/net1",
                                    "ipaddresses='{0}'".
                                    format(
                                        update1_ms_vm1_data[
                                            "NETWORK_INTERFACE"]["NET1"][
                                            "ipaddresses"]))
        # LITPCDS-11405 - Update the alias names on vm alias 'db1'
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_aliases/db1",
                                    "alias_names='{0}'".
                                    format(
                                        update1_ms_vm1_data["VM_ALIAS"][
                                            "DB1"]["alias_names"]))
        # LITPCDS-11405 - Update the address for alias 'db2'
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_aliases/db2",
                                    "address='{0}'".
                                    format(
                                        update1_ms_vm1_data["VM_ALIAS"][
                                            "DB2"]["address"]))
        # LITPCDS-11405 - Update the hostnames property for the vm service
        self.execute_cli_update_cmd(self.management_server, ms_vm1,
                                    "hostnames={0}".
                                    format(
                                        update1_ms_vm1_data[
                                            "VM_SERVICE"]["hostnames"]))
        # LITPCDS-11405 - Update properties for nfs mount 'vm_nfs_mount_1'
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_nfs_mounts/vm_nfs_mount_1",
                                    "device_path='{0}' mount_point='{1}' " \
                                    "mount_options='{2}'".format(
                                        update1_ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_1"]["device_path"],
                                        update1_ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_1"]["mount_point"],
                                        update1_ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_1"][
                                            "mount_options"]))
        # LITPCDS-11405 - Update the ssh key rsa_11
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_ssh_keys/ssh_key_rsa_11",
                                    "ssh_key='{0}' ".format(
                                        update1_ms_vm1_data["SSH_KEYS"][
                                            "SSH_KEY_RSA_11"]))
        # LITPCDS-11405 - Create vm packages
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_packages/empty_testrepo1_rpm3",
                                    "vm-package", "name={0}"
                                    .format(ms_vm1_data[
                                                "VM_PACKAGE"][
                                                "EMPTY_TESTREPO1_RPM3"][
                                                "name"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_packages/empty_rpm3", "vm-package",
                                    "name={0}".format(ms_vm1_data[
                                                          "VM_PACKAGE"][
                                                          "EMPTY_RPM3"][
                                                          "name"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_packages/empty_testrepo2_rpm3",
                                    "vm-package",
                                    "name={0}".format(
                                        ms_vm1_data["VM_PACKAGE"][
                                            "EMPTY_TEST_REPO2_RPM3"][
                                            "name"]),
                                    add_to_cleanup=False)
        # LITPCDS-11405 - Create vm yum repos
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_yum_repos/libvirt_repo1_ms_srv",
                                    "vm-yum-repo",
                                    "name={0} " \
                                    "base_url={1}".
                                    format(
                                        ms_vm1_data[
                                            "YUM_REPOS"][
                                            "LIBVIRT_REPO1_MS_SRV"][
                                            "name"],
                                        ms_vm1_data[
                                            "YUM_REPOS"][
                                            "LIBVIRT_REPO1_MS_SRV"][
                                            "base_url"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_yum_repos/libvirt_repo2_ms_srv",
                                    "vm-yum-repo",
                                    "name={0} " \
                                    "base_url={1}".
                                    format(
                                        ms_vm1_data["YUM_REPOS"][
                                            "LIBVIRT_REPO2_MS_SRV"]["name"],
                                        ms_vm1_data["YUM_REPOS"][
                                            "LIBVIRT_REPO2_MS_SRV"][
                                            "base_url"]),
                                    add_to_cleanup=False)
        # LITPCDS-11405 - Update package name
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_packages/pkg_empty_rpm1",
                                    "name={0}".format(
                                        update1_ms_vm1_data["VM_PACKAGE"][
                                            "PKG_EMPTY_RPM1"]["name"]))
        #LITPCDS-12817 - Remove vm-network-interfaces
        self.execute_cli_remove_cmd(self.management_server,
                                    ms_vm1 + "/vm_network_interfaces/net2")
        self.execute_cli_remove_cmd(self.management_server,
                                    ms_vm1 + "/vm_network_interfaces/net3")

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
        TORF-113124: Test method to verify that any unused VM-Image is
        removed from /var/lib/libvirt/images directory on node
        :param img_name: name of image removed
        :param node: node to run command on
        :return: True/ False
        """
        file_contents, _, _ = \
            self.run_command(node, 'ls /var/lib/libvirt/images/ -h',
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

    def _confirm_vm_custom_script_not_ran(self, vm_hostname, vm_ip):

        """
        Description:
        TORF-180367: Test method to check vm custom scripts were not run
        and not logged in /var/log/messages file on the node.
        :param vm_hostname: hostname of the vm
        :param vm_ip: ip of the vm
        """
        self.add_vm_to_node_list(vm_hostname,
                                 username=test_constants.LIBVIRT_VM_USERNAME,
                                 password=test_constants.LIBVIRT_VM_PASSWORD,
                                 ipv4=vm_ip)
        path_to_logs = '/var/log/messages'
        # for each script in the list doing the check if it's logged
        run_cmd = 'cat {0} | grep "customscriptmanager"'.format(path_to_logs)
        output, _, _ = self.run_command(vm_hostname, run_cmd)
        self.assertEqual([], output)

    def _check_vm_custom_script(self, node):
        """
        Description:
            Confirm vm custom scripts are not present for TORF-180365.
        :return:
        """
        updated_data1 = libvirt_test_data.UPDATE3_SERVICE_GROUP_1_DATA
        hostname_vm1 = updated_data1["HOSTNAMES"]["hostnames"]
        ip_vm1 = updated_data1["NETWORK_INTERFACES"]["NET1"]["ipaddresses"].\
            split(",")[0]

        script_data1 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA["VM_CUSTOM_SCRIPT"]
        self.assertFalse(self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-1',
                                       script_data1["custom_script_names"]))
        self._confirm_vm_custom_script_not_ran(hostname_vm1, ip_vm1)

        script_data3 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_3_DATA["VM_CUSTOM_SCRIPT"]
        self.assertFalse(self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-3',
                                       script_data3["custom_script_names"]))

        script_data4 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_4_DATA["VM_CUSTOM_SCRIPT"]
        self.assertFalse(self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-4',
                                       script_data4["custom_script_names"]))

        script_data5 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_5_DATA["VM_CUSTOM_SCRIPT"]
        self.assertFalse(self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-5',
                                       script_data5["custom_script_names"]))

        data7 = libvirt_test_data.INITIAL_SERVICE_GROUP_SLES_DATA
        script_data7 = data7["VM_CUSTOM_SCRIPT"]
        self.assertFalse(self._confirm_vm_custom_script_on_node(node, 'sles',
                                        script_data7["custom_script_names"]))

    @attr('all', 'non-revert', 'libvirt_update3', "LITPCDS-8851",
          "LITPCDS-7182", "LITPCDS-7516", "TORF-107476", "TORF-180365",
          "TORF-180367", "TORF-349676")
    def test_p_libvirt_update_plan_3(self):
        """
        @tms_id: litpcds_libvirt_tc04
        @tms_requirements_id: LITPCDS-8851, LITPCDS-7182, LITPCDS-7516,
        TORF-107476, TORF-113124, TORF-180365, TORF-180367, TORF-349676

        @tms_title: Third Update for multiple cluster services running in the
        litp model
        @tms_description: Updates the following item configurations in the
            litp model
            - Update number of VMs running on a cluster(litpcds_8851)
            - Update VM-image(litpcds_7182)
            - Update network configuration(litpcds_7516)
            - Update VM-packages and Repos(litpcds_7188)
            - Update VM-RAM-Mounts on VMs(torf_107476)
            - Remove Unused files from /var/lib/libvirt/ on
              nodes(torf-113124) test_case_05 & 09
            - Remove VM-custom-script (torf_180365)
            - Remove IPv6 vm-aliases on CS_VM1

        @tms_test_steps:
            @step: Import empty_rpm packages
            @result: Empty_rpm packages are successfully imported

            @step: Update CS_VM1, VM-aliases, VM-packages, VM-image
            VM-network-interfaces
            @result: VM-aliases, VM-packages, VM-network-interfaces, VM-image
            are updated in CS_VM1

            @step: Remove VM-aliases from CS_VM1
            @result: CS_VM1 VM-aliases are removed

            @step: Expand CS_VM1 to run on two nodes
            @result: CS_VM1 is now running on two nodes

            @step: VM-RAM-Mount is removed from CS_VM1
            @result: CS_VM1s RAM-Mount is deleted

            @step: VM-CUSTOM-Script is removed from CS_VM1
            @result: CS_VM1 VM-custom-script is removed

            @step: Update CS_VM2, VM-aliases, VM-packages, VM-image
            VM-network-interfaces
            @result: VM-aliases, VM-packages, VM-network-interfaces, VM-image
            are updated in CS_VM2

            @step: Remove VM-aliases from CS_VM2
            @result: CS_VM2 VM-aliases are removed

            @step: Expand CS_VM2 to run on two nodes
            @result: CS_VM2 is now running on two nodes

            @step: VM-RAM-Mount is updated in CS_VM2
            @result: CS_VM2s RAM-Mount is updated

            @step: Update CS_VM3, VM-aliases, VM-packages, VM-NFS-Mounts
            VM-network-interfaces
            @result: VM-aliases, VM-packages, VM-image VM-network-interfaces
            are updated in CS_VM3

            @step: Create VM-Network-Interface on CS_VM3
            @result: VM-Network-Interfaces are created on CS_VM3

            @step: Remove vm ssh key from CS_VM3
            @result: vm ssh key is removed from CS_VM3

            @step: Remove vm package from CS_VM3
            @result: vm package is removed from CS_VM3

            @step: Remove vm nfs mount from CS_VM3
            @result: vm nfs mount is removed from CS_VM3

            @step: Remove vm yum repo from CS_VM3
            @result: vm yum repo is removed from CS_VM3

            @step: VM-CUSTOM-Script is removed from CS_VM3
            @result: CS_VM3 VM-custom-script is removed

            @step: Update CS_VM4, VM-aliases, VM-network-interfaces
            @result: VM-aliases, VM-network-interfaces are updated in CS_VM4

            @step: CS_VM4 is converted from a Fail over SG to a parallel SG
            @result: CS_VM4 is now a parallel SG

            @step: Create VM-RAM-Mount for CS_VM4
            @result: CS_VM4 has a VM-RAM-Mount created

            @step: VM-CUSTOM-Script is removed from CS_VM4
            @result: CS_VM4 VM-custom-script is removed

            @step: Update CS_VM5, VM-aliases, VM-packages,
            VM-network-interfaces, VM-NFS-Mounts
            @result: VM-aliases, VM-packages, VM-network-interfaces,
            VM-NFS-Mounts are updated in CS_VM5

            @step: Remove VM-Network-Interface from CS_VM5
            @result: VM-Network_interfaces are removed from CS_VM5

            @step: VM-CUSTOM-Script is removed from CS_VM5
            @result: CS_VM5 VM-custom-script is removed

            @step: Create vm-service MS_VM1 with VM-aliases, VM-packages,
            VM-image VM-network-interfaces, hostnames, nfs-mounts, VM-YUM-repo
            @result: VM-aliases, VM-packages, VM-image VM-network-interfaces,
            hostnames, nfs-mounts, VM-YUM-repos are created in MS_VM1

            @step: Update VM-Network-Interfaces and VM-Package in MS_VM1
            @result: VM-Network-Interfaces and VM-Package are updated in
            MS_VM1

            @step: Remove vm-network-interfaces on MS_VM1
            @result: VM-network-interfaces are removed successfully from
            MS_VM1

            @step: Create and run plan
            @result: Plan finishes successfully

            @step: Validate VM-RAM-Mounts are removed and created correctly
            @result: Assert True/ False on VM-RAM-Mount existing

            @step: TORF-113124 Verify unused image files are removed from
                   nodes
            @result: Unused image file VM-Image-1 is removed from nodes

            @step: TORF-108365 Verify vm custom script on CS_VM1, CS_VM3,
                   CS_VM4, CS_VM5
            @result: vm custom script was removed from CS_VM1, CS_VM3,
                     CS_VM4, CS_VM5
            @step: TORF-349676 Verify IPv6 vm-aliases are removed from
                   /etc/hosts file on CS_VM1
            @result: IPv6 vm-aliases are removed from /etc/hosts file on CS_VM1

        @tms_test_precondition:
            - testset_libvirt_initial_setup, testset_libvirt_update_1 and
              testset_libvirt_update_2 have ran
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        primary_node = self.get_managed_node_filenames()[0]
        # Setup the test case.
        self.copy_rpms()
        self.update_services()
        self.ms_srv_update()

        image_filenames = libvirt_test_data.VM_IMAGE_FILE_NAME

        # TORF-113124: test_05_p_update_vm_image_under_deployments
        # Validate Image 1 exists on peer node /var/lib/libvirt/images
        # (expected to be removed as unused after run plan)
        self.assertTrue(
            self._check_image_on_node(image_filenames["VM_IMAGE1"],
                                      primary_node))

        # TORF-113124: test_09_p_vm_image_is_removed_from_MS_VM_after_update
        # Assert VM-image 1 exists on MS_VM under /var/lib/libvirt/images
        # (expected to be removed as unused after run plan)
        self.assertTrue(
            self._check_image_on_node(image_filenames["VM_IMAGE1"],
                                      self.management_server))

        # Create and execute plan and expect it to succeed
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)
        plan_timeout_mins = 60
        self.assertTrue(self.wait_for_plan_state(
            self.management_server,
            test_constants.PLAN_COMPLETE,
            plan_timeout_mins
        ))

        # TORF-107476: Verify mounts do or do not exist
        update3_sg1 = libvirt_test_data.UPDATE3_SERVICE_GROUP_1_DATA
        update3_sg2 = libvirt_test_data.UPDATE3_SERVICE_GROUP_2_DATA
        update3_sg4 = libvirt_test_data.UPDATE3_SERVICE_GROUP_4_DATA

        self._check_mount_conf(update3_sg1["HOSTNAMES"]["hostnames"],
                               update3_sg1["NETWORK_INTERFACES"]["NET1"]
                               ["ipaddresses"].split(',')[0],
                               update3_sg1["VM_RAM_MOUNT"]["type"],
                               update3_sg1["VM_RAM_MOUNT"]["mount_point"])

        self._check_mount_conf(update3_sg2["HOSTNAMES"]["hostnames"],
                               update3_sg2["NETWORK_INTERFACE"]["NET2"]
                               ["ipaddresses"].split(',')[0],
                               update3_sg2["VM_RAM_MOUNT"]["type"],
                               update3_sg2["VM_RAM_MOUNT"]["mount_point"])

        self._check_mount_conf(update3_sg4["HOSTNAMES"]["hostnames"],
                               update3_sg4["NETWORK_INTERFACE"]["NET7"]
                               ["ipaddresses"].split(',')[0],
                               update3_sg4["VM_RAM_MOUNT"]["type"],
                               update3_sg4["VM_RAM_MOUNT"]["mount_point"])

        # TORF - 180365 Test case 06 verification of vm custom scripts removal
        self._check_vm_custom_script(primary_node)

        # TORF-113124: test_09_p_vm_image_is_removed_from_MS_VM_after_update
        # Verify unused vm-image-1 is removed from /var/lib/libvirt/images
        # directory on the MS
        self.assertFalse(
            self._check_image_on_node(image_filenames["VM_IMAGE1"],
                                      self.management_server))

        # TORF-113124: test_05_p_update_vm_image_under_deployments
        # Verify unused vm-image-1 is removed from /var/lib/libvirt/images
        # directory on the peer node
        self.assertFalse(
            self._check_image_on_node(image_filenames["VM_IMAGE1"],
                                      primary_node))

        # TORF-349676 check /etc/hosts file for removal of the vm aliases
        # with IPv6 address
        update2_sg1 = libvirt_test_data.UPDATED_SERVICE_GROUP_1_DATA
        vm_aliases = ["IPV6a", "IPV6b"]
        for vm_alias in vm_aliases:
            self.check_host_file_on_vm(
                "test-vm-service-1",
                update2_sg1["NETWORK_INTERFACES"]["NET1"]["ipaddresses"],
                update2_sg1["VM_ALIAS"][vm_alias]["alias_names"],
                update2_sg1["VM_ALIAS"][vm_alias]["address"],
                "0")
