"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     Jan 2017
@author:    Iacopo Isimbaldi
@summary:   Testset to deploy libvirt vcs functionality
"""
from litp_generic_test import GenericTest, attr
import test_constants
import libvirt_test_data


class Libvirtupdate5(GenericTest):
    """
    TORF-159934: As a LITP user I want to be able to modify subnet
    definition in the model and have the Libvirt plugin act accordingly
    """

    def setUp(self):
        super(Libvirtupdate5, self).setUp()

        self.management_server = self.get_management_node_filename()
        self.vcs_cluster_url = self.find(self.management_server,
                                         '/deployments', 'vcs-cluster')[-1]
        self.nodes_urls = self.find(self.management_server,
                                    self.vcs_cluster_url,
                                    'node')
        self.networks_url = self.find(self.management_server,
                                      '/infrastructure',
                                      'collection-of-network')[-1]

    def tearDown(self):
        super(Libvirtupdate5, self).tearDown()

    # TORF 159934
    # Interfaces on ms server of "Services" network in KBG
    def create_ovlp_network(self):
        """
        Create a new network called ovlp.

        This method will create a bond interface on MS and a bridge interface
        on each node, so it's possible to attach the vm_services

        It also assigns an ip address from ovlp network to the vm_service
        "CS_VM2"

        :return: None
        """

        # Hardcoded eth interfaces to be sure to create a bond interface on
        # the "services" network of the vapp
        ms_if1 = {
            "NAME": "eth5",
            "MAC": "00:50:56:00:01:03"
        }
        ms_if2 = {
            "NAME": "eth4",
            "MAC": "00:50:56:00:01:02"
        }

        # Create a bond network
        network_url = self.networks_url + \
                      '/{0}'.format(
                          libvirt_test_data.OVLP_MS_DATA['network_name'])
        network_props = "name='{0}' subnet='{1}'".format(
            libvirt_test_data.OVLP_MS_DATA['network_name'],
            libvirt_test_data.OVLP_MS_DATA['subnet'])
        self.execute_cli_create_cmd(self.management_server, network_url,
                                    "network", network_props,
                                    add_to_cleanup=False)

        # Add MS to the network with a bond device with 2 interfaces
        ms_net_url = "/ms/network_interfaces"

        eth1_url_ms = ms_net_url + "/{0}".format(ms_if1['NAME'])
        eth1_props_ms = "device_name='{0}' macaddress='{1}' master='{2}'" \
            .format(ms_if1['NAME'], ms_if1['MAC'],
                    libvirt_test_data.OVLP_MS_DATA['bond_link'])

        eth2_url_ms = ms_net_url + "/{0}".format(ms_if2['NAME'])
        eth2_props_ms = "device_name='{0}' macaddress='{1}' master='{2}'" \
            .format(ms_if2['NAME'], ms_if2['MAC'],
                    libvirt_test_data.OVLP_MS_DATA['bond_link'])

        bond_url_ms = ms_net_url + \
                      "/{0}".format(
                          libvirt_test_data.OVLP_MS_DATA['bond_link'])
        bond_props_ms = "ipaddress='{0}' network_name='{1}' " \
                        "device_name='{2}'".format(
            libvirt_test_data.OVLP_MS_DATA['ip'],
            libvirt_test_data.OVLP_MS_DATA['network_name'],
            libvirt_test_data.OVLP_MS_DATA['bond_link'])

        self.execute_cli_create_cmd(self.management_server, bond_url_ms,
                                    "bond",
                                    bond_props_ms, add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, eth1_url_ms, "eth",
                                    eth1_props_ms, add_to_cleanup=False)
        self.execute_cli_create_cmd(self.management_server, eth2_url_ms, "eth",
                                    eth2_props_ms, add_to_cleanup=False)

        # Hardcoded eth interfaces to be sure to use the "services" network
        # of the vapp
        n_if1 = {
            "NAME": "eth1",
            "MAC": ["00:50:56:00:00:61",
                    "00:50:56:00:00:62"]
        }

        # Create all the interfaces on the nodes needed by the vm_service
        for node, i in zip(self.nodes_urls, xrange(
                0, len(self.nodes_urls))):
            eth1_url_n = node + "/network_interfaces/{0}".format(n_if1['NAME'])
            eth1_props_n = "device_name='{0}' macaddress='{1}' bridge='{2}'" \
                .format(n_if1['NAME'], n_if1['MAC'][i],
                        libvirt_test_data.OVLP_N_DATA['br_link'])

            bridge_url_n = node + \
                           "/network_interfaces/{0}".format(
                               libvirt_test_data.OVLP_N_DATA['br_link'])
            bridge_props_n = "device_name={0} ipaddress={1} network_name={2}" \
                .format(libvirt_test_data.OVLP_N_DATA['br_link'],
                        libvirt_test_data.OVLP_N_DATA['ovlp_ips'][i],
                        libvirt_test_data.OVLP_MS_DATA['network_name'])

            self.execute_cli_create_cmd(self.management_server, eth1_url_n,
                                        "eth",
                                        eth1_props_n, add_to_cleanup=False)
            self.execute_cli_create_cmd(self.management_server, bridge_url_n,
                                        "bridge",
                                        bridge_props_n, add_to_cleanup=False)

        # Add an ip address of ovlp to the vm service
        inf_url_vm = "/software/services/vm_service_2/vm_network_interfaces/" \
                     "{0}".format(libvirt_test_data.OVLP_VM_DATA["ovlp_name"])
        inf_props_vm = "host_device='{0}' network_name='{1}'" \
                       " device_name='{2}'".format(
            libvirt_test_data.OVLP_N_DATA['br_link'],
            libvirt_test_data.OVLP_MS_DATA['network_name'],
            libvirt_test_data.OVLP_VM_DATA['link'])

        ip_url_vm = "/deployments/d1/clusters/c1/services/{0}/applications/" \
                    "{1}/vm_network_interfaces/{2}".format(
            libvirt_test_data.OVLP_VM_DATA["service_name"],
            libvirt_test_data.OVLP_VM_DATA["application_name"],
            libvirt_test_data.OVLP_VM_DATA["ovlp_name"])

        ip_props_vm = "ipaddresses={0}".format(
            libvirt_test_data.OVLP_VM_DATA['ip'])

        self.execute_cli_create_cmd(self.management_server, inf_url_vm,
                                    "vm-network-interface", inf_props_vm,
                                    add_to_cleanup=False)
        self.execute_cli_update_cmd(
            self.management_server, ip_url_vm, ip_props_vm)

    @attr('all', 'non-revert', 'story159927', 'story159927_update_plan_5')
    def test_p_libvirt_update_plan_5(self):
        """
        @tms_id: torf_159927_tc10
        @tms_requirements_id: TORF-159927

        @tms_title: Update network subnet on 2 node cluster
        @tms_description: Test designed around Regular Networking KGB suite,
        due to no Networking expansion KGB exists. Hence, this test updates
        the subnet of a network configured with bonds and bridges,
        in a 2 node cluster deployment.

        @tms_test_steps:
            @step: Backup all networking files and find free interface on MNs
            and MS in cluster
            @result: Free interfaces from MS and MNs are stored in dictionary

            @step: Create new network with interfaces and bonds on MS and MNs
            using IP address range of litp_management network
            @result: New Network with interfaces and bonds between MS and nodes
            are created

            @step: Create/ Run Plan
            @result: Plan is created and ran

            @step:  Update litp_management network to allocate more IPs from
            newly created network in previous plan
            @result: litp_management network is updated to allocate more IPs
            from newly created network

            @step: Update relevant interfaces with bridges and bonds to allow
            new IP range to be allocated to relevant network
            @result: Relevant network interfaces and bridges are updated

            @step: Add sysparam item in the model for idempotent testing
            @result:

            @step: Create/ Run plan again
            @result: Plan is created and ran

            @step: After bridge update to relevant network run litpd restart
            @result: Sysparam tasks do not exist for first node whereas
            networking updates do meaning networking tasks are idempotent.

            @step: Create/ Run plan again
            @result: Plan is created and ran to completion

            @step: Ensure network connectivity is restored after plan completes
            and model and nodes are updated
            @result: Network credentials are updated

        @tms_test_precondition: N/A

        @tms_execution_type: Automated
        """

        self.create_ovlp_network()

        # Create and run the plan
        self.execute_cli_createplan_cmd(self.management_server)
        self.execute_cli_showplan_cmd(self.management_server)
        self.execute_cli_runplan_cmd(self.management_server)
        self.assertTrue(self.wait_for_plan_state(self.management_server,
                                                 test_constants.PLAN_COMPLETE))

        # Create a snapshot for testcase restore
        self.execute_and_wait_createsnapshot(self.management_server,
                                             add_to_cleanup=False,
                                             remove_snapshot=True)
