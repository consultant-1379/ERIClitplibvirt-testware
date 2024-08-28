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
from lxml import etree

from redhat_cmd_utils import RHCmdUtils
from libvirt_utils import LibvirtUtils
from litp_generic_test import GenericTest, attr
import os
import test_constants
import libvirt_test_data


class LibvirtGenericTest(GenericTest):
    """
    Description:
        Common assert methods shared between testcases verifying the libvirt
        vcpu cpuset attributes
    """
    def assert_domain_vcpuset(self, model_nodes, service_name, node_list,
                              expected_cpuset, standby=0,
                              vcs_name=None):
        """
        Description:
            Assert the libvirt vcpu element has the correct cpuset attribute
            value
        :param model_nodes: List of nodes in the model.
        :type model_nodes: list
        :param service_name: The name of the VM service to check.
        :type service_name: str
        :param node_list: The nodes the VM is running on.
        :type node_list: str[]
        :param expected_cpuset: The expected cpuset value.
        :type expected_cpuset: str|None
        :param standby: Number of standby instances that may be OFFLINE
        :type standby: int
        :param vcs_name: The VCS service group name to check for ONLINE
            instances
        :type vcs_name: str
        """
        idaliases = {}
        for mnode in model_nodes:
            idaliases[mnode['url'].split('/')[-1]] = mnode['name']

        if standby != 0:
            # Get the active node
            cluster_node = idaliases[node_list[0]]
            hagrp = '{0} {1}'.format(self.vcs.get_hagrp_state_cmd(), vcs_name)
            hagrp += ' | {0} "|ONLINE|"'.format(self.rhc.grep_path)
            hagrp_output, stderr, exit_code = self.run_command(
                    cluster_node, hagrp, su_root=True)

            self.assertEqual(0, exit_code)
            self.assertEqual([], stderr)
            self.assertNotEquals([], hagrp_output,
                                 'There were no ONLINE instances of {0} '
                                 'found on nodes {1}'.format(vcs_name,
                                                             node_list))

            reverse_aliases = dict((v, k) for k, v in idaliases.iteritems())
            sys_col_index = 2
            online_host = hagrp_output[0].split()[sys_col_index]
            node_list = [reverse_aliases[online_host]]

        command = LibvirtUtils.get_virsh_dumpxml_cmd(service_name)
        for nodeid in node_list:
            self.log('info', 'Getting vcpu cpuset for "{0}" on "{1}"'.format(
                    service_name, idaliases[nodeid]))
            stdout, stderr, exit_code = self.run_command(
                    idaliases[nodeid], command, su_root=True)
            self.assertEqual(0, exit_code)
            self.assertEqual([], stderr)

            root = etree.fromstring(''.join(stdout))
            actual_vcpu = root.xpath('/domain/vcpu')[0].get('cpuset')
            self.assertEqual(expected_cpuset, actual_vcpu)

    def assert_vm_cpu_affinity(self, model_nodes, service_name, node_list,
                               expected_affinity):
        """
        Description:
            Assert the CPU affinity of a VM running on a node with what is
            expected.
        :param model_nodes: List of nodes in the model.
        :type model_nodes: list
        :param service_name: The name of the VM service to check.
        :type service_name: str
        :param node_list: The nodes the VM is running on.
        :type node_list: str[]
        :param expected_affinity: The expected CPU affinity.
        :type expected_affinity: str
        """
        self.log('info', 'Asserting cpu affinity for {0}'.format(service_name))
        command = LibvirtUtils.get_virsh_vcpuinfo_cmd(service_name)
        idaliases = {}
        for mnode in model_nodes:
            idaliases[mnode['url'].split('/')[-1]] = mnode['name']

        for nodeid in node_list:
            self.log('info', 'Getting affinity for "{0}" on "{1}"'.format(
                    service_name, idaliases[nodeid]))
            stdout, stderr, exit_code = self.run_command(
                    idaliases[nodeid], command, su_root=True)
            self.assertEqual(0, exit_code)
            self.assertEqual([], stderr)
            actual_affinity = None
            for _line in stdout:
                if _line.startswith('CPU Affinity:'):
                    actual_affinity = _line.replace('CPU Affinity:',
                                                    '').strip()
                    break
            self.assertTrue(actual_affinity is not None)
            self.assertEqual(expected_affinity, actual_affinity)

    def confirm_vm_config_files_on_node(self, node, service_name):
        """
        Description:
            Assert that meta-data and network-config files are both present
            in a vm instance data directory on the node
        :param node: (str) node on which to run the check
        :param service_name: (str) name of a vm-service instance that
                             contains the config files
        """
        files_to_check = ['meta-data', 'network-config']
        for cfg_file in files_to_check:
            cfg_file_path = "{0}/{1}/{2}".format(
                test_constants.LIBVIRT_INSTANCES_DIR, service_name, cfg_file)
            self.assertTrue(self.remote_path_exists(node, cfg_file_path),
                            "Remote path '{0}' does not exist on {1}".
                            format(cfg_file_path, node))

    def check_host_file_on_vm(self, vm_hostname, vm_ip_address, alias_name,
                              alias_ip_address, expected_value):
        """
        Description:
             Checks the /etc/hosts file(s) for a specified alias IP and
             alias name on the specified VM.
        Args:
            vm_hostname (str): The hostname of the VM where check is run
            vm_ip_address (str): The IP address of the VM where check is run
            alias_ip_address (str): The IP address of the alias to check for
                                    in the file
            alias_name (str): The name of the alias to search for in the file
            expected_value (str): The expected number of times the IP
                                  is matched in the file
        """
        self.add_vm_to_nodelist(
            vm_hostname,
            vm_ip_address,
            username=test_constants.LIBVIRT_VM_USERNAME,
            password=test_constants.LIBVIRT_VM_PASSWORD)

        cat_hosts_ipv6_alias_cmd = "{0} {1} {2} | {3} '{{print $1}}'". \
            format(test_constants.GREP_PATH, alias_name,
                   test_constants.ETC_HOSTS,
                   test_constants.AWK_PATH)

        alias_ip_address = alias_ip_address.split("/")[0]
        cat_hosts_alias_count_cmd = "{0} {1} {2} | wc -l".format(
                test_constants.GREP_PATH, alias_ip_address,
                test_constants.ETC_HOSTS)

        ipaddress = self.run_command(vm_hostname, cat_hosts_ipv6_alias_cmd,
                                     test_constants.LIBVIRT_VM_USERNAME,
                                     test_constants.LIBVIRT_VM_PASSWORD,
                                     default_asserts=True)[0]
        count = self.run_command(vm_hostname, cat_hosts_alias_count_cmd,
                                 test_constants.LIBVIRT_VM_USERNAME,
                                 test_constants.LIBVIRT_VM_PASSWORD,
                                 default_asserts=True)[0]
        self.assertEqual(expected_value, count[0])

        if expected_value != "0":
            self.assertEqual(alias_ip_address, ipaddress[0], "Expected IP "
                                "address is not the same as actual IP address")


class Libvirtsetup(LibvirtGenericTest):
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
        super(Libvirtsetup, self).setUp()

        self.model = self.get_litp_model_information()
        self.management_server = self.model["ms"][0]["name"]

        # Location where the rpms to be installed are stored
        self.rpm_src_dir = \
            os.path.dirname(os.path.realpath(__file__)) + "/rpms"

        # Location where the VM SSH KEYS to be used are stored
        self.keys_src_dir = \
            os.path.dirname(os.path.realpath(__file__)) + "/vm_ssh_keys"

        # Location where the VM CUSTOM SCRIPTS to be used are stored
        self.scripts_src_dir = \
            os.path.dirname(os.path.realpath(__file__)) + "/vm_scripts"

        self.libvirt_info = self.model["libvirt"]
        self.rhc = RHCmdUtils()

        #update startup retry limit
        try:
            self.execute_cli_update_cmd(self.management_server,
            "/deployments/d1/clusters/c1/services/httpd/ha_configs/conf1",
            "startup_retry_limit=10")
        except Exception as exception:
            print "Model change unneeded in expansion test. " + \
                  "Error: '{0}'".format(exception.message)

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Results:
            The super class prints out diagnostics and variables
        """
        super(Libvirtsetup, self).tearDown()

    def copy_ssh_keys(self):
        """
        Description:
            Copy all ssh files found in the keys directory on to the ssh
            directory on the MS.
        """
        ssh_dir_root = test_constants.SSH_KEYS_FOLDER
        ## list of files
        ssh_files = []
        for index in range(1, 22):
            ssh_files.append("ssh_key_rsa_{0}".format(str(index)))
            ssh_files.append("ssh_key_rsa_{0}.pub".format(str(index)))

        filelist = []
        for ssh_file in ssh_files:
            filelist.append(self.get_filelist_dict(
                "{0}/{1}".format(self.keys_src_dir, ssh_file),
                ssh_dir_root
            ))
        self.copy_filelist_to(self.management_server,
                              filelist,
                              root_copy=False,
                              add_to_cleanup=False,
                              file_permissions=0600)

    def copy_vm_scripts(self):
        """
        Description:
            Copy all vm script files found in the vm_scripts directory on to
            the /var/www/html/vm_scripts directory on the MS.
        """
        vm_script_dir_root = "/var/www/html/vm_scripts/"
        ## list of files
        csfname_files = []
        for index in range(1, 8):
            csfname_files.append("csfname{0}.sh".format(str(index)))

        filelist = []
        for csfname_file in csfname_files:
            filelist.append(self.get_filelist_dict(
                "{0}/{1}".format(self.scripts_src_dir, csfname_file),
                vm_script_dir_root
            ))

        self.copy_filelist_to(self.management_server,
                              filelist,
                              root_copy=True,
                              add_to_cleanup=False,
                              file_permissions=0644)

    def setup_routing(self):
        """
        Description:
            Set up ebtables and routing for the test.
        # """
        # Setup the test case.
        nodes = self.model['nodes']
        for node in nodes:
            print "node: ", node['name']
            self.run_command(node['name'],
                             "/usr/bin/yum install -y ebtables", su_root=True)
            self.run_command(node['name'],
                         "/sbin/ebtables -t nat -A PREROUTING -s "
                         "52:54:00:00:00:00/ff:ff:ff:00:00:00 -i eth0 -j DROP",
                         su_root=True)
            self.run_command(node['name'],
                         "/sbin/ebtables -t nat -A PREROUTING -s "
                         "52:54:00:00:00:00/ff:ff:ff:00:00:00 -i eth6 -j DROP",
                         su_root=True)
            self.run_command(node['name'],
                         "/sbin/ebtables -t nat -A PREROUTING -s "
                         "AA:BB:CC:00:00:00/ff:ff:ff:00:00:00 -i eth0 -j DROP",
                         su_root=True)
            self.run_command(node['name'],
                         "/sbin/ebtables -t nat -A PREROUTING -s "
                         "AA:BB:CC:00:00:00/ff:ff:ff:00:00:00 -i eth6 -j DROP",
                         su_root=True)
            self.run_command(node['name'],
                         "/sbin/service ebtables save",
                         su_root=True)
            self.run_command(node['name'],
                         "/bin/systemctl enable ebtables.service",
                         su_root=True)

    def copy_rpms(self):
        """
        LITPCDS-7186 - As a LITP User I want to define packages and repos
                        for my VM service.
                    -Copy the rpms to the MS and install them to the default
                    repo
        """
        repo_dir = test_constants.PARENT_PKG_REPO_DIR
        repo_3pp = test_constants.PP_REPO_DIR_NAME
        repo_ncm = "ncm"
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
                "empty_rpm9.rpm"],
            repo_ncm: ["empty_rpm9.rpm"]
        }

        #  create ncm dir under repo dir
        self.create_dir_on_node(self.management_server, repo_dir + repo_ncm,
                                su_root=True, add_to_cleanup=False)

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

    def setup_sfs_mounts(self):
        """
        Description:
            Create SFS mounts
        Actions:
            1. Create SFS filesystems and export them
        """
        fs_path = self.libvirt_info["filesystems_path"]
        self.execute_cli_create_cmd(self.management_server,
                                    fs_path + "/fs1",
                                    "sfs-filesystem",
                                    props='path={0} size={1}'.format(
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS1"]["fs_path"],
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS1"]["fs_size"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    fs_path + "/fs2",
                                    "sfs-filesystem",
                                    props='path={0} size={1}'.format(
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS2"]["fs_path"],
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS2"]["fs_size"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    fs_path + "/fs3",
                                    "sfs-filesystem",
                                    props='path={0} size={1}'.format(
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS3"]["fs_path"],
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS3"]["fs_size"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    fs_path + "/fs4",
                                    "sfs-filesystem",
                                    props='path={0} size={1}'.format(
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS4"]["fs_path"],
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS4"]["fs_size"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    fs_path + "/fs5",
                                    "sfs-filesystem",
                                    props='path={0} size={1}'.format(
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS5"]["fs_path"],
                                        libvirt_test_data.FILESYSTEM_DATA[
                                            "FS5"]["fs_size"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            fs_path + "/fs1/exports/mount_1",
                            "sfs-export",
                            props="ipv4allowed_clients={0} options={1}".format(
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS1"]["allowed_clients"],
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS1"]["mount_option"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            fs_path + "/fs2/exports/mount_2",
                            "sfs-export",
                            props="ipv4allowed_clients={0} options={1}".format(
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS2"]["allowed_clients"],
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS2"]["mount_option"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            fs_path + "/fs3/exports/mount_3",
                            "sfs-export",
                            props="ipv4allowed_clients={0} options={1}".format(
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS3"]["allowed_clients"],
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS3"]["mount_option"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            fs_path + "/fs4/exports/mount_4",
                            "sfs-export",
                            props="ipv4allowed_clients={0} options={1}".format(
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS4"]["allowed_clients"],
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS4"]["mount_option"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            fs_path + "/fs5/exports/mount_5",
                            "sfs-export",
                            props="ipv4allowed_clients={0} options={1}".format(
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS5"]["allowed_clients"],
                                libvirt_test_data.FILESYSTEM_DATA[
                                    "FS5"]["mount_option"]),
                                    add_to_cleanup=False)

    def add_service_groups(self):
        """
        # description: Add five service groups.
        """
        # Variables for the model paths
        vm_image_1_path = self.libvirt_info[
                              "software_images_path"] + "vm_image_1"
        vm_image_2_path = self.libvirt_info[
                              "software_images_path"] + "vm_image_2"
        vm_image_3_path = self.libvirt_info[
                              "software_images_path"] + "vm_image_3"
        vm_sles_image_path = self.libvirt_info[
                              "software_images_path"] + "vm_image_sles"

        lvtd_vm1 = libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA
        sg1_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_VM1"
        vm_service_1_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_1"

        sles_vm = libvirt_test_data.INITIAL_SERVICE_GROUP_SLES_DATA
        sles_sg_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_SLES_VM"
        vm_service_sles_path = self.libvirt_info[
                                "software_services_path"] + "sles"

        ##########################
        #                        #
        #  Service Group SLES_VM #
        #                        #
        ##########################
        # description: Create vm image sles in the model
        # test_steps:
        #   step: Create vm image sles in the model
        #   result: vm image sles is created in the litp model
        self.execute_cli_create_cmd(self.management_server, vm_sles_image_path,
                                "vm-image",
                                props="source_uri='{0}' name='{1}' ".format(
                                    libvirt_test_data.VM_IMAGES[
                                        "VM_IMAGE_SLES"]["image_url"],
                                    libvirt_test_data.VM_IMAGES[
                                        "VM_IMAGE_SLES"]["image_name"]),
                                    add_to_cleanup=False)

        # description: Create a vm service
        # test_steps:
        #   step: Create a vm service under /software
        #   result: vm service is created in the model
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_sles_path, "vm-service",
                            props="cpus={0} service_name={1} ram={2} "
                                  "image_name={3} hostnames={4} "
                                  "internal_status_check={5}".format(
                            sles_vm["VM_SERVICE"]["cpus"],
                            sles_vm["VM_SERVICE"]["service_name"],
                            sles_vm["VM_SERVICE"]["ram"],
                            sles_vm["VM_SERVICE"]["image_name"],
                            sles_vm["VM_SERVICE"]["hostnames"],
                            sles_vm["VM_SERVICE"]["internal_status_check"]),
                                    add_to_cleanup=False)

        # description: Create a vcs clustered service
        # test_steps:
        #   step: Create a vcs clustered service in the model CS_SLES_VM
        #   result: CS_SLES_VM is created in model
        self.execute_cli_create_cmd(self.management_server, sles_sg_path,
                        "vcs-clustered-service",
                        props="active={0} standby={1} name={2} " \
                              "online_timeout={3} dependency_list='{4}' " \
                              "node_list={5}".format(
                            sles_vm["CLUSTER_SERVICE"]["active"],
                            sles_vm["CLUSTER_SERVICE"]["standby"],
                            sles_vm["CLUSTER_SERVICE"]["name"],
                            sles_vm["CLUSTER_SERVICE"][
                                "online_timeout"],
                            sles_vm["CLUSTER_SERVICE"][
                                "dependency_list"],
                            sles_vm["CLUSTER_SERVICE"][
                                "node_list"]), add_to_cleanup=False)

        # description: Create a ha config
        # test_steps:
        #   step: Create a ha-service-config in the model CS_SLES_VM
        #   result: ha-service-config is created for CS_SLES_VM
        self.execute_cli_create_cmd(self.management_server, sles_sg_path +
                                    "/ha_configs/service_config",
                                    "ha-service-config",
                                    props="status_timeout={0}".format(
                                    sles_vm["HA_CONFIG"]["status_timeout"]),
                                    add_to_cleanup=False)

        # description:  Add the service group to a vcs cluster
        # test_steps:
        #   step: Add service group to CS_SLES_VM
        #   result: Service group is inherited onto CS_SLES_VM
        self.execute_cli_inherit_cmd(self.management_server,
                                sles_sg_path + "/applications/sles",
                                vm_service_sles_path, add_to_cleanup=False)

        # description: Configure vm aliases
        # test_steps:
        #   step: Configure VM aliases for CS_SLES_VM
        #   result: VM aliases are added to CS_SLES_VM
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_sles_path + "/vm_aliases/ms",
                                "vm-alias",
                                props="alias_names='{0}' address='{1}'".format(
                                    sles_vm["VM_ALIAS"]["MS1"][
                                        "alias_names"],
                                    sles_vm["VM_ALIAS"]["MS1"][
                                        "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_sles_path + "/vm_aliases/ncm",
                                "vm-alias",
                                props="alias_names='{0}' address='{1}'".format(
                                    sles_vm["VM_ALIAS"]["NCM"][
                                        "alias_names"],
                                    sles_vm["VM_ALIAS"]["NCM"][
                                        "address"]), add_to_cleanup=False)

        # description: Configure network interfaces
        # test_steps:
        #   step: Configure VM-network-interfaces for CS_SLES_VM
        #   result: VM-network-interfaces are added to CS_SLES_VM
        sles_vm_net1 = sles_vm["NETWORK_INTERFACES"]["NET1"]
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_sles_path +
                            "/vm_network_interfaces/net1",
                            "vm-network-interface",
                            props="host_device='{0}' device_name='{1}' "
                                  "ipaddresses='{2}' gateway='{3}' "
                                  "network_name='{4}'".format(
                            sles_vm_net1["host_device"],
                            sles_vm_net1["device_name"],
                            sles_vm_net1["ipaddresses"],
                            sles_vm_net1["gateway"],
                            sles_vm_net1["network_name"]),
                            add_to_cleanup=False)

        # TORF-404805
        # description: Configure zypper repos
        # test_steps:
        #   step: Create a zyppe repo for CS_SLES_VM
        #   result: Zypper repo is created for CS_SLES_VM
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_sles_path + "/vm_zypper_repos/repo_NCM",
                            "vm-zypper-repo",
                            props="name='{0}' base_url='{1}'".format(
                                    sles_vm["ZYPPER_REPOS"]["NCM"]["name"],
                                    sles_vm["ZYPPER_REPOS"]["NCM"][
                                        "base_url"]), add_to_cleanup=False)

        # description: Configure vm packages
        # test_steps:
        #   step: Configure vm packages for CS_SLES_VM
        #   result: VM packages are configured for CS_SLES_VM
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_sles_path +
                                    "/vm_packages/pkg_empty_rpm",
                                    "vm-package", props="name='{0}'".format(
                sles_vm["PACKAGES"]["PKG1"]["name"]), add_to_cleanup=False)

        # description: Configure ssh keys
        # test_steps:
        #   step: Configure ssh keys for CS_SLES_VM
        #   result: ssh keys are created for CS_SLES_VM
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_sles_path +
                                    "/vm_ssh_keys/ssh_key_rsa_21",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                sles_vm["SSH_KEYS"]["KEY21"]["ssh_key"]), add_to_cleanup=False)

        # TORF-406586
        # description: Configure custom scripts
        # test_steps:
        #   step: Configure custom scripts for CS_SLES_VM
        #   result: Custom scripts are created for CS_SLES_VM
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_sles_path +
                                "/vm_custom_script/vm_custom_script",
                                "vm-custom-script",
                                props="custom_script_names='{0}'".format(
                        sles_vm["VM_CUSTOM_SCRIPT"]["custom_script_names"]),
                                    add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM1 #
        #                       #
        #########################

        # id: litpcds-7182
        # description: Create vm image 1 in the model
        # test_steps:
        #   step: Create vm image 1 in the model
        #   result: vm image 1 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, vm_image_1_path,
                                    "vm-image",
                                    props="source_uri={0} name={1}".format(
                                        lvtd_vm1["VM IMAGE"]["image_url"],
                                        lvtd_vm1["VM IMAGE"]["image_name"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create a vm service
        # test_steps:
        #   step: Create a vm service
        #   result: vm service is created in the model
        self.execute_cli_create_cmd(self.management_server, vm_service_1_path,
                                    "vm-service",
                                    props="cpus={0} service_name={1} ram={2}" \
                                          " cleanup_command='{3}' " \
                                          "image_name={4} hostnames={5} " \
                                          "internal_status_check={6}".format(
                                        lvtd_vm1["VM_SERVICE"]["cpus"],
                                        lvtd_vm1["VM_SERVICE"]["service_name"],
                                        lvtd_vm1["VM_SERVICE"]["ram"],
                                        lvtd_vm1["VM_SERVICE"][
                                            "cleanup_command"],
                                        lvtd_vm1["VM_SERVICE"]["image_name"],
                                        lvtd_vm1["VM_SERVICE"]["hostnames"],
                                        lvtd_vm1["VM_SERVICE"][
                                            "internal_status_check"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create a vcs clustered service
        # test_steps:
        #   step: Create a vcs clustered service in the model CS_VM1
        #   result: CS_VM1 is created in model
        self.execute_cli_create_cmd(self.management_server, sg1_path,
                                    "vcs-clustered-service",
                                    props="active={0} standby={1} name={2} " \
                                          "online_timeout={3} dependency_list="
                                          "'{4}' node_list={5}".format(
                                        lvtd_vm1["CLUSTER_SERVICE"]["active"],
                                        lvtd_vm1["CLUSTER_SERVICE"]["standby"],
                                        lvtd_vm1["CLUSTER_SERVICE"]["name"],
                                        lvtd_vm1["CLUSTER_SERVICE"][
                                            "online_timeout"],
                                        lvtd_vm1["CLUSTER_SERVICE"][
                                            "dependency_list"],
                                        lvtd_vm1["CLUSTER_SERVICE"][
                                            "node_list"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create a ha config
        # test_steps:
        #   step: Create a ha-service-config in the model CS_VM1
        #   result: ha-service-config is created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                    sg1_path + "/ha_configs/service_config",
                                    "ha-service-config",
                                    props="restart_limit={0} "
                                          "status_timeout={1}".format(
                                        lvtd_vm1["HA_CONFIG"]["restart_limit"],
                                        lvtd_vm1["HA_CONFIG"][
                                            "status_timeout"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description:  Add the service group to a vcs cluster
        # test_steps:
        #   step: Add service group to CS_VM1
        #   result: Service group is inherited onto CS_VM1
        self.execute_cli_inherit_cmd(self.management_server,
                                     sg1_path + "/applications/vm_service_1",
                                     vm_service_1_path, add_to_cleanup=False)

        # id: litpcds-7184
        # description: Configure vm aliases
        # test_steps:
        #   step: Configure VM aliases for CS_VM1
        #   result: VM aliases are added to CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/ms",
                                    "vm-alias",
                                    props="alias_names='{0}' address='{1}'"
                                    .format(lvtd_vm1["VM_ALIAS"]["MS1"][
                                            "alias_names"],
                                        lvtd_vm1["VM_ALIAS"]["MS1"][
                                            "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/db1",
                                    "vm-alias",
                                    props="alias_names='{0}' address='{1}'"
                                    .format(lvtd_vm1["VM_ALIAS"]["DB1"][
                                            "alias_names"],
                                        lvtd_vm1["VM_ALIAS"]["DB1"][
                                            "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/db2",
                                    "vm-alias",
                                    props="alias_names='{0}' address='{1}'"
                                    .format(lvtd_vm1["VM_ALIAS"]["DB2"][
                                            "alias_names"],
                                        lvtd_vm1["VM_ALIAS"]["DB2"][
                                            "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/sfs",
                                    "vm-alias",
                                    props="alias_names='{0}' address='{1}'"
                                    .format(lvtd_vm1["VM_ALIAS"]["SFS"][
                                            "alias_names"],
                                        lvtd_vm1["VM_ALIAS"]["SFS"][
                                            "address"]), add_to_cleanup=False)

        # id: litpcds-7179
        # description: Configure network interfaces
        # test_steps:
        #   step: Configure VM-network-interfaces for CS_VM1
        #   result: VM-network-interfaces are added to CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_network_interfaces/net1",
                                    "vm-network-interface",
                                props="host_device='{0}' network_name='{1}' " \
                                          "device_name='{2}'".format(
                                        lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                            "host_device"],
                                        lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                            "network_name"],
                                        lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                            "device_name"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_network_interfaces/net_dhcp",
                                    "vm-network-interface",
                                props="host_device='{0}' network_name='{1}' " \
                                          "device_name='{2}'".format(
                                        lvtd_vm1["NETWORK_INTERFACES"][
                                            "NET_DHCP"]["host_device"],
                                        lvtd_vm1["NETWORK_INTERFACES"][
                                            "NET_DHCP"]["network_name"],
                                        lvtd_vm1["NETWORK_INTERFACES"][
                                            "NET_DHCP"]["device_name"]),
                                    add_to_cleanup=False)

        self.execute_cli_update_cmd(self.management_server,
                                    sg1_path +
                "/applications/vm_service_1/vm_network_interfaces/net1",
                                    props="ipaddresses={0}".format(
                                        lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                            "ipaddresses"]))

        self.execute_cli_update_cmd(self.management_server,
                                    sg1_path +
                "/applications/vm_service_1/vm_network_interfaces/net_dhcp",
                                    props="ipaddresses={0}".format(
                                        lvtd_vm1["NETWORK_INTERFACES"][
                                            "NET_DHCP"]["ipaddresses"]))

        # id: litpcds-7185
        # description: Define gateway for vm service
        # test_steps:
        #   step: Define gateway for CS_VM1
        #   result: Gateway is defined for CS_VM1
        self.execute_cli_update_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_network_interfaces/net1",
                                    props="gateway=192.168.0.1".format(
                                        lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                            "gateway"]))

        # id: litpcds-7186
        # description: Configure yum repos
        # test_steps:
        #   step: Create yum repos for CS_VM1
        #   result: Yum repos are created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_1_path + "/vm_yum_repos/repo_3PP",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'".format(
                                        lvtd_vm1["YUM_REPOS"]["3PP"]["name"],
                                        lvtd_vm1["YUM_REPOS"]["3PP"][
                                            "base_url"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_yum_repos/repo_LITP",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'".format(
                                        lvtd_vm1["YUM_REPOS"]["LITP"]["name"],
                                        lvtd_vm1["YUM_REPOS"]["LITP"][
                                            "base_url"]), add_to_cleanup=False)
        # id: litpcds-7186
        # description: Configure vm packages
        # test_steps:
        #   step: Configure vm packages for CS_VM1
        #   result: VM packages are configured for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_packages/pkg_empty_rpm1",
                                    "vm-package", props="name='{0}'".format(
                lvtd_vm1["PACKAGES"]["PKG1"]["name"]), add_to_cleanup=False)

        # id: litpcds-7815
        # description: Configure nfs mounts
        # test_steps:
        #   step: Configure nfs mounts for CS_VM1
        #   result: nfs mounts are created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_nfs_mounts/vm_nfs_mount_1",
                                    "vm-nfs-mount",
                                props="device_path='{0}' mount_point='{1}' " \
                                          "mount_options='{2}' ".format(
                                        lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT1"][
                                            "device_path"],
                                        lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT1"][
                                            "mount_point"],
                                        lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT1"][
                                            "mount_options"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_nfs_mounts/vm_nfs_mount_2",
                                    "vm-nfs-mount",
                                    props="device_path='{0}' mount_point='{1}'"
                                    .format(lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT2"]
                                            ["device_path"],
                                        lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT2"][
                                            "mount_point"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_nfs_mounts/vm_nfs_mount_3",
                                    "vm-nfs-mount",
                                    props="device_path='{0}' mount_point='{1}'"
                                    .format(lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT3"]
                                            ["device_path"],
                                        lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT3"][
                                            "mount_point"],
                                        lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT3"][
                                            "mount_options"]),
                                    add_to_cleanup=False)

        # id: litpcds-6627
        # description: Configure ssh keys
        # test_steps:
        #   step: Configure ssh keys for CS_VM1
        #   result: ssh keys are created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_ssh_keys/ssh_key_rsa_11",
                                    "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm1["SSH_KEYS"]["KEY1"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_ssh_keys/ssh_key_rsa_12",
                                    "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm1["SSH_KEYS"]["KEY2"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_ssh_keys/ssh_key_rsa_13",
                                    "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm1["SSH_KEYS"]["KEY3"]["ssh_key"]), add_to_cleanup=False)

        # id: torf-107476
        # title: test_02_p_create_vm_ram_mount_RH7_tmpfs
        # description: Test to verify that a user can create a tmpfs
        # file system using default values on RHEL 7 (Create a tmpfs on
        # my CS_VM1)
        # test_steps:
        #   step: Create VM with new vm-ram-mount item with a RHEL 7 system
        #   result: vm-ram-mount is created successfully with RHEL 7 system
        self.execute_cli_create_cmd(self.management_server, vm_service_1_path
                                    + "/vm_ram_mounts/vm_ram_mount_1",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    .format(
                                        lvtd_vm1["VM_RAM_MOUNT"]["type"],
                                        lvtd_vm1["VM_RAM_MOUNT"]
                                        ["mount_point"]),
                                    add_to_cleanup=False)

        # id: torf-180365, torf-180367
        # title: test_03_p_create_vm_scripts_runtime
        # test_04_p_scripts_execution_proper_order
        # description: Positive TC that will check that you can successfully
        # create a vm service with vm-custom-script item during runtime.
        # test_steps:
        # step: Create a VM with vm-custom-script item with
        # custom_script_names="csfname1.sh,csfname2.sh,csfname3.sh,
        # csfname4.sh,csfname7.sh"

        self.execute_cli_create_cmd(self.management_server, vm_service_1_path
                                    + "/vm_custom_script/vm_custom_script_1",
                                    "vm-custom-script",
                                    props="custom_script_names='{0}'"
                                    .format(lvtd_vm1["VM_CUSTOM_SCRIPT"]
                                            ["custom_script_names"]),
                                    add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM2 #
        #                       #
        #########################

        lvtd_vm2 = libvirt_test_data.INITIAL_SERVICE_GROUP_2_DATA
        sg2_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_VM2"
        vm_service_2_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_2"

        # id: litpcds-7182
        # description: Create vm image 2 in the model
        # test_steps:
        #   step: Create vm image 2 in the model
        #   result: vm image 2 is created in the litp model successfully
        self.execute_cli_create_cmd(self.management_server, vm_image_2_path,
                                "vm-image",
                                props="source_uri='{0}' name='{1}' ".format(
                                    libvirt_test_data.VM_IMAGES[
                                        "VM_IMAGE2"]["image_url"],
                                    libvirt_test_data.VM_IMAGES[
                                        "VM_IMAGE2"]["image_name"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create CS_VM2 vcs clustered service in litp model
        # test_steps:
        #   step: Create CS_VM2 in the model
        #   result: CS_VM2 is created in the litp model successfully
        self.execute_cli_create_cmd(self.management_server, sg2_path,
                                    "vcs-clustered-service",
                            props="active={0} standby={1} name='{2}' " \
                                  "online_timeout={3} dependency_list={4} " \
                                  "node_list='{5}' ".format(
                                lvtd_vm2["CLUSTER_SERVICE"]["active"],
                                lvtd_vm2["CLUSTER_SERVICE"]["standby"],
                                lvtd_vm2["CLUSTER_SERVICE"]["name"],
                                lvtd_vm2["CLUSTER_SERVICE"][
                                    "online_timeout"],
                                lvtd_vm2["CLUSTER_SERVICE"][
                                    "dependency_list"],
                                lvtd_vm2["CLUSTER_SERVICE"][
                                    "node_list"]), add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create vm service 2 in litp model
        # test_steps:
        #   step: Create vm-service 2 in the model
        #   result: vm-service 2 is created in the litp model successfully
        self.execute_cli_create_cmd(self.management_server, vm_service_2_path,
                            "vm-service",
                            props="cleanup_command='{0}' " \
                                  "status_command='{1}' hostnames='{2}' " \
                                  "internal_status_check='{3}' " \
                                  "start_command='{4}' service_name='{5}' " \
                                  "stop_command='{6}' ram='{7}' " \
                                  "image_name='{8}' cpus='{9}' "
                                  "cpuset={10}".format(
                                lvtd_vm2["VM_SERVICE"][
                                    "cleanup_command"],
                                lvtd_vm2["VM_SERVICE"][
                                    "status_command"],
                                lvtd_vm2["VM_SERVICE"]["hostnames"],
                                lvtd_vm2["VM_SERVICE"][
                                    "internal_status_check"],
                                lvtd_vm2["VM_SERVICE"][
                                    "start_command"],
                                lvtd_vm2["VM_SERVICE"]["service_name"],
                                lvtd_vm2["VM_SERVICE"]["stop_command"],
                                lvtd_vm2["VM_SERVICE"]["ram"],
                                lvtd_vm2["VM_SERVICE"]["image_name"],
                                lvtd_vm2["VM_SERVICE"]["cpus"],
                                lvtd_vm2["VM_SERVICE"]["cpuset"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create ha service config for CS_VM2 in litp model
        # test_steps:
        #   step: Create ha service config for CS_VM2 in litp model
        #   result: ha service config is created in the litp successfully
        self.execute_cli_create_cmd(self.management_server,
            sg2_path + "/ha_configs/service_config", "ha-service-config",
            props="restart_limit={0} status_timeout={1} ".format(
                lvtd_vm2["HA_CONFIG"]["restart_limit"],
                lvtd_vm2["HA_CONFIG"]["status_timeout"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Add service group to CS_VM2 vcs clustered service
        # test_steps:
        #   step: Inherit vm-service 2 onto CS_VM2
        #   result: vm-service 2 is inherited onto CS_VM2 clustered service
        self.execute_cli_inherit_cmd(self.management_server,
                                     sg2_path + "/applications/vm_service_2",
                                     vm_service_2_path, add_to_cleanup=False)

        # id: litpcds-7184
        # description: Configure vm aliases
        # test_steps:
        #   step: Configure vm aliases for CS_VM2
        #   result: vm aliases are created for CS_VM2 successfully
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_aliases/db1",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm2["VM_ALIAS"]["DB1"][
                                    "alias_names"],
                                lvtd_vm2["VM_ALIAS"]["DB1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_aliases/ms",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm2["VM_ALIAS"]["MS1"][
                                    "alias_names"],
                                lvtd_vm2["VM_ALIAS"]["MS1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_aliases/sfs",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm2["VM_ALIAS"]["SFS"][
                                    "alias_names"],
                                lvtd_vm2["VM_ALIAS"]["SFS"][
                                    "address"]), add_to_cleanup=False)

        # id: litpcds-7179
        # description: Configure network interfaces
        # test_steps:
        #   step: Configure network interfaces for CS_VM2
        #   result: vm aliases are created for CS_VM2 successfully
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_network_interfaces/net2",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                                    "host_device"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                                    "network_name"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_network_interfaces/net3",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                                    "host_device"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                                    "network_name"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_2_path + "/vm_network_interfaces/net_dhcp",
                        "vm-network-interface",
                        props="host_device='{0}' network_name='{1}' " \
                              "device_name='{2}'".format(
                            lvtd_vm2["NETWORK_INTERFACES"][
                                "NET_DHCP"]["host_device"],
                            lvtd_vm2["NETWORK_INTERFACES"][
                                "NET_DHCP"]["network_name"],
                            lvtd_vm2["NETWORK_INTERFACES"][
                                "NET_DHCP"]["device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_update_cmd(self.management_server,
                sg2_path +
                    "/applications/vm_service_2/vm_network_interfaces/net2",
                props="ipaddresses={0}".format(
                    lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                        "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                sg2_path +
                    "/applications/vm_service_2/vm_network_interfaces/net3",
                props="ipaddresses={0}".format(
                    lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                        "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg2_path +
                "/applications/vm_service_2/vm_network_interfaces/net_dhcp",
            props="ipaddresses={0}".format(
                lvtd_vm2["NETWORK_INTERFACES"][
                    "NET_DHCP"]["ipaddresses"]))

        # id: litpcds-7185
        # description: Configure default gateway
        # test_steps:
        #   step: Define default gateway for CS_VM2
        #   result: Default gateway is defined for CS_VM2
        self.execute_cli_update_cmd(self.management_server,
            sg2_path + "/applications/vm_service_2/vm_network_interfaces/net3",
            props="gateway={0}".format(
                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                    "gateway"]))

        # id: litpcds-7186
        # description: Configure YUM repos
        # test_steps:
        #   step: Configure yum repos for CS_VM2
        #   result: YUM repos are configured for CS_VM2
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_2_path + "/vm_yum_repos/repo_3PP",
                                "vm-yum-repo",
                                props="name='{0}' base_url='{1}'".format(
                                    lvtd_vm2["YUM_REPOS"]["3PP"]["name"],
                                    lvtd_vm2["YUM_REPOS"]["3PP"]["base_url"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_2_path + "/vm_yum_repos/repo_LITP",
                                "vm-yum-repo",
                                props="name='{0}' base_url='{1}'".format(
                                    lvtd_vm2["YUM_REPOS"]["LITP"]["name"],
                                    lvtd_vm2["YUM_REPOS"]["LITP"][
                                        "base_url"]), add_to_cleanup=False)

        # id: litpcds-7186
        # description: Configure VM packages
        # test_steps:
        #   step: Configure VM Packages for CS_VM2
        #   result: VM packages are configured for CS_VM2
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_packages/pkg_empty_rpm2",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm2["PACKAGES"]["PKG2"]["name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_packages/pkg_empty_rpm3",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm2["PACKAGES"]["PKG3"]["name"]), add_to_cleanup=False)

        # id: torf-107476
        # title: test_01_p_create_vm_ram_mount_RH6_tmpfs
        # description: Test to verify that a user can create a tmpfs
        # file system using default values on RHEL 6 (Create a tmpfs on
        # my CS_VM2)
        # test_steps:
        #   step: Create VM with new vm-ram-mount item with a RHEL 6 system
        #   result: vm-ram-mount is created successfully with RHEL 6 system
        self.execute_cli_create_cmd(self.management_server, vm_service_2_path
                                    + "/vm_ram_mounts/vm_ram_mount_2",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    "mount_options='{2}' "
                                    .format(
                                      lvtd_vm2["VM_RAM_MOUNT"]["type"],
                                      lvtd_vm2["VM_RAM_MOUNT"]
                                      ["mount_point"],
                                      lvtd_vm2["VM_RAM_MOUNT"]["mount_options"]
                                      ),
                                    add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM3 #
        #                       #
        #########################

        lvtd_vm3 = libvirt_test_data.INITIAL_SERVICE_GROUP_3_DATA
        sg3_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_VM3"
        vm_service_3_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_3"

        # id: litpcds-7182
        # description: Create vm image 3 in the litp model
        # test_steps:
        #   step: Define VM-image-3 in the litp model for CS_VM3
        #   result: VM-image-3 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, vm_image_3_path,
                                    "vm-image",
                                    props="source_uri='{0}' name='{1}'".format(
                                        lvtd_vm3["VM IMAGE"]["image_url"],
                                        lvtd_vm3["VM IMAGE"]["image_name"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create CS_VM3 vcs-clustered service
        # test_steps:
        #   step: Create CS_VM3 clustered service
        #   result: CS_VM3 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, sg3_path,
                            "vcs-clustered-service",
                            props="active={0} standby={1} name='{2}' " \
                                  "online_timeout={3} dependency_list='{4}' " \
                                  "node_list='{5}'".format(
                                lvtd_vm3["CLUSTER_SERVICE"]["active"],
                                lvtd_vm3["CLUSTER_SERVICE"]["standby"],
                                lvtd_vm3["CLUSTER_SERVICE"]["name"],
                                lvtd_vm3["CLUSTER_SERVICE"][
                                    "online_timeout"],
                                lvtd_vm3["CLUSTER_SERVICE"][
                                    "dependency_list"],
                                lvtd_vm3["CLUSTER_SERVICE"][
                                    "node_list"]), add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create vm-service-3 in the litp model
        # test_steps:
        #   step: Create vm-service-3 in the litp model
        #   result: vm-service-3 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, vm_service_3_path,
                            "vm-service",
                            props="cpus='{0}' service_name='{1}' ram='{2}' " \
                                  "cleanup_command='{3}' image_name='{4}' " \
                                  "hostnames='{5}' " \
                                  "internal_status_check='{6}' " \
                                  "cpunodebind={7}".format(
                                lvtd_vm3["VM_SERVICE"]["cpus"],
                                lvtd_vm3["VM_SERVICE"]["service_name"],
                                lvtd_vm3["VM_SERVICE"]["ram"],
                                lvtd_vm3["VM_SERVICE"][
                                    "cleanup_command"],
                                lvtd_vm3["VM_SERVICE"]["image_name"],
                                lvtd_vm3["VM_SERVICE"]["hostnames"],
                                lvtd_vm3["VM_SERVICE"][
                                    "internal_status_check"],
                                lvtd_vm3['VM_SERVICE']["cpunodebind"]),
                                    add_to_cleanup=False)
        # id: litpcds-7180
        # description: Create ha-service-config in the litp model
        # test_steps:
        #   step: Create ha-service-config in the litp model
        #   result: ha-service-config is created in the litp model
        self.execute_cli_create_cmd(self.management_server,
                                    sg3_path + "/ha_configs/service_config",
                                    "ha-service-config", add_to_cleanup=False)

        # id: litpcds-7180
        # description: Inherit vm-service-3 onto CS_VM3
        # test_steps:
        #   step: Inherit vm-service-3 onto CS_VM3
        #   result: vm-service-3 is inherited onto CS_VM3 in litp model
        self.execute_cli_inherit_cmd(self.management_server,
                                     sg3_path + "/applications/vm_service_3",
                                     vm_service_3_path, add_to_cleanup=False)

        # id: litpcds-7184
        # description: Configure VM aliases for CS_VM3
        # test_steps:
        #   step: Configure VM aliases for CS_VM3
        #   result: VM aliases are created for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_aliases/db1",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm3["VM_ALIAS"]["DB1"][
                                    "alias_names"],
                                lvtd_vm3["VM_ALIAS"]["DB1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_aliases/db2",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm3["VM_ALIAS"]["DB2"][
                                    "alias_names"],
                                lvtd_vm3["VM_ALIAS"]["DB2"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_aliases/db3",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm3["VM_ALIAS"]["DB3"][
                                    "alias_names"],
                                lvtd_vm3["VM_ALIAS"]["DB3"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_aliases/db4",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm3["VM_ALIAS"]["DB4"][
                                    "alias_names"],
                                lvtd_vm3["VM_ALIAS"]["DB4"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_aliases/ms",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm3["VM_ALIAS"]["MS1"][
                                    "alias_names"],
                                lvtd_vm3["VM_ALIAS"]["MS1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_aliases/sfs",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm3["VM_ALIAS"]["SFS"][
                                    "alias_names"],
                                lvtd_vm3["VM_ALIAS"]["SFS"][
                                    "address"]), add_to_cleanup=False)
        # id: litpcds-7179
        # description: Configure network interfaces for CS_VM3
        # test_steps:
        #   step: Configure network interfaces for CS_VM3
        #   result: network interfaces are created for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_network_interfaces/net4",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm3["NETWORK_INTERFACES"]["NET4"][
                                    "host_device"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET4"][
                                    "network_name"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET4"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_network_interfaces/net5",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm3["NETWORK_INTERFACES"]["NET5"][
                                    "host_device"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET5"][
                                    "network_name"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET5"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_network_interfaces/net6",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm3["NETWORK_INTERFACES"]["NET6"][
                                    "host_device"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET6"][
                                    "network_name"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET6"][
                                    "device_name"]), add_to_cleanup=False)

        # id: litpcds-7185
        # description: Configure default gateway CS_VM3
        # test_steps:
        #   step: Define default gateway for CS_VM3
        #   result: default gateway is created for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_3_path + "/vm_network_interfaces/net_dhcp",
                        "vm-network-interface",
                        props="host_device='{0}' network_name='{1}' " \
                              "device_name='{2}' gateway6='{3}'".format(
                            lvtd_vm3["NETWORK_INTERFACES"][
                                "NET_DHCP"]["host_device"],
                            lvtd_vm3["NETWORK_INTERFACES"][
                                "NET_DHCP"]["network_name"],
                            lvtd_vm3["NETWORK_INTERFACES"][
                                "NET_DHCP"]["device_name"],
                            lvtd_vm3["NETWORK_INTERFACES"][
                                "NET_DHCP"]["gateway6"]), add_to_cleanup=False)

        # id: litpcds-12817
        # description: Configure network interfaces for CS_VM3
        # test_steps:
        #   step: Configure network interfaces for CS_VM3
        #   result: Network interfaces are created for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_network_interfaces/net32",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm3["NETWORK_INTERFACES"]["NET32"][
                                    "host_device"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET32"][
                                    "network_name"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET32"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_network_interfaces/net33",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm3["NETWORK_INTERFACES"]["NET33"][
                                    "host_device"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET33"][
                                    "network_name"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET33"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_network_interfaces/net34",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm3["NETWORK_INTERFACES"]["NET34"][
                                    "host_device"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET34"][
                                    "network_name"],
                                lvtd_vm3["NETWORK_INTERFACES"]["NET34"][
                                    "device_name"]), add_to_cleanup=False)
        # Update vm net interfaces
        self.execute_cli_update_cmd(self.management_server,
            sg3_path + "/applications/vm_service_3/vm_network_interfaces/net4",
            props="ipaddresses={0}".format(
                lvtd_vm3["NETWORK_INTERFACES"]["NET4"][
                    "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg3_path + "/applications/vm_service_3/vm_network_interfaces/net5",
            props="ipaddresses={0}".format(
                lvtd_vm3["NETWORK_INTERFACES"]["NET5"][
                    "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg3_path + "/applications/vm_service_3/vm_network_interfaces/net6",
            props="ipaddresses={0}".format(
                lvtd_vm3["NETWORK_INTERFACES"]["NET6"][
                    "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg3_path + "/applications/vm_service_3/" \
                       "vm_network_interfaces/net32",
            props="ipaddresses={0} ipv6addresses={1}".format(
                lvtd_vm3["NETWORK_INTERFACES"]["NET32"]["ipaddresses"],
                lvtd_vm3["NETWORK_INTERFACES"]["NET32"]["ipv6addresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg3_path + "/applications/vm_service_3/" \
                       "vm_network_interfaces/net33",
            props="ipaddresses={0} ipv6addresses={1}".format(
                lvtd_vm3["NETWORK_INTERFACES"]["NET33"]["ipaddresses"],
                lvtd_vm3["NETWORK_INTERFACES"]["NET33"]["ipv6addresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg3_path + "/applications/vm_service_3/" \
                       "vm_network_interfaces/net34",
            props="ipaddresses={0} ipv6addresses={1}".format(
                lvtd_vm3["NETWORK_INTERFACES"]["NET34"]["ipaddresses"],
                lvtd_vm3["NETWORK_INTERFACES"]["NET34"]["ipv6addresses"]))

        # id: litpcds-7516
        # description: Configure vm with ipv6 addresses
        # test_steps:
        #   step: Configure vm with ipv6 addresses for CS_VM3
        #   result: CS_VM3 is configured with ipv6 addresses
        self.execute_cli_update_cmd(self.management_server,
            sg3_path +
                "/applications/vm_service_3/vm_network_interfaces/net_dhcp",
            props="ipv6addresses='{0}' ipaddresses={1}".format(
                lvtd_vm3["NETWORK_INTERFACES"][
                    "NET_DHCP"]["ipv6addresses"],
                lvtd_vm3["NETWORK_INTERFACES"][
                    "NET_DHCP"]["ipaddresses"]))

        # id: litpcds-7185
        # description: Define gateway on the network interface
        # test_steps:
        #   step: Define default gateway for CS_VM3
        #   result: default gateway is defined for CS_VM3
        self.execute_cli_update_cmd(self.management_server,
            vm_service_3_path + "/vm_network_interfaces/net6",
            props="gateway={0}".format(
                lvtd_vm3["NETWORK_INTERFACES"]["NET6"][
                    "gateway"]))

        # id: litpcds-7186
        # description: Configure yum repos for CS_VM3
        # test_steps:
        #   step: Create yum repos for CS_VM3
        #   result: Yum repos are defined for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_3_path + "/vm_yum_repos/repo_3PP ",
                                "vm-yum-repo",
                                props="name='{0}' base_url='{1}'".format(
                                    lvtd_vm3["YUM_REPOS"]["3PP"]["name"],
                                    lvtd_vm3["YUM_REPOS"]["3PP"][
                                        "base_url"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_3_path + "/vm_yum_repos/repo_LITP ",
                                "vm-yum-repo",
                                props="name='{0}' base_url='{1}'".format(
                                    lvtd_vm3["YUM_REPOS"]["LITP"]["name"],
                                    lvtd_vm3["YUM_REPOS"]["LITP"][
                                        "base_url"]), add_to_cleanup=False)

        # id: litpcds-7186
        # description: Configure vm packages for CS_VM3
        # test_steps:
        #   step: Create vm packages for CS_VM3
        #   result: VM packages are defined for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_packages/pkg_empty_rpm4",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm3["PACKAGES"]["PKG4"]["name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_packages/pkg_empty_rpm5",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm3["PACKAGES"]["PKG5"]["name"]), add_to_cleanup=False)

        # id: litpcds-7815
        # description: Configure nfs mounts for CS_VM3
        # test_steps:
        #   step: Create nfs mounts for CS_VM3
        #   result: NFS mounts are created for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_3_path + "/vm_nfs_mounts/vm_nfs_mount_4",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' " \
                              "mount_options='{2}'".format(
                            lvtd_vm3["NFS_MOUNTS"]["VM_MOUNT4"][
                                "device_path"],
                            lvtd_vm3["NFS_MOUNTS"]["VM_MOUNT4"][
                                "mount_point"],
                            lvtd_vm3["NFS_MOUNTS"]["VM_MOUNT4"][
                                "mount_options"]), add_to_cleanup=False)

        # id: litpcds-6627
        # description: Configure ssh keys for CS_VM3
        # test_steps:
        #   step: Create ssh keys for CS_VM3
        #   result: SSH keys are created for CS_VM3
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_3_path + "/vm_ssh_keys/ssh_key_rsa_14",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm3["SSH_KEYS"]["KEY4"]["ssh_key"]), add_to_cleanup=False)

        # id: torf-107476
        # title: test_03_p_create_vm_ram_mount_RH6_ramfs
        # description: Test to verify that a user can create a ramfs
        # file system using default values on RHEL 6 (Create a ramfs on
        # my CS_VM3)
        # test_steps:
        #   step: Create VM with new vm-ram-mount item with a RHEL 6 system
        #   result: vm-ram-mount is created successfully with RHEL 6 system
        self.execute_cli_create_cmd(self.management_server, vm_service_3_path
                                    + "/vm_ram_mounts/vm_ram_mount_3",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    .format(
                                      lvtd_vm3["VM_RAM_MOUNT"]["type"],
                                      lvtd_vm3["VM_RAM_MOUNT"]
                                      ["mount_point"]),
                                    add_to_cleanup=False)

        # id: torf-180365, torf-180367
        # title: test_03_p_create_vm_scripts_runtime
        # test_04_p_scripts_execution_proper_order
        # test_08_n_last_script_fail_rest_pass
        # description: Positive TC that will check that you can successfully
        # create a vm service with vm-custom-script item during runtime.
        # test_steps:
        # step: Create a VM with vm-custom-script item with
        # custom_script_names="csfname2.sh,csfname3.sh,csfname1.sh,
        # csfname4.sh,csfname5.sh""
        self.execute_cli_create_cmd(self.management_server, vm_service_3_path
                                    + "/vm_custom_script/vm_custom_script_1",
                                    "vm-custom-script",
                                    props="custom_script_names='{0}'"
                                    .format(lvtd_vm3["VM_CUSTOM_SCRIPT"]
                                      ["custom_script_names"]),
                                    add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM4 #
        #                       #
        #########################
        lvtd_vm4 = libvirt_test_data.INITIAL_SERVICE_GROUP_4_DATA
        sg4_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_VM4"
        vm_service_4_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_4"

        # id: litpcds-7180
        # description: Create VCS-clustered-service CS_VM4
        # test_steps:
        #   step: Create VCS-clustered-service CS_VM4
        #   result: CS_VM4 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, sg4_path,
                        "vcs-clustered-service",
                        props="active={0} standby={1} name='{2}' " \
                              "online_timeout={3} dependency_list='{4}' " \
                              "node_list='{5}'".format(
                            lvtd_vm4["CLUSTER_SERVICE"]["active"],
                            lvtd_vm4["CLUSTER_SERVICE"]["standby"],
                            lvtd_vm4["CLUSTER_SERVICE"]["name"],
                            lvtd_vm4["CLUSTER_SERVICE"][
                                "online_timeout"],
                            lvtd_vm4["CLUSTER_SERVICE"][
                                "dependency_list"],
                            lvtd_vm4["CLUSTER_SERVICE"][
                                "node_list"]), add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create vm-service-4 for CS_VM4
        # test_steps:
        #   step: Create vm-service-4 in the litp model
        #   result: vm-service-4 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, vm_service_4_path,
                        "vm-service",
                        props="cleanup_command='{0}' status_command='{1}' " \
                              "hostnames='{2}' internal_status_check='{3}' " \
                              "start_command='{4}' service_name='{5}' " \
                              "stop_command='{6}' ram='{7}' image_name='{8}' "\
                              "cpus='{9}'".format(
                            lvtd_vm4["VM_SERVICE"][
                                "cleanup_command"],
                            lvtd_vm4["VM_SERVICE"][
                                "status_command"],
                            lvtd_vm4["VM_SERVICE"]["hostnames"],
                            lvtd_vm4["VM_SERVICE"][
                                "internal_status_check"],
                            lvtd_vm4["VM_SERVICE"][
                                "start_command"],
                            lvtd_vm4["VM_SERVICE"]["service_name"],
                            lvtd_vm4["VM_SERVICE"]["stop_command"],
                            lvtd_vm4["VM_SERVICE"]["ram"],
                            lvtd_vm4["VM_SERVICE"]["image_name"],
                            lvtd_vm4["VM_SERVICE"]["cpus"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create ha-service-config for CS_VM4 in litp model
        # test_steps:
        #   step: Create ha-service-config for CS_VM4
        #   result: ha-service-config is created for CS_VM4
        self.execute_cli_create_cmd(self.management_server,
                                    sg4_path + "/ha_configs/service_config",
                                    "ha-service-config", add_to_cleanup=False)

        # id: litpcds-7180
        # description: Inheirit vm-service-4 onto CS_VM4
        # test_steps:
        #   step: Inherit vm-service-4 onto CS_VM4 clustered service
        #   result: vm-service-4 is inherited onto CS_VM4
        self.execute_cli_inherit_cmd(self.management_server,
                             sg4_path + "/applications/vm_service_4",
                             vm_service_4_path, add_to_cleanup=False)

        # id: litpcds-7184
        # description: Configure VM aliases for CS_VM4
        # test_steps:
        #   step: Configure VM aliases for CS_VM4
        #   result: VM aliases are created for CS_VM4
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_aliases/ms",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm4["VM_ALIAS"]["MS1"][
                                    "alias_names"],
                                lvtd_vm4["VM_ALIAS"]["MS1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_aliases/sfs",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm4["VM_ALIAS"]["SFS"][
                                    "alias_names"],
                                lvtd_vm4["VM_ALIAS"]["SFS"][
                                    "address"]), add_to_cleanup=False)

        # id: litpcds-7179
        # description: Configure network interfaces for CS_VM4
        # test_steps:
        #   step: Configure network interfaces for CS_VM4
        #   result: Network interfaces are created for CS_VM4
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_network_interfaces/net7",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm4["NETWORK_INTERFACES"]["NET7"][
                                    "host_device"],
                                lvtd_vm4["NETWORK_INTERFACES"]["NET7"][
                                    "network_name"],
                                lvtd_vm4["NETWORK_INTERFACES"]["NET7"][
                                    "device_name"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_network_interfaces/net8",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm4["NETWORK_INTERFACES"]["NET8"][
                                    "host_device"],
                                lvtd_vm4["NETWORK_INTERFACES"]["NET8"][
                                    "network_name"],
                                lvtd_vm4["NETWORK_INTERFACES"]["NET8"][
                                    "device_name"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_network_interfaces/net9",
                        "vm-network-interface",
                        props="host_device='{0}' network_name='{1}' " \
                              "device_name='{2}'".format(
                            lvtd_vm4["NETWORK_INTERFACES"]["NET9"][
                                "host_device"],
                            lvtd_vm4["NETWORK_INTERFACES"]["NET9"][
                                "network_name"],
                            lvtd_vm4["NETWORK_INTERFACES"]["NET9"][
                                "device_name"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_network_interfaces/net10",
                        "vm-network-interface",
                        props="host_device='{0}' network_name='{1}' " \
                              "device_name='{2}'".format(
                            lvtd_vm4["NETWORK_INTERFACES"][
                                "NET10"]["host_device"],
                            lvtd_vm4["NETWORK_INTERFACES"][
                                "NET10"]["network_name"],
                            lvtd_vm4["NETWORK_INTERFACES"][
                                "NET10"]["device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_network_interfaces/net_dhcp",
                        "vm-network-interface",
                        props="host_device='{0}' network_name='{1}' " \
                              "device_name='{2}' gateway6='{3}'".format(
                            lvtd_vm4["NETWORK_INTERFACES"][
                                "NET_DHCP"]["host_device"],
                            lvtd_vm4["NETWORK_INTERFACES"][
                                "NET_DHCP"]["network_name"],
                            lvtd_vm4["NETWORK_INTERFACES"][
                                "NET_DHCP"]["device_name"],
                            lvtd_vm4["NETWORK_INTERFACES"][
                                "NET_DHCP"]["gateway6"]), add_to_cleanup=False)

        self.execute_cli_update_cmd(self.management_server,
                sg4_path +
                    "/applications/vm_service_4/vm_network_interfaces/net7",
                props="ipaddresses={0}".format(
                    lvtd_vm4["NETWORK_INTERFACES"]["NET7"][
                        "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg4_path + "/applications/vm_service_4/vm_network_interfaces/net8",
            props="ipaddresses={0}".format(
                lvtd_vm4["NETWORK_INTERFACES"]["NET8"][
                    "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg4_path + "/applications/vm_service_4/vm_network_interfaces/net9",
            props="ipaddresses={0}".format(
                lvtd_vm4["NETWORK_INTERFACES"]["NET9"][
                    "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg4_path +
                "/applications/vm_service_4/vm_network_interfaces/net10",
            props="ipaddresses={0}".format(
                lvtd_vm4["NETWORK_INTERFACES"][
                    "NET10"]["ipaddresses"]))

        # id: litpcds-7516
        # description: Configure vm with ipv6 addresses
        # test_steps:
        #   step: Configure vm with ipv6 addresses for CS_VM4
        #   result: CS_VM4 is configured with ipv6 addresses
        self.execute_cli_update_cmd(self.management_server,
            sg4_path +
                "/applications/vm_service_4/vm_network_interfaces/net_dhcp",
            props="ipv6addresses='{0}'".format(
                lvtd_vm4["NETWORK_INTERFACES"][
                    "NET_DHCP"]["ipv6addresses"]))

        # id: litpcds-7185
        # description: Configure default gateway for my VM service CS_VM4
        # test_steps:
        #   step: Configure default gateway for my VM service CS_VM4
        #   result: Default gateway is created for CS_VM4
        self.execute_cli_update_cmd(self.management_server,
            sg4_path +
                "/applications/vm_service_4/vm_network_interfaces/net10",
            props="gateway={0}".format(
                lvtd_vm4["NETWORK_INTERFACES"][
                    "NET10"]["gateway"]))
        # id: litpcds-7186
        # description: Configure yum repos for CS_VM4
        # test_steps:
        #   step: Create yum repos for CS_VM4
        #   result: Yum repos are defined for CS_VM4
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_yum_repos/repo_3PP",
                            "vm-yum-repo",
                            props="name='{0}' base_url='{1}' ".format(
                                lvtd_vm4["YUM_REPOS"]["3PP"]["name"],
                                lvtd_vm4["YUM_REPOS"]["3PP"][
                                    "base_url"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_yum_repos/repo_LITP",
                            "vm-yum-repo",
                            props="name='{0}' base_url='{1}'".format(
                                lvtd_vm4["YUM_REPOS"]["LITP"]["name"],
                                lvtd_vm4["YUM_REPOS"]["LITP"][
                                    "base_url"]), add_to_cleanup=False)
        # id: litpcds-7186
        # description: Configure vm packages for CS_VM4
        # test_steps:
        #   step: Create vm packages for CS_VM4
        #   result: VM packages are defined for CS_VM4
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_packages/pkg_empty_rpm6",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm4["PACKAGES"]["PKG6"]["name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_packages/pkg_empty_rpm7",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm4["PACKAGES"]["PKG7"]["name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_packages/pkg_empty_rpm8",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm4["PACKAGES"]["PKG8"]["name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_packages/pkg_empty_rpm9",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm4["PACKAGES"]["PKG9"]["name"]), add_to_cleanup=False)

        # id: litpcds-7815
        # description: Configure nfs mounts for CS_VM4
        # test_steps:
        #   step: Create nfs mounts for CS_VM4
        #   result: NFS mounts are created for CS_VM4
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_nfs_mounts/vm_nfs_mount_5",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' " \
                              "mount_options='{2}'".format(
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT5"][
                                "device_path"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT5"][
                                "mount_point"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT5"][
                                "mount_options"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_nfs_mounts/vm_nfs_mount_6",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}'".format(
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT6"][
                                "device_path"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT6"][
                                "mount_point"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_nfs_mounts/vm_nfs_mount_7",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' " \
                              "mount_options='{2}'".format(
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT7"][
                                "device_path"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT7"][
                                "mount_point"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT7"][
                                "mount_options"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_nfs_mounts/vm_nfs_mount_8",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' "
                              "mount_options='{2}'".format(
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT8"][
                                "device_path"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT8"][
                                "mount_point"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT8"][
                                "mount_options"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_4_path + "/vm_nfs_mounts/vm_nfs_mount_9",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}'".format(
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT9"][
                                "device_path"],
                            lvtd_vm4["NFS_MOUNTS"]["VM_MOUNT9"][
                                "mount_point"]), add_to_cleanup=False)
        # id: litpcds-6627
        # description: Configure ssh keys for CS_VM4
        # test_steps:
        #   step: Create ssh keys for CS_VM4
        #   result: SSH keys are created for CS_VM4
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_ssh_keys/ssh_key_rsa_15",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm4["SSH_KEYS"]["KEY5"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_ssh_keys/ssh_key_rsa_16",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm4["SSH_KEYS"]["KEY6"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_ssh_keys/ssh_key_rsa_17",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm4["SSH_KEYS"]["KEY7"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_ssh_keys/ssh_key_rsa_18",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm4["SSH_KEYS"]["KEY8"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_4_path + "/vm_ssh_keys/ssh_key_rsa_19",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm4["SSH_KEYS"]["KEY9"]["ssh_key"]), add_to_cleanup=False)

        # id: torf-180365
        # title: test_03_p_create_vm_scripts_runtime
        # torf-180367
        # test_07_n_first_script_fail_rest_pass
        # test_12_n_last_script_exceeding_timeout
        # description: Positive TC that will check that you can successfully
        # create a vm service with vm-custom-script item during runtime.
        # test_steps:
        # step: Create a VM with vm-custom-script item with
        # custom_script_names="csfname5.sh,csfname6.sh"
        self.execute_cli_create_cmd(self.management_server, vm_service_4_path
                                    + "/vm_custom_script/vm_custom_script_1",
                                    "vm-custom-script",
                                    props="custom_script_names='{0}'"
                                    .format(lvtd_vm4["VM_CUSTOM_SCRIPT"]
                                      ["custom_script_names"]),
                                    add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM5 #
        #                       #
        #########################

        lvtd_vm5 = libvirt_test_data.INITIAL_SERVICE_GROUP_5_DATA
        sg5_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_VM5"
        vm_service_5_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_5"

        # id: litpcds-7180
        # description: Create VCS-clustered-service CS_VM5
        # test_steps:
        #   step: Create VCS-clustered-service CS_VM5
        #   result: CS_VM5 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, sg5_path,
                            "vcs-clustered-service",
                            props="active={0} standby={1} name='{2}' " \
                                  "online_timeout={3} dependency_list='{4}' " \
                                  "node_list='{5}'".format(
                                lvtd_vm5["CLUSTER_SERVICE"]["active"],
                                lvtd_vm5["CLUSTER_SERVICE"]["standby"],
                                lvtd_vm5["CLUSTER_SERVICE"]["name"],
                                lvtd_vm5["CLUSTER_SERVICE"][
                                    "online_timeout"],
                                lvtd_vm5["CLUSTER_SERVICE"][
                                    "dependency_list"],
                                lvtd_vm5["CLUSTER_SERVICE"][
                                    "node_list"]), add_to_cleanup=False)
        # id: litpcds-7180
        # description: Create vm-service-5 for CS_VM5
        # test_steps:
        #   step: Create vm-service-5 in the litp model
        #   result: vm-service-5 is created in the litp model
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_5_path + "", "vm-service",
                        props="cleanup_command='{0}' status_command='{1}' " \
                              "hostnames='{2}' internal_status_check='{3}' " \
                              "start_command='{4}' service_name='{5}' " \
                              "stop_command='{6}' ram='{7}' " \
                              "image_name='{8}' cpus='{9}' " \
                              "cpuset={10}".format(
                            lvtd_vm5["VM_SERVICE"][
                                "cleanup_command"],
                            lvtd_vm5["VM_SERVICE"][
                                "status_command"],
                            lvtd_vm5["VM_SERVICE"]["hostnames"],
                            lvtd_vm5["VM_SERVICE"][
                                "internal_status_check"],
                            lvtd_vm5["VM_SERVICE"][
                                "start_command"],
                            lvtd_vm5["VM_SERVICE"]["service_name"],
                            lvtd_vm5["VM_SERVICE"]["stop_command"],
                            lvtd_vm5["VM_SERVICE"]["ram"],
                            lvtd_vm5["VM_SERVICE"]["image_name"],
                            lvtd_vm5["VM_SERVICE"]["cpus"],
                            lvtd_vm5["VM_SERVICE"]["cpuset"]),
                                    add_to_cleanup=False)
        # id: litpcds-7180
        # description: Create ha-service-config for CS_VM5 in litp model
        # test_steps:
        #   step: Create ha-service-config for CS_VM5
        #   result: ha-service-config is created for CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                                    sg5_path + "/ha_configs/service_config",
                                    "ha-service-config",
                                    props="restart_limit={0}".format(
                                        lvtd_vm5["HA_CONFIG"][
                                            "restart_limit"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Inheirit vm-service-5 onto CS_VM5
        # test_steps:
        #   step: Inherit vm-service-5 onto CS_VM5 clustered service
        #   result: vm-service-5 is inherited onto CS_VM5
        self.execute_cli_inherit_cmd(self.management_server,
                             sg5_path + "/applications/vm_service_5",
                             vm_service_5_path, add_to_cleanup=False)

        # id: litpcds-7184
        # description: Configure VM aliases for CS_VM5
        # test_steps:
        #   step: Configure VM aliases for CS_VM5
        #   result: VM aliases are created for CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_aliases/db1",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm5["VM_ALIAS"]["DB1"][
                                    "alias_names"],
                                lvtd_vm5["VM_ALIAS"]["DB1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_aliases/db4",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm5["VM_ALIAS"]["DB4"][
                                    "alias_names"],
                                lvtd_vm5["VM_ALIAS"]["DB4"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_aliases/db2",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm5["VM_ALIAS"]["DB2"][
                                    "alias_names"],
                                lvtd_vm5["VM_ALIAS"]["DB2"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_aliases/ms",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm5["VM_ALIAS"]["MS1"][
                                    "alias_names"],
                                lvtd_vm5["VM_ALIAS"]["MS1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_aliases/sfs",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm5["VM_ALIAS"]["SFS"][
                                    "alias_names"],
                                lvtd_vm5["VM_ALIAS"]["SFS"][
                                    "address"]), add_to_cleanup=False)
        # id: litpcds-7179
        # description: Configure network interfaces for CS_VM5
        # test_steps:
        #   step: Configure network interfaces for CS_VM5
        #   result: Network interfaces are created for CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_network_interfaces/net11",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET11"]["host_device"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET11"]["network_name"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET11"]["device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_network_interfaces/net12",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET12"]["host_device"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET12"]["network_name"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET12"]["device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_network_interfaces/net13",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET13"]["host_device"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET13"]["network_name"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET13"]["device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_network_interfaces/net14",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET14"]["host_device"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET14"]["network_name"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET14"]["device_name"]),
                                    add_to_cleanup=False)

        # id: litpcds-7185
        # description: Configure default gateway for my VM service CS_VM5
        # test_steps:
        #   step: Configure default gateway for my VM service CS_VM5
        #   result: Default gateway is created for CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_network_interfaces/net15",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}' gateway6='{3}'".format(
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET15"]["host_device"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET15"]["network_name"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET15"]["device_name"],
                                lvtd_vm5["NETWORK_INTERFACES"][
                                    "NET15"]["gateway6"]),
                                    add_to_cleanup=False)

        self.execute_cli_update_cmd(self.management_server,
            sg5_path +
                "/applications/vm_service_5/vm_network_interfaces/net11",
            props="ipaddresses={0}".format(
                lvtd_vm5["NETWORK_INTERFACES"][
                    "NET11"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg5_path +
                "/applications/vm_service_5/vm_network_interfaces/net12",
            props="ipaddresses={0}".format(
                lvtd_vm5["NETWORK_INTERFACES"][
                    "NET12"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg5_path +
                "/applications/vm_service_5/vm_network_interfaces/net13",
            props="ipaddresses={0}".format(
                lvtd_vm5["NETWORK_INTERFACES"][
                    "NET13"]["ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg5_path +
                "/applications/vm_service_5/vm_network_interfaces/net14",
            props="ipaddresses={0}".format(
                lvtd_vm5["NETWORK_INTERFACES"][
                    "NET14"]["ipaddresses"]))

        # id: litpcds-7516
        # description: Configure vm with ipv6 addresses
        # test_steps:
        #   step: Configure vm with ipv6 addresses for CS_VM4
        #   result: CS_VM4 is configured with ipv6 addresses
        self.execute_cli_update_cmd(self.management_server,
            sg5_path +
                "/applications/vm_service_5/vm_network_interfaces/net15",
            props="ipv6addresses='{0}' ipaddresses='{1}'".format(
                lvtd_vm5["NETWORK_INTERFACES"][
                    "NET15"]["ipv6addresses"],
                lvtd_vm5["NETWORK_INTERFACES"][
                    "NET15"]["ipaddresses"]))

        # id: litpcds-7185
        # description: Configure default gateway for my VM service CS_VM5
        # test_steps:
        #   step: Configure default gateway for my VM service CS_VM5
        #   result: Default gateway is created for CS_VM5
        self.execute_cli_update_cmd(self.management_server,
            vm_service_5_path + "/vm_network_interfaces/net13",
            props="gateway={0}".format(
                lvtd_vm5["NETWORK_INTERFACES"][
                    "NET13"]["gateway"]))

        # id: litpcds-7186
        # description: Configure yum repos for CS_VM5
        # test_steps:
        #   step: Create yum repos for CS_VM5
        #   result: Yum repos are defined for CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_5_path + "/vm_yum_repos/repo_3PP",
                        "vm-yum-repo",
                        props="name='{0}' base_url='{1}'".format(
                            lvtd_vm5["YUM_REPOS"]["3PP"]["name"],
                            lvtd_vm5["YUM_REPOS"]["3PP"][
                                "base_url"]), add_to_cleanup=False)

        # id: litpcds-7815
        # description: Configure nfs mounts for CS_VM5
        # test_steps:
        #   step: Create nfs mounts for CS_VM5
        #   result: NFS mounts are created for CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_5_path + "/vm_nfs_mounts/vm_nfs_mount_10",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}'".format(
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT10"][
                                "device_path"],
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT10"][
                                "mount_point"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_5_path + "/vm_nfs_mounts/vm_nfs_mount_11",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' " \
                              "mount_options='{2}'".format(
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT11"][
                                "device_path"],
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT11"][
                                "mount_point"],
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT11"][
                                "mount_options"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_5_path + "/vm_nfs_mounts/vm_nfs_mount_12",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' " \
                              "mount_options='{2}'".format(
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT12"][
                                "device_path"],
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT12"][
                                "mount_point"],
                            lvtd_vm5["NFS_MOUNTS"]["VM_MOUNT12"][
                                "mount_options"]),
                                    add_to_cleanup=False)
        # id: litpcds-6627
        # description: Configure ssh keys for CS_VM5
        # test_steps:
        #   step: Create ssh keys for CS_VM5
        #   result: SSH keys are created for CS_VM5
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_5_path + "/vm_ssh_keys/ssh_key_rsa_10",
                            "vm-ssh-key",
                            props="ssh_key='{0}'".format(
                                lvtd_vm5["SSH_KEYS"]["KEY10"][
                                    "ssh_key"]), add_to_cleanup=False)

        # id: torf-180365
        # title: test_03_p_create_vm_scripts_runtime
        # description: Positive TC that will check that you can successfully
        # create a vm service with vm-custom-script item during runtime.
        # test_steps:
        # step: Create a VM with vm-custom-script item with
        # custom_script_names="system_memory.sh"
        self.execute_cli_create_cmd(self.management_server, vm_service_5_path
                                    + "/vm_custom_script/vm_custom_script_1",
                                    "vm-custom-script",
                                    props="custom_script_names='{0}'"
                                    .format(lvtd_vm5["VM_CUSTOM_SCRIPT"]
                                      ["custom_script_names"]),
                                    add_to_cleanup=False)

        # TORF-271798: As a LITP engineer I want to update the Libvirt
        # plugin and adapter to create the network-config V1 file to be
        # compatible with the native RHEL7.4 cloud-init
        # TORF-271798 TC_07: Deploy a VM based on a rhel7.4 image onto peer
        # servers under a FO SG
        #########################
        #                       #
        #  Service Group CS_VM6 #
        #                       #
        #########################
        lvtd_vm6 = libvirt_test_data.INITIAL_SERVICE_GROUP_6_DATA
        rhel7_4_image_path = \
            self.libvirt_info["software_images_path"] + "vm_image_5"

        # Create RHEL7.4 vm image in the model
        vm6_image = lvtd_vm6["VM_IMAGE"]
        self.execute_cli_create_cmd(self.management_server,
                                    url=rhel7_4_image_path,
                                    class_type="vm-image",
                                    props="source_uri={0} name={1}".format(
                                        vm6_image["image_url"],
                                        vm6_image["image_name"]),
                                    add_to_cleanup=False)

        # Create a vm service based on rhel7.4 image
        vm6_service = lvtd_vm6["VM_SERVICE"]
        vm_service_6_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_6"
        self.execute_cli_create_cmd(self.management_server,
                                    url=vm_service_6_path,
                                    class_type="vm-service",
                                    props="cpus={0} service_name={1} ram={2} "
                                          "cleanup_command='{3}' "
                                          "image_name={4} hostnames={5} "
                                          "internal_status_check={6}".
                                    format(vm6_service["cpus"],
                                           vm6_service["service_name"],
                                           vm6_service["ram"],
                                           vm6_service["cleanup_command"],
                                           vm6_service["image_name"],
                                           vm6_service["hostnames"],
                                           vm6_service["internal_status_check"]
                                           ), add_to_cleanup=False)

        # Create a FO vcs clustered service
        vm6_cluster_srv = lvtd_vm6["CLUSTER_SERVICE"]
        sg6_path = \
            self.libvirt_info["cluster_services_path"] + "/CS_VM6"
        self.execute_cli_create_cmd(self.management_server,
                                    url=sg6_path,
                                    class_type="vcs-clustered-service",
                                    props="active={0} standby={1} name={2} "
                                          "node_list={3} online_timeout={4} "
                                          "dependency_list={5}".
                                    format(vm6_cluster_srv["active"],
                                           vm6_cluster_srv["standby"],
                                           vm6_cluster_srv["name"],
                                           vm6_cluster_srv["node_list"],
                                           vm6_cluster_srv["online_timeout"],
                                           vm6_cluster_srv["dependency_list"]),
                                    add_to_cleanup=False)

        # Create ha service config for CS_VM6 in the model
        self.execute_cli_create_cmd(self.management_server,
                                    sg6_path + "/ha_configs/service_config",
                                    "ha-service-config", add_to_cleanup=False)

        # Add the service group to a vcs cluster
        sg6_applications_path = sg6_path + "/applications/vm_service_6"
        self.execute_cli_inherit_cmd(self.management_server,
                                     sg6_applications_path,
                                     vm_service_6_path, add_to_cleanup=False)

        # Configure vm aliases
        for alias_name, alias_props in lvtd_vm6["VM_ALIAS"].items():
            vm_alias_path = "/vm_aliases/{0}".format(alias_name)
            self.execute_cli_create_cmd(self.management_server,
                                        url=vm_service_6_path + vm_alias_path,
                                        class_type="vm-alias",
                                        props="alias_names='{0}' address='{1}'"
                                        .format(
                                            alias_props["alias_names"],
                                            alias_props["address"]),
                                        add_to_cleanup=False)

        # Configure vm network interfaces
        vm_net1_path = vm_service_6_path + "/vm_network_interfaces/net1"
        vm_net1_props = lvtd_vm6["NETWORK_INTERFACES"]["NET1"]
        self.execute_cli_create_cmd(self.management_server,
                                    url=vm_net1_path,
                                    class_type="vm-network-interface",
                                    props="host_device={0} device_name={1} "
                                          "network_name={2}".
                                    format(vm_net1_props["host_device"],
                                           vm_net1_props["device_name"],
                                           vm_net1_props["network_name"]),
                                    add_to_cleanup=False)

        vm_net2_path = vm_service_6_path + "/vm_network_interfaces/net2"
        vm_net2_props = lvtd_vm6["NETWORK_INTERFACES"]["NET2"]
        self.execute_cli_create_cmd(self.management_server,
                                    url=vm_net2_path,
                                    class_type="vm-network-interface",
                                    props="host_device={0} device_name={1} "
                                          "network_name={2}".
                                    format(vm_net2_props["host_device"],
                                           vm_net2_props["device_name"],
                                           vm_net2_props["network_name"]),
                                    add_to_cleanup=False)

        vm_net3_path = vm_service_6_path + "/vm_network_interfaces/net_dhcp"
        vm_net3_props = lvtd_vm6["NETWORK_INTERFACES"]["NET_DHCP"]
        self.execute_cli_create_cmd(self.management_server,
                                    url=vm_net3_path,
                                    class_type="vm-network-interface",
                                    props="host_device={0} device_name={1} "
                                          "network_name={2}".
                                    format(vm_net3_props["host_device"],
                                           vm_net3_props["device_name"],
                                           vm_net3_props["network_name"]),
                                    add_to_cleanup=False)

        # Update vm net interfaces
        self.execute_cli_update_cmd(self.management_server,
                                    sg6_applications_path +
                                    "/vm_network_interfaces/net1",
                                    props="ipaddresses={0}".format(
                                        vm_net1_props["ipaddresses"]))

        self.execute_cli_update_cmd(self.management_server,
                                    sg6_applications_path +
                                    "/vm_network_interfaces/net2",
                                    props="ipv6addresses={0}".format(
                                        vm_net2_props["ipv6addresses"]))

        self.execute_cli_update_cmd(self.management_server,
                                    sg6_applications_path +
                                    "/vm_network_interfaces/net_dhcp",
                                    props="ipaddresses={0}".format(
                                        vm_net3_props["ipaddresses"]))

        # Define gateway on the vm network interface
        self.execute_cli_update_cmd(self.management_server,
                                    url=vm_net1_path,
                                    props="gateway={0}".format(
                                        vm_net1_props["gateway"]))

        # Configure vm custom scripts
        self.execute_cli_create_cmd(self.management_server,
                                    url=vm_service_6_path +
                                    "/vm_custom_script/vm_custom_script_1",
                                    class_type="vm-custom-script",
                                    props="custom_script_names='{0}'".format(
                                        lvtd_vm6["VM_CUSTOM_SCRIPT"][
                                            "custom_scripts"]),
                                    add_to_cleanup=False)

    def add_ms_service_group(self):
        """
        id: litpcds_11405
        description: As a LITP User I want VM services defined in the
        services collection of an MS
        """
        ms_vm1 = "/ms/services/MS_VM1"
        ms_data = libvirt_test_data.MS_NET_DATA
        ms_vm1_data = libvirt_test_data.MS_VM1_DATA

        # Remove specified network interface properties
        self.execute_cli_update_cmd(self.management_server,
                                    "/ms/network_interfaces/b0",
                                    "ipaddress ipv6address network_name ",
                                    action_del=True)

        # Update network interface bridge
        self.execute_cli_update_cmd(self.management_server,
                                    "/ms/network_interfaces/b0",
                                    "bridge={0}".format(
                                        ms_data["NETWORK_INTERFACE"][
                                            "b0"]["bridge"]))

        # Create new network interface
        self.execute_cli_create_cmd(self.management_server,
                                    "/ms/network_interfaces/br0",
                                    "bridge",
                                    "device_name={0} forwarding_delay={1} "
                                    "ipaddress={2} ipv6address={3} "
                                    "network_name={4}".
                                    format(
                                        ms_data[
                                            "NETWORK_INTERFACE"][
                                            "br0"]["device_name"],
                                        ms_data[
                                            "NETWORK_INTERFACE"][
                                            "br0"]["forwarding_delay"],
                                        ms_data[
                                            "NETWORK_INTERFACE"][
                                            "br0"]["ipaddress"],
                                        ms_data[
                                            "NETWORK_INTERFACE"][
                                            "br0"]["ipv6address"],
                                        ms_data[
                                            "NETWORK_INTERFACE"][
                                            "br0"]["network_name"]),
                                    add_to_cleanup=False)

        self.create_ms_vm(ms_vm1, ms_vm1_data)

    def create_ms_vm(self, ms_vm1, ms_vm1_data):
        """
        Description:
            Create MS vm on the provided path using a data dictionary
        :param ms_vm1: The litp path on which to create the vm
        :param ms_vm1_data: The dictionary containing the details for the vm
        :return:
        """
        # Create new vm service
        self.execute_cli_create_cmd(self.management_server, ms_vm1,
                                "vm-service",
                                "image_name={0} cpus={1} ram='{2}' " \
                                "internal_status_check={3} hostnames={4} " \
                                "service_name='{5}'".
                                format(
                                    ms_vm1_data["VM_SERVICE"][
                                        "image_name"],
                                    ms_vm1_data["VM_SERVICE"]["cpus"],
                                    ms_vm1_data["VM_SERVICE"]["ram"],
                                    ms_vm1_data["VM_SERVICE"][
                                        "internal_status_check"],
                                    ms_vm1_data["VM_SERVICE"]["hostnames"],
                                    ms_vm1_data["VM_SERVICE"][
                                        "service_name"]),
                                add_to_cleanup=False)
        # Create vm aliases
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_aliases/db1", "vm-alias",
                                    "alias_names='{0}' address='{1}'".
                                    format(
                                        ms_vm1_data["VM_ALIAS"]["DB1"][
                                            "alias_names"],
                                        ms_vm1_data["VM_ALIAS"]["DB1"][
                                            "address"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_aliases/db2", "vm-alias",
                                    "alias_names='{0}' address='{1}'".
                                    format(
                                        ms_vm1_data["VM_ALIAS"]["DB2"][
                                            "alias_names"],
                                        ms_vm1_data["VM_ALIAS"]["DB2"][
                                            "address"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    ms_vm1
                                    + "/vm_aliases/ms", "vm-alias",
                                    "alias_names='{0}' address='{1}'".
                                    format(
                                        ms_vm1_data["VM_ALIAS"]["MS"][
                                            "alias_names"],
                                        ms_vm1_data["VM_ALIAS"]["MS"][
                                            "address"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_aliases/sfs", "vm-alias",
                                    "alias_names='{0}' address='{1}'".
                                    format(
                                        ms_vm1_data["VM_ALIAS"]["SFS"][
                                            "alias_names"],
                                        ms_vm1_data["VM_ALIAS"]["SFS"][
                                            "address"]),
                                    add_to_cleanup=False)
        # Create new network interface
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_network_interfaces/net1",
                                    "vm-network-interface",
                                    "host_device='{0}' network_name='{1}' " \
                                    "device_name='{2}'".format(
                                        ms_vm1_data["NETWORK_INTERFACE"][
                                            "NET1"]["host_device"],
                                        ms_vm1_data["NETWORK_INTERFACE"][
                                            "NET1"]["network_name"],
                                        ms_vm1_data["NETWORK_INTERFACE"][
                                            "NET1"]["device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_network_interfaces/net1",
                                    "ipaddresses={0}".format(
                                        ms_vm1_data["NETWORK_INTERFACE"][
                                            "NET1"]["ipaddresses"]))
        # Create vm yum repos
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_yum_repos/repo_3PP",
                                    "vm-yum-repo",
                                    "name='{0}' base_url='{1}'".format(
                                        ms_vm1_data["YUM_REPOS"]["3PP"][
                                            "name"],
                                        ms_vm1_data["YUM_REPOS"]["3PP"][
                                            "base_url"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_yum_repos/repo_LITP",
                                    "vm-yum-repo",
                                    "name='{0}' base_url='{1}'".format(
                                        ms_vm1_data[
                                            "YUM_REPOS"]["LITP"]["name"],
                                        ms_vm1_data[
                                            "YUM_REPOS"]["LITP"][
                                            "base_url"]),
                                    add_to_cleanup=False)

        # Create nfs mounts
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_nfs_mounts/vm_nfs_mount_1",
                                    "vm-nfs-mount",
                                    "device_path='{0}' mount_point='{1}' " \
                                    "mount_options='{2}'".
                                    format(
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_1"]["device_path"],
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_1"]["mount_point"],
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_1"][
                                            "mount_options"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_nfs_mounts/vm_nfs_mount_2",
                                    "vm-nfs-mount",
                                    "device_path='{0}' mount_point='{1}'".
                                    format(
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_2"][
                                            "device_path"],
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_2"][
                                            "mount_point"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_nfs_mounts/vm_nfs_mount_3",
                                    "vm-nfs-mount",
                                    "device_path='{0}' mount_point='{1}' " \
                                    "mount_options='{2}'".
                                    format(
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_3"][
                                            "device_path"],
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_3"][
                                            "mount_point"],
                                        ms_vm1_data["NFS_MOUNT"][
                                            "VM_NFS_MOUNT_3"][
                                            "mount_options"]),
                                    add_to_cleanup=False)
        # LITPCDS-6627 - Create ssh keys
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_ssh_keys/ssh_key_rsa_11",
                                    "vm-ssh-key",
                                    "ssh_key='{0}'".format(
                                        ms_vm1_data[
                                            "SSH_KEYS"]["SSH_KEY_RSA_11"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_ssh_keys/ssh_key_rsa_12",
                                    "vm-ssh-key",
                                    "ssh_key='{0}'".format(
                                        ms_vm1_data[
                                            "SSH_KEYS"]["SSH_KEY_RSA_12"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_ssh_keys/ssh_key_rsa_13",
                                    "vm-ssh-key",
                                    "ssh_key='{0}'".format(
                                        ms_vm1_data["SSH_KEYS"][
                                            "SSH_KEY_RSA_13"]),
                                    add_to_cleanup=False)
        # Update gateway of network interface
        self.execute_cli_update_cmd(self.management_server, ms_vm1
                                    + "/vm_network_interfaces/net1",
                                    "gateway={0}".format(
                                        ms_vm1_data[
                                            "NETWORK_INTERFACE"]["NET1"][
                                            "gateway"]))
        # Create vm package
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_packages/pkg_empty_rpm1",
                                    "vm-package", "name='empty_rpm1'".
                                    format(
                ms_vm1_data["VM_PACKAGE"][
                    "PKG_EMPTY_RPM1"]["name"]),
                                    add_to_cleanup=False)

        # [TORF-107476]: - Test case 04 - As a LITP User I want my VM to
        # mount a ramfs filesystem on MS_VM1
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_ram_mounts/vm_ram_mount_ms",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    "mount_options='{2}' "
                                    .format(
                                      ms_vm1_data["VM_RAM_MOUNT"]["type"],
                                      ms_vm1_data["VM_RAM_MOUNT"]
                                      ["mount_point"],
                                      ms_vm1_data["VM_RAM_MOUNT"]
                                      ["mount_options"]
                                      ),
                                    add_to_cleanup=False)

        # [TORF-180365]: - Test case 03 - create a custom script on MS_VM1
        self.execute_cli_create_cmd(self.management_server, ms_vm1
                                    + "/vm_custom_script/vm_custom_script_ms",
                                    "vm-custom-script",
                                    props="custom_script_names='{0}'"
                                    .format(
                                      ms_vm1_data["VM_CUSTOM_SCRIPT"]
                                      ["custom_script_names"]),
                                    add_to_cleanup=False)

    def stop_ms_vm(self, vm_data):
        """
        Description: Verify I can run a VM on the MS under puppet
        control
        Steps:
            1. Stop the service MS_VM1.
            2. Trigger a new run of puppet.
            3. Verify that the service is started again by puppet
        """
        ms_vm_data = vm_data
        service_name = ms_vm_data["VM_SERVICE"]['service_name']

        service_status = self.rhc.get_systemctl_is_active_cmd(service_name)
        service_stop = self.rhc.get_systemctl_stop_cmd(service_name)
        running_status = ['active']
        stop_status = ['inactive']

        # Check service is running
        stdout, stderr, rc = self.run_command(self.management_server,
                                              service_status,
                                              su_root=True)
        self.assertEqual(0, rc)
        self.assertEqual([], stderr)
        self.assertEqual(running_status, stdout)

        # Stop service
        _, _, rc = self.run_command(self.management_server,
                                    service_stop,
                                    su_root=True)
        self.assertEqual(0, rc)

        # Check service is stopped
        stdout, stderr, rc = self.run_command(self.management_server,
                                              service_status,
                                              su_root=True)
        self.assertEqual(3, rc)
        self.assertEqual([], stderr)
        self.assertEqual(stop_status, stdout)

        # Trigger a new run of puppet
        self.wait_full_puppet_run(self.management_server)

        # Check service is restarted by puppet
        stdout, stderr, rc = self.run_command(self.management_server,
                                              service_status,
                                              su_root=True)
        self.assertEqual(0, rc)
        self.assertEqual([], stderr)
        self.assertEqual(running_status, stdout)

    def test_ms_vm_start_after_instances_dir_file_changes(self):
        """
        Description: This test verifies the fix for support ticket:
                    TORF-532848 "RHEL7: 335 expansion upgrade got
                    failed in restarting esmon on lms"
                    It verifies when live files are missing or changes
                     are made to the config file on the MS, then the
                     vm service can be restarted
        Steps:
            1. Stop vm service
            2. Remove .live from instances dir
            3. Start vm service and verify that it is active
            4. Stop vm service
            5. Make a change to the config file e.g. cpu from 2 to 3
            6. Start vm service and verify that it is active
        """
        serv_name = libvirt_test_data.MS_VM1_DATA["VM_SERVICE"]['service_name']
        active_cmd = self.rhc.get_systemctl_is_active_cmd(serv_name)
        start_cmd = self.rhc.get_systemctl_start_cmd(serv_name)
        stop_cmd = self.rhc.get_systemctl_stop_cmd(serv_name)
        vm_instance_dir = "{0}/{1}".format(test_constants.
                                           LIBVIRT_INSTANCES_DIR, serv_name)
        config_file_path = "{0}/config.json".format(vm_instance_dir)

        # stop vm service
        stop_out = self.run_command(self.management_server, stop_cmd,
                                    su_root=True, default_asserts=True)
        self.assertEqual([], stop_out[0], "stop cmd was not successful")

        # Check service is stopped (status = 'inactive')
        vm_status = self.run_command(self.management_server, active_cmd,
                                     su_root=True)
        self.assertEqual(['inactive'], vm_status[0], "vm service is not "
                                                    "stopped")

        # Remove .live from instances dir
        remove_cmd = "{0} {1}/*.live".format(test_constants.RM_RF_PATH,
                                             vm_instance_dir)

        rm_out = self.run_command(self.management_server, remove_cmd,
                                  su_root=True, default_asserts=True)
        self.assertEqual([], rm_out[0], "Remove was not successful")

        # check no live file
        live_cmd = "{0} {1}/ | grep .live".format(test_constants.LS_PATH,
                                                  vm_instance_dir)
        check_live_out = self.run_command(self.management_server, live_cmd,
                                          su_root=True)
        self.assertEqual([], check_live_out[0], ".live files are present")

        # start vm service
        start_out = self.run_command(self.management_server, start_cmd,
                                     su_root=True)
        self.assertEqual([], start_out[0], "start cmd was not successful")

        # Check service is active
        vm_status = self.run_command(self.management_server, active_cmd,
                                     su_root=True, default_asserts=True)
        self.assertEqual(['active'], vm_status[0], "vm service is not active")

        # stop vm service
        stop_out = self.run_command(self.management_server, stop_cmd,
                                    su_root=True, default_asserts=True)
        self.assertEqual([], stop_out[0], "stop cmd was not successful")

        # make change to config file (cpu from 2 to 3)
        cpu_string = '"cpu": "{0}"'
        sed_cmd = self.rhc.get_replace_str_in_file_cmd(cpu_string.format("2"),
                                           cpu_string.format("3"),
                                           config_file_path, sed_args='-i')
        sed_out = self.run_command(self.management_server, sed_cmd,
                                   su_root=True, default_asserts=True)
        self.assertEqual([], sed_out[0], "sed cmd was not successful")

        # check change is made
        grep_cmd = "{0} '{1}' {2}".format(test_constants.GREP_PATH,
                                      cpu_string.format("3"), config_file_path)

        grep_out = self.run_command(self.management_server, grep_cmd,
                                   su_root=True, default_asserts=True)
        self.assertTrue(self.is_text_in_list(cpu_string.format("3"),
                                     grep_out[0]), "change to config "
                                                   "file was not successful")

        # Start service
        start_out = self.run_command(self.management_server, start_cmd,
                                    su_root=True)
        self.assertEqual([], start_out[0], "start cmd was not successful")

        # Check service is active
        vm_status = self.run_command(self.management_server, active_cmd,
                                          su_root=True, default_asserts=True)

        self.assertEqual(['active'], vm_status[0], "vm service is not active")

    def initial_setup_11387(self):
        """
        LITPCDS_11387:
        Description:
            As a LITP user I want to specify additional filesystems
            for my VM running on the MS so that I can store persistent data
        """
        ms_vm_sg = "/ms/services/MS_VM1"
        storage_profile1 = "/infrastructure/storage/storage_profiles/" \
                           "sp11387"
        disk1_path = "/infrastructure/systems/sys1/disks/d1"

        disk1_dict = libvirt_test_data.DISK1_DATA
        ms_srv_dict = libvirt_test_data.MS_VM1_DATA

        # Create disk
        uuid = self.get_local_disk_uuid(self.management_server, "vg_root")
        self.execute_cli_create_cmd(self.management_server,
                                    disk1_path,
                                    "disk",
                                    props="name='{0}' size='{1}'" \
                                          " bootable='{2}' " \
                                          "uuid='{3}'".
                                    format(disk1_dict["DISK"]["name"],
                                           disk1_dict["DISK"]["size"],
                                           disk1_dict["DISK"]["bootable"],
                                           uuid),
                                    add_to_cleanup=False)

        # Create storage
        self.execute_cli_create_cmd(self.management_server,
                                    storage_profile1,
                                    "storage-profile",
                                    props="volume_driver='{0}'".
                                    format(
                                        disk1_dict["STORAGE_PROFILE"][
                                            "volume_driver"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    storage_profile1 + "/volume_groups/vg1",
                                    "volume-group",
                                    props="volume_group_name='{0}'".
                                    format(
                                        disk1_dict["VOLUME_GROUP"]["VG1"][
                                            "volume_group_name"]),
                                    add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    storage_profile1 +
                                    "/volume_groups/vg1/physical_devices/" \
                                    "pd11387",
                                    "physical-device",
                                    props="device_name='{0}'".
                                    format(
                                        disk1_dict["VOLUME_GROUP"][
                                            "VG1"]["physical_devices"][
                                            "device_name"]),
                                    add_to_cleanup=False)

        self.execute_cli_inherit_cmd(self.management_server,
                                     "/ms/storage_profile",
                                     storage_profile1, add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    storage_profile1 +
                                    "/volume_groups/vg1/file_systems/fs1",
                                    "file-system",
                                    props="type='{0}' mount_point='{1}' " \
                                          "size='{2}'".
                                    format(
                                        disk1_dict["VOLUME_GROUP"][
                                            "VG1"]["file_system"]["fs1"][
                                            "type"],
                                        disk1_dict["VOLUME_GROUP"][
                                            "VG1"]["file_system"]["fs1"][
                                            "mount_point"],
                                        disk1_dict["VOLUME_GROUP"][
                                            "VG1"]["file_system"]["fs1"][
                                            "size"]),
                                    add_to_cleanup=False)

        # Create vm disk
        self.execute_cli_create_cmd(self.management_server, ms_vm_sg +
                                    "/vm_disks/vmd1",
                                    "vm-disk",
                                    props="host_volume_group='{0}' " \
                                          "host_file_system='{1}' " \
                                          "mount_point='{2}'".
                                    format(
                                        ms_srv_dict["VM_DISK"][
                                            "VMD1"]["host_volume_group"],
                                        ms_srv_dict["VM_DISK"][
                                            "VMD1"]["host_file_system"],
                                        ms_srv_dict["VM_DISK"][
                                            "VMD1"]["mount_point"]),
                                    add_to_cleanup=False)

    def add_service_groups_expansion_kgb(self):
        """
        # description: Add 1 service group for usage in expansion KGB.
        """
        # Variables for the model paths
        vm_image_1_path = self.libvirt_info[
                              "software_images_path"] + "vm_image_1"
        vm_image_2_path = self.libvirt_info[
                              "software_images_path"] + "vm_image_2"

        lvtd_vm1 = libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA
        sg1_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_VM1"
        vm_service_1_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_1"

        #########################
        #                       #
        #  Service Group CS_VM1 #
        #                       #
        #########################

        # id: litpcds-7182
        # description: Create vm image 1 in the model
        # test_steps:
        #   step: Create vm image 1 in the model
        #   result: vm image 1 is created in the litp model
        self.execute_cli_create_cmd(self.management_server, vm_image_1_path,
                                    "vm-image",
                                    props="source_uri={0} name={1}".format(
                                        lvtd_vm1["VM IMAGE"]["image_url"],
                                        lvtd_vm1["VM IMAGE"]["image_name"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create a vm service
        # test_steps:
        #   step: Create a vm service
        #   result: vm service is created in the model
        self.execute_cli_create_cmd(self.management_server, vm_service_1_path,
                            "vm-service",
                            props="cpus={0} service_name={1} ram={2}" \
                                  " cleanup_command='{3}' " \
                                  "image_name={4} hostnames={5} " \
                                  "internal_status_check={6}".format(
                                lvtd_vm1["VM_SERVICE"]["cpus"],
                                lvtd_vm1["VM_SERVICE"]["service_name"],
                                lvtd_vm1["VM_SERVICE"]["ram"],
                                lvtd_vm1["VM_SERVICE"][
                                    "cleanup_command"],
                                lvtd_vm1["VM_SERVICE"]["image_name"],
                                lvtd_vm1["VM_SERVICE"]["hostnames"],
                                lvtd_vm1["VM_SERVICE"][
                                    "internal_status_check"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create a vcs clustered service
        # test_steps:
        #   step: Create a vcs clustered service in the model CS_VM1
        #   result: CS_VM1 is created in model
        self.execute_cli_create_cmd(self.management_server, sg1_path,
                        "vcs-clustered-service",
                        props="active={0} standby={1} name={2} " \
                              "online_timeout={3} dependency_list='{4}' " \
                              "node_list={5}".format(
                            lvtd_vm1["CLUSTER_SERVICE"]["active"],
                            lvtd_vm1["CLUSTER_SERVICE"]["standby"],
                            lvtd_vm1["CLUSTER_SERVICE"]["name"],
                            lvtd_vm1["CLUSTER_SERVICE"][
                                "online_timeout"],
                            lvtd_vm1["CLUSTER_SERVICE"][
                                "dependency_list"],
                            lvtd_vm1["CLUSTER_SERVICE"][
                                "node_list"]), add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create a ha config
        # test_steps:
        #   step: Create a ha-service-config in the model CS_VM1
        #   result: ha-service-config is created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                    sg1_path + "/ha_configs/service_config",
                                    "ha-service-config",
                                    props="restart_limit={0}".format(
                                        lvtd_vm1["HA_CONFIG"][
                                            "restart_limit"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description:  Add the service group to a vcs cluster
        # test_steps:
        #   step: Add service group to CS_VM1
        #   result: Service group is inherited onto CS_VM1
        self.execute_cli_inherit_cmd(self.management_server,
                                     sg1_path + "/applications/vm_service_1",
                                     vm_service_1_path, add_to_cleanup=False)

        # id: litpcds-7184
        # description: Configure vm aliases
        # test_steps:
        #   step: Configure VM aliases for CS_VM1
        #   result: VM aliases are added to CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/ms",
                                "vm-alias",
                                props="alias_names='{0}' address='{1}'".format(
                                    lvtd_vm1["VM_ALIAS"]["MS1"][
                                        "alias_names"],
                                    lvtd_vm1["VM_ALIAS"]["MS1"][
                                        "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/db1",
                                "vm-alias",
                                props="alias_names='{0}' address='{1}'".format(
                                    lvtd_vm1["VM_ALIAS"]["DB1"][
                                        "alias_names"],
                                    lvtd_vm1["VM_ALIAS"]["DB1"][
                                        "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/db2",
                                "vm-alias",
                                props="alias_names='{0}' address='{1}'".format(
                                    lvtd_vm1["VM_ALIAS"]["DB2"][
                                        "alias_names"],
                                    lvtd_vm1["VM_ALIAS"]["DB2"][
                                        "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path + "/vm_aliases/sfs",
                                "vm-alias",
                                props="alias_names='{0}' address='{1}'".format(
                                    lvtd_vm1["VM_ALIAS"]["SFS"][
                                        "alias_names"],
                                    lvtd_vm1["VM_ALIAS"]["SFS"][
                                        "address"]), add_to_cleanup=False)

        # id: litpcds-7179
        # description: Configure network interfaces
        # test_steps:
        #   step: Configure VM-network-interfaces for CS_VM1
        #   result: VM-network-interfaces are added to CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_network_interfaces/net1",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                    "host_device"],
                                lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                    "network_name"],
                                lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                                    "device_name"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_1_path + "/vm_network_interfaces/net_dhcp",
                        "vm-network-interface",
                        props="host_device='{0}' network_name='{1}' " \
                              "device_name='{2}'".format(
                            lvtd_vm1["NETWORK_INTERFACES"][
                                "NET_DHCP"]["host_device"],
                            lvtd_vm1["NETWORK_INTERFACES"][
                                "NET_DHCP"]["network_name"],
                            lvtd_vm1["NETWORK_INTERFACES"][
                                "NET_DHCP"]["device_name"]),
                                    add_to_cleanup=False)

        self.execute_cli_update_cmd(self.management_server,
            sg1_path + "/applications/vm_service_1/vm_network_interfaces/"
                       "net1",
            props="ipaddresses={0}".format(
                lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                    "ipaddresses"]))

        self.execute_cli_update_cmd(self.management_server,
            sg1_path +
                "/applications/vm_service_1/vm_network_interfaces/net_dhcp",
            props="ipaddresses={0}".format(
                lvtd_vm1["NETWORK_INTERFACES"][
                    "NET_DHCP"]["ipaddresses"]))

        # id: litpcds-7185
        # description: Define gateway for vm service
        # test_steps:
        #   step: Define gateway for CS_VM1
        #   result: Gateway is defined for CS_VM1
        self.execute_cli_update_cmd(self.management_server,
                vm_service_1_path + "/vm_network_interfaces/net1",
                props="gateway=192.168.0.1".format(
                    lvtd_vm1["NETWORK_INTERFACES"]["NET1"][
                        "gateway"]))

        # id: litpcds-7186
        # description: Configure yum repos
        # test_steps:
        #   step: Create yum repos for CS_VM1
        #   result: Yum repos are created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_1_path + "/vm_yum_repos/repo_3PP",
                                "vm-yum-repo",
                                props="name='{0}' base_url='{1}'".format(
                                    lvtd_vm1["YUM_REPOS"]["3PP"]["name"],
                                    lvtd_vm1["YUM_REPOS"]["3PP"][
                                        "base_url"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                                    vm_service_1_path +
                                    "/vm_yum_repos/repo_LITP",
                                    "vm-yum-repo",
                                    props="name='{0}' base_url='{1}'".format(
                                        lvtd_vm1["YUM_REPOS"]["LITP"]["name"],
                                        lvtd_vm1["YUM_REPOS"]["LITP"][
                                            "base_url"]), add_to_cleanup=False)
        # id: litpcds-7186
        # description: Configure vm packages
        # test_steps:
        #   step: Configure vm packages for CS_VM1
        #   result: VM packages are configured for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_packages/pkg_empty_rpm1",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm1["PACKAGES"]["PKG1"]["name"]), add_to_cleanup=False)

        # id: litpcds-7815
        # description: Configure nfs mounts
        # test_steps:
        #   step: Configure nfs mounts for CS_VM1
        #   result: nfs mounts are created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_1_path + "/vm_nfs_mounts/vm_nfs_mount_1",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' " \
                              "mount_options='{2}' ".format(
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT1"][
                                "device_path"],
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT1"][
                                "mount_point"],
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT1"][
                                "mount_options"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_1_path + "/vm_nfs_mounts/vm_nfs_mount_2",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' ".format(
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT2"][
                                "device_path"],
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT2"][
                                "mount_point"]), add_to_cleanup=False)

        self.execute_cli_create_cmd(self.management_server,
                        vm_service_1_path + "/vm_nfs_mounts/vm_nfs_mount_3",
                        "vm-nfs-mount",
                        props="device_path='{0}' mount_point='{1}' ".format(
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT3"][
                                "device_path"],
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT3"][
                                "mount_point"],
                            lvtd_vm1["NFS_MOUNTS"]["VM_MOUNT3"][
                                "mount_options"]), add_to_cleanup=False)

        # id: litpcds-6627
        # description: Configure ssh keys
        # test_steps:
        #   step: Configure ssh keys for CS_VM1
        #   result: ssh keys are created for CS_VM1
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_ssh_keys/ssh_key_rsa_11",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm1["SSH_KEYS"]["KEY1"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_ssh_keys/ssh_key_rsa_12",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm1["SSH_KEYS"]["KEY2"]["ssh_key"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_1_path + "/vm_ssh_keys/ssh_key_rsa_13",
                            "vm-ssh-key", props="ssh_key='{0}'".format(
                lvtd_vm1["SSH_KEYS"]["KEY3"]["ssh_key"]), add_to_cleanup=False)

        # id: torf-107476
        # title: test_02_p_create_vm_ram_mount_RH7_tmpfs
        # description: Test to verify that a user can create a tmpfs
        # file system using default values on RHEL 7 (Create a tmpfs on
        # my CS_VM1)
        # test_steps:
        #   step: Create VM with new vm-ram-mount item with a RHEL 7 system
        #   result: vm-ram-mount is created successfully with RHEL 7 system
        self.execute_cli_create_cmd(self.management_server, vm_service_1_path
                                    + "/vm_ram_mounts/vm_ram_mount_1",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    .format(
                                      lvtd_vm1["VM_RAM_MOUNT"]["type"],
                                      lvtd_vm1["VM_RAM_MOUNT"]
                                      ["mount_point"]),
                                    add_to_cleanup=False)

        #########################
        #                       #
        #  Service Group CS_VM2 #
        #                       #
        #########################

        lvtd_vm2 = libvirt_test_data.INITIAL_SERVICE_GROUP_2_DATA
        sg2_path = self.libvirt_info[
                       "cluster_services_path"] + "/CS_VM2"
        vm_service_2_path = self.libvirt_info[
                                "software_services_path"] + "vm_service_2"

        # id: litpcds-7182
        # description: Create vm image 2 in the model
        # test_steps:
        #   step: Create vm image 2 in the model
        #   result: vm image 2 is created in the litp model successfully
        self.execute_cli_create_cmd(self.management_server, vm_image_2_path,
                                "vm-image",
                                props="source_uri='{0}' name='{1}' ".format(
                                    libvirt_test_data.VM_IMAGES[
                                        "VM_IMAGE2"]["image_url"],
                                    libvirt_test_data.VM_IMAGES[
                                        "VM_IMAGE2"]["image_name"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create CS_VM2 vcs clustered service in litp model
        # test_steps:
        #   step: Create CS_VM2 in the model
        #   result: CS_VM2 is created in the litp model successfully
        self.execute_cli_create_cmd(self.management_server, sg2_path,
                                    "vcs-clustered-service",
                            props="active={0} standby={1} name='{2}' " \
                                  "online_timeout={3} dependency_list={4} " \
                                  "node_list='{5}' ".format(
                                lvtd_vm2["CLUSTER_SERVICE"]["active"],
                                lvtd_vm2["CLUSTER_SERVICE"]["standby"],
                                lvtd_vm2["CLUSTER_SERVICE"]["name"],
                                lvtd_vm2["CLUSTER_SERVICE"]["online_timeout"],
                                lvtd_vm2["CLUSTER_SERVICE"]["dependency_list"],
                                lvtd_vm2["CLUSTER_SERVICE_EXPANSION"][
                                    "node_list"]), add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create vm service 2 in litp model
        # test_steps:
        #   step: Create vm-service 2 in the model
        #   result: vm-service 2 is created in the litp model successfully
        self.execute_cli_create_cmd(self.management_server, vm_service_2_path,
                            "vm-service",
                            props="cleanup_command='{0}' " \
                                  "status_command='{1}' hostnames='{2}' " \
                                  "internal_status_check='{3}' " \
                                  "start_command='{4}' service_name='{5}' " \
                                  "stop_command='{6}' ram='{7}' " \
                                  "image_name='{8}' cpus='{9}'".format(
                                lvtd_vm2["VM_SERVICE"][
                                    "cleanup_command"],
                                lvtd_vm2["VM_SERVICE"][
                                    "status_command"],
                                lvtd_vm2["VM_SERVICE"]["hostnames"],
                                lvtd_vm2["VM_SERVICE"][
                                    "internal_status_check"],
                                lvtd_vm2["VM_SERVICE"][
                                    "start_command"],
                                lvtd_vm2["VM_SERVICE"]["service_name"],
                                lvtd_vm2["VM_SERVICE"]["stop_command"],
                                lvtd_vm2["VM_SERVICE"]["ram"],
                                lvtd_vm2["VM_SERVICE"]["image_name"],
                                lvtd_vm2["VM_SERVICE"]["cpus"]),
                                    add_to_cleanup=False)

        # id: litpcds-7180
        # description: Create ha service config for CS_VM2 in litp model
        # test_steps:
        #   step: Create ha service config for CS_VM2 in litp model
        #   result: ha service config is created in the litp successfully
        self.execute_cli_create_cmd(self.management_server,
            sg2_path + "/ha_configs/service_config", "ha-service-config",
            props="restart_limit={0} ".format(
                lvtd_vm2["HA_CONFIG"]["restart_limit"]), add_to_cleanup=False)

        # id: litpcds-7180
        # description: Add service group to CS_VM2 vcs clustered service
        # test_steps:
        #   step: Inherit vm-service 2 onto CS_VM2
        #   result: vm-service 2 is inherited onto CS_VM2 clustered service
        self.execute_cli_inherit_cmd(self.management_server,
                                     sg2_path + "/applications/vm_service_2",
                                     vm_service_2_path, add_to_cleanup=False)

        # id: litpcds-7184
        # description: Configure vm aliases
        # test_steps:
        #   step: Configure vm aliases for CS_VM2
        #   result: vm aliases are created for CS_VM2 successfully
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_aliases/db1",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm2["VM_ALIAS"]["DB1"][
                                    "alias_names"],
                                lvtd_vm2["VM_ALIAS"]["DB1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_aliases/ms",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm2["VM_ALIAS"]["MS1"][
                                    "alias_names"],
                                lvtd_vm2["VM_ALIAS"]["MS1"][
                                    "address"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_aliases/sfs",
                            "vm-alias",
                            props="alias_names='{0}' address='{1}'".format(
                                lvtd_vm2["VM_ALIAS"]["SFS"][
                                    "alias_names"],
                                lvtd_vm2["VM_ALIAS"]["SFS"][
                                    "address"]), add_to_cleanup=False)

        # id: litpcds-7179
        # description: Configure network interfaces
        # test_steps:
        #   step: Configure network interfaces for CS_VM2
        #   result: vm aliases are created for CS_VM2 successfully
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_network_interfaces/net2",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                                    "host_device"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                                    "network_name"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_network_interfaces/net3",
                            "vm-network-interface",
                            props="host_device='{0}' network_name='{1}' " \
                                  "device_name='{2}'".format(
                                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                                    "host_device"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                                    "network_name"],
                                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                                    "device_name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                        vm_service_2_path + "/vm_network_interfaces/net_dhcp",
                        "vm-network-interface",
                        props="host_device='{0}' network_name='{1}' " \
                              "device_name='{2}'".format(
                            lvtd_vm2["NETWORK_INTERFACES"][
                                "NET_DHCP"]["host_device"],
                            lvtd_vm2["NETWORK_INTERFACES"][
                                "NET_DHCP"]["network_name"],
                            lvtd_vm2["NETWORK_INTERFACES"][
                                "NET_DHCP"]["device_name"]),
                                    add_to_cleanup=False)
        self.execute_cli_update_cmd(self.management_server,
                sg2_path +
                    "/applications/vm_service_2/vm_network_interfaces/net2",
                props="ipaddresses={0}".format(
                    lvtd_vm2["NETWORK_INTERFACES"]["NET2"][
                        "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
                sg2_path +
                    "/applications/vm_service_2/vm_network_interfaces/net3",
                props="ipaddresses={0}".format(
                    lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                        "ipaddresses"]))
        self.execute_cli_update_cmd(self.management_server,
            sg2_path +
                "/applications/vm_service_2/vm_network_interfaces/net_dhcp",
            props="ipaddresses={0}".format(
                lvtd_vm2["NETWORK_INTERFACES"][
                    "NET_DHCP"]["ipaddresses"]))

        # id: litpcds-7185
        # description: Configure default gateway
        # test_steps:
        #   step: Define default gateway for CS_VM2
        #   result: Default gateway is defined for CS_VM2
        self.execute_cli_update_cmd(self.management_server,
            sg2_path + "/applications/vm_service_2/vm_network_interfaces/net3",
            props="gateway={0}".format(
                lvtd_vm2["NETWORK_INTERFACES"]["NET3"][
                    "gateway"]))

        # id: litpcds-7186
        # description: Configure YUM repos
        # test_steps:
        #   step: Configure yum repos for CS_VM2
        #   result: YUM repos are configured for CS_VM2
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_2_path + "/vm_yum_repos/repo_3PP",
                                "vm-yum-repo",
                                props="name='{0}' base_url='{1}'".format(
                                    lvtd_vm2["YUM_REPOS"]["3PP"]["name"],
                                    lvtd_vm2["YUM_REPOS"]["3PP"]["base_url"]),
                                    add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                                vm_service_2_path + "/vm_yum_repos/repo_LITP",
                                "vm-yum-repo",
                                props="name='{0}' base_url='{1}'".format(
                                    lvtd_vm2["YUM_REPOS"]["LITP"]["name"],
                                    lvtd_vm2["YUM_REPOS"]["LITP"][
                                        "base_url"]), add_to_cleanup=False)

        # id: litpcds-7186
        # description: Configure VM packages
        # test_steps:
        #   step: Configure VM Packages for CS_VM2
        #   result: VM packages are configured for CS_VM2
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_packages/pkg_empty_rpm2",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm2["PACKAGES"]["PKG2"]["name"]), add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server,
                            vm_service_2_path + "/vm_packages/pkg_empty_rpm3",
                            "vm-package", props="name='{0}'".format(
                lvtd_vm2["PACKAGES"]["PKG3"]["name"]), add_to_cleanup=False)

        # id: torf-107476
        # title: test_01_p_create_vm_ram_mount_RH6_tmpfs
        # description: Test to verify that a user can create a tmpfs
        # file system using default values on RHEL 6 (Create a tmpfs on
        # my CS_VM2)
        # test_steps:
        #   step: Create VM with new vm-ram-mount item with a RHEL 6 system
        #   result: vm-ram-mount is created successfully with RHEL 6 system
        self.execute_cli_create_cmd(self.management_server, vm_service_2_path
                                    + "/vm_ram_mounts/vm_ram_mount_2",
                                    "vm-ram-mount",
                                    props="type='{0}' mount_point='{1}' "
                                    "mount_options='{2}' "
                                    .format(
                                      lvtd_vm2["VM_RAM_MOUNT"]["type"],
                                      lvtd_vm2["VM_RAM_MOUNT"]
                                      ["mount_point"],
                                      lvtd_vm2["VM_RAM_MOUNT"]["mount_options"]
                                      ),
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
            Confirm vm custom scripts are present for TORF-180365.
            Confirm scripts were run successfully for TORF-180367
        :param node: node the check is ran on
        """

        lvtd_vm1 = libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA
        lvtd_vm3 = libvirt_test_data.INITIAL_SERVICE_GROUP_3_DATA
        lvtd_vm4 = libvirt_test_data.INITIAL_SERVICE_GROUP_4_DATA
        lvtd_vm5 = libvirt_test_data.INITIAL_SERVICE_GROUP_5_DATA
        lvtd_vm7 = libvirt_test_data.INITIAL_SERVICE_GROUP_SLES_DATA

        # Checking one VM
        hostnames_vm5 = lvtd_vm5["VM_SERVICE"]["hostnames"].split(",")
        hostname_vm5 = hostnames_vm5[0]
        ips_vm5 = lvtd_vm5["NETWORK_INTERFACES"]["NET11"]["ipaddresses"].\
            split(",")
        ip_vm5 = ips_vm5[0]

        script_data1 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-1',
                                       script_data1["custom_script_names"])
        self._confirm_vm_custom_script_ran(lvtd_vm1["VM_SERVICE"]["hostnames"],
                                           lvtd_vm1["NETWORK_INTERFACES"]
                                           ["NET1"]["ipaddresses"],
                                           script_data1["custom_script_names"])

        script_data3 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_3_DATA["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-3',
                                       script_data3["custom_script_names"])
        self._confirm_vm_custom_script_ran(lvtd_vm3["VM_SERVICE"]["hostnames"],
                                           lvtd_vm3["NETWORK_INTERFACES"]
                                           ["NET4"]["ipaddresses"],
                                           script_data3["custom_script_names"])

        script_data4 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_4_DATA["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-4',
                                       script_data4["custom_script_names"])
        self._confirm_vm_custom_script_ran(lvtd_vm4["VM_SERVICE"]["hostnames"],
                                           lvtd_vm4["NETWORK_INTERFACES"]
                                           ["NET7"]["ipaddresses"],
                                           script_data4["custom_script_names"])

        script_data5 = \
            libvirt_test_data.INITIAL_SERVICE_GROUP_5_DATA["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node,
                                       'test-vm-service-5',
                                       script_data5["custom_script_names"])
        self._confirm_vm_custom_script_ran(hostname_vm5, ip_vm5,
                                           script_data5["custom_script_names"])

        # TORF-271798: verify vm-service based on a rhel7.4 image.
        lvtd_vm6 = libvirt_test_data.INITIAL_SERVICE_GROUP_6_DATA
        script_data6 = lvtd_vm6["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node, 'test-vm-service-6',
                                               script_data6["custom_scripts"])
        self._confirm_vm_custom_script_ran(lvtd_vm6["VM_SERVICE"]["hostnames"],
                                           lvtd_vm6["NETWORK_INTERFACES"]
                                           ["NET1"]["ipaddresses"],
                                           script_data6["custom_scripts"])

        # TORF-406586 verify custom scipts work on sles
        script_data7 = lvtd_vm7["VM_CUSTOM_SCRIPT"]
        self._confirm_vm_custom_script_on_node(node, 'sles', script_data7
        ["custom_script_names"])
        self._confirm_vm_custom_script_ran(lvtd_vm7["VM_SERVICE"]["hostnames"],
                                           lvtd_vm7["NETWORK_INTERFACES"]
                                           ["NET1"]["ipaddresses"],
                                           script_data7["custom_script_names"])

    def _copy_dummy_file_to_node(self, node):
        """
        testset_story113124: test_07_p_remove_.part_vm_images
        :param node: (str) System to copy temporary file to
            /var/lib/libvirt/images directory
        :return: Nothing
        """
        local_file_path = os.path.join(os.path.dirname(__file__),
                                       'temp_doc_story_113124.txt')

        self.copy_file_to(node, local_file_path, '/var/lib/libvirt/images',
                          root_copy=True, add_to_cleanup=False)

        file_contents, _, _ = \
            self.run_command(node, 'ls /var/lib/libvirt/images/ -h',
                             su_root=True)

        self.assertTrue(self.is_text_in_list('temp_doc_story_113124.txt',
                                             file_contents))

    @attr('all', 'non-revert', 'libvirt_setup1', "LITPCDS-7180",
          "LITPCDS-7184", "LITPCDS-7185", "LITPCDS-7186", "LITPCDS-7516",
          "TORF-107476", "TORF-113124", "TORF-180365", "TORF-180367",
          "TORF-219762", "TORF-291089", "TORF-271798", "TORF-404805",
          "TORF-406586", "TORF-422322", "TORF-419532", "TORF-532848")
    def test_p_libvirt_initial_setup_plan(self):
        """
        @tms_id: litpcds_libvirt_tc01
        @tms_requirements_id: LITPCDS-7186, LITPCDS-7184,
        LITPCDS-7182, LITPCDS-7180, LITPCDS-6627, LITPCDS-7815, LITPCDS-7185,
        TORF-107476, LITPCDS-7516, LITPCDS-7815, LITPCDS-7179, LITPCDS-11405,
        LITPCDS-11387, TORF-113124, TORF-180365, TORF-180367, TORF-219762,
        TORF-291089, TORF-271798, TORF-404805, TORF-406586, TORF-422322,
        TORF-419532, TORF-532848

        @tms_title: Initial installation of multiple cluster services
            running virtual machines.
        @tms_description: Install various configurations of
            - VCS clustered services(litpcds_7180) parallel SGs failover SGs,
            - VM-services(litpcds_7182),
            - VM-packages(litpcds_7186),
            - Service inheritence (litpcds_7180),
            - VM-aliases (litpcds_7184),
            - VM-repos (litpcds_7186),
            - VM-zypper-repos (TORF-404805),
            - SSH keys (litpcds_6627),
            - NFS mount points (litpcds_7815),
            - Default Gateways(litpcds_7185),
            - VM-RAM-Mounts (torf_107476),
            - IPv6 addresses (litpcds_7516),
            - NFS sharing (litpcds_7815),
            - Network Config (litpcds_7179),
            - VM on MS (litpcds_11405),
            - VM starts after changes to files in instances dir (TORF-532848),
            - Remove Unused files from /var/lib/libvirt/images on
             nodes(torf-113124),
            - Additional Filesystems on MS (litpcds_11387),
            - VM custom scripts (torf-180365, torf-180367, TORF-406586)
            - VM cpu cpuset (TORF-219762)
            - VM cpu cpunodebind (TORF-291089)
            - Networking Config Version 1 file (TORF-271798)

        @tms_test_steps:
            @step: Import empty_rpm packages
            @result: empty_rpm packages 1 -> 9 are imported successfully

            @step: Copy SSH keys to the MS
            @result: SSH keys are added to .ssh file on MS

            @step: Copy VM Scripts to the MS
            @result: VM Scripts are added to /var/www/html/vm_scripts/ dir
                      on MS

            @step: Setup ebtables on peer nodes
            @result: Ebtables are established and saved on nodes

            @step: Create five sfs-file systems (litpcds_7815)
            @result: SFS-filesystems are created successfully in the litp

            @step: Create/ Update network interfaces on MS
            @result: MS network interfaces are updated on the MS

            @step: Create MS_VM1 on MS with vm_aliases, vm_network_interfaces,
            yum repos, vm_nfs_mounts, vm_ssh_keys, vm_ram_mounts
            @result: MS_VM1 is created

            @step: Setup CS_VM1, vm_image_1, vm-service-1, ha-configs,
            vm-aliases, vm-network-interfaces, yum_repos, vm_packages,
            vm_nfs_mounts, vm_ram_mounts, vm_ssh_keys, vm_custom_script,
            @result: CS_VM1 is created

            @step: Setup CS_VM2, vm_image_2, vm-service-2, ha-configs,
            vm-aliases, vm-network-interfaces, yum_repos, vm_packages,
            vm_nfs_mounts, vm_ram_mounts, vm_ssh_keys, cpuset
            @result: CS_VM2 is created

            @step: Setup CS_VM3, vm_image_3, vm-service-3, ha-configs,
            vm-aliases, vm-network-interfaces, yum_repos, vm_packages,
            vm_nfs_mounts, vm_ram_mounts, vm_ssh_keys, vm_custom_script,
            cpunodebind
            @result: CS_VM3 is created

            @step: Setup CS_VM4, vm-service-4, ha-configs, vm-aliases,
            vm-network-interfaces, yum_repos, vm_packages, vm_nfs_mounts,
            vm_ram_mounts, vm_ssh_keys, vm_custom_script
            @result: CS_VM4 is created

            @step: Setup CS_VM5, vm-service-5, ha-configs, vm-aliases,
            vm-network-interfaces, yum_repos, vm_packages, vm_nfs_mounts,
            vm_ram_mounts, vm_ssh_keys, vm_custom_script, cpuset
            @result: CS_VM5 is created

            @step: Setup CS_VM6, vm-service-6 based on rhel7.4 image,
            vm-aliases, vm-network-interfaces, vm_custom_scripts
            @result: CS_VM6 is created

            @step: Setup CS_SLES_VM, vm_image_sles, sles service, ha-configs,
            vm-aliases, vm-network-interfaces, zypper_repos, vm_packages,
            vm_ssh_keys, vm_custom_script,
            @result: CS_SLES_VM is created

            @step: Create disk, storage-profile, volume-group and
            physical-device in litp model
            @result: Disk, storage-profile, volume-group and
            physical-device items are created successfully in litp model

            @step: Copy temp_doc_story113124.txt file into
            /var/lib/libvirt/images/ directory on node
            @result: temp_doc_story113124.txt is copied to node

            @step: create and run plan
            @result: Plan is successfully created and running

            @step: While plan is running, stop plan at 'Copy VM image file'
            task
            @result: Plan stops after 'Copy VM image file' succeeded

            @step: litpd restart command is run
            @result: The litp model is restarted

            @step: create and run plan again, Plan stops after
            'Bring VCS service group Grp_CS_c1_CS_VM1 online' task is complete
            @result: Plan stops after 'Bring VCS service group
            Grp_CS_c1_CS_VM1 online'

            @step: litpd restart command is run
            @result: The litp model is restarted

            @step: create and run plan again
            @result: Plan completes successfully

            @step: Stop VM running on MS for one complete puppet cycle
            @result: Verify service is restarted by sub-sequent puppet cycle

            @step: Remove .live files from MS VM instances dir and
                   verify service can be started
            @result: service is started with missing .live files

            @step: Make a change to MS VM config.json and verify
                   service can be started
            @result: service is started with a change to config file

            @step: Verify sles service is running on primary node
            @result: sles is running on node1

            @step: Verify VM_ram_mounts are correctly setup
            @result: Validate VM-RAM-MOUNTS are correct

            @step: Verify VM_custom scripts are correctly setup
            @result: Validate VM-CUSTOM-SCRIPTS are correct

            @step: Verify temp_doc_story113124.txt file is removed
            @result: temp_doc_story113124.txt file is removed from
             /var/lib/libvirt/images directory

            @step: Verify CS_VM1 has access to all CPUs.
            @result: Validate CM_VM1 has access to all CPUs.

            @step: Verify CS_VM2 has access to vcpu-0 only.
            @result: Validate CM_VM2 has access to vcpu-0 only.

            @step: Verify CS_VM5 has access to vcpu-0 and vcpu-1.
            @result: Validate CM_VM5 has access to vcpu-0 and vcpu-1.

            @step: Verify CS_VM3 has cpuset set in domain XML with the
             value 0-1
            @result: Validate CS_VM3 has the value vcpu="0-1" in its domain
             XML configuration

            @step: Verify new network-config V1 file is created in addition to
                   existing meta-data file
            @result: network-config V1 and meta-data files are both located in
                     /var/lib/libvirt/instances/<vm-service> directory

            @step: Verify test-vm-service-6 is running on the active node of
                   CS_VM6
            @result: test-vm-service-6 is running on node1

            @step: Verify test-vm-service-6 is pingable (ipv4 and ipv6) from MS
            @result: Ping and ping6 commands are successful for
                     test-vm-service-6

        @tms_test_precondition:
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """

        # Setup the test case.
        primary_node = self.get_managed_node_filenames()[0]
        plan_timeout_mins = 100

        self.copy_rpms()
        self.copy_ssh_keys()
        self.copy_vm_scripts()
        self.setup_routing()
        self.setup_sfs_mounts()
        self.add_ms_service_group()
        self.add_service_groups()

        self.initial_setup_11387()
        # Create and execute plan again and expect it to succeed
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)

        # LITPCDS-11387 - TC01 idempotency Check
        self.assertTrue(self.wait_for_task_state(
            self.management_server,
            'Copy VM image file "{0}" to node "{1}" for instance "{2}" as part'
            ' of VM deploy'.format(
                libvirt_test_data.VM_IMAGE_FILE_NAME["VM_IMAGE1"],
                self.management_server,
                libvirt_test_data.MS_VM1_DATA["VM_SERVICE"]["service_name"]),
            test_constants.PLAN_TASKS_SUCCESS,
            timeout_mins=plan_timeout_mins
        ))

        self.restart_litpd_service(self.management_server)

        # TORF-113124: test_07_p_remove_.part_vm_images
        # Adding dummy file to /var/lib/libvirt/images
        self._copy_dummy_file_to_node(primary_node)

        # Create and execute plan, expect it to succeed
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)

        # LITPCDS-8851 - TC01 idempotency Check
        self.assertTrue(self.wait_for_task_state(
            self.management_server,
            'Bring VCS service group "Grp_CS_c1_CS_VM1" online',
            test_constants.PLAN_TASKS_RUNNING,
            ignore_variables=False,
            timeout_mins=plan_timeout_mins
        ))

        self.restart_litpd_service(self.management_server)

        self.wait_for_vcs_service_group_online(primary_node,
                                               "Grp_CS_c1_CS_VM1", 1,
                                               wait_time_mins=10)

        # Create and execute plan, expect it to succeed
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)

        self.assertTrue(self.wait_for_plan_state(
            self.management_server,
            test_constants.PLAN_COMPLETE,
            plan_timeout_mins
        ))

        self.stop_ms_vm(libvirt_test_data.MS_VM1_DATA)
        self.test_ms_vm_start_after_instances_dir_file_changes()

        lvtd_vm1 = libvirt_test_data.INITIAL_SERVICE_GROUP_1_DATA
        lvtd_vm2 = libvirt_test_data.INITIAL_SERVICE_GROUP_2_DATA
        lvtd_vm3 = libvirt_test_data.INITIAL_SERVICE_GROUP_3_DATA
        lvtd_vm4 = libvirt_test_data.INITIAL_SERVICE_GROUP_4_DATA
        lvtd_vm5 = libvirt_test_data.INITIAL_SERVICE_GROUP_5_DATA
        lvtd_vm6 = libvirt_test_data.INITIAL_SERVICE_GROUP_6_DATA
        lvtd_vm7 = libvirt_test_data.INITIAL_SERVICE_GROUP_SLES_DATA
        lvtd_ms_vm1 = libvirt_test_data.MS_VM1_DATA

        # TORF-404805 TC23 sles service is running
        self.get_service_status(primary_node, lvtd_vm7["VM_SERVICE"]
        ["service_name"])

        # TORF - 180365 Test case 03 verification of vm custom scripts.
        # TORF - 180367 Test case 04 verification of proper run of 5 scripts
        # TORF-406586 TC04 Custom script functionality on sles
        self._check_vm_custom_script(primary_node)

        # TORF- 107476 Test case 01 verification of mount point
        self._check_mount_conf(lvtd_vm2["VM_SERVICE"]["hostnames"],
                               lvtd_vm2["NETWORK_INTERFACES"]["NET2"]
                               ["ipaddresses"],
                               lvtd_vm2["VM_RAM_MOUNT"]["type"],
                               lvtd_vm2["VM_RAM_MOUNT"]["mount_point"])

        # TORF- 107476 Test case 02 verification of mount point
        self._check_mount_conf(lvtd_vm1["VM_SERVICE"]["hostnames"],
                               lvtd_vm1["NETWORK_INTERFACES"]["NET1"]
                               ["ipaddresses"],
                               lvtd_vm1["VM_RAM_MOUNT"]["type"],
                               lvtd_vm1["VM_RAM_MOUNT"]["mount_point"])

        # TORF- 107476 Test case 03 verification of mount point
        self._check_mount_conf(lvtd_vm3["VM_SERVICE"]["hostnames"],
                               lvtd_vm3["NETWORK_INTERFACES"]["NET4"]
                               ["ipaddresses"],
                               lvtd_vm3["VM_RAM_MOUNT"]["type"],
                               lvtd_vm3["VM_RAM_MOUNT"]["mount_point"])

        # TORF- 107476 Test case 04 verification of mount point
        self._check_mount_conf(lvtd_ms_vm1["VM_SERVICE"]["hostnames"],
                               lvtd_ms_vm1["NETWORK_INTERFACE"]["NET1"]
                               ["ipaddresses"],
                               lvtd_ms_vm1["VM_RAM_MOUNT"]["type"],
                               lvtd_ms_vm1["VM_RAM_MOUNT"]["mount_point"])

        # TORF-113124: Verify the dummy file is removed
        file_contents, _, _ = \
            self.run_command(primary_node, 'ls /var/lib/libvirt/images/ -h',
                             su_root=True)
        self.assertFalse(self.is_text_in_list('temp_doc_story_113124.txt',
                                              file_contents))

        # TORF-219762: Verify vm cpu affinity with undefined cpuset property
        lvtd_vm1_nodelist = lvtd_vm1['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_vm_cpu_affinity(self.model['nodes'],
                                    lvtd_vm1['VM_SERVICE']['service_name'],
                                    lvtd_vm1_nodelist, 'yy')

        # TORF-219762: Verify vm cpu affinity with cpuset property set to "0"
        lvtd_vm2_nodelist = lvtd_vm2['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_vm_cpu_affinity(self.model['nodes'],
                                    lvtd_vm2['VM_SERVICE']['service_name'],
                                    lvtd_vm2_nodelist, 'y-')

        # TORF-219762: Verify vm cpu affinity with cpuset property set to "0-1"
        lvtd_vm5_nodelist = lvtd_vm5['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_vm_cpu_affinity(self.model['nodes'],
                                    lvtd_vm5['VM_SERVICE']['service_name'],
                                    lvtd_vm5_nodelist, 'yy')

        # TORF-291089: Verify vm cpu affinity with unset cpunodebind property
        # has no cpuset attribute in its vcpu element
        self.assert_domain_vcpuset(
                self.model['nodes'],
                lvtd_vm1['VM_SERVICE']['service_name'],
                lvtd_vm1_nodelist, None,
                standby=int(lvtd_vm1['CLUSTER_SERVICE']['standby']),
                vcs_name='Grp_CS_c1_{0}'.format(lvtd_vm1['CLUSTER_SERVICE'][
                                                    'name']))

        # TORF-291089: Verify vm cpu affinity with cpunodebind property with
        # a value of "0" has a vcpu element with the attribute cpuset="0-1"
        lvtd_vm3_nodelist = lvtd_vm3['CLUSTER_SERVICE']['node_list'].split(',')
        self.assert_domain_vcpuset(
                self.model['nodes'],
                lvtd_vm3['VM_SERVICE']['service_name'],
                lvtd_vm3_nodelist, '0-1',
                standby=int(lvtd_vm3['CLUSTER_SERVICE']['standby']),
                vcs_name='Grp_CS_c1_{0}'.format(lvtd_vm3['CLUSTER_SERVICE'][
                                                    'name']))

        # TORF-271798 TC_01: Verify meta-data and network-config files are both
        # present for a rhel6 based vm-service deployed on MS
        vm_service_name = lvtd_ms_vm1['VM_SERVICE']['service_name']
        self.confirm_vm_config_files_on_node(self.management_server,
                                             vm_service_name)

        # TORF-271798 TC_02,TC_03,TC_07: Verify meta-data and network-config
        # files are both present for a rhel6 based vm-service deployed under
        #  PL&FO SGs and for a rhel7.4 based vm-service deployed under a FO SG
        peer_nodes = {}
        for node in self.model['nodes']:
            peer_nodes[node['url'].split('/')[-1]] = node['name']

        lvtd_vm4_nodelist = lvtd_vm4['CLUSTER_SERVICE']['node_list'].split(',')
        lvtd_vm6_nodelist = lvtd_vm6['CLUSTER_SERVICE']['node_list'].split(',')
        lvtd_vm7_nodelist = lvtd_vm7['CLUSTER_SERVICE']['node_list'].split(',')

        vm_services_dict = \
            {lvtd_vm1['VM_SERVICE']['service_name']: lvtd_vm1_nodelist,
             lvtd_vm3['VM_SERVICE']['service_name']: lvtd_vm3_nodelist,
             lvtd_vm4['VM_SERVICE']['service_name']: lvtd_vm4_nodelist,
             lvtd_vm5['VM_SERVICE']['service_name']: lvtd_vm5_nodelist,
             lvtd_vm6['VM_SERVICE']['service_name']: lvtd_vm6_nodelist,
             lvtd_vm7['VM_SERVICE']['service_name']: lvtd_vm7_nodelist
             }

        for vm_service_name, vm_nodelist in vm_services_dict.items():
            for node in vm_nodelist:
                node_hostname = peer_nodes[node]
                self.confirm_vm_config_files_on_node(node_hostname,
                                                     vm_service_name)

        # TORF-271798 TC_07: assert rhel7.4 based vm service is up and running
        sg6_name = 'Grp_CS_c1_CS_VM6'
        sg6_states = self.run_vcs_hagrp_display_command(primary_node, sg6_name,
                                                        "State")
        online_nodes = [sg_state['SYSTEM'] for sg_state in sg6_states['State']
                        if "|ONLINE|" in sg_state['VALUE']]
        self.assertEqual(len(online_nodes), int(lvtd_vm6['CLUSTER_SERVICE'][
            'active']), 'Service Group {0} is not ONLINE on all active nodes'.
                         format(sg6_name))
        for node in online_nodes:
            self.get_service_status_cmd(node, vm_service_name,
                                        assert_running=True)

        # TORF-271798: ping rhel7.4 based vm-service and make sure reachable
        vm6_networks = lvtd_vm6["NETWORK_INTERFACES"]
        vm6_ipv4 = vm6_networks["NET1"]["ipaddresses"]
        self.assertTrue(self.is_ip_pingable(self.management_server, vm6_ipv4,
                                            timeout_secs=30),
                        "VM ip {0} cannot be pinged".format(vm6_ipv4))

        vm6_ipv6 = vm6_networks["NET2"]["ipv6addresses"].split("/")[0]
        self.assertTrue(self.is_ip_pingable(self.management_server, vm6_ipv6,
                                            ipv4=False, timeout_secs=30),
                        "VM ipv6 {0} cannot be pinged".format(vm6_ipv6))

    @attr('expansion', 'non-revert', 'libvirt_setup_expansion', "LITPCDS-7180",
          "LITPCDS-7184", "LITPCDS-7185", "LITPCDS-7186", "LITPCDS-7516",
          "TORF-107476")
    def test_p_libvirt_initial_expansion_setup_plan(self):
        """
        @tms_id: litpcds_libvirt_expansion_tc01
        @tms_requirements_id: LITPCDS-7186, LITPCDS-7184,
        LITPCDS-7182, LITPCDS-7180, LITPCDS-6627, LITPCDS-7815, LITPCDS-7185,
        TORF-107476, LITPCDS-7516, LITPCDS-7815, LITPCDS-7179

        @tms_title: Initial installation of a 1 node PL cluster service
            running virtual machines.
        @tms_description: Install various configurations of
            - VCS clustered services(litpcds_7180) parallel SG,
            - VM-services(litpcds_7182),
            - VM-packages(litpcds_7186),
            - Service inheritence (litpcds_7180),
            - VM-aliases (litpcds_7184),
            - VM-repos (litpcds_7186),
            - SSH keys (litpcds_6627),
            - NFS mount points (litpcds_7815),
            - Default Gateways(litpcds_7185),
            - VM-RAM-Mounts (torf_107476),
            - IPv6 addresses (litpcds_7516),
            - NFS sharing (litpcds_7815),
            - Network Config (litpcds_7179),

        @tms_test_steps:
            @step: Import empty_rpm packages
            @result: empty_rpm packages 1 -> 8 are imported successfully

            @step: Copy SSH keys to the MS
            @result: SSH keys are added to .ssh file on MS

            @step: Setup ebtables on peer nodes
            @result: Ebtables are established and saved on nodes

            @step: Create five sfs-file systems (litpcds_7815)
            @result: SFS-filesystems are created successfully in the litp

            @step: Create/ Update network interfaces on MS
            @result: MS network interfaces are updated on the MS

            @step: Setup CS_VM1, vm_image_1, vm-service-1, ha-configs,
            vm-aliases, vm-network-interfaces, yum_repos, vm_packages,
            vm_nfs_mounts, vm_ram_mounts, vm_ssh_keys
            @result: CS_VM1 is created

            @step: Setup CS_VM2, vm_image_2, vm-service-2, ha-configs,
            vm-aliases, vm-network-interfaces, yum_repos, vm_packages,
            vm_nfs_mounts, vm_ram_mounts, vm_ssh_keys
            @result: CS_VM2 is created

            @step: Create disk, storage-profile, volume-group and
            physical-device in litp model
            @result: Disk, storage-profile, volume-group and
            physical-device items are created successfully in litp model

            @step: create and run plan again
            @result: Plan completes successfully

        @tms_test_precondition:
            - A 1 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        # Setup the test case.
        self.copy_rpms()
        self.copy_ssh_keys()
        self.setup_routing()
        self.setup_sfs_mounts()
        self.add_service_groups_expansion_kgb()
        # Create and execute plan and expect it to succeed
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)
        plan_timeout_mins = 90

        self.assertTrue(self.wait_for_plan_state(
            self.management_server,
            test_constants.PLAN_COMPLETE,
            plan_timeout_mins
        ))
