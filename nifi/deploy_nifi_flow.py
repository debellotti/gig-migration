import json
import os
import sys
import time

import requests
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

NIFI_URL = os.getenv("NIFI_URL", "https://localhost:8443/nifi-api")
USERNAME = os.getenv("NIFI_USERNAME", "admin")
PASSWORD = os.getenv("NIFI_PASSWORD", "admin123456789")
FLOW_JSON_PATH = os.getenv("FLOW_JSON_PATH", "nifi/flow.json")


def wait_for_nifi(session, timeout=300):
    print("Waiting for NiFi to be ready...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = session.get(f"{NIFI_URL}/access/config", verify=False, timeout=5)
            if r.status_code == 200:
                print("NiFi is ready.")
                return True
        except Exception:
            pass
        time.sleep(5)
    print("Timeout waiting for NiFi.")
    return False


def get_access_token(session):
    r = session.post(
        f"{NIFI_URL}/access/token",
        data={"username": USERNAME, "password": PASSWORD},
        verify=False,
    )
    r.raise_for_status()
    return r.text


def get_nifi_version(session):
    r = session.get(f"{NIFI_URL}/flow/about", verify=False)
    r.raise_for_status()
    return r.json()["about"]["version"]


def get_root_group_id(session):
    r = session.get(f"{NIFI_URL}/process-groups/root", verify=False)
    r.raise_for_status()
    return r.json()["id"]


def get_existing_processors(session, group_id):
    r = session.get(f"{NIFI_URL}/process-groups/{group_id}/processors", verify=False)
    r.raise_for_status()
    return {p["component"]["name"]: p for p in r.json()["processors"]}


def update_processor(session, existing, proc_def, nifi_version):
    proc_id = existing["id"]
    revision = existing["revision"]
    body = {
        "revision": revision,
        "component": {
            "id": proc_id,
            "config": {
                "properties": proc_def["properties"],
                "schedulingPeriod": proc_def["schedulingPeriod"],
                "schedulingStrategy": proc_def["schedulingStrategy"],
                "autoTerminatedRelationships": proc_def["autoTerminatedRelationships"],
            },
        },
    }
    r = session.put(f"{NIFI_URL}/processors/{proc_id}", json=body, verify=False)
    r.raise_for_status()
    return r.json()


def create_processor(session, group_id, proc_def, nifi_version):
    body = {
        "revision": {"version": 0},
        "component": {
            "type": proc_def["type"],
            "name": proc_def["name"],
            "position": proc_def["position"],
            "bundle": {
                "group": proc_def["bundle"]["group"],
                "artifact": proc_def["bundle"]["artifact"],
                "version": nifi_version,
            },
            "config": {
                "properties": proc_def["properties"],
                "schedulingPeriod": proc_def["schedulingPeriod"],
                "schedulingStrategy": proc_def["schedulingStrategy"],
                "autoTerminatedRelationships": proc_def["autoTerminatedRelationships"],
            },
        },
    }
    r = session.post(
        f"{NIFI_URL}/process-groups/{group_id}/processors", json=body, verify=False
    )
    r.raise_for_status()
    return r.json()


def get_existing_connections(session, group_id):
    r = session.get(f"{NIFI_URL}/process-groups/{group_id}/connections", verify=False)
    r.raise_for_status()
    return r.json()["connections"]


def create_connection(session, group_id, conn_def, id_map, root_group_id):
    body = {
        "revision": {"version": 0},
        "component": {
            "source": {
                "id": id_map[conn_def["source"]["id"]],
                "type": conn_def["source"]["type"],
                "groupId": root_group_id,
            },
            "destination": {
                "id": id_map[conn_def["destination"]["id"]],
                "type": conn_def["destination"]["type"],
                "groupId": root_group_id,
            },
            "selectedRelationships": conn_def["selectedRelationships"],
            "backPressureObjectThreshold": conn_def["backPressureObjectThreshold"],
            "backPressureDataSizeThreshold": conn_def["backPressureDataSizeThreshold"],
        },
    }
    r = session.post(
        f"{NIFI_URL}/process-groups/{group_id}/connections", json=body, verify=False
    )
    r.raise_for_status()
    return r.json()


def start_all_processors(session, group_id):
    body = {"id": group_id, "state": "RUNNING", "disconnectedNodeAcknowledged": False}
    r = session.put(f"{NIFI_URL}/flow/process-groups/{group_id}", json=body, verify=False)
    r.raise_for_status()
    print("All processors started.")


def main():
    with open(FLOW_JSON_PATH) as f:
        flow = json.load(f)

    contents = flow["flowContents"]
    processors = contents["processors"]
    connections = contents["connections"]

    session = requests.Session()

    if not wait_for_nifi(session):
        sys.exit(1)

    token = get_access_token(session)
    session.headers["Authorization"] = f"Bearer {token}"

    nifi_version = get_nifi_version(session)
    print(f"NiFi version: {nifi_version}")

    root_id = get_root_group_id(session)
    print(f"Root process group: {root_id}")

    existing_processors = get_existing_processors(session, root_id)
    id_map = {}

    for proc in processors:
        if proc["name"] in existing_processors:
            result = update_processor(session, existing_processors[proc["name"]], proc, nifi_version)
            id_map[proc["identifier"]] = result["id"]
            print(f"Updated processor '{proc['name']}' -> {result['id']}")
        else:
            result = create_processor(session, root_id, proc, nifi_version)
            id_map[proc["identifier"]] = result["id"]
            print(f"Created processor '{proc['name']}' -> {result['id']}")

    existing_connections = get_existing_connections(session, root_id)

    for conn in connections:
        src_id = id_map[conn["source"]["id"]]
        dst_id = id_map[conn["destination"]["id"]]
        already_exists = any(
            c["component"]["source"]["id"] == src_id
            and c["component"]["destination"]["id"] == dst_id
            for c in existing_connections
        )
        if already_exists:
            print("Connection already exists, skip.")
        else:
            result = create_connection(session, root_id, conn, id_map, root_id)
            print(f"Created connection -> {result['id']}")

    start_all_processors(session, root_id)
    print("Flow deployed successfully.")


if __name__ == "__main__":
    main()
