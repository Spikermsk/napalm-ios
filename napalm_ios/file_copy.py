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
        self._netmiko_scp_obj.establish_scp_conn()

    def _disconnect(self):
        self._netmiko_scp_obj.close_scp_chan()

    def get_file(self):
        if self.direction != 'get':
            msg = "Attempting get_file, but direction not set to get."
            raise FileTransferException(msg)
        self._netmiko_scp_obj.get_file()

    def _verify_space_and_transfer(self):
        """Verify sufficient space available and transfer file."""
        if not self._verify_space_available():
            msg = "Insufficent space available on device."
            raise FileTransferException(msg)
        self._transfer_file(self)

    def _transfer_file(self):
        """SCP transfer file."""
        if self.direction == 'put':
            self._netmiko_scp_obj.put_file()
        elif self.direction == 'get':
            self._netmiko_scp_obj.get_file()

    def put_file(self):
        """
        Transfer file from control machine to remote network device.
    
        Raises FileTransferException on failure.
        """
        if self.direction != 'put':
            msg = "Attempting put_file, but direction not set to put."
            raise FileTransferException(msg)

        if not self._check_file_exists():
            self._verify_space_and_transfer()
        else:
            # File already exists, check current MD5
            if self._remote_md5() != self._local_md5():
                self._verify_space_and_transfer()
            else:
                # File already matches
                return None

        # File transferred verify MD5
        if self._remote_md5() != self._local_md5():
            msg = "File transferred to remote device, but MD5 does not match."
            raise FileTransferException(msg)

        return None

    def _remote_md5(self):
        return self._netmiko_scp_obj.remote_md5()

    def _local_md5(self):
        return self._netmiko_scp_obj.file_md5()

    def _compare_md5(self):
        return self._netmiko_scp_obj.compare_md5()

    def _remote_space_available(self):
        return self._netmiko_scp_obj.remote_space_available()

    def _local_space_available(self):
        return self._netmiko_scp_obj.local_space_available()

    def _verify_space_available(self):
        """Return boolean indicating whether sufficient space available for file."""
        return self._netmiko_scp_obj.verify_space_available()

    def _check_file_exists(self):
        return self._netmiko_scp_obj.check_file_exists()

    def _remote_file_size(self):
        return self._netmiko_scp_obj.remote_file_size()

    def _local_file_size(self):
        return self._netmiko_scp_obj.file_size
