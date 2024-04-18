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
from dataclasses import asdict, dataclass
from typing import Optional
from pydantic import BaseModel

from rpe.extractors import Extractor
from rpe.extractors.models import ExtractedMetadata, ExtractedResources
from rpe.extractors.pubsub_metadata import (
    PubsubMessageMetadata,
    get_pubsub_message_metadata,
)
from rpe.resources.gcp import GoogleAPIResource


class MicromanagerMetadata(PubsubMessageMetadata, ExtractedMetadata):
    pass


class MicromanagerEvaluationRequest(Extractor):
    @classmethod
    def extract(cls, message):
        message_data = json.loads(message.data)

        name = message_data.get("name")
        asset_type = message_data.get("asset_type")
        project_id = message_data.get("project_id")
        metadata = message_data.get("metadata") or {}
        metadata.update((get_pubsub_message_metadata(message)).dict())

        resource = GoogleAPIResource.from_cai_data(
            name, asset_type, project_id=project_id
        )

        metadata = MicromanagerMetadata(**metadata)

        return ExtractedResources(resources=[resource], metadata=metadata)
