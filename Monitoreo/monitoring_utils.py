import json

def get_metric_dict(run):
    metric_dict = {}
    for m in run.dict()["metrics"]:
        metric_name = m["metric_id"].split("(")[0]
        metric_dict[metric_name] = m["id"]
    return metric_dict

def get_metric(run, metric_id):
    cur_val = float(run.dump_dict()["metric_results"][metric_id]["widget"][0]["params"]["counters"][0]["value"])
    ref_val = float(run.dump_dict()["metric_results"][metric_id]["widget"][1]["params"]["counters"][0]["value"])
    return cur_val, ref_val

def detect_data_drift(run):
    value = float(run.dict()["metrics"][0]["value"]["share"])
    threshold = float(run.dict()["metrics"][0]["metric_id"].split("=")[1][:-1])
    return value >= threshold

def get_username():
    with open("/opt/ml/metadata/resource-metadata.json", "r") as f:
        app_metadata = json.loads(f.read())
        space_name = app_metadata["SpaceName"]
    return space_name