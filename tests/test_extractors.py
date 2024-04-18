import json
import os

import pytest
import mock

from rpe.exceptions import ExtractorException
from rpe.extractors.gcp_auditlogs import GCPAuditLog
from rpe.resources.gcp import GcpComputeDisk, GcpComputeInstance, GcpStorageBucket
from rpe.extractors.micromanager import MicromanagerEvaluationRequest


def get_test_data(filename):
    """Load json data from the tests dir"""
    p = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "data",
        filename,
    )

    with open(p) as f:
        return json.load(f)


# parameters for testing logs that should return a single asset
test_single_asset_log_params = [
    # filename, expected_resource_type, expected_operation_type, expected_resource_name
    (
        "app-engine-debug.json",
        "appengine.googleapis.com/Instance",
        "update",
        "aef-default-test-instance",
    ),
    ("bq-ds-set-iam-policy.json", "bigquery.googleapis.com/Dataset", "update", "wooo"),
    (
        "bigtable-set-iam-policy.json",
        "bigtableadmin.googleapis.com/Instance",
        "update",
        "example-instance",
    ),
    (
        "pubsub-subscription-set-iam-policy.json",
        "pubsub.googleapis.com/Subscription",
        "update",
        "test-subscription",
    ),
    (
        "pubsub-topic-set-iam-policy.json",
        "pubsub.googleapis.com/Topic",
        "update",
        "test-topic",
    ),
    # CloudSQL logs are inconsistent. See https://issuetracker.google.com/issues/137629452
    (
        "cloudsql-resource.labels.json",
        "sqladmin.googleapis.com/Instance",
        "create",
        "test-instance",
    ),
    (
        "cloudsql-protoPayload.request.body.json",
        "sqladmin.googleapis.com/Instance",
        "create",
        "test-instance",
    ),
    (
        "cloudsql-protoPayload.request.resource.instanceName.instanceId.json",
        "sqladmin.googleapis.com/Instance",
        "create",
        "test-instance",
    ),
    (
        "cloudfunctions-set-iam-policy.json",
        "cloudfunctions.googleapis.com/CloudFunction",
        "update",
        "example_function",
    ),
    (
        "compute_networks_insert_1.json",
        "compute.googleapis.com/Network",
        "create",
        "xyz",
    ),
    (
        "compute_networks_insert_2.json",
        "compute.googleapis.com/Network",
        "create",
        "xyzcli",
    ),
    (
        "compute_networks_insert_3.json",
        "compute.googleapis.com/Network",
        "update",
        "datalab-network",
    ),
    (
        "compute-subnetworks-enable-flow-logs.json",
        "compute.googleapis.com/Subnetwork",
        "update",
        "example",
    ),
    (
        "compute-subnetworks-set-private-ip-google-access.json",
        "compute.googleapis.com/Subnetwork",
        "update",
        "example",
    ),
    (
        "compute-firewalls-enable-logs-policy.json",
        "compute.googleapis.com/Firewall",
        "create",
        "test-firewall",
    ),
    (
        "dataproc_createcluster.json",
        "dataproc.googleapis.com/Cluster",
        "create",
        "test-dataproc-cluster",
    ),
    (
        "datafusion-create-instance.json",
        "datafusion.googleapis.com/Instance",
        "create",
        "test-instance",
    ),
    (
        "datafusion-update-instance.json",
        "datafusion.googleapis.com/Instance",
        "update",
        "test-instance",
    ),
    (
        "gke-cluster-update.json",
        "container.googleapis.com/Cluster",
        "update",
        "example-cluster",
    ),
    (
        "gke-nodepool-set.json",
        "container.googleapis.com/NodePool",
        "update",
        "example-pool",
    ),
    (
        "project_get_iam.json",
        "cloudresourcemanager.googleapis.com/Project",
        "read",
        "cd-np-test1",
    ),
    (
        "project_set_iam.json",
        "cloudresourcemanager.googleapis.com/Project",
        "update",
        "cd-np-test1",
    ),
    (
        "servicemanagement-enable-service.json",
        "serviceusage.googleapis.com/Service",
        "update",
        "youtubeadsreach.googleapis.com",
    ),
    (
        "servicemanagement-disable-service.json",
        "serviceusage.googleapis.com/Service",
        "update",
        "youtubereporting.googleapis.com",
    ),
    (
        "servicemanagement-activate-service.json",
        "serviceusage.googleapis.com/Service",
        "update",
        "calendar-json.googleapis.com",
    ),
    (
        "servicemanagement-deactivate-service.json",
        "serviceusage.googleapis.com/Service",
        "update",
        "zync.googleapis.com",
    ),
    (
        "serviceusage-enable.json",
        "serviceusage.googleapis.com/Service",
        "update",
        "youtubereporting.googleapis.com",
    ),
    (
        "serviceusage-disable.json",
        "serviceusage.googleapis.com/Service",
        "update",
        "zync.googleapis.com",
    ),
    (
        "storage_bucket_delete.json",
        "storage.googleapis.com/Bucket",
        "delete",
        "test-bucket",
    ),
    (
        "storage_bucket_update.json",
        "storage.googleapis.com/Bucket",
        "update",
        "test-bucket",
    ),
    ("dataflow-job-step.json", "dataflow.googleapis.com/Job", "create", "job-id"),
    (
        "memorystore-redis.json",
        "redis.googleapis.com/Instance",
        "create",
        "test-instance",
    ),
    (
        "dataform-create-repository.json",
        "dataform.googleapis.com/Repository",
        "create",
        "test-repository",
    ),
    (
        "dataform-create-workspace.json",
        "dataform.googleapis.com/Workspace",
        "create",
        "test-workspace",
    ),
    (
        "dataform-update-repository.json",
        "dataform.googleapis.com/Repository",
        "update",
        "test-repository",
    ),
]

test_micromanager_log = [
    (
        "compute_instance_micromanager.json",
        "test-instance",
        GcpComputeInstance,
        True,
        "instance",
        "instance-message-id",
    ),
    (
        "storage_bucket_micromanager.json",
        "test-bucket",
        GcpStorageBucket,
        True,
        "bucket",
        "bucket-message-id",
    ),
    (
        "storage_bucket_no_metadata_micromanager.json",
        "test-bucket",
        GcpStorageBucket,
        False,
        {},
        "bucket-message-id",
    ),
]

test_log_resource_count_params = [
    ("serviceusage-batchenable.json", 3),
    ("compute-hardened-images.json", 3),
]


@pytest.mark.parametrize(
    "filename,expected_resource_type,expected_operation_type,expected_resource_name",
    test_single_asset_log_params,
)
def test_single_asset_log_messages(
    filename, expected_resource_type, expected_operation_type, expected_resource_name
):
    log_message = get_test_data(filename)

    extracted = GCPAuditLog.extract(log_message)

    assert len(extracted.resources) == 1
    resource = extracted.resources[0]

    assert resource.resource_type == expected_resource_type
    assert extracted.metadata.operation == expected_operation_type
    assert resource.resource_name == expected_resource_name


@pytest.mark.parametrize(
    "filename, expected_resource_name, expected_resource_class, has_message_metadata, "
    "expected_message_metadata, expected_message_id",
    test_micromanager_log,
)
def test_micromanager_extractor(
    filename,
    expected_resource_name,
    expected_resource_class,
    has_message_metadata,
    expected_message_metadata,
    expected_message_id,
):
    log_message = get_test_data(filename)
    mock_context = mock.Mock(spec=["data", "publish_time", "message_id", "attributes"])
    mock_context.data = json.dumps(log_message.get("data"), indent=2).encode("utf-8")
    mock_context.publish_time = log_message.get("publish_time")
    mock_context.message_id = log_message.get("message_id")
    mock_context.attributes = log_message.get("attributes")

    extracted = MicromanagerEvaluationRequest.extract(mock_context)

    assert len(extracted.resources) == 1
    resource = extracted.resources[0]
    metadata = extracted.metadata

    assert resource.resource_name == expected_resource_name
    assert resource.__class__ == expected_resource_class
    assert hasattr(metadata, "src") == has_message_metadata
    if hasattr(metadata, "src"):
        assert metadata.src == expected_message_metadata
    assert metadata.message_id == expected_message_id


@pytest.mark.parametrize(
    "filename,expected_resource_count", test_log_resource_count_params
)
def test_log_resource_count(filename, expected_resource_count):
    log_message = get_test_data(filename)

    extracted = GCPAuditLog.extract(log_message)
    assert len(extracted.resources) == expected_resource_count


@pytest.mark.parametrize(
    "filename,expected_disk_names",
    [
        ("compute_instance_creation_logs_1.json", ["console-devicenames", "disk2name"]),
        ("compute_instance_creation_logs_2.json", []),
        ("compute_instance_creation_logs_3.json", ["console-nochange"]),
        ("compute_instance_creation_logs_4.json", ["gcloud-devicename-mismatch"]),
        (
            "compute_instance_creation_logs_5.json",
            ["demo-testing-good-boot", "demo-testing-good-data"],
        ),
    ],
)
def test_compute_instance_logs_get_disk_names(filename, expected_disk_names):
    """
    Instance creation audit logs contain details about the disks, but extracting the disk name is
    complicated. This tests multiple known log formats for instance creation against expected disk names.
    """

    log = get_test_data(filename)

    extracted = GCPAuditLog.extract(log)

    disk_names = [
        resource.resource_name
        for resource in extracted.resources
        if resource.type() == GcpComputeDisk.resource_type
    ]
    assert sorted(disk_names) == sorted(expected_disk_names)


def test_invalid_audit_log():
    with pytest.raises(ExtractorException):
        GCPAuditLog.extract({})
