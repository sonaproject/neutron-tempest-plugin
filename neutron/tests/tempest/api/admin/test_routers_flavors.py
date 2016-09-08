#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from tempest.lib import exceptions as lib_exc
from tempest import test
import testtools

from neutron.tests.tempest.api import base_routers as base


class RoutersFlavorTestCase(base.BaseRouterTest):

    @classmethod
    @test.requires_ext(extension="router", service="network")
    @test.requires_ext(extension="flavors", service="network")
    def skip_checks(cls):
        super(RoutersFlavorTestCase, cls).skip_checks()

    @classmethod
    def resource_setup(cls):
        super(RoutersFlavorTestCase, cls).resource_setup()
        cls.service_profiles = []
        cls.flavor_service_profiles = []
        # make a flavor based on legacy router for regular tenant to use
        driver = ('neutron.services.l3_router.service_providers.'
                  'single_node.SingleNodeDriver')
        sp = cls.admin_client.create_service_profile(driver=driver)
        cls.service_profiles.append(sp['service_profile'])
        cls.flavor = cls.create_flavor(
                name='special_flavor',
                description='econonomy class',
                service_type='L3_ROUTER_NAT')
        cls.admin_client.create_flavor_service_profile(
            cls.flavor['id'], sp['service_profile']['id'])
        cls.flavor_service_profiles.append((cls.flavor['id'],
                                            sp['service_profile']['id']))

    @classmethod
    def resource_cleanup(cls):
        for flavor_id, service_profile_id in cls.flavor_service_profiles:
            cls.admin_client.delete_flavor_service_profile(flavor_id,
                                                           service_profile_id)
        for service_profile in cls.service_profiles:
            cls.admin_client.delete_service_profile(
                service_profile['id'])
        super(RoutersFlavorTestCase, cls).resource_cleanup()

    @test.idempotent_id('a4d01977-e968-4983-b4d9-824ea6c33f4b')
    def test_create_router_with_flavor(self):
        # ensure regular client can see flavor
        flavors = self.client.list_flavors(id=self.flavor['id'])
        flavor = flavors['flavors'][0]
        self.assertEqual('special_flavor', flavor['name'])

        # ensure client can create router with flavor
        router = self.create_router('name', flavor_id=flavor['id'])
        self.assertEqual(flavor['id'], router['flavor_id'])

    @test.idempotent_id('30e73858-a0fc-409c-a2e0-e9cd2826f6a2')
    def test_delete_router_flavor_in_use(self):
        self.create_router('name', flavor_id=self.flavor['id'])
        with testtools.ExpectedException(lib_exc.Conflict):
            self.admin_client.delete_flavor(self.flavor['id'])

    @test.idempotent_id('83939cf7-5070-41bc-9a3e-cd9f22df2186')
    def test_badrequest_on_requesting_flags_and_flavor(self):
        with testtools.ExpectedException(lib_exc.BadRequest):
            self.admin_client.create_router(
                'name', flavor_id=self.flavor['id'], distributed=True)
