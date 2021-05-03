load('ext://local_output', 'local_output')
# -*- mode: Python -*-
# live reload
def tanzu_develop(k8s_object, deps=["."], resource_deps=[], live_update=[]):

    # 1. Create a CRD that we can create instances that act as Tilt's image target
    twp_crd = """
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: tiltworkloadproxys.experimental.desktop.io
spec:
  group: experimental.desktop.io
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                image:
                  type: string
  scope: Namespaced
  names:
    plural: tiltworkloadproxys
    singular: tiltworkloadproxy
    kind: TiltWorkloadProxy
    shortNames:
    - twp
"""
    local("cat << EOF | kubectl apply -f - " + twp_crd + "EOF")
    
    # 2. Tell Tilt about it, so Tilt knows which container to update
    k8s_kind('TiltWorkloadProxy', api_version='experimental.desktop.io/v1',
            image_json_path="{.spec.image}")

    # 3. Fetch the image from the cluster
    ksvc_image_json_path = '{.spec.template.spec.containers[0].image}'
    ksvc_image = local_output('kubectl get ksvc ' + k8s_object + ' -o jsonpath=\'' + ksvc_image_json_path + '\'')
    ksvc_image = ksvc_image.replace('@sha256', '') # 3rd party `file_sync_only` wants image-name:actualsha not image-name@sha246:actualsha

    # 4. Create an instance of the tilt workload proxy to represent the app
    twp_template = """
apiVersion: "experimental.desktop.io/v1"
kind: TiltWorkloadProxy
metadata:
  name: {k8s_object}-twp
spec:
  image: {image}    
"""
    twp = twp_template.format(k8s_object=k8s_object, image=ksvc_image)
    local("cat << EOF | kubectl apply -f - " + twp + "EOF")

    k8s_resource(k8s_object+'-twp', port_forwards=8080,
                resource_deps=resource_deps,
                extra_pod_selectors=[{'serving.knative.dev/service' : k8s_object}])

    # 5. Wire-up Tilt's live updates to the pod
    file_sync_only(image=ksvc_image,
                   manifests=[blob(twp)],
                   deps=deps,
                   live_update=live_update)
 
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
        # TODO: specify hotreloading capable entrypoint that comes from Tiltfile
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

