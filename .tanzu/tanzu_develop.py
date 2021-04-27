load('ext://local_output', 'local_output')
# -*- mode: Python -*-
# live reload
def tanzu_develop(workload='', manifests=[], deps=["."], resource_deps=[], live_update=[]):
    k8s_kind('Workload', api_version='experimental.kontinue.io/v1',
            image_json_path='{.metadata.dev_image}')
    k8s_resource(workload, port_forwards=8080,
                resource_deps=resource_deps, 
                extra_pod_selectors=[{'serving.knative.dev/service': workload}])
    workload_yaml = local_output('kubectl get workloads ' + workload + ' -o yaml')
    image_ref = local_output('kubectl get workloaddecorators ' + workload +'-workload-template -o jsonpath=\'{.status.template.spec.containers[?(@.name=="workload")].image}\'')
    image_ref = image_ref.split("@sha256", 1)[0]
    # add image to workload_yaml
    workload_yaml = workload_yaml.replace("metadata:", "metadata:\n  dev_image: " + image_ref, 1)
    print(workload_yaml)
    manifests.append(blob(workload_yaml))
    file_sync_only(image_ref, manifests, deps, live_update)
# module function
# non build development with only file sync
def file_sync_only(image='', manifests=[], deps=["."], live_update=[]):
    if type(manifests) == "string":
        manifests = [manifests]
    # ex) image is "nginx" or "nginx:1.17" format
    # "nginx" => return "nginx" and "1.16" (from manifests)
    # "nginx:1.17" => return "nginx" and "1.17"
    deployed_image, deployed_tag = _get_current_tag(image, manifests)
    # ":" is null command
    custom_build(deployed_image, ':',
        tag=deployed_tag,
        deps=deps,
        skips_local_docker=True,
        live_update=live_update
    )
    k8s_yaml(manifests)
    _first_sync_from_liveupdate(deployed_image, live_update)
# get current tags from image setting from first arg in file_sync_only() or in manifests
def _get_current_tag(image='', manifests=[]):
    p = image.split(':')
    if len(p) == 2:
        return p[0], p[1]
    tags = []
    for m in manifests:
        if type(m) == str:
            output = str(local(r"grep 'image: %s' %s | cut -d ':' -f 3 | uniq || true" % (image, m))).strip()
            if (output != ''):
                tags = tags + output.split("\n")
    if len(tags) == 0:
        tags = ["latest"]
    elif len(tags) > 1:
        fail("found multiple image tags for %s in manifests %s" % (image, manifests))
    return image, tags[0]
# sync files at first time
def _first_sync_from_liveupdate(image, live_update):
    for l in live_update:
        if type(l) == "live_update_sync_step":
            local_path, remote_path = _get_sync_params(l)
            local_resource('%s-sync' % local_path,
                'touch %s' % local_path)
# return sync(local_path, remote_path)'s args
def _get_sync_params(sync):
    output = str(sync).split("'")
    local_path = output[1].replace(os.getcwd() + "/", "")
    remote_path = output[3]
    return local_path, remote_path
