#!/usr/bin/env python3

import asyncio
import logging
import time

import kopf
import kubernetes.client as k8s_client
import dateutil.parser


AT_ANNOTATION = 'jobber.vaizki.fi/schedule-at'
LOG = logging.getLogger('jobber')
JOBQ = asyncio.PriorityQueue()


class AtJob():
    def __init__(self, namespace, name, at_ts):
        self.namespace = namespace
        self.name = name
        self.at_ts = at_ts

    def __repr__(self):
        return f'AtJob({self.namespace}/{self.name})'

    async def handler(self):
        ts = time.time()
        if self.at_ts <= ts:
            LOG.info('Job %s is scheduled before it was detected, scheduling immediately',
                     self)
            await self._schedule_now()
            return True
        delay = self.at_ts - ts
        LOG.info('Job %s will be scheduled in %d seconds', self, delay)
        try:
            await asyncio.sleep(delay)
            await self._schedule_now()
        except asyncio.CancelledError:
            return False
        return True

    async def _schedule_now(self):
        LOG.info('Scheduling %s now', self)
        batch_api = k8s_client.BatchV1Api()
        patch = { 'spec': { 'parallelism': 1 },
                  'metadata': { 'annotations': { AT_ANNOTATION: None } }
              }
        batch_api.patch_namespaced_job(self.name, self.namespace, patch)


async def handle_job(namespace, name, at_time):
    LOG.info('Handling Job %s/%s scheduled at %s',
             namespace, name, at_time)
    try:
        at_ts = dateutil.parser.parse(at_time).timestamp()
    except dateutil.parser.ParserError:
        LOG.warning('Invalid time string: %s, Job will never be scheduled!', at_time)
        return
    job = AtJob(namespace, name, at_ts)
    if await job.handler():
        LOG.debug('Job %s has been scheduled, daemon exiting', job)
    else:
        LOG.info('Job %s is left waiting, exiting', job)


@kopf.daemon('batch', 'v1', 'jobs', annotations={AT_ANNOTATION: kopf.PRESENT},
             field='spec.parallelism', value=0,
             cancellation_timeout=1.0)
async def on_job(namespace, meta, **kwargs):
    await handle_job(namespace, meta['name'], meta['annotations'][AT_ANNOTATION])
