# Spring PetClinic Sample Application - Harsha's version[![Build Status](https://travis-ci.org/spring-projects/spring-petclinic.png?branch=main)](https://travis-ci.org/spring-projects/spring-petclinic/)
A copy of [Scott Andrews' Pet Clinic](https://github.com/scothis/spring-petclinic) meant to be used in Educates, with inner-loop tooling.

## My changes

- Changed [message.properties](https://github.com/hnandiwada/spring-petclinic-test/blob/main/src/main/resources/messages/messages.properties) to say "Welcome from Harsha!" rather than just "Welcome".
- Pointed [workload.yaml](https://github.com/hnandiwada/spring-petclinic-test/blob/main/config/workload.yaml) to this repo rather than Scott Andrews'.
- Downloaded Tilt with the below command. Unfortunately, because of permissions in the environment, we can't move this into `/usr/local/bin`. This does have the added benefit that we get to keep the binary in version control - we just have to run `./tilt up --stream=true` instead of `tilt`.
```
curl -fsSL https://github.com/tilt-dev/tilt/releases/download/v0.19.5/tilt.0.19.5.linux.x86_64.tar.gz | tar -xzv tilt
```
- Added `.tanzu` directory which Tilt uses.
- Added a Tiltfile. I changed the image fields to point to the Harbor image that Kontinue generates. I also changed the file sync destinations in the container based on the structure of the container.
    - WIP - There is no `.build` directory in this Pet Clinic directory because all the building happens in-cluster at the moment