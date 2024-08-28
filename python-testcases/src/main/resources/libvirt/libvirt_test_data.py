import test_constants

####################################################
# DATA FOR SETUP OF SFS SHARES USED IN VM SERVICES #
####################################################

FILESYSTEM_DATA = dict()
FILESYSTEM_DATA["FS1"] = {"fs_path": "/vx/story7815-mount_1", "fs_size": "10M", "allowed_clients": "192.168.0.0/24", "mount_option": "rw,no_root_squash"}
FILESYSTEM_DATA["FS2"] = {"fs_path": "/vx/story7815-mount_2", "fs_size": "10M", "allowed_clients": "192.168.0.0/24", "mount_option": "rw,no_root_squash"}
FILESYSTEM_DATA["FS3"] = {"fs_path": "/vx/story7815-mount_3", "fs_size": "10M", "allowed_clients": "192.168.0.0/24", "mount_option": "rw,no_root_squash"}
FILESYSTEM_DATA["FS4"] = {"fs_path": "/vx/story7815-mount_4", "fs_size": "10M", "allowed_clients": "192.168.0.0/24", "mount_option": "rw,no_root_squash"}
FILESYSTEM_DATA["FS5"] = {"fs_path": "/vx/story7815-mount_5", "fs_size": "10M", "allowed_clients": "192.168.0.0/24", "mount_option": "rw,no_root_squash"}

##############################################
# VM IMAGES USED BY LIBVIRT IN THIS KGB ONLY #
##############################################

##############################################################################################################
## NOTE: vm_test_image-5 is the RHEl7.4 image; Rest are RHEL7.2 images;
##############################################################################################################
VM_IMAGES = dict()
VM_IMAGES["VM_IMAGE1"] = {"image_url": "http://ms1/images/vm_test_image-1-1.0.6.qcow2", "image_name": "vm-image-1"}
VM_IMAGES["VM_IMAGE2"] = {"image_url": "http://ms1/images/vm_test_image-2-1.0.8.qcow2", "image_name": "vm-image-2"}
VM_IMAGES["VM_IMAGE3"] = {"image_url": "http://ms1/images/vm_test_image-3-1.0.8.qcow2", "image_name": "vm-image-3"}
VM_IMAGES["VM_IMAGE4"] = {"image_url": "http://ms1/images/vm_test_image-4-1.0.8.qcow2", "image_name": "vm_image_4"}
VM_IMAGES["VM_IMAGE5"] = {"image_url": "http://ms1/images/vm_test_image-5-1.0.7.qcow2", "image_name": "vm-image-5"}
VM_IMAGES["VM_IMAGE_SLES"] = {"image_url": "http://ms1/images/vm_test_image-SLES15-1.24.3.qcow2", "image_name": "vm-image-sles"}

#########################
# VM IMAGE FILE NAMES	#
#########################
VM_IMAGE_FILE_NAME = {"VM_IMAGE1": "vm_test_image-1-1.0.6.qcow2",
                      "VM_IMAGE2": "vm_test_image-2-1.0.8.qcow2",
                      "VM_IMAGE3": "vm_test_image-3-1.0.8.qcow2",
                      "VM_IMAGE4": "vm_test_image-4-1.0.8.qcow2",
                      "VM_IMAGE_SLES": "vm_test_image-SLES15-1.24.3.qcow2"}

########################
# SERVICE GROUP 1 DATA #
########################
INITIAL_SERVICE_GROUP_1_DATA = dict()
INITIAL_SERVICE_GROUP_1_DATA["VM IMAGE"] = VM_IMAGES["VM_IMAGE1"]
INITIAL_SERVICE_GROUP_1_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_VM1",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "",
                                                   "node_list": "n1"
                                                   }
INITIAL_SERVICE_GROUP_1_DATA["HA_CONFIG"] = {"restart_limit": "1",
                                             "status_timeout": "100"
                                             }
INITIAL_SERVICE_GROUP_1_DATA["VM_SERVICE"] = {"cpus": "1",
                                              "service_name": "test-vm-service-1",
                                              "ram": "256M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-1 force-stop",
                                              "image_name": VM_IMAGES["VM_IMAGE1"]["image_name"],
                                              "hostnames": "tmo-vm-1",
                                              "internal_status_check": "on"
                                              }
INITIAL_SERVICE_GROUP_1_DATA["VM_ALIAS"] = {"MS1": {"alias_names": "ms1",
                                                    "address": "192.168.0.42"
                                                    },
                                            "DB1": {"alias_names": "dbsvc1",
                                                    "address": "111.222.1.2"
                                                    },
                                            "DB2": {"alias_names": "dbsvc2.foo-domain.tld",
                                                    "address": "111.222.1.3"
                                                    },
                                            "SFS": {"alias_names": "nas4",
                                                    "address": "172.16.30.14"
                                                    }
                                            }
INITIAL_SERVICE_GROUP_1_DATA["NETWORK_INTERFACES"] = {"NET1": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.2",
                                                               "gateway":"192.168.0.1"
                                                               },
                                                      "NET_DHCP": {"host_device": "br6",
                                                                   "network_name": "dhcp_network",
                                                                   "device_name": "eth1",
                                                                   "ipaddresses": "dhcp"
                                                                   }
                                                      }
INITIAL_SERVICE_GROUP_1_DATA["YUM_REPOS"] = {"3PP": {"name": "3PP",
                                                     "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                                     },
                                             "LITP": {"name": "LITP",
                                                      "base_url": "http://ms1/litp"
                                                      }
                                             }
INITIAL_SERVICE_GROUP_1_DATA["PACKAGES"] = {"PKG1": {"name": "empty_rpm1"}}
INITIAL_SERVICE_GROUP_1_DATA["NFS_MOUNTS"] = {"VM_MOUNT1": {"device_path": "nas4:/vx/story7815-mount_1",
                                                            "mount_point": "/tmp/mount_1",
                                                            "mount_options": "retrans=8,rsize=32768"
                                                            },
                                              "VM_MOUNT2": {"device_path": "172.16.30.14:/vx/story7815-mount_2",
                                                            "mount_point": "/tmp/mount_2"
                                                            },
                                              "VM_MOUNT3": {"device_path": "172.16.30.14:/vx/story7815-mount_3",
                                                            "mount_point": "/tmp/mount_3",
                                                            "mount_options": "retrans=6,rsize=16384"
                                                            }
                                              }
INITIAL_SERVICE_GROUP_1_DATA["SSH_KEYS"] = {"KEY1": {"ssh_key":"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEApPdyRQeCoh36f8ayxgJLg6nZvWD3nc2kV1T+6xXY6dFTlR4TBjkj5pMq6fGNzSZBfzCB7LvBz0DxLWgKYhIumt1QTFDAszULwfst94XqHd+HSAEBQ0+cZ5VQmjXtt7OpklofsSsC4SilWCJW2g1G4Lo7W5BP/qeBj/yGvE9qKnctZ26OtuO7R1fcpOIXC5KFT9cecvROijCBE90HQYLzt1VlDQn2DRqOH7w11S5abNskZrrpM2lhXorKEozORP9WrCuZW1PEnQDRGAzqKiaAw/5q/3m/L72NtUyiXzi5+92ZgvvxXSOernpeIocoPbUMVcma945dfm8FxC60/UB//Q== root@atvts1852"},
                                            "KEY2": {"ssh_key":"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvB3N6WOJ9qAQjGWfwpXvUWYWz8A7Ezwv/pihAYCbObDo71Ycsa3kuz2gUK9uS6Pw5DlNFAbFPk4zi/52Oj+frw4W56HnStxe13zB7ca4N0HFHMEE1QOyZ/wzv+DubwoKuz8I5yA9BD5Oli3DJXVVqxhjxRjiOQ7xs+CHsqHxzgulSJpWmbkli7BoVXsCoFN0oQmfXc7liqCciCZCvPwc+mKtJfH4oozKajwfcvyRyQhd1hqFwsaa7dxKuLww0mT6V+scduwCMVSuJH0b34Qow4ZR0XWwHGIzCf5XApypZPcuaEhRBtqpWysujlnYrkieprGn/nKna/t6USJdC9uPWQ== root@atvts1852"},
                                            "KEY3": {"ssh_key":"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8g3u0guI42gog7dFNBoBOtXZ+/okb+HZoTj37Iz5c60+qpehKHTdqnewxT+BX1h/GZg0CKb8+tR3GFqifBDAVXqwHfpQnGMVsHeItM09XDoYvRjWkkDAwpT3OLdEKfNmu+0rJEwvrx5w+aDsvrzfrDUGNWTBSogpXKLL1kCsCsfCNdU42xy6GygzgqyL/lo5RFBTbuDkI0Y4xSzwTxb8CPjbPcughBedWxAI0aYGh+IcV+fP2reMVeDyFqPeKiXcdL+8kWAb+pkR1WUr46dKxP/PkQGkpVEXxsjtDwisNJDFb3wC8pF3G2T5L3And01rhMg5hhLpCZn3yWSZUvjU6Q== root@atvts1852"}
                                            }
INITIAL_SERVICE_GROUP_1_DATA["VM_RAM_MOUNT"] = {"type": "tmpfs",
                                                "mount_point": "/mnt/data",
                                                "mount_options": "size=512M,noexec,nodev,nosuid"
                                                }
INITIAL_SERVICE_GROUP_1_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname1.sh,csfname2.sh,csfname3.sh,csfname4.sh,csfname7.sh"
                                                    }
###########################
# SERVICE GROUP SLES DATA #
###########################

INITIAL_SERVICE_GROUP_SLES_DATA = dict()
INITIAL_SERVICE_GROUP_SLES_DATA["VM IMAGE"] = VM_IMAGES["VM_IMAGE_SLES"]
INITIAL_SERVICE_GROUP_SLES_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_SLES_VM",
                                                   "online_timeout": "1500",
                                                   "dependency_list": "",
                                                   "node_list": "n1"
                                                   }
INITIAL_SERVICE_GROUP_SLES_DATA["HA_CONFIG"] = {"status_timeout": "15"
                                             }
INITIAL_SERVICE_GROUP_SLES_DATA["VM_SERVICE"] = {"cpus": "2",
                                              "service_name": "sles",
                                              "ram": "4096M",
                                              "image_name": VM_IMAGES["VM_IMAGE_SLES"]["image_name"],
                                              "hostnames": "sles-vm",
                                              "internal_status_check": "on"
                                              }
INITIAL_SERVICE_GROUP_SLES_DATA["VM_ALIAS"] = {"MS1": {"alias_names": "ms1",
                                                    "address": "192.168.0.42"
                                                    },
                                            "NCM": {"alias_names": "n1-sles",
                                                    "address": "192.168.0.139"
                                                    }
                                            }
INITIAL_SERVICE_GROUP_SLES_DATA["NETWORK_INTERFACES"] = {"NET1": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.139",
                                                               "gateway":"192.168.0.1"
                                                               }
                                                      }
INITIAL_SERVICE_GROUP_SLES_DATA["ZYPPER_REPOS"] = {"NCM": {"name": "ncm",
                                                     "base_url": "http://ms1/ncm"}
                                             }
INITIAL_SERVICE_GROUP_SLES_DATA["PACKAGES"] = {"PKG1": {"name": 'empty_rpm9'}}
INITIAL_SERVICE_GROUP_SLES_DATA["SSH_KEYS"] = {"KEY21": {"ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCRsHzi+1jEthhukKYK+HC5bdJJi6rSTfR84JaWX1aIapSOJYBebQ76H3maPY/C+POOBVYFKlHE5tsLARiwLn6JO1Z6DEva2+Bel+jry7uq7+JmrqLxyAESwqK9+4t61clndHFopBv0ZmdrosTDOEQav+hjDmLajtEhrAS8BD+SfV6lKTdGEoMBQ9FU/L8AAzMJ2i4ksMjebqRAhJMVzeLyd1FK3s3zt2RTp/fRX6qGVRiX2ciGqv1POm43WlI+ot7fOK3t4S/aDCLJBl0LWISZGGMg1e/QGBsZy75dxmg0eihQprd/s5/UXOhQJ/y7sT7vHm8im28inu1V8mMIA53l cloud-user"}
                                               }
INITIAL_SERVICE_GROUP_SLES_DATA["VM_CUSTOM_SCRIPT"] = {"custom_script_names": "csfname2.sh,csfname3.sh,csfname4.sh,csfname5.sh,csfname6.sh"
                                                    }

########################
# SERVICE GROUP 2 DATA #
########################
INITIAL_SERVICE_GROUP_2_DATA = dict()
INITIAL_SERVICE_GROUP_2_DATA["VM IMAGE"] = VM_IMAGES["VM_IMAGE2"]
INITIAL_SERVICE_GROUP_2_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_VM2",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "",
                                                   "node_list": "n2"
                                                   }
INITIAL_SERVICE_GROUP_2_DATA["CLUSTER_SERVICE_EXPANSION"] = {"node_list": "n1"}
INITIAL_SERVICE_GROUP_2_DATA["VM_SERVICE"] = {"cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-2 force-stop",
                                              "status_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-2 status",
                                              "hostnames": "tmo-vm-2",
                                              "internal_status_check": "off",
                                              "start_command": "/bin/systemctl start test-vm-service-2",
                                              "service_name": "test-vm-service-2",
                                              "stop_command": "/bin/systemctl stop test-vm-service-2",
                                              "ram": "144M",
                                              "image_name": "vm-image-2",
                                              "cpus": "1",
                                              "cpuset": "0"
                                              }
INITIAL_SERVICE_GROUP_2_DATA["HA_CONFIG"] = {"restart_limit": "1",
                                             "status_timeout": "100"
                                             }
INITIAL_SERVICE_GROUP_2_DATA["VM_ALIAS"] = {"MS1": {"alias_names": "ms1",
                                                    "address": "192.168.0.42"
                                                    },
                                            "DB1": {"alias_names": "dbsvc1",
                                                    "address": "111.222.1.2"
                                                    },
                                            "SFS": {"alias_names": "nas4",
                                                    "address": "172.16.30.14"
                                                    }
                                            }
INITIAL_SERVICE_GROUP_2_DATA["NETWORK_INTERFACES"] = {"NET2": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.3"
                                                               },
                                                      "NET3": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth1",
                                                               "ipaddresses": "192.168.0.4",
                                                               "gateway": "192.168.0.1"
                                                               },
                                                      "NET_DHCP": {"host_device": "br6",
                                                                   "network_name": "dhcp_network",
                                                                   "device_name": "eth2",
                                                                   "ipaddresses": "dhcp"
                                                                   }
                                                      }
INITIAL_SERVICE_GROUP_2_DATA["YUM_REPOS"] = {"3PP":  {"name": "3PP",
                                                      "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                                      },
                                             "LITP": {"name": "LITP",
                                                      "base_url": "http://ms1/litp"
                                                      }
                                             }
INITIAL_SERVICE_GROUP_2_DATA["PACKAGES"] = {"PKG2": {"name": "empty_rpm2"},
                                            "PKG3": {"name": "empty_rpm3"}
                                            }
INITIAL_SERVICE_GROUP_2_DATA["VM_RAM_MOUNT"] = {"type": "tmpfs",
                                                "mount_point": "/mnt/data",
                                                "mount_options": "size=128M,noexec,nodev,nosuid"
                                                }

########################
# SERVICE GROUP 3 DATA #
########################

INITIAL_SERVICE_GROUP_3_DATA = dict()
INITIAL_SERVICE_GROUP_3_DATA["VM IMAGE"] = VM_IMAGES["VM_IMAGE3"]
INITIAL_SERVICE_GROUP_3_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "1",
                                                   "name": "CS_VM3",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "",
                                                   "node_list": "n1,n2"
                                                   }
INITIAL_SERVICE_GROUP_3_DATA["VM_SERVICE"] = {"cpus": "1",
                                              "service_name": "test-vm-service-3",
                                              "ram": "144M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-3 force-stop",
                                              "image_name": "vm-image-1",
                                              "hostnames": "tmo-vm-3",
                                              "internal_status_check": "on",
                                              "cpunodebind": "0"
                                              }
INITIAL_SERVICE_GROUP_3_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc1",
                                                    "address": "111.222.1.2"
                                                    },
                                            "DB2": {"alias_names": "dbsvc2.foo-domain.tld",
                                                    "address": "111.222.1.3"
                                                    },
                                            "DB3": {"alias_names": "dbsvc3.foo-domain.tld,dbsvc3",
                                                    "address": "111.222.1.4"
                                                    },
                                            "DB4": {"alias_names": "dbsvc4.foo-domain.tld,dbsvc4.foo-domain2.tld2,dbsvc4",
                                                    "address": "111.222.1.5"
                                                    },
                                            "MS1": {"alias_names": "ms1",
                                                    "address": "192.168.0.42"
                                                    },
                                            "SFS": {"alias_names": "nas4",
                                                    "address": "172.16.30.14"
                                                    }
                                            }
INITIAL_SERVICE_GROUP_3_DATA["NETWORK_INTERFACES"] = {"NET4": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.5"
                                                               },
                                                      "NET5": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth1",
                                                               "ipaddresses": "192.168.0.6"
                                                               },
                                                      "NET6": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth2",
                                                               "ipaddresses": "192.168.0.7",
                                                               "gateway": "192.168.0.1"
                                                               },
                                                      "NET32": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth4",
                                                                "ipaddresses": "192.168.0.45",
                                                                "ipv6addresses": "2001:db8:85a3::7516:18"
                                                                },
                                                      "NET33": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth5",
                                                                "ipaddresses": "192.168.0.46",
                                                                "ipv6addresses": "2001:db8:85a3::7516:19"
                                                                },
                                                      "NET34": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth6",
                                                                "ipaddresses": "192.168.0.47",
                                                                "ipv6addresses": "2001:db8:85a3::7516:20"
                                                                },
                                                      "NET_DHCP": {"host_device": "br6",
                                                                   "network_name": "dhcp_network",
                                                                   "device_name": "eth3",
                                                                   "gateway6": "2001:db8:85a3::7516:10",
                                                                   "ipv6addresses": "2001:db8:85a3::7516:11/48",
                                                                   "ipaddresses": "dhcp"
                                                                   }
                                                      }
INITIAL_SERVICE_GROUP_3_DATA["YUM_REPOS"] = {"3PP":  {"name": "3PP",
                                                      "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                                      },
                                             "LITP": {"name": "LITP",
                                                      "base_url": "http://ms1/litp"
                                                      }
                                             }
INITIAL_SERVICE_GROUP_3_DATA["PACKAGES"] = {"PKG4": {"name": "empty_rpm4"},
                                            "PKG5": {"name": "empty_rpm5"}
                                            }
INITIAL_SERVICE_GROUP_3_DATA["NFS_MOUNTS"] = {"VM_MOUNT4": {"device_path": "nas4:/vx/story7815-mount_4",
                                                            "mount_point": "/tmp/mount_4",
                                                            "mount_options": "retrans=3,wsize=16384"
                                                            }
                                              }
INITIAL_SERVICE_GROUP_3_DATA["SSH_KEYS"] = {"KEY4": {"ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvCuWxbw+ONUEfFEOQo9/XaqqxCoxF2yS5CchB0AmLSoPaYdnn4THXCGNuxMYOv4ABXKANNamJWGBIQjqZWqCSCnxyCCvfmCAs0M+or2Sokor7nOD99CpTeAgtmzhrWK+aupB5REy/VzW7P6vDtQxZBBXx/3vpr81ViYmuLIqSbZU1BfU2cZdDQVOXnkPAW3i3RhMLj2wvJDrsEUb0Xa6s4baqa0R94TSa4AkNvdlNE+ugKN9X3mCAZPDNd5DUogp8Oxt2wY7cZVpaEPJFO0iP5eshKvyMXikgDKwU+IqaBF8y6ShSRFSIuQFvL1OLOpo69MchE1JGu459YnoOHUGNw== root@atvts1852"}}
INITIAL_SERVICE_GROUP_3_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                "mount_point": "/mnt/data",
                                                "mount_options": "size=512M,noexec,nodev,nosuid"
                                                }
INITIAL_SERVICE_GROUP_3_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname2.sh,csfname3.sh,csfname1.sh,csfname4.sh,csfname5.sh"
                                                    }

########################
# SERVICE GROUP 4 DATA #
########################

INITIAL_SERVICE_GROUP_4_DATA = dict()
INITIAL_SERVICE_GROUP_4_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "1",
                                                   "name": "CS_VM4",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "CS_VM3",
                                                   "node_list": "n1,n2"
                                                   }
INITIAL_SERVICE_GROUP_4_DATA["VM_SERVICE"] = {"cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-4 force-stop",
                                              "status_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-4 status",
                                              "hostnames": "tmo-vm-4",
                                              "internal_status_check": "on",
                                              "start_command": "/bin/systemctl start test-vm-service-4",
                                              "service_name": "test-vm-service-4",
                                              "stop_command": "/bin/systemctl stop test-vm-service-4",
                                              "ram": "144M",
                                              "image_name": "vm-image-2",
                                              "cpus": "1"
                                              }
INITIAL_SERVICE_GROUP_4_DATA["VM_ALIAS"] = {"MS1": {"alias_names": "ms1",
                                                    "address": "192.168.0.42"
                                                    },
                                            "SFS": {"alias_names": "nas4",
                                                    "address": "172.16.30.14"
                                                    }
                                            }
INITIAL_SERVICE_GROUP_4_DATA["NETWORK_INTERFACES"] = {"NET7": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.8"
                                                               },
                                                      "NET8": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth1",
                                                               "ipaddresses": "192.168.0.9"
                                                               },
                                                      "NET9": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth2",
                                                               "ipaddresses": "192.168.0.10"
                                                               },
                                                      "NET10": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth4",
                                                                "ipaddresses": "192.168.0.11",
                                                                "gateway": "192.168.0.1"
                                                                },
                                                      "NET_DHCP": {"host_device": "br6",
                                                                   "network_name": "dhcp_network",
                                                                   "device_name": "eth3",
                                                                   "gateway6": "2001:db8:85a3::7516:1",
                                                                   "ipv6addresses": "2001:db8:85a3::7516:2/48"
                                                                   }
                                                      }
INITIAL_SERVICE_GROUP_4_DATA["YUM_REPOS"] = {"3PP":  {"name": "3PP",
                                                      "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                                      },
                                             "LITP": {"name": "LITP",
                                                      "base_url": "http://ms1/litp"
                                                      }
                                             }
INITIAL_SERVICE_GROUP_4_DATA["PACKAGES"] = {"PKG6": {"name": 'empty_rpm6'},
                                            "PKG7": {"name": 'empty_rpm7'},
                                            "PKG8": {"name": 'empty_rpm8'},
                                            "PKG9": {"name": 'empty_rpm9'}
                                            }
INITIAL_SERVICE_GROUP_4_DATA["NFS_MOUNTS"] = {"VM_MOUNT5": {"device_path": "172.16.30.14:/vx/story7815-mount_1",
                                                            "mount_point": "/tmp/mount_5",
                                                            "mount_options": "rsize=32768,wsize=32768,timeo=14,soft"
                                                            },
                                              "VM_MOUNT6": {"device_path": "172.16.30.14:/vx/story7815-mount_2",
                                                            "mount_point": "/tmp/mount_6"
                                                            },
                                              "VM_MOUNT7": {"device_path": "nas4:/vx/story7815-mount_3",
                                                            "mount_point": "/tmp/mount_7",
                                                            "mount_options": "rsize=65536"
                                                            },
                                              "VM_MOUNT8": {"device_path": "172.16.30.14:/vx/story7815-mount_4",
                                                            "mount_point": "/tmp/mount_8",
                                                            "mount_options": "rsize=32768,wsize=16384,timeo=14,soft"
                                                            },
                                              "VM_MOUNT9": {"device_path": "172.16.30.14:/vx/story7815-mount_5",
                                                            "mount_point": "/tmp/mount_9"
                                                            }
                                              }
INITIAL_SERVICE_GROUP_4_DATA["SSH_KEYS"] = {"KEY5": {"ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAny9V3hymQdOgm2JcPQYa9sg/tzzJaYZSaS1KJ53DadN3dFxS6nBb9pDF+Fj5cldOGSgeLwV+GCufXyjO+5Mp1jAhetQXWlSOzznwj2uzDZHDu5jj2NpoFxIDfjuTsAreC0fg9GZueIYtEkO6x1wW0x1foNf2Q9wAQ1WFWm0NYCaHUbS0XMQTeM8UNCFAXsm7htOmWwijyxPyHPzjXzFnwJUQHvb6y5mBTgrAXi8m8JWVUlM0AYz/6XpgQ7P4Bl6KT+8IbwIBuOm4GbQkB0/vYBK8HrPM6F5z6tQBs4HaXbr+8pLA0Or5NqaE9xRMUtP+uCZdd7CUWhL7hjl/v0oOWQ== root@atvts1852"},"KEY6":{"ssh_key":"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAy438d6c/272g0nOCrBDYANfECrYFTnOSXtqPKwqePp9QxPeYgnTv44u0f+6bOmMdB7M8PJnRx0fIT6nUkuHqK0i2CykkJgy6ZX+nfHVhxT5OpuypxCICa2RHALWToAZXxKM1sr64B6PjPDKwCckdpQiYfoE8/Yz42+tdN3l0xFLfc8yDuca1FT3oMUhsfii/tPSYn+htftzbFBSiCCwyqfRCwcXQzu9AEqTIFrdOZyg0bKTSS/4SCfmPc/ZHCXyKCYaNHX+T9HL18+bmOnStVy6sHGTBmtDArmhlmLC1OCaLE5/DjhhBFP23St84GDShYN1gAz4lAr2p6ot2rIPojw== root@atvts1852"},"KEY7":{"ssh_key":"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAyg4oyr0K706YERlCHYtE4JS1WBmM+mXMdgpjXgzKCKFIGW4gxfB78I4LRn/giWE6JLOAfy4YJOVaNfjx/Oui4/QXpkc4AhgtYXVGRpBy5lSxlLZ0PMMD2KKi2KSFayIpqW3joOLDFkNi6xtdie5+iW622Kd450swcEQVwWdjLGHy/asBL+Kjzk5lnl46A/AwKl1Mr39avTj5gQrSwuZlXgi/gAdB2j78VB86cPvwgGKZGRmh/x4olCzucb4hdgJBX9WC7MwkCqQBtFesrJmbI37wadQbOBzH9pkKzt2HaFKpULigB03EKDgqfy62XYKfIHbbWMjHhIJciy3o30NGdw== root@atvts1852"},	"KEY8":{"ssh_key":"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAtRpgOw67RQhCsiFpZQuUUyZHNUewAwGjZEjKS5McII4ULdc6+hbfq+bFn1KG0gok3aEiVFfh6DgLLQzJHT8Ovt1C7SagSyl5EwZ70X1J9Vyf+E/DGu0D8+/dppMaPTssU0O1O4vH1R8WMixgRLqxqdncJSmq+yM1P85KIxoR4RIp/ohxfYGdIwfGMBKgfVOjaEv527DG28vidAAYy/EnZyxtVe13b37CPh1CARYpvYRaLi4dCZ1jeCKbIsDKAU81pnfQEfElpYAfMWNbd9ZKwzphJCUucw0WH+JjXFa1HqWE31TN1vSdbPeP+3U+74q4CvA+htR7q7Yytj589XEldw== root@atvts1852"},"KEY9":{"ssh_key":"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAy0TFTSwmA69vlZIytcOqlj4F19HBlcjuQQ+bSupOMAB2xgoG3Gp0z7B3D+FgBmMS2PCGejVHgywjqx0B5AIJ4hk0zPHSBxrNGK7EqD4nhfpXLv307GRiaGXt/kgOTJfSFV1xk1NmB03WkmymtedPpppJGQy1eev+jcjI4y7aDXOr/LWm7gfdbehSqiKDlYpfGZbhByDtfjOZGf+XPf3aROyy8DIMIcfHRP+MqHkQlhmv81I+3F5IhN2JhJFvRGZMTSd+1IsK0EZmmETrseY6HXB/H6xSxJEAbJjAUo+Ufr/Xlb0Pg/evQJUA2Om7BpPfGbwXfHh5NbeQA6m7ReMwQQ== root@atvts1852"}}
INITIAL_SERVICE_GROUP_4_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname5.sh,csfname6.sh"
                                                    }

########################
# SERVICE GROUP 5 DATA #
########################
INITIAL_SERVICE_GROUP_5_DATA = dict()
INITIAL_SERVICE_GROUP_5_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                   "standby": "0",
                                                   "name": "CS_VM5",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "CS_VM3,CS_VM4",
                                                   "node_list": "n1,n2"
                                                   }
INITIAL_SERVICE_GROUP_5_DATA["VM_SERVICE"] = {"cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-5 force-stop",
                                              "status_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-5 status",
                                              "hostnames": "tmo-vm-5-n1,tmo-vm-5-n2",
                                              "internal_status_check": "on",
                                              "start_command": "/bin/systemctl start test-vm-service-5",
                                              "service_name": "test-vm-service-5",
                                              "stop_command": "/bin/systemctl stop test-vm-service-5",
                                              "ram": "144M",
                                              "image_name": "vm-image-3",
                                              "cpus": "1",
                                              "cpuset": "0-1"
                                              }
INITIAL_SERVICE_GROUP_5_DATA["HA_CONFIG"] = {"restart_limit": "1"}
INITIAL_SERVICE_GROUP_5_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc1",
                                                    "address": "111.222.1.2"
                                                    },
                                            "DB4": {"alias_names": "dbsvc4.foo-domain.tld,dbsvc4.foo-domain2.tld2,dbsvc4",
                                                    "address": "111.222.1.5"
                                                    },
                                            "DB2": {"alias_names": "dbsvc2.foo-domain.tld",
                                                    "address": "111.222.1.3"
                                                    },
                                            "MS1": {"alias_names": "ms1",
                                                    "address": "192.168.0.42"
                                                    },
                                            "SFS": {"alias_names": "nas4",
                                                    "address": "172.16.30.14"
                                                    }
                                            }
INITIAL_SERVICE_GROUP_5_DATA["NETWORK_INTERFACES"] = {"NET11": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth0",
                                                                "ipaddresses": "192.168.0.12,192.168.0.13"
                                                                },
                                                      "NET12": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth1",
                                                                "ipaddresses": "192.168.0.14,192.168.0.15"
                                                                },
                                                      "NET13": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth2",
                                                                "ipaddresses": "192.168.0.16,192.168.0.17",
                                                                "gateway": "192.168.0.1"
                                                                },
                                                      "NET14": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth3",
                                                                "ipaddresses": "192.168.0.18,192.168.0.19"
                                                                },
                                                      "NET15": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth4",
                                                                "gateway6": "2001:db8:85a3::7516:12",
                                                                "ipv6addresses": "2001:db8:85a3::7516:13/48,2001:db8:85a3::7516:14/48",
                                                                "ipaddresses": "192.168.0.20,192.168.0.21"
                                                                }
                                                      }
INITIAL_SERVICE_GROUP_5_DATA["YUM_REPOS"] = {"3PP": {"name": "3PP",
                                                     "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                                     }
                                             }
INITIAL_SERVICE_GROUP_5_DATA["NFS_MOUNTS"] = {"VM_MOUNT10": {"device_path": "nas4:/vx/story7815-mount_2",
                                                             "mount_point": "/tmp/mount_10"
                                                             },
                                              "VM_MOUNT11": {"device_path": "172.16.30.14:/vx/story7815-mount_2",
                                                             "mount_point": "/tmp/mount_11",
                                                             "mount_options": "timeo=14,soft,rsize=32768"
                                                             },
                                              "VM_MOUNT12": {"device_path": "172.16.30.14:/vx/story7815-mount_3",
                                                             "mount_point": "/tmp/mount_12",
                                                             "mount_options": "timeo=14,soft"
                                                             }
                                              }
INITIAL_SERVICE_GROUP_5_DATA["SSH_KEYS"] = {"KEY10": {"ssh_key": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA1sotosrlehl1llmO+7j/c0dH/Kj508jwONePNfgWUPbWVtZ5UEH0GI150R2iizVVe9+lqff5rRoA593xogE6ImR6ydqvXm200u6KveALiRa1iqZyhDN3aJNabgziqCj5Db/HcXI38zOGYRulUQ2EokFS8M058O2ungmli0VlWvmdUbpIXU5rylaOHKecPmBw6VUxGnC+CgUDd+gUOdmeDtxml6wAuKHbz7jfnw9Odd5AfoCOL4pxFkFUBsyQb4L/hu6DCiwPv1hzsVI3P/izEGVS01ehpbWkKDHAkPxddqW24X6MyRLZpXwY6Hwf0JSkWF52seqjGf/MMJd/h8AJdQ== root@atvts1852"}}
INITIAL_SERVICE_GROUP_5_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname1.sh"
                                                    }

########################
# SERVICE GROUP 6 DATA #
########################
INITIAL_SERVICE_GROUP_6_DATA = dict()
INITIAL_SERVICE_GROUP_6_DATA["VM_IMAGE"] = VM_IMAGES["VM_IMAGE5"]
INITIAL_SERVICE_GROUP_6_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "1",
                                                   "name": "CS_VM6",
                                                   "dependency_list": "",
                                                   "online_timeout": "300",
                                                   "node_list": "n1,n2"
                                                   }
INITIAL_SERVICE_GROUP_6_DATA["VM_SERVICE"] = {"cpus": "1",
                                              "service_name": "test-vm-service-6",
                                              "ram": "256M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-6 force-stop",
                                              "image_name": "vm-image-5",
                                              "hostnames": "tmo-vm-6",
                                              "internal_status_check": "on"
                                              }
INITIAL_SERVICE_GROUP_6_DATA["VM_ALIAS"] = {"db1": {"alias_names": "dbsvc1",
                                                    "address": "111.222.1.2"
                                                    },
                                            "db2": {"alias_names": "dbsvc2",
                                                    "address": "111.222.1.3"
                                                    },
                                            "ms1": {"alias_names": "ms1",
                                                    "address": "192.168.0.42"
                                                    }
                                            }
INITIAL_SERVICE_GROUP_6_DATA["NETWORK_INTERFACES"] = {"NET1": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.29",
                                                               "gateway": "192.168.0.1"
                                                               },
                                                      "NET2": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth1",
                                                               "ipv6addresses": "2001:1b70:82a1:103::15/64"
                                                               },
                                                      "NET_DHCP": {"host_device": "br6",
                                                                   "network_name": "dhcp_network",
                                                                   "device_name": "eth2",
                                                                   "ipaddresses": "dhcp"
                                                                   }
                                                      }
INITIAL_SERVICE_GROUP_6_DATA["VM_CUSTOM_SCRIPT"] = {"custom_scripts": "csfname2.sh,csfname3.sh"}


################################
# UPDATED SERVICE GROUP 1 DATA #
################################

UPDATED_SERVICE_GROUP_1_DATA = dict()
UPDATED_SERVICE_GROUP_1_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_VM1",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "",
                                                   "node_list": "n1"
                                                   }
UPDATED_SERVICE_GROUP_1_DATA["HA_CONFIG"] = {"restart_limit": "1",
                                             "status_timeout": "120"
                                             }
UPDATED_SERVICE_GROUP_1_DATA["VM_SERVICE"] = {"cpus": "2",
                                              "service_name": "test-vm-service-1",
                                              "ram": "266M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-1 force-stop",
                                              "image_name": VM_IMAGES["VM_IMAGE1"]["image_name"],
                                              "hostnames": "smo-vm-1",
                                              "internal_status_check": "off"
                                              }
UPDATED_SERVICE_GROUP_1_DATA["VM_ALIAS"] = {"MS": {"alias_names": "ms1",
                                                   "address": "192.168.0.42"
                                                   },
                                            "DB1": {"alias_names": "dbsvc1",
                                                    "address": "111.222.1.2"
                                                    },
                                            "DB2": {"alias_names": "dbsvc2.foo-domain.tld",
                                                    "address": "111.222.1.3"
                                                    },
                                            "SFS": {"alias_names": "nas4",
                                                    "address": "172.16.30.14"
                                                    },
                                            "DB20": {"alias_names": "dbsvc20",
                                                     "address": "111.222.1.20"
                                                     },
                                            "DB21": {"alias_names": "dbsvc21.foobar.tld",
                                                     "address": "111.222.1.21"
                                                     },
                                            "IPV6a": {"alias_names": "ipv6a-service",
                                                      "address": "fdde:4d7e:d471:1::835:90:103/64"
                                                     },
                                            "IPV6b": {"alias_names": "ipv6b-service",
                                                      "address": "fdde:4d7e:d471:1::835:90:104"
                                                      }
                                            }
UPDATED_SERVICE_GROUP_1_DATA["NETWORK_INTERFACES"] = {"NET1": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.2"
                                                               },
                                                      "NET_DHCP": {"host_device": "br6",
                                                                   "network_name": "dhcp_network",
                                                                   "device_name": "eth1",
                                                                   "ipaddresses": "dhcp"
                                                                   },
                                                      "NET20": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth2",
                                                                "ipaddresses": "192.168.0.22"
                                                                },
                                                      "NET21": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth3",
                                                                "ipaddresses": "192.168.0.23"
                                                                }
                                                      }
UPDATED_SERVICE_GROUP_1_DATA["YUM_REPOS"] = {"3PP": {"name": "3PP",
                                                     "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                                     },
                                             "LITP": {"name": "LITP",
                                                      "base_url": "http://ms1/litp"
                                                      },
                                             "libvirt_repo1": {"name": "libvirt_repo1",
                                                               "base_url": "http://ms1/libvirt_repo1"
                                                               },
                                             "libvirt_repo2": {"name": "libvirt_repo2",
                                                               "base_url": "http://ms1/libvirt_repo2"
                                                               }
                                             }
UPDATED_SERVICE_GROUP_1_DATA["PACKAGES"] = {"PKG1": {"name": "empty_testrepo1_rpm1"},
                                            "PKG2": {"name": "empty_rpm3"},
                                            "PKG3": {"name": "empty_testrepo2_rpm1"}
                                            }
UPDATED_SERVICE_GROUP_1_DATA["NFS_MOUNTS"] = {"VM_MOUNT1": {"device_path": "nas4:/vx/story7815-mount_1",
                                                            "mount_point": "/tmp/mount_1",
                                                            "mount_options": "retrans=8,rsize=32768"
                                                            },
                                              "VM_MOUNT2": {"device_path": "/vx/story7815-mount_2",
                                                            "mount_point": "/tmp/mount_2"
                                                            },
                                              "VM_MOUNT3": {"device_path": "/vx/story7815-mount_3",
                                                            "mount_point": "/tmp/mount_3",
                                                            "mount_options": "retrans=6,rsize=16384"
                                                            }
                                              }
UPDATED_SERVICE_GROUP_1_DATA["SSH_KEYS"] = {"KEY1": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEApPdyRQeCoh36f8ayxgJLg6nZvWD3nc2kV1T+6xXY6dFTlR4TBjkj5pMq6fGNzSZBfzCB7LvBz0DxLWgKYhIumt1QTFDAszULwfst94XqHd+HSAEBQ0+cZ5VQmjXtt7OpklofsSsC4SilWCJW2g1G4Lo7W5BP/qeBj/yGvE9qKnctZ26OtuO7R1fcpOIXC5KFT9cecvROijCBE90HQYLzt1VlDQn2DRqOH7w11S5abNskZrrpM2lhXorKEozORP9WrCuZW1PEnQDRGAzqKiaAw/5q/3m/L72NtUyiXzi5+92ZgvvxXSOernpeIocoPbUMVcma945dfm8FxC60/UB//Q== root@atvts1852",
                                            "KEY2": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvB3N6WOJ9qAQjGWfwpXvUWYWz8A7Ezwv/pihAYCbObDo71Ycsa3kuz2gUK9uS6Pw5DlNFAbFPk4zi/52Oj+frw4W56HnStxe13zB7ca4N0HFHMEE1QOyZ/wzv+DubwoKuz8I5yA9BD5Oli3DJXVVqxhjxRjiOQ7xs+CHsqHxzgulSJpWmbkli7BoVXsCoFN0oQmfXc7liqCciCZCvPwc+mKtJfH4oozKajwfcvyRyQhd1hqFwsaa7dxKuLww0mT6V+scduwCMVSuJH0b34Qow4ZR0XWwHGIzCf5XApypZPcuaEhRBtqpWysujlnYrkieprGn/nKna/t6USJdC9uPWQ== root@atvts1852",
                                            "KEY3": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8g3u0guI42gog7dFNBoBOtXZ+/okb+HZoTj37Iz5c60+qpehKHTdqnewxT+BX1h/GZg0CKb8+tR3GFqifBDAVXqwHfpQnGMVsHeItM09XDoYvRjWkkDAwpT3OLdEKfNmu+0rJEwvrx5w+aDsvrzfrDUGNWTBSogpXKLL1kCsCsfCNdU42xy6GygzgqyL/lo5RFBTbuDkI0Y4xSzwTxb8CPjbPcughBedWxAI0aYGh+IcV+fP2reMVeDyFqPeKiXcdL+8kWAb+pkR1WUr46dKxP/PkQGkpVEXxsjtDwisNJDFb3wC8pF3G2T5L3And01rhMg5hhLpCZn3yWSZUvjU6Q== root@atvts1852"
                                            }
UPDATED_SERVICE_GROUP_1_DATA["VM_RAM_MOUNT"] = {"type": "tmpfs",
                                                "mount_point": "/mnt/data",
                                                "mount_options": "size=512M,noexec,nodev,nosuid"
                                                }
UPDATED_SERVICE_GROUP_1_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname2.sh,csfname1.sh,csfname3.sh,csfname4.sh,csfname7.sh"
                                                    }

#TORF-297880 - tc_09
#TORF-343548 - tc_01
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE1"] = {"props": 'name="423 vm_test_rule1" action=drop provider=iptables proto=tcp dport=54 ',
                                                     "item_name": "fw_rule1_v4",
                                                     "ipv6": False
                                                     }
#TORF-297880 - tc_06
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE2"] = {"props": 'name="413 vm_test_rule1_ipv6" action=drop provider=ip6tables proto=udp dport=12 ',
                                                     "item_name": "fw_rule1_v6",
                                                     "ipv6": True
                                                     }
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE3"] = {"props": 'name="413 vm_test_rule2" action=accept source=192.168.0.0/16 proto=tcp dport=22 provider=iptables',
                                                     "item_name": "fw_rule2_v4",
                                                     "ipv6": False
                                                     }
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE4"] = {"props": 'name="222 vm_test_rule2_ipv6" action=accept source=2001:db8::/32 proto=tcp dport=22 provider=ip6tables',
                                                     "item_name": "fw_rule2_v6",
                                                     "ipv6": True
                                                     }
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE5"] = {"props": 'name="324 vm_test_rule3_ipv6" action=drop provider=ip6tables proto=tcp dport=22 ',
                                                     "item_name": "fw_rule3_v6",
                                                     "ipv6": True
                                                     }
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE6"] = {"props": 'name="215 vm_test_rule3" action=accept provider=iptables proto=tcp dport=22 ',
                                                     "item_name": "fw_rule3_v4",
                                                     "ipv6": False
                                                     }
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE7"] = {"props": 'name="895 vm_test_rule4_ipv6" action=accept provider=ip6tables proto=tcp dport=22 ',
                                                     "item_name": "fw_rule4_v6",
                                                     "ipv6": True
                                                     }
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE8"] = {"props": 'name="623 vm_test_rule4" action=drop provider=iptables proto=udp dport=42 ',
                                                     "item_name": "fw_rule4_v4",
                                                     "ipv6": False
                                                     }
#TORF-297880 - tc_07
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE9"] = {"props": 'name="811 vm_test_rule5" action=accept provider=iptables',
                                                     "item_name": "fw_rule5_v4",
                                                     "ipv6": False
                                                     }
#TORF-297880 - tc_10
UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE10"] = {"props": 'name="123 vm_test_rule6" action=accept provider=iptables proto=udp dport=42-55 ',
                                                      "item_name": "fw_rule6_v4",
                                                      "ipv6": False
                                                      }

VM_FIREWALL_RULES_1 = [UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE1"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE2"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE3"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE4"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE5"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE6"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE7"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE8"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE9"],
                       UPDATED_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE10"]
                       ]

UPDATED_SERVICE_GROUP_1_DATA["EXP_IPTABLES_OUTPUT"] = {"iptables": [['DROP', '423 vm_test_rule1', 'tcp', '54'],
                                                                    ['ACCEPT', '413 vm_test_rule2', '192.168.0.0/16'],
                                                                    ['ACCEPT', '215 vm_test_rule3', 'tcp', '22'],
                                                                    ['DROP', '623 vm_test_rule4', 'udp', '42'],
                                                                    ['ACCEPT', '811 vm_test_rule5', 'tcp', '22'],
                                                                    ['ACCEPT', '123 vm_test_rule6', 'udp', '42:55']
                                                                    ],
                                                       "ip6tables": [['DROP', '413 vm_test_rule1_ipv6', 'udp', '12'],
                                                                     ['ACCEPT', '222 vm_test_rule2_ipv6', '2001:db8::/32'],
                                                                     ['DROP', '324 vm_test_rule3_ipv6', 'tcp', '22'],
                                                                     ['ACCEPT', '895 vm_test_rule4_ipv6', 'tcp', '22']
                                                                     ]
                                                       }

###############################
# UPDATED SERVICE GROUP SLES DATA #
################################

UPDATED_SERVICE_GROUP_SLES_DATA = dict()
UPDATED_SERVICE_GROUP_SLES_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_SLES_VM",
                                                   "online_timeout": "1500",
                                                   "dependency_list": "",
                                                   "node_list": "n1"
                                                   }
UPDATED_SERVICE_GROUP_SLES_DATA["NETWORK_INTERFACES"] = {"NET1": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.139",
                                                               "gateway":"192.168.0.1"
                                                               }
                                                      }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_SERVICE"] = {"cpus": "2",
                                              "service_name": "sles",
                                              "ram": "4096M",
                                              "image_name": VM_IMAGES["VM_IMAGE_SLES"]["image_name"],
                                               "hostnames": "sles-vm",
                                              "internal_status_check": "off"
                                              }
UPDATED_SERVICE_GROUP_SLES_DATA["HA_CONFIG"] = {"restart_limit": "3", "status_interval": "30"
                                                }
UPDATED_SERVICE_GROUP_SLES_DATA["ZYPPER_REPOS"] = {"NCM": {"name": "ncm",
                                                     "base_url": "http://ms1/ncm2"}
                                             }
UPDATED_SERVICE_GROUP_SLES_DATA["PACKAGES"] = {"PKG1": {"name": "empty_rpm3"}
                                            }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE1"] = {"props": 'name="601 test_reach_traffic-nodes" action=drop source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_1",
                                                      "ipv6": True
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE2"] = {"props": 'name="602 test_drop_traffic_nodes" action=drop source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_2",
                                                      "ipv6": True
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE3"] = {"props": 'name="603 test_reach_traffic_nodes" action=accept source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_3",
                                                      "ipv6": True
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE4"] = {"props": 'name="604 test_reach_traffic_nodes" action=accept source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_4",
                                                      "ipv6": True
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE5"] = {"props": 'name="401 test_drop_traffic_nodes" action=accept provider=iptables source="10.0.0.0/24"',
                                                      "item_name": "fw_v4_1",
                                                      "ipv6": False
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE6"] = {"props": 'name="402 test_drop_traffic_nodes" action=drop provider=iptables source="10.10.0.0/24"',
                                                      "item_name": "fw_v4_2",
                                                      "ipv6": False
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE7"] = {"props": 'name="403 test_reach_traffic_nodes" action=drop provider=iptables source="10.20.0.0/24"',
                                                      "item_name": "fw_v4_3",
                                                      "ipv6": False
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE8"] = {"props": 'name="404 test_reach_traffic_nodes" action=accept provider=iptables source="10.30.0.0/24"',
                                                      "item_name": "fw_v4_4",
                                                      "ipv6": False
                                                       }

VM_FIREWALL_RULES_SLES_1 = [UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE1"],
                          UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE2"],
                          UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE3"],
                          UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE4"],
                          UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE5"],
                          UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE6"],
                          UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE7"],
                          UPDATED_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE8"]
                         ]
UPDATED_SERVICE_GROUP_SLES_DATA["EXP_IPTABLES_OUTPUT"] = {"iptables": [['ACCEPT', '401 test_drop_traffic_nodes', '10.0.0.0/24'],
                                                                    ['DROP', '402 test_drop_traffic_nodes', '10.10.0.0/24'],
                                                                    ['DROP', '403 test_reach_traffic_nodes', '10.20.0.0/24'],
                                                                    ['ACCEPT', '404 test_reach_traffic_nodes', '10.30.0.0/24'],
                                                                    ],
                                                       "ip6tables": [['DROP', '601 test_reach_traffic-nodes', '2001:db8::/32'],
                                                                     ['DROP', '602 test_drop_traffic_nodes', '2001:db8::/32'],
                                                                     ['ACCEPT', '603 test_reach_traffic_nodes', '2001:db8::/32'],
                                                                     ['ACCEPT', '604 test_reach_traffic_nodes', '2001:db8::/32'],
                                                                     ]
                                                       }
UPDATED_SERVICE_GROUP_SLES_DATA["VM_CUSTOM_SCRIPT"] = {"custom_script_names": "csfname3.sh,csfname4.sh,csfname5.sh,csfname6.sh,csfname7.sh"}

################################
# UPDATED SERVICE GROUP 2 DATA #
################################

UPDATED_SERVICE_GROUP_2_DATA = dict()
UPDATED_SERVICE_GROUP_2_DATA["HOSTNAMES"] = {"hostnames": "smo-vm-2"}
UPDATED_SERVICE_GROUP_2_DATA["HA_CONFIG"] = {"restart_limit": "1"}
UPDATED_SERVICE_GROUP_2_DATA["VM_SERVICE"] = {"cpus": "1",
                                              "service_name": "test-vm-service-2",
                                              "ram": "144M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-2 force-stop",
                                              "image_name": VM_IMAGES["VM_IMAGE2"]["image_name"],
                                              "hostnames": "smo-vm-2",
                                              "internal_status_check": "on"
                                              }
UPDATED_SERVICE_GROUP_2_DATA["VM_ALIAS"] = {"DB22": {"alias_names": "dbsvc22.foobar.tld,dbsvc22",
                                                     "address": "111.222.1.22"
                                                     },
                                            "DB23": {"alias_names": "dbsvc23.foobar.tld,dbsvc23.foobar2.tld",
                                                     "address": "111.222.1.23"
                                                     }
                                            }
UPDATED_SERVICE_GROUP_2_DATA["NETWORK_INTERFACES"] = {"NET22": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth3",
                                                                "ipaddresses": "192.168.0.24"
                                                                }
                                                      }
UPDATED_SERVICE_GROUP_2_DATA["YUM_REPOS"] = {"3PP": {"name": "3PP",
                                                     "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                                     },
                                             "LITP": {"name": "LITP",
                                                      "base_url": "http://ms1/litp"
                                                      },
                                             "libvirt_repo1": {"name": "libvirt_repo1",
                                                               "base_url": "http://ms1/libvirt_repo3"
                                                               }
                                             }
UPDATED_SERVICE_GROUP_2_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                "mount_point": "/mnt/data/tmp",
                                                "mount_options": "size=512M,noexec,nodev,nosuid"
                                                }

################################
# UPDATED SERVICE GROUP 3 DATA #
################################

UPDATED_SERVICE_GROUP_3_DATA = dict()
UPDATED_SERVICE_GROUP_3_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_VM3",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "",
                                                   "node_list": "n1"
                                                   }
UPDATED_SERVICE_GROUP_3_DATA["HA_CONFIG"] = {"restart_limit": "1"}
UPDATED_SERVICE_GROUP_3_DATA["VM_SERVICE"] = {"cpus": "2",
                                              "service_name": "test-vm-service-3",
                                              "ram": "150M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-3 force-stop",
                                              "image_name": VM_IMAGES["VM_IMAGE3"]["image_name"],
                                              "hostnames": "smo-vm-3",
                                              "internal_status_check": "on"
                                              }
UPDATED_SERVICE_GROUP_3_DATA["VM_ALIAS"] = {"DB24": {"alias_names": "dbsvc24",
                                                     "address": "111.222.1.24"
                                                     }
                                            }
UPDATED_SERVICE_GROUP_3_DATA["NETWORK_INTERFACES"] = {"NET23": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth6",
                                                                "ipaddresses": "192.168.0.25"
                                                                },
                                                      "NET24": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth7",
                                                                "ipaddresses": "192.168.0.26"
                                                                },
                                                      "NET34": {"device_name": "eth5"
                                                                }
                                                      }
UPDATED_SERVICE_GROUP_3_DATA["NFS_MOUNTS"] = {"VM_MOUNT16": {"device_path": "nas4:/vx/story7815-mount_2",
                                                             "mount_point": "/tmp/mount_16"
                                                             },
                                              "VM_MOUNT17": {"device_path": "172.16.30.14:/vx/story7815-mount_3",
                                                             "mount_point": "/tmp/mount_17",
                                                             "mount_options": "wsize=16384"
                                                             },
                                              "VM_MOUNT18": {"device_path": "172.16.30.14:/vx/story7815-mount_4",
                                                             "mount_point": "/tmp/mount_18"
                                                             }
                                              }
UPDATED_SERVICE_GROUP_3_DATA["VM_RAM_MOUNT"] = {"type": "tmpfs",
                                                "mount_point": "/mnt/data"
                                                }
UPDATED_SERVICE_GROUP_3_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname2.sh,csfname3.sh,csfname1.sh,csfname4.sh,csfname5.sh"
                                                    }

################################
# UPDATED SERVICE GROUP 4 DATA #
################################

UPDATED_SERVICE_GROUP_4_DATA = dict()
UPDATED_SERVICE_GROUP_4_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_VM4",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "",
                                                   "node_list": "n1"
                                                   }
UPDATED_SERVICE_GROUP_4_DATA["HA_CONFIG"] = {"restart_limit": "1"}
UPDATED_SERVICE_GROUP_4_DATA["VM_SERVICE"] = {"cpus": "2",
                                              "service_name":"test-vm-service-4",
                                              "ram": "150M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-4 force-stop",
                                              "hostnames": "smo-vm-4",
                                              "internal_status_check": "on"
                                              }
UPDATED_SERVICE_GROUP_4_DATA["NETWORK_INTERFACES"] = {"NET25": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth5",
                                                                "ipaddresses": "192.168.0.27"
                                                                },
                                                      "IF_PREFIX": {"network_name": "mgmt",
                                                                    "device_name": "eth6",
                                                                    "host_device": "br0",
                                                                    "ipaddresses": "192.168.0.60",
                                                                    "mac_prefix": "AA:BB:CC"
                                                                    }
                                                      }
UPDATED_SERVICE_GROUP_4_DATA["VM_ALIAS"] = {"DB25": {"alias_names": "dbsvc25.foobar.tld,dbsvc25.foobar2.tld,dbsvc25",
                                                     "address": "111.222.1.25"
                                                     },
                                            "DB26": {"alias_names": "dbsvc26",
                                                     "address": "111.222.1.26"
                                                     }
                                            }
UPDATED_SERVICE_GROUP_4_DATA["PACKAGES"] = {"EMPTY_RPM1": {"name": "empty_rpm1"},
                                            "PKG_EMPTY_RPM7": {"name": "empty_testrepo1_rpm1"},
                                            "PKG_EMPTY_RPM6": {"name": "empty_testrepo1_rpm2"}
                                            }
UPDATED_SERVICE_GROUP_4_DATA["YUM_REPOS"] = {"libvirt_repo1": {"name": "libvirt_repo1",
                                                               "base_url": "http://ms1/libvirt_repo1"
                                                               }
                                             }
UPDATED_SERVICE_GROUP_4_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname2.sh,csfname3.sh,csfname1.sh"
                                                    }

################################
# UPDATED SERVICE GROUP 5 DATA #
################################

UPDATED_SERVICE_GROUP_5_DATA = dict()
UPDATED_SERVICE_GROUP_5_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                   "standby": "0",
                                                   "name": "CS_VM5",
                                                   "online_timeout": "1200",
                                                   "dependency_list": "",
                                                   "node_list": "n1"
                                                   }
UPDATED_SERVICE_GROUP_5_DATA["HA_CONFIG"] = {"restart_limit": "1"}
UPDATED_SERVICE_GROUP_5_DATA["VM_SERVICE"] = {"cpus": "2",
                                              "service_name": "test-vm-service-5",
                                              "ram": "150M",
                                              "image_name":"vm-image-2",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-5 force-stop",
                                              "hostnames": "smo-vm-5-n1",
                                              "internal_status_check": "on"
                                              }
UPDATED_SERVICE_GROUP_5_DATA["NETWORK_INTERFACES"] = {"NET11": {"ipaddresses": "192.168.0.12"
                                                                },
                                                      "NET12": {"ipaddresses": "192.168.0.55"
                                                                },
                                                      "NET13": {"ipaddresses": "192.168.0.16",
                                                                "gateway": "192.168.0.1"
                                                                },
                                                      "NET14": {"ipaddresses": "192.168.0.18"
                                                                },
                                                      "NET26": {"host_device": "br0",
                                                                "network_name": "mgmt",
                                                                "device_name": "eth5",
                                                                "ipaddresses": "192.168.0.28"
                                                                },
                                                      "NET15": {"gateway6": "2001:db8:85a3::7516:12",
                                                                "ipv6addresses": "2001:db8:85a3::7516:13/48",
                                                                "ipaddresses": "192.168.0.20"
                                                                }
                                                      }
UPDATED_SERVICE_GROUP_5_DATA["VM_ALIAS"] = {"DB27": {"alias_names": "dbsvc27",
                                                     "address": "111.222.1.27"
                                                     },
                                            "DB28": {"alias_names": "dbsvc28,dbsvc28.foobar.tld",
                                                     "address": "111.222.1.28"
                                                     },
                                            "DB29": {"alias_names": "dbsvc29.foobar.tld,dbsvc29.foobar2.tld",
                                                     "address": "111.222.1.29"
                                                     }
                                            }
UPDATED_SERVICE_GROUP_5_DATA["PACKAGES"] = {"EMPTY_TESTREPO1_RPM1": {"name": "empty_testrepo1_rpm1"},
                                            "EMPTY_RPM2": {"name": "empty_rpm2"},
                                            "EMPTY_RPM3": {"name": "empty_rpm3"}
                                            }
UPDATED_SERVICE_GROUP_5_DATA["YUM_REPOS"] = {"libvirt_repo1": {"name": "libvirt_repo1",
                                                               "base_url": "http://ms1/libvirt_repo1"
                                                               },
                                             "libvirt_repo2": {"name": "libvirt_repo2",
                                                               "base_url": "http://ms1/libvirt_repo2"
                                                               }
                                             }
UPDATED_SERVICE_GROUP_5_DATA["VM_RAM_MOUNT"] = {"type": "tmpfs",
                                                "mount_point": "/mnt/data"
                                                }
UPDATED_SERVICE_GROUP_5_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                                    "custom_script_names": "csfname6.sh,csfname2.sh,csfname3.sh,csfname1.sh"
                                                    }

###############################
# UPDATED SERVICE GROUP 6 DATA #
################################

UPDATED_SERVICE_GROUP_6_DATA = dict()
UPDATED_SERVICE_GROUP_6_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                   "standby": "0",
                                                   "name": "CS_VM6",
                                                   "online_timeout": "600",
                                                   "node_list": "n1,n2"
                                                   }
UPDATED_SERVICE_GROUP_6_DATA["VM_SERVICE"] = {"cpus": "1",
                                              "service_name": "test-vm-service-6",
                                              "ram": "256M",
                                              "cleanup_command": "/usr/share/litp_libvirt/vm_utils test-vm-service-6 force-stop",
                                              "image_name": "vm-image-5",
                                              "hostnames": "smo-vm-6-n1,smo-vm-6-n2",
                                              "internal_status_check": "off"
                                              }
UPDATED_SERVICE_GROUP_6_DATA["NETWORK_INTERFACES"] = {"NET1": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.79,192.168.0.80",
                                                               "gateway": "192.168.0.1"
                                                               },
                                                      "NET2": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth1",
                                                               "ipv6addresses": "2001:1b70:82a1:103::40/64,2001:1b70:82a1:103::41/64"
                                                               },
                                                      "NET_DHCP": {"host_device": "br6",
                                                                   "network_name": "dhcp_network",
                                                                   "device_name": "eth2",
                                                                   "ipaddresses": "dhcp"
                                                                   },
                                                      "NET3": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth3",
                                                               "gateway6": "2001:1b70:82a1:103::45",
                                                               "ipv6addresses": "2001:1b70:82a1:103::46/64,2001:1b70:82a1:103::47/64",
                                                               "ipaddresses": "192.168.0.81,192.168.0.82"
                                                               }
                                                      }
UPDATED_SERVICE_GROUP_6_DATA["VM_FIREWALL_RULES"] = [{"props": 'name="333 vm_test_rule1" action=drop provider=iptables dport=25',
                                                      "item_name": "fw_rule1_v4",
                                                      "ipv6": False
                                                      },
                                                     {"props": 'name="561 vm_test_rule1_ipv6" action=accept provider=ip6tables',
                                                      "item_name": "fw_rule1_v6",
                                                      "ipv6": True
                                                      },
                                                     {"props": 'name="413 vm_test_rule2" action=accept source=192.168.0.0/24 provider=iptables',
                                                      "item_name": "fw_rule3_v4",
                                                      "ipv6": False
                                                      },
                                                     {"props": 'name="322 vm_test_rule2_ipv6" action=accept source=2001:1b70::/64 provider=ip6tables',
                                                      "item_name": "fw_rule2_v6",
                                                      "ipv6": True
                                                      }
                                                     ]
UPDATED_SERVICE_GROUP_6_DATA["EXP_IPTABLES_OUTPUT"] = {"iptables": [['DROP', '333 vm_test_rule1', '25'],
                                                                    ['ACCEPT', '413 vm_test_rule2', '192.168.0.0/24']
                                                                    ],
                                                       "ip6tables": [['ACCEPT', '561 vm_test_rule1_ipv6'],
                                                                     ['ACCEPT', '322 vm_test_rule2_ipv6', '2001:1b70::/64']
                                                                     ]
                                                       }

#################################
# UPDATED2 SERVICE GROUP 1 DATA #
#################################

UPDATED2_SERVICE_GROUP_1_DATA = dict()
UPDATED2_SERVICE_GROUP_1_DATA["VM_SERVICE"] = {"cpus": "3",
                                               "ram": "270M",
                                               "image_name": "vm-image-3",
                                               "cpuset": "0-1"
                                               }
UPDATED2_SERVICE_GROUP_1_DATA["PACKAGES"] = {"PKG_EMPTY_RPM1": {"name": "empty_rpm2"}
                                             }
UPDATED2_SERVICE_GROUP_1_DATA["HOSTNAMES"] = {"hostnames": "smo-vm-1"}
UPDATED2_SERVICE_GROUP_1_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc21"
                                                     },
                                             "DB2": {"address": "111.222.1.22"
                                                     },
                                             "DB20": {"alias_names": "dbsvc40,dbsvc40.foobar.tld"
                                                      },
                                             "DB21": {"address": "111.222.1.41"
                                                      },
                                             "IPV6a": {"alias_names": "ipv6a-service",
                                                       "address": "fdde:4d7e:d471:1::835:90:103/128"
                                                       },
                                             "IPV6b": {"alias_names": "ipv6b-service",
                                                       "address": "fdde:4d7e:d471:1::835:90:105/64"
                                                       }
                                             }
UPDATED2_SERVICE_GROUP_1_DATA["NETWORK_INTERFACES"] = {"NET1": {"ipaddresses": "192.168.0.30"
                                                                }
                                                       }
UPDATED2_SERVICE_GROUP_1_DATA["NFS_MOUNTS"] = {"VM_MOUNT1": {"device_path": "172.16.30.14:/vx/story7815-mount_2"
                                                             }
                                               }
UPDATED2_SERVICE_GROUP_1_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                 "mount_point": "/mnt/data/tmp",
                                                 "mount_options": "size=512M,noexec,nodev,nosuid"
                                                 }

UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE1"] = {"props": 'name="423 vm_test_rule1" action=drop provider=iptables proto=tcp dport=54 ',
                                                      "item_name": "fw_rule1_v4",
                                                      "ipv6": False
                                                      }
#TORF-297880 - tc_06 & #TORF-343548 - tc_02 v6
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE2"] = {"props": 'name="121 vm_test_rule1_ipv6" action=drop provider=ip6tables proto=udp dport=12',
                                                      "item_name": "fw_rule1_v6",
                                                      "ipv6": True
                                                      }
#TORF-343548 - tc_02 v4
##TORF-297880 - tc_09
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE3"] = {"props": 'name="676 vm_test_rule2" action=accept source=192.168.0.0/16 proto=udp dport=22 provider=iptables',
                                                      "item_name": "fw_rule2_v4",
                                                      "ipv6": False
                                                      }
#TORF-343548 - tc_02 v6
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE4"] = {"props": 'name="921 vm_test_rule2_ipv6" action=accept source=2001:db8::/32 proto=tcp dport=23 provider=ip6tables',
                                                      "item_name": "fw_rule2_v6",
                                                      "ipv6": True
                                                      }

#TORF-343548 - tc_03 v6
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE5"] = {"props": 'name="324 vm_test_rule3_ipv6" action=drop provider=ip6tables proto=tcp dport=22 ',
                                                     "item_name": "fw_rule3_v6",
                                                     "ipv6": True
                                                     }
#TORF-343548 - tc_03 v4
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE6"] = {"props": 'name="215 vm_test_rule3" action=accept provider=iptables proto=tcp dport=22',
                                                      "item_name": "fw_rule3_v4",
                                                      "ipv6": False
                                                      }
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE7"] = {"props": 'name="895 vm_test_rule4_ipv6" action=accept provider=ip6tables proto=tcp dport=22',
                                                      "item_name": "fw_rule4_v6",
                                                      "ipv6": True
                                                      }
#TORF-343548 - tc_03 v4
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE8"] = {"props": 'name="623 vm_test_rule4" action=accept provider=iptables proto=udp dport=42',
                                                      "item_name": "fw_rule4_v4",
                                                      "ipv6": False
                                                      }
#TORF-297880 - tc_07 & #TORF-343548 - tc_02 v4
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE9"] = {"props": 'name="621 vm_test_rule5" action=accept provider=iptables proto=tcp dport=22',
                                                      "item_name": "fw_rule5_v4",
                                                      "ipv6": False
                                                      }
#TORF-297880 - tc_10 & #TORF-343548 - tc_02 v4
UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE10"] = {"props": 'name="217 vm_test_rule6"',
                                                       "item_name": "fw_rule6_v4",
                                                       "ipv6": False
                                                       }

VM_FIREWALL_RULES_2 = [UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE1"],
                      UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE2"],
                      UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE3"],
                      UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE4"],
                      UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE7"],
                      UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE9"],
                      UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE10"]]

VM_FIREWALL_RULES_TO_UPDATE = [UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE3"],
                               UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE4"],
                               UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE9"],
                               UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE10"],
                               UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE2"],
                               UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE5"]]

#TORF-343548 - tc_03 v4 & v6
VM_FIREWALL_RULES_TO_REMOVE = [UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE5"],
                               UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE8"],
                               UPDATED2_SERVICE_GROUP_1_DATA["VM_FIREWALL_RULE6"]]

UPDATED2_SERVICE_GROUP_1_DATA["EXP_IPTABLES_OUTPUT"] = {"iptables": [['DROP', '423 vm_test_rule1', 'tcp', '54'],
                                                                     ['ACCEPT', '676 vm_test_rule2', '192.168.0.0/16', 'udp', '22'],
                                                                     ['ACCEPT', '621 vm_test_rule5', 'tcp', '22'],
                                                                     ['ACCEPT', '217 vm_test_rule6', 'udp', '42:55']
                                                                     ],
                                                       "ip6tables": [['DROP', '121 vm_test_rule1_ipv6', 'udp', '12'],
                                                                     ['ACCEPT', '921 vm_test_rule2_ipv6', '2001:db8::/32', 'tcp', '23'],
                                                                     ['ACCEPT', '895 vm_test_rule4_ipv6', 'tcp', '22']
                                                                     ]
                                                        }

UPDATED2_SERVICE_GROUP_1_DATA["RULE_REMOVED"] = {"iptables": [['DROP', '623 vm_test_rule4'],
                                                              ['ACCEPT', '623 vm_test_rule4']],
                                                 "ip6tables": [['DROP', '324 vm_test_rule3_ipv6']]}

####################################
# UPDATED2 SERVICE GROUP SLES DATA #
####################################
UPDATED2_SERVICE_GROUP_SLES_DATA = dict()

UPDATED2_SERVICE_GROUP_SLES_DATA["NETWORK_INTERFACES"] = {"NET1": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth0",
                                                               "ipaddresses": "192.168.0.139",
                                                               "gateway":"192.168.0.1"
                                                               }
                                                      }

UPDATED2_SERVICE_GROUP_SLES_DATA["VM_SERVICE"] = {"cpus": "2",
                                              "service_name": "sles",
                                              "ram": "4096M",
                                              "image_name": VM_IMAGES["VM_IMAGE_SLES"]["image_name"],
                                               "hostnames": "sles-vm",
                                              "internal_status_check": "off"
                                              }
UPDATED2_SERVICE_GROUP_SLES_DATA["ZYPPER_REPOS"] = {"NCM": {"name": "ncm2",
                                                     "base_url": "http://ms1/ncm"}
                                                    }
UPDATED2_SERVICE_GROUP_SLES_DATA["PACKAGES"] = {"PKG1": {"name": "empty_rpm9"}
                                                }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE1"] = {"props": 'name="701 test_reach_to drop_traffic-nodes" action=drop source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_1",
                                                      "ipv6": True
                                                       }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE2"] = {"props": 'name="702 test_drop_ipchange_traffic_nodes" action=drop source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_2",
                                                      "ipv6": True
                                                       }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE3"] = {"props": 'name="703 test_reach_ipchange_traffic_nodes" action=accept source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_3",
                                                      "ipv6": True
                                                       }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE4"] = {"props": 'name="704 test_drop_to_reach_traffic_nodes" action=drop source="2001:db8::/32" provider=ip6tables',
                                                      "item_name": "fw_v6_4",
                                                      "ipv6": True
                                                       }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE5"] = {"props": 'name="501 test_drop_to_accept_traffic_nodes" action=accept provider=iptables source="10.0.0.0/24"',
                                                      "item_name": "fw_v4_1",
                                                      "ipv6": False
                                                       }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE6"] = {"props": 'name="502 test_drop_ipchange_traffic_nodes" action=drop provider=iptables source="10.20.0.0/24"',
                                                      "item_name": "fw_v4_2",
                                                      "ipv6": False
                                                       }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE7"] = {"props": 'name="503 test_reach_to_drop_traffic_nodes" action=drop provider=iptables source="10.20.0.0/24"',
                                                      "item_name": "fw_v4_3",
                                                      "ipv6": False
                                                       }
UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE8"] = {"props": 'name="504 test_reach_ipchange_traffic_nodes" action=accept provider=iptables source="10.40.0.0/24"',
                                                      "item_name": "fw_v4_4",
                                                      "ipv6": False
                                                       }

VM_FIREWALL_RULES_SLES_2 = [UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE1"],
                          UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE2"],
                          UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE3"],
                          UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE4"],
                          UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE5"],
                          UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE6"],
                          UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE7"],
                          UPDATED2_SERVICE_GROUP_SLES_DATA["VM_FIREWALL_RULE8"]
                         ]
UPDATED2_SERVICE_GROUP_SLES_DATA["EXP_IPTABLES_OUTPUT"] = {"iptables": [['ACCEPT', '501 test_drop_to_accept_traffic_nodes', '10.0.0.0/24'],
                                                                    ['DROP', '502 test_drop_ipchange_traffic_nodes', '10.20.0.0/24'],
                                                                    ['DROP', '503 test_reach_to_drop_traffic_nodes', '10.20.0.0/24'],
                                                                    ['ACCEPT', '504 test_reach_ipchange_traffic_nodes', '10.40.0.0/24'],
                                                                    ],
                                                       "ip6tables": [['DROP', '701 test_reach_to drop_traffic-nodes', '2001:db8::/32'],
                                                                     ['DROP', '702 test_drop_ipchange_traffic_nodes', '2001:db8::/32'],
                                                                     ['ACCEPT', '703 test_reach_ipchange_traffic_nodes', '2001:db8::/32'],
                                                                     ['DROP', '704 test_drop_to_reach_traffic_nodes', '2001:db8::/32'],
                                                                     ]
                                                       }

#################################
# UPDATED2 SERVICE GROUP 2 DATA #
#################################

UPDATED2_SERVICE_GROUP_2_DATA = dict()
UPDATED2_SERVICE_GROUP_2_DATA["VM_SERVICE"] = {"image_name": "vm-image-3",
                                               "cpuset": "1"
                                               }
UPDATED2_SERVICE_GROUP_2_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc21",
                                                     "address": "111.222.1.21"
                                                     },
                                             "DB22": {"alias_names": "dbsvc42",
                                                      "address": "111.222.1.42"
                                                      }
                                             }
UPDATED2_SERVICE_GROUP_2_DATA["HOSTNAMES"] = {"hostnames": "smo-vm-2"}
UPDATED2_SERVICE_GROUP_2_DATA["NETWORK_INTERFACES"] = {"NET2": {"ipaddresses": "192.168.0.4"
                                                                },
                                                       "NET3": {"ipaddresses": "192.168.0.3"
                                                                },
                                                       "NET30": {"host_device": "br0",
                                                                 "network_name": "mgmt",
                                                                 "device_name": "eth4",
                                                                 "ipaddresses": "192.168.0.35"
                                                                 },
                                                       "NET31": {"host_device": "br0",
                                                                 "network_name": "mgmt",
                                                                 "device_name": "eth5",
                                                                 "ipaddresses": "192.168.0.36"
                                                                 }
                                                       }
UPDATED2_SERVICE_GROUP_2_DATA["NFS_MOUNTS"] = {"VM_MOUNT13": {"device_path": '172.16.30.14://vx/story7815-mount_1',
                                                              "mount_point": '/tmp/mount_13',
                                                              "mount_options": "rsize=32768,wsize=32768"
                                                              },
                                               "VM_MOUNT14": {"device_path": '172.16.30.14:/vx/story7815-mount_4',
                                                              "mount_point": '/tmp/mount_14'
                                                              },
                                               "VM_MOUNT15": {"device_path": 'nas4:/vx/story7815-mount_5',
                                                              "mount_point": '/tmp/mount_15',
                                                              "mount_options": 'retrans=6,wsize=32768'
                                                              }
                                               }
UPDATED2_SERVICE_GROUP_2_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                 "mount_point": "/mnt/data/tmp",
                                                 "mount_options": "size=512M,noexec,nodev,nosuid"
                                                 }

#################################
# UPDATED2 SERVICE GROUP 3 DATA #
#################################

UPDATED2_SERVICE_GROUP_3_DATA = dict()
UPDATED2_SERVICE_GROUP_3_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                    "standby": "0",
                                                    "name": "CS_VM3",
                                                    "online_timeout": "1200",
                                                    "dependency_list": "",
                                                    "node_list": "n1,n2"
                                                    }
UPDATED2_SERVICE_GROUP_3_DATA["NETWORK_INTERFACES"] = {"NET4": {"ipaddresses": "192.168.0.5,192.168.0.64"
                                                                },
                                                       "NET5": {"ipaddresses":"192.168.0.6,192.168.0.31"
                                                                },
                                                       "NET6": {"ipaddresses":"192.168.0.7,192.168.0.74"
                                                                },
                                                       "NET_DHCP": {"ipv6addresses":"2001:db8:85a3::7516:11/48,2001:db8:85a3::7516:16/48",
                                                                    "ipaddresses":"dhcp"
                                                                    },
                                                       "NET32": {"ipaddresses":"192.168.0.45,192.168.0.56",
                                                                 "ipv6addresses":"2001:db8:85a3::7516:18,2001:db8:85a3::7516:28"
                                                                 },
                                                       "NET33": {"ipaddresses":"192.168.0.46,192.168.0.52",
                                                                 "ipv6addresses":"2001:db8:85a3::7516:19,2001:db8:85a3::7516:24"
                                                                 },
                                                       "NET34": {"ipaddresses":"192.168.0.47,192.168.0.50",
                                                                 "ipv6addresses":"2001:db8:85a3::7516:20,2001:db8:85a3::7516:26"
                                                                 },
                                                       "NET23": {"device_name": "eth5",
                                                                 "ipaddresses":"192.168.0.26,192.168.0.29"
                                                                 },
                                                       "NET24": {"device_name": "eth6",
                                                                 "ipaddresses":"192.168.0.66,192.168.0.68"
                                                                 }
                                                       }
UPDATED2_SERVICE_GROUP_3_DATA["VM_SERVICE"] = {"hostnames": "smo-vm-3",
                                               "image_name": "vm-image-3"
                                               }
UPDATED2_SERVICE_GROUP_3_DATA["PACKAGES"] = {"pkg_empty_rpm4": {"name": "empty_rpm6"}
                                             }
UPDATED2_SERVICE_GROUP_3_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc21.foobar.tld,dbsvc21,dbsvc21.foobar2.tld"
                                                     },
                                             "DB2": {"address": "111.222.1.22"
                                                     },
                                             "DB3": {"alias_names": "dbsvc3,dbsvc3.foo-domain.tld"
                                                     },
                                             "DB4": {"address": "111.222.1.30"
                                                     }
                                             }
UPDATED2_SERVICE_GROUP_3_DATA["VM_RAM_MOUNT"] = {"type": "tmpfs",
                                                 "mount_point": "/mnt/data",
                                                 "mount_options": "size=512M,noexec,nodev,nosuid"
                                                 }

#################################
# UPDATED2 SERVICE GROUP 4 DATA #
#################################

UPDATED2_SERVICE_GROUP_4_DATA = dict()
UPDATED2_SERVICE_GROUP_4_DATA["VM_SERVICE"] = {"cpus": "1",
                                               "ram": "158M",
                                               "image_name": "vm-image-3"
                                               }
UPDATED2_SERVICE_GROUP_4_DATA["VM_ALIAS"] = {"DB25": {"alias_names": "dbsvc45",
                                                      "address": "111.222.1.45"
                                                      },
                                             "DB26": {"alias_names": "dbsvc46",
                                                      "address": "111.222.1.46"
                                                      }
                                             }
UPDATED2_SERVICE_GROUP_4_DATA["NETWORK_INTERFACES"] = {"NET8": {"ipaddresses": "192.168.0.32"
                                                                },
                                                       "NET9": {"ipaddresses": "192.168.0.33"
                                                                },
                                                       "NET10": {"ipaddresses": "192.168.0.34"
                                                                 }
                                                       }

#################################
# UPDATED2 SERVICE GROUP 5 DATA #
#################################

UPDATED2_SERVICE_GROUP_5_DATA = dict()
UPDATED2_SERVICE_GROUP_5_DATA["VM_SERVICE"] = {"cpus": "1",
                                               "ram": "164M",
                                               "image_name": "vm-image-1"
                                               }
UPDATED2_SERVICE_GROUP_5_DATA["PACKAGES"] = {"pkg_empty_rpm3": {"name": "empty_rpm5"}
                                             }
UPDATED2_SERVICE_GROUP_5_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc21"
                                                     },
                                             "DB2": {"address": "111.222.1.22"
                                                     },
                                             "DB4": {"alias_names": "dbsvc24"
                                                     },
                                             "DB27": {"address": "111.222.1.27"
                                                      }
                                             }
UPDATED2_SERVICE_GROUP_5_DATA["NETWORK_INTERFACES"] = {"NET11": {"ipaddresses": "192.168.0.20"
                                                                 },
                                                       "NET13": {"ipaddresses": "192.168.0.12"
                                                                 },
                                                       "NET15": {"ipaddresses": "192.168.0.16"
                                                                 },
                                                       "NET35": {"host_device": "br0",
                                                                 "network_name": "mgmt",
                                                                 "device_name": "eth6",
                                                                 "ipaddresses": "192.168.0.48",
                                                                 "ipv6addresses": "2001:db8:85a3::7516:21"
                                                                 },
                                                       "NET36": {"host_device": "br0",
                                                                 "network_name": "mgmt",
                                                                 "device_name": "eth7",
                                                                 "ipaddresses": "192.168.0.49",
                                                                 "ipv6addresses": "2001:db8:85a3::7516:22"
                                                                 },
                                                       "NET37": {"host_device": "br0",
                                                                 "network_name": "mgmt",
                                                                 "device_name": "eth8",
                                                                 "ipaddresses": "192.168.0.54",
                                                                 "ipv6addresses": "2001:db8:85a3::7516:23"
                                                                 }
                                                       }
#################################
# UPDATE 3 Service Group 1 DATA #
#################################

UPDATE3_SERVICE_GROUP_1_DATA = dict()
UPDATE3_SERVICE_GROUP_1_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc41"
                                                    },
                                            "DB2": {"address": "111.222.1.42"
                                                    }
                                            }
UPDATE3_SERVICE_GROUP_1_DATA["VM_PACKAGE"] = {"PKG_EMPTY_1": {"name": "empty_rpm4"}
                                              }
UPDATE3_SERVICE_GROUP_1_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                   "standby": "0",
                                                   "node_list": "n2,n1",
                                                   "image_name": "vm-image-2"
                                                   }
UPDATE3_SERVICE_GROUP_1_DATA["NETWORK_INTERFACES"] = {"NET1": {"ipaddresses": "192.168.0.58,192.168.0.59"
                                                               },
                                                     "NET20": {"ipaddresses":"192.168.0.22,192.168.0.63"
                                                               },
                                                     "NET21": {"ipaddresses":"192.168.0.23,192.168.0.62"
                                                               }
                                                      }
UPDATE3_SERVICE_GROUP_1_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                "mount_point": "/mnt/data/tmp",
                                                "mount_options": "size=5%"
                                                }
UPDATE3_SERVICE_GROUP_1_DATA["HOSTNAMES"] = {"hostnames": "smo-vm-1"}

#################################
# UPDATE 3 Service Group 2 DATA #
#################################

UPDATE3_SERVICE_GROUP_2_DATA = dict()
UPDATE3_SERVICE_GROUP_2_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                   "standby": "0",
                                                   "node_list": "n2,n1"
                                                   }
UPDATE3_SERVICE_GROUP_2_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc41",
                                                    "address": "111.222.1.41"
                                                    }
                                            }
UPDATE3_SERVICE_GROUP_2_DATA["NETWORK_INTERFACE"] = {"NET31": {"ipaddresses": "192.168.0.36,192.168.0.37"
                                                               },
                                                     "NET22": {"ipaddresses": "192.168.0.24,192.168.0.38"
                                                               },
                                                     "NET2": {"ipaddresses": "192.168.0.4,192.168.0.39"
                                                              },
                                                     "NET3": {"ipaddresses": "192.168.0.3,192.168.0.40"
                                                              },
                                                     "NET30": {"ipaddresses": "192.168.0.35,192.168.0.41"
                                                               }
                                                     }
UPDATE3_SERVICE_GROUP_2_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                "mount_point": "/mnt/data/tmp",
                                                "mount_options": "size=5%"
                                                }
UPDATE3_SERVICE_GROUP_2_DATA["HOSTNAMES"] = {"hostnames": "smo-vm-2"}

#################################
# UPDATE 3 Service Group 3 DATA #
#################################

UPDATE3_SERVICE_GROUP_3_DATA = dict()
UPDATE3_SERVICE_GROUP_3_DATA["CLUSTER_SERVICE"] = {"image_name": "vm_image_4"}
UPDATE3_SERVICE_GROUP_3_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc41"
                                                    },
                                            "DB2": {"address": "111.222.1.42"
                                                    }
                                            }
UPDATE3_SERVICE_GROUP_3_DATA["NFS_MOUNT"] = {"MOUNT_16": {"device_path": "172.16.30.14:/vx/story7815-mount_3",
                                                          "mount_point": "/tmp/7815_update_mnt_point"
                                                          }
                                             }
UPDATE3_SERVICE_GROUP_3_DATA["VM_PACKAGE"] = {"PKG_EMPTY_4": {"name": "empty_rpm7"
                                                              }
                                              }
UPDATE3_SERVICE_GROUP_3_DATA["NETWORK_INTERFACE"] = {"NET33": {"host_device": "br0",
                                                               "network_name": "mgmt",
                                                               "device_name": "eth7",
                                                               "ipaddresses": "192.168.0.72,192.168.0.69",
                                                               "ipv6addresses": "2001:db8:85a3::7516:19,2001:db8:85a3::7516:29"
                                                               }
                                                     }

#################################
# UPDATE 3 Service Group 4 DATA #
#################################

UPDATE3_SERVICE_GROUP_4_DATA = dict()
UPDATE3_SERVICE_GROUP_4_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                   "standby": "0",
                                                   "image_name": "vm_image_4"
                                                   }
UPDATE3_SERVICE_GROUP_4_DATA["VM_ALIAS"] = {"DB25": {"alias_names": "dbsvc65",
                                                     "address": "111.222.1.65"
                                                     }
                                            }
UPDATE3_SERVICE_GROUP_4_DATA["NETWORK_INTERFACE"] = {"DHCP": {"gateway6": "2001:db8:85a3::7516:17",
                                                              "ipv6addresses": "2001:db8:85a3::7516:15,2001:db8:85a3::7516:30"
                                                              },
                                                     "NET10": {"ipaddresses": "192.168.0.34,192.168.0.2"
                                                               },
                                                     "NET9": {"ipaddresses": "192.168.0.33,192.168.0.70"
                                                              },
                                                     "NET8": {"ipaddresses": "192.168.0.32,192.168.0.9"
                                                              },
                                                     "NET7": {"ipaddresses": "192.168.0.8,192.168.0.10"
                                                              },
                                                     "NET25": {"ipaddresses": "192.168.0.27,192.168.0.11"
                                                               },
                                                     "IF_PREFIX": {"ipaddresses": "192.168.0.60,192.168.0.61"
                                                                   }
                                                     }
UPDATE3_SERVICE_GROUP_4_DATA["VM_PACKAGE"] = {"PKG_EMPTY_4": {"name": "empty_rpm7"}
                                              }
UPDATE3_SERVICE_GROUP_4_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                "mount_point": "/mnt/data/tmp",
                                                "mount_options": "size=512M,nosuid"
                                                }
UPDATE3_SERVICE_GROUP_4_DATA["HOSTNAMES"] = {"hostnames": "smo-vm-4"}

#################################
# UPDATE 3 Service Group 5 DATA #
#################################

UPDATE3_SERVICE_GROUP_5_DATA = dict()
UPDATE3_SERVICE_GROUP_5_DATA["CLUSTER_SERVICE"] = {"image_name": "vm_image_4"}
UPDATE3_SERVICE_GROUP_5_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc41"
                                                    },
                                            "DB2": {"address": "111.222.1.42"
                                                    }
                                            }
UPDATE3_SERVICE_GROUP_5_DATA["NFS_MOUNT"] = {"MOUNT_10": {"mount_options": "retrans=32"}
                                             }
UPDATE3_SERVICE_GROUP_5_DATA["VM_PACKAGE"] = {"PKG_3": {"name": "empty_rpm8"}
                                              }


#################################
# UPDATED4 SERVICE GROUP 2 DATA #
#################################

UPDATED4_SERVICE_GROUP_2_DATA = dict()
UPDATED4_SERVICE_GROUP_2_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                    "node_list": "n2",
                                                    "inactive_nodes":"n1"
                                                    }
UPDATED4_SERVICE_GROUP_2_DATA["NETWORK_INTERFACES"] = {"NET2": {"ipaddresses": "192.168.0.4"
                                                                },
                                                       "NET3": {"ipaddresses": "192.168.0.3"
                                                                },
                                                       "NET22": {"ipaddresses": "192.168.0.24"
                                                                 },
                                                       "NET30": {"ipaddresses": "192.168.0.35"
                                                                 },
                                                       "NET31": {"ipaddresses": "192.168.0.36"
                                                                 },
                                                       "NET_DHCP": {"ipaddresses": "dhcp"
                                                                    }
                                                       }

#################################
# UPDATED4 SERVICE GROUP 4 DATA #
#################################

UPDATED4_SERVICE_GROUP_4_DATA = dict()
UPDATED4_SERVICE_GROUP_4_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                                                 "mount_point": "/mnt/data/tmp",
                                                 "mount_options": "size=512M,noexec,nodev,nosuid"
                                                 }
UPDATED4_SERVICE_GROUP_4_DATA["HOSTNAMES"] = {"hostnames": "smo-vm-4"}
UPDATED4_SERVICE_GROUP_4_DATA["NETWORK_INTERFACES"] = {"NET8": {"ipaddresses": "192.168.0.32"
                                                                }
                                                       }

###########################
# MS network initial data #
###########################
MS_NET_DATA = dict()
MS_NET_DATA["NETWORK_INTERFACE"] = {"b0": {"bridge": "br0"
                                           },
                                    "br0": {"device_name": "br0",
                                            "forwarding_delay": "4",
                                            "ipaddress": "192.168.0.42",
                                            "ipv6address": "2001:1b70:82a1:0103::42/64",
                                            "network_name": "mgmt"
                                            }
                                    }

#######################
# MS_VM1 initial data #
#######################

MS_VM1_DATA = dict()
MS_VM1_DATA["VM_SERVICE"] = {"image_name": "vm-image-1",
                             "cpus": "2",
                             "ram": '512M',
                             "internal_status_check": "off",
                             "hostnames": "tmo-vm-ms1",
                             "service_name": 'test-vm-service-ms'
                             }
MS_VM1_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc1",
                                   "address": "111.222.1.2"
                                   },
                           "DB2": {"alias_names": 'dbsvc2.foo-domain.tld',
                                   "address": '111.222.1.3'
                                   },
                           "MS": {"alias_names": 'ms1',
                                  "address": '192.168.0.42'
                                  },
                           "SFS": {"alias_names": 'nas4',
                                   "address": '172.16.30.14'
                                   }
                           }
MS_VM1_DATA["NETWORK_INTERFACE"] = {"NET1": {"host_device": 'br0',
                                             "network_name": 'mgmt',
                                             "device_name": 'eth0',
                                             "ipaddresses": "192.168.0.51",
                                             "gateway": "192.168.0.1"
                                             }
                                    }
MS_VM1_DATA["YUM_REPOS"] = {"3PP": {"name": '3PP',
                                    "base_url": "http://ms1/{0}".format(test_constants.PP_REPO_DIR_NAME)
                                    },
                            "LITP": {"name": 'LITP',
                                     "base_url": 'http://ms1/litp'
                                     },
                            "LIBVIRT_REPO1_MS_SRV": {"name": "libvirt_repo1_ms_srv",
                                                     "base_url": "http://ms1/libvirt_repo1_ms_srv"
                                                     },
                            "LIBVIRT_REPO2_MS_SRV": {"name": "libvirt_repo2_ms_srv",
                                                     "base_url": "http://ms1/libvirt_repo2_ms_srv"
                                                     }
                            }
MS_VM1_DATA["VM_PACKAGE"] = {"PKG_EMPTY_RPM1": {"name": 'empty_rpm1'
                                                },
                             "EMPTY_TESTREPO1_RPM3": {"name": "empty_testrepo1_rpm3"
                                                      },
                             "EMPTY_RPM3": {"name": "empty_rpm3"
                                            },
                             "EMPTY_TEST_REPO2_RPM3": {"name": "empty_testrepo2_rpm3"
                                                       }
                             }
MS_VM1_DATA["NFS_MOUNT"] = {"VM_NFS_MOUNT_1": {"device_path": 'nas4:/vx/story7815-mount_1',
                                               "mount_point": '/tmp/mount_1',
                                               "mount_options": 'retrans=8,rsize=32768'
                                               },
                            "VM_NFS_MOUNT_2": {"device_path": '172.16.30.14:/vx/story7815-mount_2',
                                               "mount_point": '/tmp/mount_2'
                                               },
                            "VM_NFS_MOUNT_3": {"device_path": '172.16.30.14:/vx/story7815-mount_3',
                                               "mount_point": '/tmp/mount_3',
                                               "mount_options": 'retrans=6,rsize=16384'
                                               }
                            }
MS_VM1_DATA["SSH_KEYS"] = {"SSH_KEY_RSA_11": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEApPdyRQeCoh36f8ayxgJLg6nZvWD3nc2kV1T+6xXY6dFTlR4TBjkj5pMq6fGNzSZBfzCB7LvBz0DxLWgKYhIumt1QTFDAszULwfst94XqHd+HSAEBQ0+cZ5VQmjXtt7OpklofsSsC4SilWCJW2g1G4Lo7W5BP/qeBj/yGvE9qKnctZ26OtuO7R1fcpOIXC5KFT9cecvROijCBE90HQYLzt1VlDQn2DRqOH7w11S5abNskZrrpM2lhXorKEozORP9WrCuZW1PEnQDRGAzqKiaAw/5q/3m/L72NtUyiXzi5+92ZgvvxXSOernpeIocoPbUMVcma945dfm8FxC60/UB//Q== root@atvts1852",
                           "SSH_KEY_RSA_12": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvB3N6WOJ9qAQjGWfwpXvUWYWz8A7Ezwv/pihAYCbObDo71Ycsa3kuz2gUK9uS6Pw5DlNFAbFPk4zi/52Oj+frw4W56HnStxe13zB7ca4N0HFHMEE1QOyZ/wzv+DubwoKuz8I5yA9BD5Oli3DJXVVqxhjxRjiOQ7xs+CHsqHxzgulSJpWmbkli7BoVXsCoFN0oQmfXc7liqCciCZCvPwc+mKtJfH4oozKajwfcvyRyQhd1hqFwsaa7dxKuLww0mT6V+scduwCMVSuJH0b34Qow4ZR0XWwHGIzCf5XApypZPcuaEhRBtqpWysujlnYrkieprGn/nKna/t6USJdC9uPWQ== root@atvts1852",
                           "SSH_KEY_RSA_13": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8g3u0guI42gog7dFNBoBOtXZ+/okb+HZoTj37Iz5c60+qpehKHTdqnewxT+BX1h/GZg0CKb8+tR3GFqifBDAVXqwHfpQnGMVsHeItM09XDoYvRjWkkDAwpT3OLdEKfNmu+0rJEwvrx5w+aDsvrzfrDUGNWTBSogpXKLL1kCsCsfCNdU42xy6GygzgqyL/lo5RFBTbuDkI0Y4xSzwTxb8CPjbPcughBedWxAI0aYGh+IcV+fP2reMVeDyFqPeKiXcdL+8kWAb+pkR1WUr46dKxP/PkQGkpVEXxsjtDwisNJDFb3wC8pF3G2T5L3And01rhMg5hhLpCZn3yWSZUvjU6Q== root@atvts1852"
                           }
MS_VM1_DATA["VM_RAM_MOUNT"] = {"type": "ramfs",
                               "mount_point": "/mnt/data",
                               "mount_options": "size=512M,noexec,nodev,nosuid"
                               }
MS_VM1_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                   "custom_script_names": "csfname1.sh"
                                   }
MS_VM1_DATA["VM_DISK"] = {"VMD1": {"host_volume_group": "vg1",
                                   "host_file_system": "fs1",
                                   "mount_point": "/jump"
                                   }
                          }

#######################
# UPDATE1 MS_VM1 data #
#######################

UPDATE1_MS_VM1_DATA = dict()
UPDATE1_MS_VM1_DATA["VM_IMAGE"] = VM_IMAGES["VM_IMAGE2"]["image_name"]
UPDATE1_MS_VM1_DATA["NETWORK_INTERFACE"] = {"NET1": {"ipaddresses": "192.168.0.52"
                                                     }
                                            }
UPDATE1_MS_VM1_DATA["VM_ALIAS"] = {"DB1": {"alias_names": "dbsvc21"
                                           },
                                    "DB2": {"address": '111.222.1.22'
                                            }
                                   }
UPDATE1_MS_VM1_DATA["VM_SERVICE"] = {"hostnames": "smo-vm-ms1"}
UPDATE1_MS_VM1_DATA["VM_PACKAGE"] = {"PKG_EMPTY_RPM1": {"name": 'empty_testrepo1_rpm4'
                                                        }
                                     }
UPDATE1_MS_VM1_DATA["NFS_MOUNT"] = {"VM_NFS_MOUNT_1": {"device_path": 'nas4:/vx/story7815-mount_4',
                                                       "mount_point": '/tmp/ms_vm_update_mnt_point',
                                                       "mount_options": 'retrans=3'
                                                       }
                                    }
UPDATE1_MS_VM1_DATA["SSH_KEYS"] = {"SSH_KEY_RSA_11": "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvCuWxbw+ONUEfFEOQo9/XaqqxCoxF2yS5CchB0AmLSoPaYdnn4THXCGNuxMYOv4ABXKANNamJWGBIQjqZWqCSCnxyCCvfmCAs0M+or2Sokor7nOD99CpTeAgtmzhrWK+aupB5REy/VzW7P6vDtQxZBBXx/3vpr81ViYmuLIqSbZU1BfU2cZdDQVOXnkPAW3i3RhMLj2wvJDrsEUb0Xa6s4baqa0R94TSa4AkNvdlNE+ugKN9X3mCAZPDNd5DUogp8Oxt2wY7cZVpaEPJFO0iP5eshKvyMXikgDKwU+IqaBF8y6ShSRFSIuQFvL1OLOpo69MchE1JGu459YnoOHUGNw== root@atvts1852"}
UPDATE1_MS_VM1_DATA["VM_CUSTOM_SCRIPT"] = {"type": "vm-custom-script",
                                           "custom_script_names": "csfname2.sh,csfname3.sh,csfname1.sh"
                                           }
UPDATE1_MS_VM1_DATA["VM_DISK"] = {"VMD1": {"mount_point": "/tmp/mount_ms"
                                           },
                                  "VMD2": {"host_volume_group": "vg1",
                                           "host_file_system": "fs2",
                                           "mount_point": "/mount"
                                           }
                                  }

#######################
# UPDATE2 MS_VM1 data #
#######################
UPDATE2_MS_VM1_DATA = dict()
UPDATE2_MS_VM1_DATA["NETWORK_INTERFACE"] = {"NET2": {"host_device": 'br0',
                                                     "network_name": 'mgmt',
                                                     "device_name": 'eth1',
                                                     "ipaddresses": "192.168.0.52",
                                                     "ipv6addresses": "2001:db8:85a3::7516:24"
                                                     },
                                            "NET3": {"host_device": 'br0',
                                                     "network_name": 'mgmt',
                                                     "device_name": 'eth2',
                                                     "ipaddresses": "192.168.0.53",
                                                     "ipv6addresses": "2001:db8:85a3::7516:25"
                                                     }
                                            }

##############
# DISK1 data #
##############

DISK1_DATA = dict()
DISK1_DATA["DISK"] = {"name": "hd1",
                      "size": "1164G",
                      "bootable": "true",
                      "uuid": "6000c298af63af562a5f966fa5c10063"
                      }
DISK1_DATA["STORAGE_PROFILE"] = {"volume_driver": "lvm"}
DISK1_DATA["VOLUME_GROUP"] = {"VG1": {"volume_group_name": "vg_root",
                                      "physical_devices": {"device_name": "hd1"
                                                           },
                                      "file_system": {"fs1": {"type": "ext4",
                                                              "mount_point": "/jump",
                                                              "size": "12M"
                                                              },
                                                      "fs2": {"type": "ext4",
                                                              "mount_point": "/mount",
                                                              "size": "12M"
                                                              }
                                                      }
                                      }
                              }

############
# TIMEOUTS #
############

TIMEOUTS = dict()
TIMEOUTS["OFFLINE"] = {"CS_VM3": "300",
                       "CS_VM4": "300",
                       "CS_VM5": "300"
                       }
TIMEOUTS["ONLINE"] = {"CS_VM3": "300",
                      "CS_VM4": "300",
                      "CS_VM5": "300"
                      }

############################################
# Sleep variable for parallel failure test #
############################################

SLEEP = 60

##################################
# EXPANDED SERVICE GROUP 1 DATA #
##################################

EXPANDED_SERVICE_GROUP_1_DATA = dict()
EXPANDED_SERVICE_GROUP_1_DATA["CLUSTER_SERVICE"] = {"active": "3",
                                                    "node_list": "n1,n2,n3"
                                                    }
EXPANDED_SERVICE_GROUP_1_DATA["VM_SERVICE"] = {"image_name": VM_IMAGES["VM_IMAGE2"]["image_name"],
                                               "hostnames": "tmo-vm-1-n1,tmo-vm-1-n2,tmo-vm-1-n3"
                                               }
EXPANDED_SERVICE_GROUP_1_DATA["NETWORK_INTERFACES"] = {"NET1": {"ipaddresses": "192.168.0.30,192.168.0.31,192.168.0.32"
                                                                }
                                                       }
##################################
# CONTRACTED SERVICE GROUP 1 DATA #
##################################

CONTRACT_SERVICE_GROUP_1_DATA = dict()
CONTRACT_SERVICE_GROUP_1_DATA["CLUSTER_SERVICE"] = {"active": "1",
                                                    "node_list": "n1"
                                                    }
CONTRACT_SERVICE_GROUP_1_DATA["VM_SERVICE"] = {"image_name": VM_IMAGES["VM_IMAGE3"]["image_name"],
                                               "hostnames": "tmo-vm-1-n1"
                                               }
CONTRACT_SERVICE_GROUP_1_DATA["NETWORK_INTERFACES"] = {"NET1": {"ipaddresses": "192.168.0.2"
                                                                }
                                                       }
##################################
# EXPANDED SERVICE GROUP 2 DATA #
##################################

EXPANDED_SERVICE_GROUP_2_DATA = dict()
EXPANDED_SERVICE_GROUP_2_DATA["CLUSTER_SERVICE"] = {"active": "3",
                                                    "node_list": "n2,n3,n4"
                                                    }
EXPANDED_SERVICE_GROUP_2_DATA["VM_SERVICE"] = {"image_name": VM_IMAGES["VM_IMAGE2"]["image_name"],
                                               "hostnames": "tmo-vm-2-n2,tmo-vm-2-n3,tmo-vm-2-n4"
                                               }
EXPANDED_SERVICE_GROUP_2_DATA["NETWORK_INTERFACES"] = {"NET2": {"ipaddresses": "192.168.0.3,192.168.0.6,192.168.0.8"
                                                                },
                                                       "NET3": {"ipaddresses": "192.168.0.4,192.168.0.7,192.168.0.12"
                                                                }
                                                       }

##########################################
# UPDATE 2 EXPANDED SERVICE GROUP 1 DATA #
##########################################

EXPANDED_SERVICE_GROUP_1_UPDATE_3_DATA = dict()
EXPANDED_SERVICE_GROUP_1_UPDATE_3_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                             "node_list": "n1,n2"
                                                             }
EXPANDED_SERVICE_GROUP_1_UPDATE_3_DATA["VM_SERVICE"] = {"hostnames": "tmo-vm-1-n1,tmo-vm-1-n2"
                                                        }
EXPANDED_SERVICE_GROUP_1_UPDATE_3_DATA["NETWORK_INTERFACES"] = {"NET1": {"ipaddresses": "192.168.0.2,192.168.0.3"
                                                                         }
                                                                }

##########################################
# UPDATE 2 EXPANDED SERVICE GROUP 2 DATA #
##########################################

EXPANDED_SERVICE_GROUP_2_UPDATE_3_DATA = dict()
EXPANDED_SERVICE_GROUP_2_UPDATE_3_DATA["CLUSTER_SERVICE"] = {"active": "2",
                                                             "node_list": "n3,n1"
                                                             }
EXPANDED_SERVICE_GROUP_2_UPDATE_3_DATA["VM_SERVICE"] = {"hostnames": "tmo-vm-2-n3,tmo-vm-2-n1"
                                                        }
EXPANDED_SERVICE_GROUP_2_UPDATE_3_DATA["NETWORK_INTERFACES"] = {"NET2": {"ipaddresses": "192.168.0.6,192.168.0.8"
                                                                         },
                                                                "NET3": {"ipaddresses": "192.168.0.7,192.168.0.12"
                                                                         }
                                                                }

##########################################
# UPDATE 5 LIBVIRT SUBNET EXPANSION DATA #
##########################################

MGMT_MS_DATA = dict()
MGMT_MS_DATA["bond_link"] = "bondmgmt"
MGMT_MS_DATA["ip"] = "192.168.0.42"
MGMT_MS_DATA["network_name"] = "mgmt"
MGMT_MS_DATA["subnet"] = "192.168.0.0/16"

OVLP_MS_DATA = dict()
OVLP_MS_DATA["bond_link"] = "bondovlp"
OVLP_MS_DATA["ip"] = "192.169.0.42"
OVLP_MS_DATA["network_name"] = "ovlp"
OVLP_MS_DATA["subnet"] = "192.169.0.0/16"

OVLP_N_DATA = dict()
OVLP_N_DATA["br_link"] = "br1"
OVLP_N_DATA["mgmt_ips"] = ["192.168.0.43", "192.168.0.44"]
OVLP_N_DATA["ovlp_ips"] = ["192.169.0.43", "192.169.0.44"]

OVLP_VM_DATA = dict()
OVLP_VM_DATA["application_name"] = "vm_service_2"
OVLP_VM_DATA["ip"] = "192.169.0.2"
OVLP_VM_DATA["link"] = "eth6"
OVLP_VM_DATA["node"] = "n2"
OVLP_VM_DATA["ovlp_name"] = "netovlp"
OVLP_VM_DATA["service_name"] = "CS_VM2"
