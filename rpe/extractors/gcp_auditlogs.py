# Copyright 2021 The resource-policy-evaluation-library Authors. All rights reserved.
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

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel

import dateutil.parser
import jmespath

from rpe.exceptions import ExtractorException
from rpe.extractors import Extractor
from rpe.extractors.models import ExtractedMetadata, ExtractedResources
from rpe.resources.gcp import GoogleAPIResource


class OperationEnum(str, Enum):
    create = "create"
    read = "read"
    update = "update"
    delete = "delete"


class GCPAuditLogMetadata(ExtractedMetadata):
    id: str
    timestamp: datetime
    principal: Optional[str]
    method_name: Optional[str]
    operation: Optional[OperationEnum]


class GCPAuditLog(Extractor):
    @classmethod
    def extract(cls, log_message):
        # Attempt to load it like a pubsub message, without requiring the pubsub client to be installed
        if not isinstance(log_message, dict):
            message_data = json.loads(log_message.data)
        else:
            message_data = log_message

        if not cls.is_audit_log(message_data):
            raise ExtractorException("Not an audit log")

        metadata = cls.get_metadata(message_data)
        resources = cls.get_resources(message_data)

        return ExtractedResources(
            resources=resources,
            metadata=metadata,
        )

    @classmethod
    def is_audit_log(cls, message_data):
        log_type = jmespath.search('protoPayload."@type"', message_data)
        log_name = message_data.get("logName", "")

        # normal activity logs have logName in this form:
        #  projects/<p>/logs/cloudaudit.googleapis.com%2Factivity
        # data access logs have a logName field that looks like:
        #  projects/<p>/logs/cloudaudit.googleapis.com%2Fdata_access

        return all(
            [
                log_type == "type.googleapis.com/google.cloud.audit.AuditLog",
                log_name.split("/")[-1].startswith("cloudaudit.googleapis.com"),
            ]
        )

    @classmethod
    def get_metadata(cls, message_data):
        method_name = jmespath.search("protoPayload.methodName", message_data)
        insert_id = message_data.get("insertId")

        log_timestamp = message_data.get("timestamp")
        timestamp = dateutil.parser.parse(log_timestamp)

        principal_email = jmespath.search(
            "protoPayload.authenticationInfo.principalEmail", message_data
        )

        operation = cls.get_operation_type(method_name)

        return GCPAuditLogMetadata(
            id=insert_id,
            timestamp=timestamp,
            method_name=method_name,
            operation=operation,
            principal=principal_email,
        )

    @classmethod
    def get_operation_type(cls, method_name):
        last = method_name.split(".")[-1].lower()
        # For batch methods, look for the verb after the word 'batch'
        if last.startswith("batch"):
            last = last[5:]

        read_prefixes = ("get", "list")
        if last.startswith(read_prefixes):
            return "read"

        update_prefixes = (
            "update",
            "patch",
            "set",
            "debug",
            "enable",
            "disable",
            "expand",
            "deactivate",
            "activate",
            "switch",
        )

        if last.startswith(update_prefixes):
            return "update"

        create_prefixes = (
            "create",
            "insert",
        )

        if last.startswith(create_prefixes):
            return "create"

        delete_prefixes = ("delete",)
        if last.startswith(delete_prefixes):
            return "delete"

        return None

    @classmethod
    def get_resources(cls, message):
        resources = []

        res_type = jmespath.search("resource.type", message)
        if res_type is None:
            return resources

        # just shortening the many calls to jmespath throughout this function
        # this sub-function saves us from passing the message each time
        def prop(exp):
            return jmespath.search(exp, message)

        def add_resource():
            r = resource_data.copy()
            res = GoogleAPIResource.from_resource_data(**r)
            resources.append(res)

        method_name = prop("protoPayload.methodName")

        if res_type == "cloudsql_database" and method_name.startswith(
            "cloudsql.instances"
        ):
            resource_data = {
                "resource_type": "sqladmin.googleapis.com/Instance",
                # CloudSQL logs are inconsistent. See https://issuetracker.google.com/issues/137629452
                "name": (
                    prop("resource.labels.database_id").split(":")[-1]
                    or prop("protoPayload.request.body.name")
                    or prop("protoPayload.request.resource.instanceName.instanceId")
                ),
                "location": prop("resource.labels.region"),
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "gcs_bucket" and method_name.startswith(
            ("storage.buckets", "storage.setIamPermissions")
        ):
            resource_data = {
                "resource_type": "storage.googleapis.com/Bucket",
                "name": prop("resource.labels.bucket_name"),
                "location": prop("resource.labels.location"),
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "bigquery_dataset":
            if "DatasetService" in method_name or "etIamPolicy" in method_name:
                resource_data = {
                    "resource_type": "bigquery.googleapis.com/Dataset",
                    "name": prop("resource.labels.dataset_id"),
                    "project_id": prop("resource.labels.project_id"),
                }
                add_resource()

        elif res_type == "project" and "etIamPolicy" in method_name:
            resource_data = {
                "resource_type": "cloudresourcemanager.googleapis.com/Project",
                "name": prop("resource.labels.project_id"),
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "pubsub_subscription" and "etIamPolicy" in method_name:
            resource_data = {
                "resource_type": "pubsub.googleapis.com/Subscription",
                "name": prop("resource.labels.subscription_id").split("/")[-1],
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "pubsub_topic" and "etIamPolicy" in method_name:
            resource_data = {
                "resource_type": "pubsub.googleapis.com/Topic",
                "name": prop("resource.labels.topic_id").split("/")[-1],
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "audited_resource" and (
            "EnableService" in method_name
            or "DisableService" in method_name
            or "ctivateService" in method_name
        ):
            resource_data = {
                "resource_type": "serviceusage.googleapis.com/Service",
                "project_id": prop("resource.labels.project_id"),
            }

            # Check if multiple services were included in the request
            # The Google Cloud Console generates (De)activate calls that logs a different format so we check both
            # known formats
            services = prop("protoPayload.request.serviceIds") or prop(
                "protoPayload.request.serviceNames"
            )
            if services:
                for s in services:
                    resource_data["name"] = s
                    add_resource()
            else:
                resource_data["name"] = prop("protoPayload.resourceName").split("/")[-1]
                add_resource()

        elif res_type == "audited_resource" and "DeactivateServices" in method_name:
            resource_data = {
                "resource_type": "serviceusage.googleapis.com/Service",
                "name": prop("resource.labels.service"),
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "gce_network":
            resource_data = {
                "resource_type": "compute.googleapis.com/Network",
                "name": prop("protoPayload.resourceName").split("/")[-1],
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "gce_subnetwork":
            resource_data = {
                "resource_type": "compute.googleapis.com/Subnetwork",
                "name": prop("resource.labels.subnetwork_name"),
                "project_id": prop("resource.labels.project_id"),
                "location": prop("resource.labels.location"),
            }
            add_resource()

        elif res_type == "gce_firewall_rule":
            resource_data = {
                "resource_type": "compute.googleapis.com/Firewall",
                "name": prop("protoPayload.resourceName").split("/")[-1],
                "project_id": prop("resource.labels.project_id"),
            }
            add_resource()

        elif res_type == "gae_app" and "DebugInstance" in method_name:
            instance_data = prop("protoPayload.resourceName").split("/")
            resource_data = {
                "resource_type": "appengine.googleapis.com/Instance",
                "name": instance_data[-1],
                "app": instance_data[1],
                "service": instance_data[3],
                "version": instance_data[5],
            }
            add_resource()

        elif res_type == "gce_instance":
            instance_name = prop("protoPayload.resourceName").split("/")[-1]

            resource_data = {
                "resource_type": "compute.googleapis.com/Instance",
                "name": instance_name,
                "location": prop("resource.labels.zone"),
                "project_id": prop("resource.labels.project_id"),
            }

            # Logs are sent for some resources that are hidden by the compute API. We've found that some of these
            # start with reserved prefixes. If the instance looks like a hidden resource, stop looking for
            # resources and return immediately
            compute_reserved_prefixes = ("aef-", "aet-")
            if resource_data["name"].startswith(compute_reserved_prefixes):
                return resources

            add_resource()

            # Also add disk resources since theres not a separate log message for these
            disks = prop("protoPayload.request.disks") or []

            for disk in disks:
                # The name of the disk is complicated. If the diskName is set in initParams use that
                # If not AND its the boot disk, use the instance name
                # Otherwise use the device name

                disk_name = jmespath.search("initializeParams.diskName", disk)
                device_name = jmespath.search("deviceName", disk)
                boot = jmespath.search("boot", disk)

                actual_disk_name = disk_name or (boot and instance_name) or device_name

                resource_data = {
                    "resource_type": "compute.googleapis.com/Disk",
                    "name": actual_disk_name,
                    "location": prop("resource.labels.zone"),
                    "project_id": prop("resource.labels.project_id"),
                }

                add_resource()

        elif res_type == "cloud_function":
            resource_data = {
                "name": prop("resource.labels.function_name"),
                "project_id": prop("resource.labels.project_id"),
                "location": prop("resource.labels.region"),
                "resource_type": "cloudfunctions.googleapis.com/CloudFunction",
            }

            add_resource()

        elif res_type == "cloud_dataproc_cluster":
            resource_data = {
                "resource_type": "dataproc.googleapis.com/Cluster",
                "project_id": prop("resource.labels.project_id"),
                "name": prop("resource.labels.cluster_name"),
                "location": prop("resource.labels.region"),
            }
            add_resource()

        elif res_type == "gke_cluster":
            resource_data = {
                "resource_type": "container.googleapis.com/Cluster",
                "name": prop("resource.labels.cluster_name"),
                "project_id": prop("resource.labels.project_id"),
                "location": prop("resource.labels.location"),
            }
            add_resource()

            # add node pool resources for eval on new cluster creation
            if (
                "create" in method_name.lower()
                and prop("protoPayload.request.cluster.nodePools") is not None
            ):
                resource_data["resource_type"] = "container.googleapis.com/NodePool"
                resource_data["cluster"] = prop("resource.labels.cluster_name")
                for pool in prop("protoPayload.request.cluster.nodePools"):
                    resource_data["name"] = pool.get("name")
                    add_resource()

        elif res_type == "gke_nodepool":
            resource_data = {
                "resource_type": "container.googleapis.com/NodePool",
                "cluster": prop("resource.labels.cluster_name"),
                "name": prop("resource.labels.nodepool_name"),
                "project_id": prop("resource.labels.project_id"),
                "location": prop("resource.labels.location"),
            }
            add_resource()

        elif res_type == "audited_resource" and "BigtableInstanceAdmin" in method_name:
            resource_data = {
                "name": prop("protoPayload.resourceName").split("/")[-1],
                "project_id": prop("resource.labels.project_id"),
            }

            resource_data["resource_type"] = "bigtableadmin.googleapis.com/Instance"
            add_resource()

        elif res_type == "dataflow_step" and "create" in method_name:
            # The endpoint expects the job id instead of name
            resource_data = {
                "name": prop("protoPayload.request.job_id"),
                "project_id": prop("resource.labels.project_id"),
                "location": prop("resource.labels.region"),
            }

            resource_data["resource_type"] = "dataflow.googleapis.com/Job"
            add_resource()

        elif res_type == "audited_resource" and "CloudRedis" in method_name:
            resource_data = {
                "name": prop("protoPayload.resourceName").split("/")[-1],
                "project_id": prop("resource.labels.project_id"),
                "location": prop("protoPayload.resourceLocation.currentLocations")[0],
            }

            resource_data["resource_type"] = "redis.googleapis.com/Instance"
            add_resource()

        elif (
            res_type == "audited_resource"
            and prop("resource.labels.service") == "datafusion.googleapis.com"
        ):
            name_bits = prop("protoPayload.resourceName").split("/")
            resource_data = {
                "name": name_bits[5],
                "project_id": name_bits[1],
                "location": name_bits[3],
                "resource_type": "datafusion.googleapis.com/Instance",
            }
            add_resource()

        elif (
            res_type == "audited_resource"
            and prop("resource.labels.service") == "dataform.googleapis.com"
        ):
            name_bits = prop("protoPayload.resourceName").split("/")
            resource_data = {
                "name": name_bits[len(name_bits) - 1],
                "project_id": name_bits[1],
                "location": name_bits[3],
            }
            if len(name_bits) == 6 and name_bits[4] == "repositories":
                resource_data["resource_type"] = "dataform.googleapis.com/Repository"
                add_resource()
            elif len(name_bits) == 8 and name_bits[6] == "workspaces":
                resource_data["resource_type"] = "dataform.googleapis.com/Workspace"
                resource_data["repository"] = name_bits[5]
                add_resource()

        return resources
