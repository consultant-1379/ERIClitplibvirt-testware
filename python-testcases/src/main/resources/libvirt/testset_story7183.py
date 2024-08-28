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
@summary:   Agile: LITPCDS-7183
'''
import os
import re

import test_constants
from litp_generic_test import GenericTest, attr
import libvirt_test_data


class Story7183(GenericTest):
    """
    As a LITP User I want to upgrade the libvirt adaptor package so that I can
    keep up to date with the latest delivery
    """

    def setUp(self):
        """
        Description:
            Runs before every single test
        Actions:
            1. Call the super class setup method
            2. Set up variables used in the tests
        Results:
            The super class prints out diagnostics and variables
            are defined which are required in the tests.
        """
        super(Story7183, self).setUp()

        # Get the MS name and nodes from the host.properties file
        self.management_server = self.get_management_node_filename()
        self.primary_node = self.get_managed_node_filenames()[0]
        self.secondary_node = self.get_managed_node_filenames()[1]

        # Location where RPMs to be used are stored
        self.rpm_src_dir = os.path.dirname(os.path.realpath(__file__)) + \
            "/rpms/"
        # Repo where rpms will be installed
        self.repo_dir_litp = test_constants.LITP_PKG_REPO_DIR

        self.adaptor_package = 'ERIClitpmnlibvirt_CXP9031529'

        # Current assumption is that only 1 VCS cluster will exist
        self.vcs_cluster_url = self.find(self.management_server,
                                    "/deployments", "vcs-cluster")[-1]
        self.cluster_id = self.vcs_cluster_url.split("/")[-1]

        # Get version of adaptor package installed on the primary node
        self.primary_initial_version = self._get_versions()[0]
        self.primary_initial_package = (self.adaptor_package + '-' +
            self.primary_initial_version + '.rpm')

        self.upgrade_version = "99.99.99"
        self.package_string = "{0}-{1}-1.noarch.rpm"
        self.upgrade_package = self.package_string.format(
            self.adaptor_package, self.upgrade_version)
        self.downgrade_version = "0.0.1"
        self.downgrade_package = self.package_string.format(
            self.adaptor_package, self.downgrade_version)

        self.update_adaptor_node_one_re = (r'^Update\slibvirt\sadaptor.+'
            r'node\s"{0}"$'.format(self.primary_node))
        self.update_adaptor_node_two_re = (r'^Update\slibvirt\sadaptor.+'
            r'node\s"{0}"$'.format(self.secondary_node))

        self.rpmrebuild_package = "rpmrebuild-2.11-1.noarch.rpm"

    def tearDown(self):
        """
        Description:
            Runs after every single test
        Actions:
            -
        Results:
            The super class prints out diagnostics and variables
        """
        super(Story7183, self).tearDown()

    def set_litp_libvirt_logger_level(self, level):
        """
        Sets the debug level on the litp_libvirt_logging config file on each
            managed node

        Args: level (string): the desired log level for the litp_libvirt
            adaptor
        Returns: -
        """
        litp_libvirt_logger_file = "/etc/litp_libvirt_logging.conf"

        for node in [self.primary_node, self.secondary_node]:
            cmd = "sed -i 's/^level=.*/level={0}/' {1}".format(level,
                                                   litp_libvirt_logger_file)

            stdout, stderr, r_code = self.run_command(node, cmd, su_root=True)
            self.assertEqual(0, r_code)
            self.assertEqual([], stdout)
            self.assertEqual([], stderr)

    ## Worker methods for story 7183
    def _get_rpmrebuild_cmd(self, new_version):
        """
        Get the RPM rebuild command to build RPM again with a new version
        """
        return ('/usr/bin/rpmrebuild -p --notest-install '
                '--directory=/tmp '
                '--change-spec-preamble='
                '\'sed -e "s/^Version:.*/Version: {0}"/\' '
                '{1}/{2}'.format(new_version, self.repo_dir_litp,
                                 self.primary_initial_package))

    def _run_rpmrebuild_adaptor(self):
        """
        This method sets up the upgrade and downgrade adaptor rpms on the MS.
        It is neccessary to run before the tests in this class as it allows us
        to generate an identical RPM of the current adaptor RPM (each time the
        tests are run)but with a new version. The tool used is rpmrebuild,
        available at http://rpmrebuild.sourceforge.net/

        Steps:
            Copy to and install the rpmrebuild RPM on the MS
            Issue a command to generate an upgrade version RPM
            Issue a command to generate a downgrade version RPM
        """
        filelist = [self.get_filelist_dict(self.rpm_src_dir + \
                                           self.rpmrebuild_package, "/tmp/")]
        self.copy_filelist_to(self.management_server, filelist,
                              add_to_cleanup=True, root_copy=True)
        self.install_rpm_on_node(self.management_server, "/tmp/" + \
                                 self.rpmrebuild_package)

        cmd = self._get_rpmrebuild_cmd(self.upgrade_version)
        _, _, rc = self.run_command(self.management_server, cmd, su_root=True)
        self.assertEqual(rc, 0)

        cmd = self._get_rpmrebuild_cmd(self.downgrade_version)
        _, _, rc = self.run_command(self.management_server, cmd, su_root=True)
        self.assertEqual(rc, 0)

    def _createrepo_command(self):
        """
        Run the createrepo on the litp repo on the MS
        """
        cmd = self.rhc.get_createrepo_cmd(
            test_constants.LITP_PKG_REPO_DIR + '/')
        _, stderr, returnc = self.run_command(self.management_server, cmd,
                                              su_root=True)
        self.assertEqual([], stderr)
        self.assertEqual(0, returnc)

    def stop_puppet_service_on_nodes(self, peer_nodes):
        """
        Stop puppet service on MS and on supplied list of peer nodes.
        """
        self.stop_service(self.management_server, 'puppet')
        for node in peer_nodes:
            self.stop_service(node, 'puppet')

    def start_puppet_service_on_nodes(self, peer_nodes):
        """
        Start puppet service on supplied list of peer nodes and on MS.
        """
        for node in peer_nodes:
            self.start_service(node, 'puppet')
        self.start_service(self.management_server, 'puppet')

    def _yum_clean_check_commands(self):
        """
        Stop puppet on MS and peer nodes to avoid yum issue TORF-114913.
        Run commands on both nodes:
        1) yum clean all
        2) yum history new
        3) rpm --rebuilddb
        4) yum check-update
        Start puppet on peer nodes and MS.
        """
        self.stop_puppet_service_on_nodes(
                         [self.primary_node, self.secondary_node])

        for node in [self.primary_node, self.secondary_node]:
            cmd = self.rhc.get_yum_cmd("clean all")
            _, stderr, returnc = self.run_command(node, cmd, su_root=True)
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

            cmd = self.rhc.get_yum_cmd("history new")
            _, stderr, returnc = self.run_command(node, cmd, su_root=True)
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

            cmd = "/bin/rpm --rebuilddb"
            _, stderr, returnc = self.run_command(node, cmd, su_root=True)
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

            cmd = self.rhc.get_yum_cmd("check-update")
            _, stderr, returnc = self.run_command(node, cmd, su_root=True)
            self.assertEqual([], stderr)
            # check-update returns status 100 if packages available, and 0 if
            # not: http://www.linuxcommand.org/man_pages/yum8.html
            self.assertTrue(returnc in [0, 100])

        self.start_puppet_service_on_nodes(
                          [self.primary_node, self.secondary_node])

    def _test_clustered_service_running(self, cs_id, expected):
        """
        Test that each clustered service is online the correct number of times
        as given in the configuration constants.
        """
        cs_grp_name = self.vcs.generate_clustered_service_name(cs_id,
                                                               self.cluster_id)
        # Get output from the hagrp -state command
        cmd = self.vcs.get_hagrp_state_cmd()
        hagrp_output, stderr, return_code = self.run_command(self.primary_node,
                                                             cmd, su_root=True)

        self.assertEqual(0, return_code)
        self.assertEqual([], stderr)

        # Search in the output from hagrp and count
        # the number of times that it is online
        reg_ex = cs_grp_name + r'\s+State\s+\w+\s+\|ONLINE\|$'
        online_cnt = 0
        for line in hagrp_output:
            if re.search(reg_ex, line):
                online_cnt = online_cnt + 1
        # Check that the group is online the correct number of times
        self.assertEqual(int(expected), online_cnt)

    def _import_package(self, pkg_to_add):
        """
        Run the cli import command to import the given package
        """
        self.execute_cli_import_cmd(self.management_server,
                                    '/tmp/noarch/' + pkg_to_add,
                                    self.repo_dir_litp)

    def _get_package_version_yum(self, package_type, node):
        """
        Return the package version on a node by running the "yum list" command
        and then parse the output to return the version only
        """
        cmd = self.rhc.get_yum_cmd("list {0} {1}".format(package_type,
                                                         self.adaptor_package))
        stdout, stderr, returnc = self.run_command(node, cmd)
        self.assertNotEqual([], stdout)
        # If there is no 'available' package then the command will return an
        # error and a status code of 1
        if returnc == 1:
            self.assertTrue("Error: No matching Packages to list" in stderr)
        else:
            self.assertEqual([], stderr)
            self.assertEqual(0, returnc)

        # If the package is not present return None as version
        if not self.is_text_in_list(self.adaptor_package, stdout):
            return None

        line = [l for l in stdout if l.startswith(self.adaptor_package)][0]
        version_release = line.split()[1]
        version = version_release.split('-')[0]

        return version

    def _get_versions(self):
        """
        Return the 'available' and 'installed' adaptor RPM versions on each
        node
        """
        self._yum_clean_check_commands()

        sc1_installed_version = self._get_package_version_yum('installed',
                                                          self.primary_node)
        sc1_available_version = self._get_package_version_yum('available',
                                                          self.primary_node)
        sc2_installed_version = self._get_package_version_yum('installed',
                                                          self.secondary_node)
        sc2_available_version = self._get_package_version_yum('available',
                                                          self.secondary_node)
        return (sc1_installed_version, sc1_available_version,
                sc2_installed_version, sc2_available_version)

    def _get_plan_subtasks(self):
        """
        Run the show_plan command and parse to output to return the task
        descriptions
        """
        plan_stdout, _, _ = \
            self.execute_cli_showplan_cmd(self.management_server)
        parsed_plan = self.cli.parse_plan_output(plan_stdout)
        subtasks = []
        for task in parsed_plan.values():
            for subtask in task.values():
                subtasks.append(''.join(subtask['DESC'][1:]))
        return subtasks

    @staticmethod
    def _check_adaptor_task(re_string, subtasks):
        """
        Method to check if the compiled re_sting is in the plan descriptions
        """
        compiled_re = re.compile(re_string)
        for subtask in subtasks:
            if compiled_re.match(subtask):
                return True

        return False

    def _check_tasks(self, upgrade_tasks=False):
        """
        Check the tasks show with the show_plan command.
        Case 1: Ensure that the upgrade tasks are not shown
        Case 2: Check that the lock tasks and upgrade tasks are shown
        """
        subtasks = self._get_plan_subtasks()

        if upgrade_tasks:
            self.assertTrue('Lock VCS on node "{0}"'.format(
                self.primary_node) in subtasks)
            self.assertTrue('Unlock VCS on node "{0}"'.format(
                self.primary_node) in subtasks)
            self.assertTrue('Lock VCS on node "{0}"'.format(
                self.secondary_node) in subtasks)
            self.assertTrue('Unlock VCS on node "{0}"'.format(
                self.secondary_node) in subtasks)
            self.assertEqual(True, self._check_adaptor_task(
                self.update_adaptor_node_one_re, subtasks))
            self.assertEqual(True, self._check_adaptor_task(
                self.update_adaptor_node_two_re, subtasks))
        else:
            self.assertEqual(False, self._check_adaptor_task(
                self.update_adaptor_node_one_re, subtasks))
            self.assertEqual(False, self._check_adaptor_task(
                self.update_adaptor_node_two_re, subtasks))

    def _check_rpm_not_yet_installed(self, new_available_version):
        """
        Check the new version of the adaptor is available on each node but not
        yet installed. This check is run after the new version of the adaptor
        RPM has been installed in the MS litp repo, but before the plan is run.
        Therefore a new version should be available to each node, but not yet
        installed.
        """
        sc1_installed_version, sc1_available_version, sc2_installed_version, \
        sc2_available_version = self._get_versions()
        self.assertEqual(self.primary_initial_version, sc1_installed_version)
        self.assertEqual(new_available_version, sc1_available_version)
        self.assertEqual(self.primary_initial_version, sc2_installed_version)
        self.assertEqual(new_available_version, sc2_available_version)

    def _check_initial_setup(self):
        """
        Check the version of the adaptor on each node initially
        1: The version installed on each node should be: the same on the other
           node; not equal to the upgrade or downgrade versions
        2: There should be no 'available' version on each node
        """
        sc1_installed_version, sc1_available_version, sc2_installed_version, \
        sc2_available_version = self._get_versions()
        self.assertEqual(self.primary_initial_version, sc1_installed_version)
        self.assertEqual(None, sc1_available_version)
        self.assertEqual(self.primary_initial_version, sc2_installed_version)
        self.assertEqual(None, sc2_available_version)

        self.assertNotEqual(self.primary_initial_version, self.upgrade_version)
        self.assertNotEqual(self.primary_initial_version,
                            self.downgrade_version)

    @attr('all', 'non-revert', 'story7183', 'story7183_tc01')
    def test_story7183_01_p_adaptor_rpm_independant_upgrade_prepare(self):
        """
        @tms_id: litpcds_7183_tc01
        @tms_requirements_id: LITPCDS-7183
        @tms_title: Prepare for independent RPM package Upgrade

        @tms_description: To ensure that it is possible to upgrade the libvirt
        adaptor automatically by importing a newer version of the rpm in to
        the litp repository. This test will validate that correct tasks
        are generated.

        @tms_test_steps:
            @step: Copy newer version of RPM package onto the MS
            @result: MS has new RPM package copied over

            @step: Verify the RPM has not been installed yet
            @result: RPM has not been installed

            @step: Create plan to trigger the adaptor package upgrade
            @result: Plan is created and adaptor package is upgraded

            @step: Validate the adaptor upgrade task is in plan
            @result: Plan has adaptor upgrade in plan

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        self._check_initial_setup()

        self._import_package(self.upgrade_package)

        self._check_rpm_not_yet_installed(self.upgrade_version)

        self.execute_cli_createplan_cmd(self.management_server)
        self._check_tasks(upgrade_tasks=True)

    @attr('all', 'non-revert', 'story7183', 'story7183_tc02')
    def test_story7183_02_p_adaptor_rpm_independant_upgrade_verify(self):
        """
        @tms_id: litpcds_7183_tc02
        @tms_requirements_id: LITPCDS-7183
        @tms_title: Verify independent RPM package Upgrade

        @tms_description: To ensure that it is possible to upgrade the
        libvirt adaptor automatically by importing a newer version of the
        rpm in to the litp repository. Test case 1 makes an updated rpm
        available. This test verifies that the upgrade is successful after a
        plan has been executed.

        @tms_test_steps:
            @step: Verify the new version of RPM package is installed on both
            nodes
            @result: Validate the RPM package is installed on nodes

            @step: Verify the VM service is online
            @result: VM service is online

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        sc1_installed_version, sc1_available_version, sc2_installed_version, \
        sc2_available_version = self._get_versions()
        self.assertEqual(self.upgrade_version, sc1_installed_version)
        self.assertEqual(None, sc1_available_version)
        self.assertEqual(self.upgrade_version, sc2_installed_version)
        self.assertEqual(None, sc2_available_version)

        latest_sg1_data = libvirt_test_data.UPDATED_SERVICE_GROUP_1_DATA
        latest_sg2_data = libvirt_test_data.INITIAL_SERVICE_GROUP_2_DATA
        latest_sg3_data = libvirt_test_data.UPDATED_SERVICE_GROUP_3_DATA
        latest_sg4_data = libvirt_test_data.UPDATED_SERVICE_GROUP_4_DATA
        latest_sg5_data = libvirt_test_data.UPDATED_SERVICE_GROUP_5_DATA

        sg1_expected = latest_sg1_data["CLUSTER_SERVICE"]["active"]
        sg2_expected = latest_sg2_data["CLUSTER_SERVICE"]["active"]
        sg3_expected = latest_sg3_data["CLUSTER_SERVICE"]["active"]
        sg4_expected = latest_sg4_data["CLUSTER_SERVICE"]["active"]
        sg5_expected = latest_sg5_data["CLUSTER_SERVICE"]["active"]

        self._test_clustered_service_running('CS_VM1', sg1_expected)
        self._test_clustered_service_running('CS_VM2', sg2_expected)
        self._test_clustered_service_running('CS_VM3', sg3_expected)
        self._test_clustered_service_running('CS_VM4', sg4_expected)
        self._test_clustered_service_running('CS_VM5', sg5_expected)

        # Need to set the logging level back to debug after adaptor upgrade
        self.set_litp_libvirt_logger_level("DEBUG")

    @attr('all', 'non-revert', 'story7183', 'story7183_tc03')
    def test_story7183_03_p_adaptor_rpm_independant_upgrade_cancel(self):
        """
        @tms_id: litpcds_7183_tc03
        @tms_requirements_id: LITPCDS-7183
        @tms_title: Cancel independent RPM package Upgrade

        @tms_description: To ensure that it is possible to cancel an upgrade
        of the libvirt adaptor rpm as such by removing the updated rpm from
        the litp repository and issuing the create plan command once more

        @tms_test_steps:
            @step: Copy and import the newer version of the RPM package
            onto the MS
            @result: RPM package is copied over

            @step: Verify the RPM package is not installed yet
            @result: RPM package is not installed

            @step: Create plan to trigger the adaptor package upgrade
            @result: Plan is created and adaptor package is upgraded

            @step: Manually remove the RPM upgrade from the LITP repo
            @result: Package is removed from the LITP repo

            @step: Validate there is no adaptor upgrade task
            @result: No upgrade task is generated

            @step: Validate the initial setup is still the same
            @result: Initial setup has not been configured

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """
        self._check_initial_setup()

        self._import_package(self.upgrade_package)

        self._check_rpm_not_yet_installed(self.upgrade_version)

        self.execute_cli_createplan_cmd(self.management_server)
        self._check_tasks(upgrade_tasks=True)

        path = "{0}/{1}".format(self.repo_dir_litp, self.upgrade_package)
        self.assertTrue(self.mv_file_on_node(self.management_server, path,
                                             '/tmp', su_root=True))

        self._createrepo_command()

        self.execute_cli_createplan_cmd(self.management_server)

        self._check_tasks()

        self._check_initial_setup()

    @attr('all', 'non-revert', 'story7183', 'story7183_tc04')
    def test_story7183_04_n_adaptor_rpm_independant_downgrade(self):
        """
        @tms_id: litpcds_7183_tc04
        @tms_requirements_id: LITPCDS-7183
        @tms_title: Independent RPM adaptor package Downgrade

        @tms_description: To ensure that should the libvirt adaptor rpm in
        the litp repository be an older version, that no downgrade tasks are
        created

        @tms_test_steps:
            @step: Copy and import the older version of the RPM package
            onto the MS
            @result: RPM package is copied over

            @step: Verify the RPM package is not installed yet
            @result: RPM package is not installed

            @step: Remove current version package from the MS
            @result: RPM package has been removed

            @step: Ensure the file is removed correctly from the repo
            @result: RPM package is removed

            @step: Validate there is no adaptor upgrade task
            @result: No upgrade task is generated

            @step: Validate the initial setup is still the same
            @result: Initial setup has not been configured

            @step: Copy the current version back into the repo
            @result: Repo is copied back into the repo

        @tms_test_precondition:
            - testset_libvirt_initial_setup has run
            - A 2 node LITP cluster installed
            - A network with a bridge setup
            - A network with DHCP setup
            - VM images are present on the MS
        @tms_execution_type: Automated
        """

        #Taken from old version in order to run the tests.
        self._run_rpmrebuild_adaptor()

        self._check_initial_setup()

        self._import_package(self.downgrade_package)

        self._check_rpm_not_yet_installed(None)

        cmd = self.rhc.get_move_cmd("{0}/{1}".format(self.repo_dir_litp,
                                     self.primary_initial_package), "/tmp")
        _, _, rc = self.run_command(self.management_server, cmd, su_root=True)
        self.assertEqual(rc, 0)
        self._createrepo_command()

        self.execute_cli_createplan_cmd(self.management_server)

        self._check_tasks()

        self._check_initial_setup()

        path = "/tmp/{0}".format(self.primary_initial_package)
        self.assertTrue(self.mv_file_on_node(self.management_server, path,
                                             self.repo_dir_litp, su_root=True))

        self._createrepo_command()
