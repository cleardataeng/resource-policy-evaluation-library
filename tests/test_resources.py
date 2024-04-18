# Copyright 2019 The resource-policy-evaluation-library Authors. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import collections

import pytest
from google.oauth2.credentials import Credentials
from googleapiclient.http import HttpMockSequence

from rpe.exceptions import ResourceException
from rpe.resources.gcp import (
    GcpAppEngineInstance,
    GcpBigqueryDataset,
    GcpBigtableInstance,
    GcpCloudFunction,
    GcpComputeDisk,
    GcpComputeFirewall,
    GcpComputeInstance,
    GcpComputeSubnetwork,
    GcpDataflowJob,
    GcpDatafusionInstance,
    GcpDataprocCluster,
    GcpDataformRepository,
    GcpDataformWorkspace,
    GcpGkeCluster,
    GcpGkeClusterNodepool,
    GcpMemcacheInstance,
    GcpOrganization,
    GcpProject,
    GcpProjectService,
    GcpPubsubSubscription,
    GcpPubsubTopic,
    GcpRedisInstance,
    GcpSqlInstance,
    GcpStorageBucket,
    GoogleAPIResource,
)

test_project = "my_project"
test_resource_name = "my_resource"
client_kwargs = {"credentials": Credentials(token="")}

ResourceTestCase = collections.namedtuple(
    "ResourceTestCase", "resource_data cls resource_type name http uniquifier"
)

test_cases = [
    ResourceTestCase(
        resource_data={
            "name": "my_resource",
            "app": "my_project",
            "service": "default",
            "version": "0123456789",
            "project_id": test_project,
        },
        cls=GcpAppEngineInstance,
        resource_type="appengine.googleapis.com/Instance",
        name="//appengine.googleapis.com/apps/my_project/services/default/versions/0123456789/instances/my_resource",
        http=HttpMockSequence(
            [
                (
                    {"status": 200},
                    '{"name":"name", "startTime":"appEngine_startTime", "vmStatus" : "RUNNING"}',
                ),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="appEngine_startTime",
    ),
    ResourceTestCase(
        resource_data={"name": test_resource_name, "project_id": test_project},
        cls=GcpBigqueryDataset,
        resource_type="bigquery.googleapis.com/Dataset",
        name="//bigquery.googleapis.com/projects/my_project/datasets/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "id":"dataset_id"}'),
            ]
        ),
        uniquifier="dataset_id",
    ),
    ResourceTestCase(
        resource_data={"name": test_resource_name, "project_id": test_project},
        cls=GcpBigtableInstance,
        resource_type="bigtableadmin.googleapis.com/Instance",
        name="//bigtable.googleapis.com/projects/my_project/instances/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "state":"READY"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1-a",
            "project_id": test_project,
        },
        cls=GcpCloudFunction,
        resource_type="cloudfunctions.googleapis.com/CloudFunction",
        name="//cloudfunctions.googleapis.com/projects/my_project/locations/us-central1-a/functions/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "status":"ACTIVE"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1-a",
            "project_id": test_project,
        },
        cls=GcpComputeDisk,
        resource_type="compute.googleapis.com/Disk",
        name="//compute.googleapis.com/projects/my_project/zones/us-central1-a/disks/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "id":"disk_id"}'),
            ]
        ),
        uniquifier="disk_id",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1-a",
            "project_id": test_project,
        },
        cls=GcpComputeInstance,
        resource_type="compute.googleapis.com/Instance",
        name="//compute.googleapis.com/projects/my_project/zones/us-central1-a/instances/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "id":"disk_id"}'),
            ]
        ),
        uniquifier="disk_id",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1-a",
            "project_id": test_project,
        },
        cls=GcpGkeCluster,
        resource_type="container.googleapis.com/Cluster",
        name="//container.googleapis.com/projects/my_project/locations/us-central1-a/clusters/my_resource",
        http=HttpMockSequence(
            [
                (
                    {"status": 200},
                    '{"name":"name", "id":"cluster_id", "status" : "RUNNING"}',
                ),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="cluster_id",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1-a",
            "cluster": "parent_resource",
            "project_id": test_project,
        },
        cls=GcpGkeClusterNodepool,
        resource_type="container.googleapis.com/NodePool",
        name="//container.googleapis.com/projects/my_project/locations/us-central1-a/clusters/parent_resource/nodePools/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "status" : "RUNNING"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={
            "name": "012345678901",
        },
        cls=GcpOrganization,
        resource_type="cloudresourcemanager.googleapis.com/Organization",
        name="//cloudresourcemanager.googleapis.com/organizations/012345678901",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name"}'),
            ]
        ),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={"name": test_project, "project_id": test_project},
        cls=GcpProject,
        resource_type="cloudresourcemanager.googleapis.com/Project",
        name="//cloudresourcemanager.googleapis.com/projects/my_project",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "projectNumber":"project_number"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="project_number",
    ),
    ResourceTestCase(
        resource_data={"name": "compute.googleapis.com", "project_id": test_project},
        cls=GcpProjectService,
        resource_type="serviceusage.googleapis.com/Service",
        name="//serviceusage.googleapis.com/projects/my_project/services/compute.googleapis.com",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name"}'),
            ]
        ),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
        },
        cls=GcpDatafusionInstance,
        resource_type="datafusion.googleapis.com/Instance",
        name="//datafusion.googleapis.com/projects/my_project/locations/us-central1/instances/my_resource",
        http=HttpMockSequence(
            [
                (
                    {"status": 200},
                    '{"name":"name", "createTime":"datafusion_createTime" , "state":"RUNNING"}',
                ),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="datafusion_createTime",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "global",
            "project_id": test_project,
        },
        cls=GcpDataprocCluster,
        resource_type="dataproc.googleapis.com/Cluster",
        name="//dataproc.googleapis.com/projects/my_project/regions/global/clusters/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "clusterUuid":"cluster_Uuid"}'),
            ]
        ),
        uniquifier="cluster_Uuid",
    ),
    ResourceTestCase(
        resource_data={"name": test_resource_name, "project_id": test_project},
        cls=GcpPubsubSubscription,
        resource_type="pubsub.googleapis.com/Subscription",
        name="//pubsub.googleapis.com/projects/my_project/subscriptions/my_resource",
        http=HttpMockSequence([({"status": 200}, '{"name":"name"}')]),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={"name": test_resource_name, "project_id": test_project},
        cls=GcpPubsubTopic,
        resource_type="pubsub.googleapis.com/Topic",
        name="//pubsub.googleapis.com/projects/my_project/topics/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name"}'),
            ]
        ),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={"name": test_resource_name, "project_id": test_project},
        cls=GcpSqlInstance,
        resource_type="sqladmin.googleapis.com/Instance",
        name="//cloudsql.googleapis.com/projects/my_project/instances/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name" , "state":"RUNNABLE"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier=None,
    ),
    ResourceTestCase(
        resource_data={"name": test_resource_name, "project_id": test_project},
        cls=GcpStorageBucket,
        resource_type="storage.googleapis.com/Bucket",
        # This should include the collection name `/buckets/`, but CAI doesn't do that
        # See: https://issuetracker.google.com/issues/131586763
        name="//storage.googleapis.com/my_resource",
        http=HttpMockSequence(
            [
                (
                    {"status": 200},
                    '{"name":"name", "timeCreated":"bucket_timeCreated"}',
                ),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="bucket_timeCreated",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
        },
        cls=GcpComputeSubnetwork,
        resource_type="compute.googleapis.com/Subnetwork",
        name="//compute.googleapis.com/projects/my_project/regions/us-central1/subnetworks/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "id":"subnetwork_id"}'),
            ]
        ),
        uniquifier="subnetwork_id",
    ),
    ResourceTestCase(
        resource_data={"name": test_resource_name, "project_id": test_project},
        cls=GcpComputeFirewall,
        resource_type="compute.googleapis.com/Firewall",
        name="//compute.googleapis.com/projects/my_project/global/firewalls/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "id":"firewall_id"}'),
            ]
        ),
        uniquifier="firewall_id",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
        },
        cls=GcpDataflowJob,
        resource_type="dataflow.googleapis.com/Job",
        name="//dataflow.googleapis.com/projects/my_project/locations/us-central1/jobs/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"name":"name", "id":"dataflow_id"}'),
            ]
        ),
        uniquifier="dataflow_id",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
        },
        cls=GcpRedisInstance,
        resource_type="redis.googleapis.com/Instance",
        name="//redis.googleapis.com/projects/my_project/locations/us-central1/instances/my_resource",
        http=HttpMockSequence(
            [
                (
                    {"status": 200},
                    '{"name":"name", "createTime":"redis_createTime", "state":"READY"}',
                ),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="redis_createTime",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
        },
        cls=GcpMemcacheInstance,
        resource_type="memcache.googleapis.com/Instance",
        name="//memcache.googleapis.com/projects/my_project/locations/us-central1/instances/my_resource",
        http=HttpMockSequence(
            [
                (
                    {"status": 200},
                    '{"name":"name", "createTime":"memcache_createTime", "state":"READY"}',
                ),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="memcache_createTime",
    ),
]

location_test_cases = [
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1-a",
            "project_id": test_project,
        },
        cls=GcpRedisInstance,
        resource_type="redis.googleapis.com/Instance",
        name="//redis.googleapis.com/projects/my_project/locations/us-central1/instances/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"createTime":"createTime"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="startTime",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
        },
        cls=GcpMemcacheInstance,
        resource_type="memcache.googleapis.com/Instance",
        name="//memcache.googleapis.com/projects/my_project/locations/us-central1/instances/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"createTime":"createTime"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="createTime",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
        },
        cls=GcpDataformRepository,
        resource_type="dataform.googleapis.com/Repository",
        name="//dataform.googleapis.com/projects/my_project/locations/us-central1/repositories/my_resource",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"createTime":"createTime"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="createTime",
    ),
    ResourceTestCase(
        resource_data={
            "name": test_resource_name,
            "location": "us-central1",
            "project_id": test_project,
            "repository": "test_repository",
        },
        cls=GcpDataformWorkspace,
        resource_type="dataform.googleapis.com/Workspace",
        name="//dataform.googleapis.com/projects/my_project/locations/us-central1/repositories/test_repository/workspaces/test_resource_name",
        http=HttpMockSequence(
            [
                ({"status": 200}, '{"createTime":"createTime"}'),
                ({"status": 200}, "{}"),
            ]
        ),
        uniquifier="createTime",
    ),
]


@pytest.mark.parametrize(
    "case", test_cases, ids=[case.cls.__name__ for case in test_cases]
)
def test_gcp_from_resource(case):
    r = GoogleAPIResource.from_resource_data(
        resource_type=case.resource_type, http=case.http, **case.resource_data
    )
    assert r.__class__ == case.cls
    assert isinstance(r._get_request_args(), dict)
    assert r.uniquifier == case.uniquifier


def test_gcp_from_resource_no_type():
    with pytest.raises(TypeError) as excinfo:
        GoogleAPIResource.from_resource_data(project_id=test_project)

    assert "required keyword-only argument" in str(excinfo.value)
    assert "resource_type" in str(excinfo.value)


def test_gcp_resource_bad_type():
    with pytest.raises(ResourceException) as excinfo:
        GoogleAPIResource.from_resource_data(resource_type="fake.type")

    assert "Unrecognized resource type" in str(excinfo.value)


@pytest.mark.parametrize(
    "case", test_cases, ids=[case.cls.__name__ for case in test_cases]
)
def test_gcp_full_resource_name(case):
    r = GoogleAPIResource.from_resource_data(
        resource_type=case.resource_type,
        client_kwargs=client_kwargs,
        **case.resource_data
    )
    assert r.full_resource_name() == case.name


@pytest.mark.parametrize(
    "case", location_test_cases, ids=[case.cls.__name__ for case in location_test_cases]
)
def test_gcp_location(case):
    r = GoogleAPIResource.from_resource_data(
        resource_type=case.resource_type,
        client_kwargs=client_kwargs,
        **case.resource_data
    )
    assert r.location == case.resource_data.get("location")


def test_missing_resource_data():
    with pytest.raises(ResourceException) as excinfo:
        GcpAppEngineInstance(name=test_resource_name)

    assert "Missing data required for resource creation" in str(excinfo.value)


def test_gcp_to_dict():
    r = GoogleAPIResource.from_resource_data(
        resource_type="storage.googleapis.com/Bucket",
        client_kwargs=client_kwargs,
        name=test_resource_name,
        project_id=test_project,
    )

    data = r.to_dict()
    # with no creds, we should still get this key but it should be none
    assert data["project_id"] == test_project
