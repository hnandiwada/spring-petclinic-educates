allow_k8s_contexts('eduk8s')
load('.tanzu/file_sync_only.py', 'file_sync_only')

mvnw = "./mvnw"
if os.name == "nt":
  mvnw = "mvnw.bat"

#  './mvnw -Dmaven.test.skip=true -Dspring-boot.repackage.excludeDevtools=false package && rm -rf .build/* && unzip -o target/spring-petclinic-*.jar -d .build/',
local_resource(
  'spring-petclinic-compile',
  './mvnw -Dmaven.test.skip=true -Dspring-boot.repackage.excludeDevtools=false package && ' +
    'rm -rf target/jar-staging && ' +
    'unzip -o target/spring-petclinic-*.jar -d target/jar-staging && ' +
    'rsync --delete --inplace --checksum -r target/jar-staging/ .build',
  deps=['src', 'pom.xml'])

file_sync_only("harbor-repo.vmware.com/kontinuedemo/spring-petclinic",
    ["./config/workload.yaml"],
    deps=['.build/'],
    live_update=[
      sync('.build/BOOT-INF/lib', '/workspace/BOOT-INF/lib'),
      sync('.build/META-INF', '/workspace/META-INF'),
      sync('.build/BOOT-INF/classes', '/workspace/BOOT-INF/classes'),
      run("#TODO: figure out how to restart the container; i.e. something like 'kill -HUP 1' that actually works")
    ],
)

k8s_kind('Workload', pod_readiness='ignore')

k8s_resource(workload='spring-petclinic', port_forwards=8080,
             resource_deps=['spring-petclinic-compile'],
             extra_pod_selectors=[{'app': 'spring-petclinic'}])
