"""Test fixtures."""
from __future__ import print_function
from __future__ import unicode_literals

from builtins import super

import pytest
from napalm_base.test import conftest as parent_conftest

from napalm_base.test.double import BaseTestDouble
from napalm_base.utils import py23_compat

from napalm_ios import ios


@pytest.fixture(scope='class')
def set_device_parameters(request):
    """Set up the class."""
    def fin():
        request.cls.device.close()
    request.addfinalizer(fin)

    request.cls.driver = ios.IOSDriver
    request.cls.patched_driver = PatchedIOSDriver
    request.cls.vendor = 'ios'
    parent_conftest.set_device_parameters(request)


def pytest_generate_tests(metafunc):
    """Generate test cases dynamically."""
    parent_conftest.pytest_generate_tests(metafunc, __file__)


class PatchedIOSDriver(ios.IOSDriver):
    """Patched IOS Driver."""

    def __init__(self, hostname, username, password, timeout=60, optional_args=None):

        super().__init__(hostname, username, password, timeout, optional_args)

        self.patched_attrs = ['device']
        self.device = FakeIOSDevice()

    def disconnect(self):
        pass

    def is_alive(self):
        return {
            'is_alive': True  # In testing everything works..
        }

    def open(self):
        pass


class FakeIOSDevice(BaseTestDouble):
    """IOS device test double."""

    def send_command(self, command, **kwargs):
        filename = '{}.txt'.format(self.sanitize_text(command))
        full_path = self.find_file(filename)
        result = self.read_txt_file(full_path)
        return py23_compat.text_type(result)

    def disconnect(self):
        pass


@pytest.fixture(scope='module')
def scp_fixture_get(request):
    """ 
    Create an FileTransfer object (direction=get)

    Return a tuple (ssh_conn, scp_handle)
    """
    device_under_test = request.config.getoption('test_device')
    test_devices = parse_yaml(PWD + "/etc/test_devices.yml")
    device = test_devices[device_under_test]
    device['verbose'] = False
    ssh_conn = ConnectHandler(**device)

    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    local_file = 'testx.txt'
    dest_file = local_file
    direction = 'get'

    scp_transfer = FileTransfer(ssh_conn, source_file=source_file, dest_file=dest_file,
                                file_system=dest_file_system, direction=direction)
    scp_transfer.establish_scp_conn()

    # Make sure SCP is enabled
    scp_transfer.enable_scp()

    # Delete the test transfer files
    if os.path.exists(local_file):
        os.remove(local_file)

    return (ssh_conn, scp_transfer)


@pytest.fixture(scope='module')
def scp_fixture(request):
    """
    Create an FileTransfer object.

    Return a tuple (ssh_conn, scp_handle)
    """

    ip_addr = '184.105.247.70'
    username = 'pyclass'
    optional_args = {}
    optional_args['port'] = 22
    password = getpass()

    driver = get_network_driver('ios')
    device = driver(ip_addr, username, password, optional_args=optional_args)

    print()
    print(">>>Test device open")
    device.open()

    pp(device.get_facts())
   
    # ADJUST TO TRANSFER IMAGE FILE
    dest_file_system = 'flash:'
    source_file = 'test9.txt'
    dest_file = 'test9.txt'
    scp_changed = False
    direction = 'put'

    scp_transfer = FileCopy(device, source_file=source_file, dest_file=dest_file,
                            file_system=dest_file_system, direction=direction)
    scp_transfer._connect()
    ssh_conn = ConnectHandler(**device)

    # Delete the test transfer files
    #if scp_transfer.check_file_exists():
    #    delete_file_ios(ssh_conn, dest_file_system, dest_file)
    #if os.path.exists(local_file):
    #    os.remove(local_file)

    return (ssh_conn, scp_transfer)
