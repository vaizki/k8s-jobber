
# K8s Jobber Operator

Quickly implemented Kubernetes controller to enable scheduling of Jobs at a later time.

## Usage:

To schedule a Job later,

1. Set .spec.parallelism to 0, which will prevent immediate scheduling of the Job and associated Pods
2. Add annotation jobber.vaizki.fi/schedule-at with a ISO 8601 style timestamp

The Job will be scheduled at or *after* the specified time. 

Note: The controller will change the parallelism to 1 and remove the annotation. This behaviour is subject to change.

## Docker image

Find it at https://hub.docker.com/r/vaizki/k8s-jobber

## Example

    kind: Job
    apiVersion: batch/v1
    metadata:
      name: back-to-the-future
      annotations:
        jobber.vaizki.fi/schedule-at: '2021-12-03T17:28:00.000Z'
    spec:
      parallelism: 0
      backoffLimit: 4
      template:
        spec:
          restartPolicy: Never
          containers:
          - name: delorean
            image: bash
            command:
            - echo
            - "What happens in the future stays in the future"

## Deployment

See k8s-jobber.yaml in this repo. Currently you should specify namespaces to watch with -n on the kopf command line.


## Limitations

This is a naive proof-of-concept implementation and not exhaustively tested. Use at your own risk.

## TODO

Instead of requiring setting parallelism to zero, support Job suspended states which were introduced in k8s 1.22 as alpha features, see: 
https://kubernetes.io/blog/2021/04/12/introducing-suspended-jobs/