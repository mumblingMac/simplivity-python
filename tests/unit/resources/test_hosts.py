###
# (C) Copyright [2019-2020] Hewlett Packard Enterprise Development LP
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
##

import unittest
from unittest import mock

from simplivity.connection import Connection
from simplivity import exceptions
from simplivity.resources import hosts


class HostsTest(unittest.TestCase):
    def setUp(self):
        self.connection = Connection('127.0.0.1')
        self.connection._access_token = "123456789"
        self.hosts = hosts.Hosts(self.connection)

    @mock.patch.object(Connection, "get")
    def test_get_all_returns_resource_obj(self, mock_get):
        url = "{}?case=sensitive&limit=500&offset=0&order=descending&sort=name".format(hosts.URL)
        resource_data = [{'id': '12345'}, {'id': '67890'}]
        mock_get.return_value = {hosts.DATA_FIELD: resource_data}

        objs = self.hosts.get_all()
        self.assertIsInstance(objs[0], hosts.Host)
        self.assertEqual(objs[0].data, resource_data[0])
        mock_get.assert_called_once_with(url)

    @mock.patch.object(Connection, "get")
    def test_get_by_name_found(self, mock_get):
        name = "testname"
        url = "{}?case=sensitive&limit=500&name={}&offset=0&order=descending&sort=name".format(hosts.URL, name)
        resource_data = [{'id': '12345', 'name': name}]
        mock_get.return_value = {hosts.DATA_FIELD: resource_data}

        obj = self.hosts.get_by_name(name)
        self.assertIsInstance(obj, hosts.Host)
        mock_get.assert_called_once_with(url)

    @mock.patch.object(Connection, "get")
    def test_get_by_name_not_found(self, mock_get):
        name = "testname"
        resource_data = []
        mock_get.return_value = {hosts.DATA_FIELD: resource_data}

        with self.assertRaises(exceptions.HPESimpliVityResourceNotFound) as error:
            self.hosts.get_by_name(name)

        self.assertEqual(error.exception.msg, "Resource not found with the name {}".format(name))

    @mock.patch.object(Connection, "get")
    def test_get_by_id_found(self, mock_get):
        resource_id = "12345"
        url = "{}?case=sensitive&id={}&limit=500&offset=0&order=descending&sort=name".format(hosts.URL, resource_id)
        resource_data = [{'id': resource_id}]
        mock_get.return_value = {hosts.DATA_FIELD: resource_data}

        obj = self.hosts.get_by_id(resource_id)
        self.assertIsInstance(obj, hosts.Host)
        mock_get.assert_called_once_with(url)

    @mock.patch.object(Connection, "get")
    def test_get_by_id_not_found(self, mock_get):
        resource_id = "12345"
        resource_data = []
        mock_get.return_value = {hosts.DATA_FIELD: resource_data}

        with self.assertRaises(exceptions.HPESimpliVityResourceNotFound) as error:
            self.hosts.get_by_id(resource_id)

        self.assertEqual(error.exception.msg, "Resource not found with the id {}".format(resource_id))

    def test_get_by_data(self):
        resource_data = {'id': '12345'}

        obj = self.hosts.get_by_data(resource_data)
        self.assertIsInstance(obj, hosts.Host)
        self.assertEqual(obj.data, resource_data)

    @mock.patch.object(Connection, "post")
    def test_remove(self, mock_post):
        mock_post.return_value = None, [{"object_id": "12345"}]

        host_data = {"id": "12345"}
        host = self.hosts.get_by_data(host_data)

        host.remove()
        self.assertEqual(host.data, None)

        mock_post.assert_called_once_with(
            "/hosts/12345/remove_from_federation",
            {"force": False},
            custom_headers={"Content-type": "application/vnd.simplivity.v1.9+json"},
        )

    @mock.patch.object(Connection, "post")
    def test_remove_with_force(self, mock_post):
        mock_post.return_value = None, [{"object_id": "12345"}]

        host_data = {"id": "12345"}
        host = self.hosts.get_by_data(host_data)

        host.remove(force=True)
        self.assertEqual(host.data, None)

        mock_post.assert_called_once_with(
            "/hosts/12345/remove_from_federation",
            {"force": True},
            custom_headers={"Content-type": "application/vnd.simplivity.v1.9+json"},
        )

    @mock.patch.object(Connection, "get")
    def test_get_hardware(self, mock_get):
        resource_data = {"host": {"serial_number": "abcdef", "manufacturer": "HPE",
                                  "model_number": "ProLiant DL380 Gen9", "status": "GREEN",
                                  "host_id": "12345"
                                  }}

        mock_get.return_value = resource_data
        host_data = {"id": "12345"}
        host = self.hosts.get_by_data(host_data)

        hardware_data = host.get_hardware()
        self.assertEqual(hardware_data, resource_data)

    @mock.patch.object(Connection, "get")
    def test_get_virtual_controller_shutdown_status(self, mock_get):
        resource_data = {"shutdown_status": {"status": "NONE"}}
        mock_get.return_value = resource_data
        host_data = {"id": "12345"}
        host = self.hosts.get_by_data(host_data)

        virtual_controller_status = host.get_virtual_controller_shutdown_status()
        self.assertEqual(virtual_controller_status, 'NONE')

    @mock.patch.object(Connection, "post")
    def test_shutdown_virtual_controller_ha_wait(self, mock_post):
        mock_post.return_value = None, {'shutdown_status': {'status': 'IN_PROGRESS'}}
        host_data = {"id": "12345"}
        host = self.hosts.get_by_data(host_data)
        response = host.shutdown_virtual_controller()
        self.assertEqual(response, 'IN_PROGRESS')
        mock_post.assert_called_once_with("/hosts/12345/shutdown_virtual_controller",
                                          {"ha_wait": True}, custom_headers=None)

    @mock.patch.object(Connection, "post")
    def test_shutdown_virtual_controller(self, mock_post):
        mock_post.return_value = None, {'shutdown_status': {'status': 'IN_PROGRESS'}}
        host_data = {"id": "12345"}
        host = self.hosts.get_by_data(host_data)

        response = host.shutdown_virtual_controller(ha_wait=False)
        self.assertEqual(response, 'IN_PROGRESS')
        mock_post.assert_called_once_with("/hosts/12345/shutdown_virtual_controller",
                                          {"ha_wait": False}, custom_headers=None)

    @mock.patch.object(Connection, "post")
    def test_cancel_virtual_controller_shutdown(self, mock_post):
        mock_post.return_value = None, {'cancellation_status': {'status': 'SUCCESS'}}
        host_data = {"id": "12345"}
        host = self.hosts.get_by_data(host_data)

        response = host.cancel_virtual_controller_shutdown()
        self.assertEqual(response, "SUCCESS")
        mock_post.assert_called_once_with("/hosts/12345/cancel_virtual_controller_shutdown", None,
                                          custom_headers=None)


if __name__ == '__main__':
    unittest.main()
