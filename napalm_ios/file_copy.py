#
# The contents of this file are licensed under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with the
# License. You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

# Python3 support
from __future__ import print_function
from __future__ import unicode_literals

from napalm_base.file_copy import BaseFileCopy
from napalm_base.exceptions import FileTransferException
from netmiko import FileTransfer


class FileCopy(BaseFileCopy):

    def __init__(self, napalm_conn, source_file, dest_file, direction='put', file_system=None):
        self.napalm_conn = napalm_conn     # NAPALM connection
        self.source_file = source_file
        self.dest_file = dest_file
        self.direction = direction

        if not file_system:
            self.file_system = self.ctl_chan.device._autodetect_fs()
        else:
            self.file_system = file_system

        self._netmiko_scp_obj = FileTransfer(self.napalm_conn.device,
                                             source_file=self.source_file,
                                             dest_file=self.dest_file,
                                             file_system=self.file_system,
                                             direction=self.direction)

    def __enter__(self):
        raise NotImplementedError

    def __exit__(self):
        raise NotImplementedError

    def _connect(self):
        """Establish Secure Copy connection."""
        self._netmiko_scp_obj.establish_scp_conn()

    def _disconnect(self):
        """Disconnect Secure Copy connection."""
        self._netmiko_scp_obj.close_scp_chan()

    def _verify_space_and_transfer(self):
        """Verify sufficient space available and transfer file."""
        if not self._verify_space_available():
            msg = "Insufficent space available on device."
            raise FileTransferException(msg)
        self._execute_transfer()

    def _execute_transfer(self):
        """SCP transfer file."""
        if self.direction == 'put':
            self._netmiko_scp_obj.put_file()
        elif self.direction == 'get':
            self._netmiko_scp_obj.get_file()

    def _transfer_wrapper(self, direction):
        """Wrapper function that handles both put and get file transfers."""
        if self.direction != direction:
            msg = "Attempting {}, but self.direction not set to {}".format(direction, direction)
            raise FileTransferException(msg)

        if not self._check_file_exists():
            self._verify_space_and_transfer()
        else:
            # File already exists, check current MD5
            if self._compare_md5():
                self._verify_space_and_transfer()
            else:
                # File already matches
                return None

        # File transferred verify MD5
        if not self._compare_md5():
            msg = "File transferred to remote device, but MD5 does not match."
            raise FileTransferException(msg)

        return None

    def get_file(self):
        """
        Transfer file from control machine to remote network device.

        Raises FileTransferException on failure.
        """
        return self._transfer_wrapper(direction='get')

    def put_file(self):
        """
        Transfer file from control machine to remote network device.

        Raises FileTransferException on failure.
        """
        return self._transfer_wrapper(direction='put')

    def _remote_md5(self):
        """Always return the MD5 from the remote device (maybe source or dest file)."""
        if self.direction == 'put':
            return self._netmiko_scp_obj.remote_md5(remote_file=self.dest_file)
        elif self.direction == 'get':
            return self._netmiko_scp_obj.source_md5

    def _local_md5(self):
        """Always return the MD5 from the control machine (maybe source or dest file)."""
        if self.direction == 'put':
            return self._netmiko_scp_obj.source_md5
        if self.direction == 'get':
            return self._netmiko_scp_obj.file_md5(self.dest_file)

    def _compare_md5(self):
        """
        MD5 comparison between source and dest file (after transfer).

        Return boolean
        """
        return self._remote_md5() == self._local_md5()

    def _remote_space_available(self):
        """Return space available on remote device."""
        return self._netmiko_scp_obj.remote_space_available()

    def _local_space_available(self):
        """Return space available on control machine."""
        return self._netmiko_scp_obj.local_space_available()

    def _verify_space_available(self):
        """
        Check whether sufficient space available for file.

        Automatically checks direction of file transfer.

        Returns boolean.
        """
        return self._netmiko_scp_obj.verify_space_available()

    def _check_file_exists(self):
        """
        Check whether file already exists.

        Automatically checks direction of file transfer.

        Returns boolean.
        """
        return self._netmiko_scp_obj.check_file_exists()

    def _remote_file_size(self):
        """Return size of file on remote machine."""
        return self._netmiko_scp_obj.remote_file_size()

    def _local_file_size(self):
        """Return size of file on control machine."""
        return self._netmiko_scp_obj.file_size
