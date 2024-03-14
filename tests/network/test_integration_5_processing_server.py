from pathlib import Path
from requests import get as request_get, post as request_post
from time import sleep
from src.ocrd_network.constants import AgentType, JobState
from src.ocrd_network.logging_utils import get_processing_job_logging_file_path
from tests.base import assets
from tests.network.config import test_config

PROCESSING_SERVER_URL = test_config.PROCESSING_SERVER_URL


def poll_till_timeout_fail_or_success(test_url: str, tries: int, wait: int) -> JobState:
    job_state = JobState.unset
    while tries > 0:
        sleep(wait)
        response = request_get(url=test_url)
        assert response.status_code == 200, f"Processing server: {test_url}, {response.status_code}"
        job_state = response.json()["state"]
        if job_state == JobState.success or job_state == JobState.failed:
            break
        tries -= 1
    return job_state


def test_processing_server_connectivity():
    test_url = f"{PROCESSING_SERVER_URL}/"
    response = request_get(test_url)
    assert response.status_code == 200, f"Processing server is not reachable on: {test_url}, {response.status_code}"
    message = response.json()["message"]
    assert message.startswith("The home page of"), f"Processing server home page message is corrupted"


# TODO: The processing workers are still not registered when deployed separately.
#  Fix that by extending the processing server.
def test_processing_server_deployed_processors():
    test_url = f"{PROCESSING_SERVER_URL}/processor"
    response = request_get(test_url)
    processors = response.json()
    assert response.status_code == 200, f"Processing server: {test_url}, {response.status_code}"
    assert processors == [], f"Mismatch in deployed processors"


def test_processing_server_processing_request():
    workspace_root = "kant_aufklaerung_1784/data"
    path_to_mets = assets.path_to(f"{workspace_root}/mets.xml")
    input_file_grp = "OCR-D-IMG"
    output_file_grp = f"OCR-D-DUMMY-TEST-PS"
    test_processing_job_input = {
        "path_to_mets": path_to_mets,
        "input_file_grps": [input_file_grp],
        "output_file_grps": [output_file_grp],
        "agent_type": AgentType.PROCESSING_WORKER,
        "parameters": {}
    }
    test_processor = "ocrd-dummy"
    test_url = f"{PROCESSING_SERVER_URL}/processor/run/{test_processor}"
    response = request_post(
        url=test_url,
        headers={"accept": "application/json"},
        json=test_processing_job_input
    )
    print(response.json())
    print(response.__dict__)
    assert response.status_code == 200, f"Processing server: {test_url}, {response.status_code}"
    processing_job_id = response.json()["job_id"]
    assert processing_job_id

    job_state = poll_till_timeout_fail_or_success(
        test_url=f"{PROCESSING_SERVER_URL}/processor/job/{processing_job_id}", tries=10, wait=10
    )
    assert job_state == JobState.success

    # Check the existence of the results locally
    assert Path(assets.path_to(f"{workspace_root}/{output_file_grp}")).exists()
    path_to_log_file = get_processing_job_logging_file_path(job_id=processing_job_id)
    assert Path(path_to_log_file).exists()


def test_processing_server_workflow_request():
    # Note: the used workflow path is volume mapped
    path_to_dummy_wf = "/ocrd-data/assets/dummy-workflow.txt"
    workspace_root = "kant_aufklaerung_1784/data"
    path_to_mets = assets.path_to(f"{workspace_root}/mets.xml")

    # submit the workflow job
    test_url = f"{PROCESSING_SERVER_URL}/workflow/run?mets_path={path_to_mets}&page_wise=True"
    response = request_post(
        url=test_url,
        headers={"accept": "application/json"},
        files={"workflow": open(path_to_dummy_wf, 'rb')}
    )
    # print(response.json())
    # print(response.__dict__)
    assert response.status_code == 200, f"Processing server: {test_url}, {response.status_code}"
    wf_job_id = response.json()["job_id"]
    assert wf_job_id

    job_state = poll_till_timeout_fail_or_success(
        test_url=f"{PROCESSING_SERVER_URL}/workflow/job-simple/{wf_job_id}", tries=30, wait=10
    )
    assert job_state == JobState.success

    # Check the existence of the results locally
    # The output file groups are defined in the `path_to_dummy_wf`
    assert Path(assets.path_to(f"{workspace_root}/OCR-D-DUMMY1")).exists()
    assert Path(assets.path_to(f"{workspace_root}/OCR-D-DUMMY2")).exists()
    assert Path(assets.path_to(f"{workspace_root}/OCR-D-DUMMY3")).exists()
