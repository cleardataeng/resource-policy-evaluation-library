from rpe.resources.gcp import GoogleAPIResource
from googleapiclient.http import HttpMockSequence
import pytest


@pytest.mark.parametrize(
    "name,asset_type,http,inferred_key",
    [
        pytest.param(
            "//storage.googleapis.com/buckets/test-bucket",
            "storage.googleapis.com/Bucket",
            HttpMockSequence(
                [
                    ({"status": 200}, '{"location": "US"}'),
                    ({"status": 200}, '{"iam_policy":""}'),
                ]
            ),
            "location",
            id="bucket_location",
        ),
        pytest.param(
            "//compute.googleapis.com/projects/test-project/zones/test-zone/instances/test-instance",
            "compute.googleapis.com/Instance",
            HttpMockSequence(
                [
                    ({"status": 200}, '{"id": "1234567890"}'),
                    ({"status": 200}, '{"iam_policy":""}'),
                ]
            ),
            "uniquifier",
            id="instance_uniquifier",
        ),
    ],
)
def test_inferred_data_lookup_success(name, asset_type, http, inferred_key):
    res = GoogleAPIResource.from_cai_data(name, asset_type, http=http)

    assert inferred_key not in res._resource_data
    res.to_dict()
    assert inferred_key in res._resource_data


@pytest.mark.parametrize(
    "name,asset_type,http",
    [
        pytest.param(
            "//storage.googleapis.com/buckets/test-bucket",
            "storage.googleapis.com/Bucket",
            HttpMockSequence(
                [
                    ({"status": 401}, '{"msg": "oops"}'),
                ]
            ),
            id="resource_401",
        ),
        pytest.param(
            "//compute.googleapis.com/projects/test-project/zones/test-zone/instances/test-instance",
            "compute.googleapis.com/Instance",
            HttpMockSequence(
                [
                    ({"status": 404}, '{"msg": "something went wrong"}'),
                ]
            ),
            id="resource_404",
        ),
        pytest.param(
            "//compute.googleapis.com/projects/test-project/zones/test-zone/instances/test-instance",
            "compute.googleapis.com/Instance",
            HttpMockSequence(
                [
                    ({"status": 200}, "HTTP ERROR: NOT JSON"),
                ]
            ),
            id="malformed_json",
        ),
    ],
)
def test_todict_eats_exceptions(name, asset_type, http):
    res = GoogleAPIResource.from_cai_data(name, asset_type, http=http)

    res.to_dict()
