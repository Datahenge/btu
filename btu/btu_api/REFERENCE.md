```python
import logging
import signal
import time
import os
import socket
from uuid import uuid4

from datetime import datetime
from itertools import repeat

from rq.exceptions import NoSuchJobError
from rq.job import Job	as rq_Job
from rq.queue import Queue
from rq.utils import backend_class, import_attribute
from rq.compat import string_types

from redis import WatchError

# from .utils import from_unix, to_unix, get_next_scheduled_time, rationalize_until

logger = logging.getLogger(__name__)


class Scheduler(object):
    redis_scheduler_namespace_prefix = 'rq:scheduler_instance:'
    scheduler_key = 'rq:scheduler'
    scheduler_lock_key = 'rq:scheduler_lock'
    scheduled_jobs_key = 'rq:scheduler:scheduled_jobs'
    queue_class = Queue
    job_class = Job

    def __init__(self, queue_name='default', queue=None, interval=60, connection=None,
                 job_class=None, queue_class=None, name=None):
        from rq.connections import resolve_connection
        self.connection = resolve_connection(connection)
        self._queue = queue
        if self._queue is None:
            self.queue_name = queue_name
        else:
            self.queue_name = self._queue.name
        self._interval = interval
        self.log = logger
        self._lock_acquired = False
        self.job_class = backend_class(self, 'job_class', override=job_class)
        self.queue_class_name = None
        if isinstance(queue_class, string_types):
            self.queue_class_name = queue_class
        self.queue_class = backend_class(self, 'queue_class', override=queue_class)
        self.name = name or uuid4().hex

 
    def _create_job(self, func, args=None, kwargs=None, commit=True,
                    result_ttl=None, ttl=None, id=None, description=None,
                    queue_name=None, timeout=None, meta=None, depends_on=None):
        """
        Creates an RQ job and saves it to Redis. The job is assigned to the
        given queue name if not None else it is assigned to scheduler queue by
        default.
        """
        if args is None:
            args = ()
        if kwargs is None:
            kwargs = {}
        job = self.job_class.create(
                func, args=args, connection=self.connection,
                kwargs=kwargs, result_ttl=result_ttl, ttl=ttl, id=id,
                description=description, timeout=timeout, meta=meta, depends_on=depends_on)
        if queue_name:
            job.origin = queue_name
        else:
            job.origin = self.queue_name

        if self.queue_class_name:
            job.meta["queue_class_name"] = self.queue_class_name

        if commit:
            job.save()
        return job

    def enqueue_at(self, scheduled_time, func, *args, **kwargs):
        """
        Pushes a job to the scheduler queue. The scheduled queue is a Redis sorted
        set ordered by timestamp - which in this case is job's scheduled execution time.

        All args and kwargs are passed onto the job, except for the following kwarg
        keys (which affect the job creation itself):
        - timeout
        - job_id
        - job_ttl
        - job_result_ttl
        - job_description
        - depends_on
        - meta
        - queue_name

        Usage:

        from datetime import datetime
        from redis import Redis
        from rq.scheduler import Scheduler

        from foo import func

        redis = Redis()
        scheduler = Scheduler(queue_name='default', connection=redis)
        scheduler.enqueue_at(datetime(2020, 1, 1), func, 'argument', keyword='argument')
        """
        timeout = kwargs.pop('timeout', None)
        job_id = kwargs.pop('job_id', None)
        job_ttl = kwargs.pop('job_ttl', None)
        job_result_ttl = kwargs.pop('job_result_ttl', None)
        job_description = kwargs.pop('job_description', None)
        depends_on = kwargs.pop('depends_on', None)
        meta = kwargs.pop('meta', None)
        queue_name = kwargs.pop('queue_name', None)

        job = self._create_job(func, args=args, kwargs=kwargs, timeout=timeout,
                               id=job_id, result_ttl=job_result_ttl, ttl=job_ttl,
                               description=job_description, meta=meta, queue_name=queue_name, depends_on=depends_on)
        self.connection.zadd(self.scheduled_jobs_key,
                              {job.id: to_unix(scheduled_time)})
        return job

    def cron(self, cron_string, func, args=None, kwargs=None, repeat=None,
             queue_name=None, id=None, timeout=None, description=None, meta=None, use_local_timezone=False, depends_on=None):
        """
        Schedule a cronjob
        """
        scheduled_time = get_next_scheduled_time(cron_string, use_local_timezone=use_local_timezone)

        # Set result_ttl to -1, as jobs scheduled via cron are periodic ones.
        # Otherwise the job would expire after 500 sec.
        job = self._create_job(func, args=args, kwargs=kwargs, commit=False,
                               result_ttl=-1, id=id, queue_name=queue_name,
                               description=description, timeout=timeout, meta=meta, depends_on=depends_on)

        job.meta['cron_string'] = cron_string
        job.meta['use_local_timezone'] = use_local_timezone

        if repeat is not None:
            job.meta['repeat'] = int(repeat)

        job.save()

        self.connection.zadd(self.scheduled_jobs_key,
                              {job.id: to_unix(scheduled_time)})
        return job



    def enqueue_job(self, job):
        """
        Move a scheduled job to a queue. In addition, it also does puts the job
        back into the scheduler if needed.
        """
        self.log.debug('Pushing {0}({1}) to {2}'.format(job.func_name, job.id, job.origin))

        interval = job.meta.get('interval', None)
        repeat = job.meta.get('repeat', None)
        cron_string = job.meta.get('cron_string', None)
        use_local_timezone = job.meta.get('use_local_timezone', None)

        # If job is a repeated job, decrement counter
        if repeat:
            job.meta['repeat'] = int(repeat) - 1

        queue = self.get_queue_for_job(job)
        queue.enqueue_job(job)
        self.connection.zrem(self.scheduled_jobs_key, job.id)

        if interval:
            # If this is a repeat job and counter has reached 0, don't repeat
            if repeat is not None:
                if job.meta['repeat'] == 0:
                    return
            self.connection.zadd(self.scheduled_jobs_key,
                                  {job.id: to_unix(datetime.utcnow()) + int(interval)})
        elif cron_string:
            # If this is a repeat job and counter has reached 0, don't repeat
            if repeat is not None:
                if job.meta['repeat'] == 0:
                    return
            self.connection.zadd(self.scheduled_jobs_key,
                                  {job.id: to_unix(get_next_scheduled_time(cron_string, use_local_timezone=use_local_timezone))})

   
```

```python
import sys
import selectors
import json
import io
import struct

class Message:
    def __init__(self, selector, sock, addr, request):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self.request = request
        self._recv_buffer = b""
        self._send_buffer = b""
        self._request_queued = False
        self._jsonheader_len = None
        self.jsonheader = None
        self.response = None

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("sending", repr(self._send_buffer), "to", self.addr)
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message(
        self, *, content_bytes, content_type, content_encoding
    ):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def _process_response_json_content(self):
        content = self.response
        result = content.get("result")
        print(f"got result: {result}")

    def _process_response_binary_content(self):
        content = self.response
        print(f"got response: {repr(content)}")

    def process_events(self, mask):
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.response is None:
                self.process_response()

    def write(self):
        if not self._request_queued:
            self.queue_request()

        self._write()

        if self._request_queued:
            if not self._send_buffer:
                # Set selector to listen for read events, we're done writing.
                self._set_selector_events_mask("r")

    def close(self):
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as e:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(e)}",
            )

        try:
            self.sock.close()
        except OSError as e:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(e)}",
            )
        finally:
            # Delete reference to socket object for garbage collection
            self.sock = None

    def queue_request(self):
        content = self.request["content"]
        content_type = self.request["type"]
        content_encoding = self.request["encoding"]
        if content_type == "text/json":
            req = {
                "content_bytes": self._json_encode(content, content_encoding),
                "content_type": content_type,
                "content_encoding": content_encoding,
            }
        else:
            req = {
                "content_bytes": content,
                "content_type": content_type,
                "content_encoding": content_encoding,
            }
        message = self._create_message(**req)
        self._send_buffer += message
        self._request_queued = True

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:hdrlen]
            )[0]
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len
        if len(self._recv_buffer) >= hdrlen:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[hdrlen:]
            for reqhdr in (
                "byteorder",
                "content-length",
                "content-type",
                "content-encoding",
            ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

    def process_response(self):
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.response = self._json_decode(data, encoding)
            print("received response", repr(self.response), "from", self.addr)
            self._process_response_json_content()
        else:
            # Binary or unknown content-type
            self.response = data
            print(
                f'received {self.jsonheader["content-type"]} response from',
                self.addr,
            )
            self._process_response_binary_content()
        # Close when response has been processed
        self.close()
'''
