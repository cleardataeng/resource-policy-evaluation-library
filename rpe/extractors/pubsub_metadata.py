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

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from google.pubsub_v1 import PubsubMessage
import jmespath


class PubsubMessageMetadata(BaseModel):
    publish_time: datetime
    message_id: str
    attributes: Optional[dict]


def get_pubsub_message_metadata(message: PubsubMessage):
    return PubsubMessageMetadata(
        publish_time=message.publish_time,
        message_id=message.message_id,
        attributes=dict(message.attributes),
    )
