"""Render background worker and optional cron entry points for Mentions.

Run from backend: python -m core.company.mention_worker run
Trigger one global passage: python -m core.company.mention_worker enqueue-global
"""
from __future__ import annotations
import argparse
from datetime import timedelta,datetime
import json
import logging
import signal
import threading
import uuid
from google.api_core.exceptions import NotFound,PreconditionFailed
from core.company import mention_jobs as jobs
from core.company import mention_service as engine
from core.company.mention_watch_service import require_mention_watch_enabled
from api.company.models import MentionRunRequest
from utils.gcs import bucket

logger=logging.getLogger(__name__)
LEASE_SECONDS=300
RENEW_SECONDS=30


class RunnerLease:
    """CAS lease with renewal: only one leader executes steps per dataset."""
    def __init__(self):
        self.token=str(uuid.uuid4());self.generation=None;self.expires=jobs.now()
        self.lost=threading.Event();self.stop=threading.Event();self.mutex=threading.Lock();self.thread=None
    @property
    def valid(self):return self.generation is not None and not self.lost.is_set() and jobs.now()<self.expires
    def _write(self,expected):
        expiry=jobs.now()+timedelta(seconds=LEASE_SECONDS)
        blob=bucket.blob(f'{jobs.ROOT}/runner-lease.json');blob.cache_control='private, no-store, max-age=0'
        blob.upload_from_string(json.dumps({'owner':self.token,'expires':expiry.isoformat()}),content_type='application/json',if_generation_match=expected)
        self.generation=int(blob.generation);self.expires=expiry
    def acquire(self):
        blob=bucket.blob(f'{jobs.ROOT}/runner-lease.json');expected=0
        try:
            blob.reload();expected=int(blob.generation)
            value=json.loads(bucket.blob(blob.name,generation=expected).download_as_text(if_generation_match=expected))
            if datetime.fromisoformat(value['expires'])>jobs.now():return False
        except NotFound:expected=0
        except PreconditionFailed:return False
        try:self._write(expected)
        except PreconditionFailed:return False
        logger.info('[MENTION WORKER] leader acquired scope=%s',jobs.ROOT)
        try:jobs.heartbeat()
        except Exception:logger.exception('[MENTION WORKER] initial heartbeat failed')
        return True
    def renew(self):
        with self.mutex:
            if not self.valid:return False
            try:self._write(self.generation)
            except Exception:
                self.lost.set();logger.exception('[MENTION WORKER] lease renewal failed');return False
        try:jobs.heartbeat()
        except Exception:logger.exception('[MENTION WORKER] heartbeat failed')
        return True
    def _loop(self):
        while not self.stop.wait(RENEW_SECONDS):
            if not self.renew():return
    def __enter__(self):
        if self.acquire():
            self.thread=threading.Thread(target=self._loop,daemon=True);self.thread.start()
        return self
    def __exit__(self,*args):
        self.stop.set()
        if self.thread:self.thread.join(timeout=2)
        with self.mutex:
            if self.generation is not None:
                try:bucket.blob(f'{jobs.ROOT}/runner-lease.json').delete(if_generation_match=self.generation)
                except (NotFound,PreconditionFailed):pass


def execute_step(lease):
    if not lease.valid:return False
    work=jobs.claim_work(lease.token)
    if work is None:return False
    row=work['row'];state=None;failure=None;skipped=False
    try:
        if not row.get('action_started'):
            try:
                require_mention_watch_enabled(row['id_company'])
                row['eligibility_checked']=True
            except Exception as exc:
                from fastapi import HTTPException
                if isinstance(exc,HTTPException) and exc.status_code in (404,409):failure=exc;skipped=True
                else:raise
        if not skipped:
            if row.get('action_started'):
                state=engine.step(row['id_run'])
            elif row['action']=='COLLECT':
                state=engine.create_for_job(MentionRunRequest(id_company=row['id_company'],**row['options']),row['id_run'])
            else:
                operation=f"{work['id_job']}:{row['id_company']}:{row['action']}"
                state=engine.prepare_server_action(row['id_run'],operation,row['action'],row.get('search_workers',1))
            if not row.get('action_started') and state['status'] not in ('COMPLETE','PARTIAL'):state=engine.step(row['id_run'])
    except Exception as exc:
        logger.exception('[MENTION WORKER] step failed company=%s run=%s',row['id_company'],row['id_run'])
        failure=exc;state=None
    # A stale worker may finish a network call, but cannot commit a job cursor.
    if lease.valid:
        jobs.finish_work(work,lease.token,state=state,error=failure,skipped=skipped)
        logger.info('[MENTION WORKER] saved job=%s company=%s stage=%s',work['id_job'],row['id_company'],state['status'] if state is not None else ('SKIPPED' if skipped else 'ERROR'))
    return True


def work_once():
    with RunnerLease() as lease:return execute_step(lease) if lease.valid else False


def run_forever(stop=None):
    stop=stop or threading.Event()
    while not stop.is_set():
        try:
            with RunnerLease() as lease:
                if not lease.valid:stop.wait(5);continue
                next_schedule_check=jobs.now()
                while lease.valid and not stop.is_set():
                    if jobs.now()>=next_schedule_check:
                        jobs.maybe_schedule();next_schedule_check=jobs.now()+timedelta(seconds=30)
                    if not execute_step(lease):stop.wait(3)
        except Exception:
            logger.exception('[MENTION WORKER] polling failed; queue preserved')
            stop.wait(5)


def main():
    parser=argparse.ArgumentParser(description='Mentions server worker')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('run');sub.add_parser('once');sub.add_parser('enqueue-global')
    individual=sub.add_parser('enqueue-company');individual.add_argument('id_company')
    args=parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    if args.command=='enqueue-global':print(json.dumps(jobs.launch_global(),ensure_ascii=False));return
    if args.command=='enqueue-company':print(json.dumps(jobs.launch_company(args.id_company),ensure_ascii=False));return
    if args.command=='once':work_once();return
    stop=threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stop.set())
    run_forever(stop)


if __name__=='__main__':main()
