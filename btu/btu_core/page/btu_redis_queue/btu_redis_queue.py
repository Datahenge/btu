import datetime
from rq.job import Job
from rq import Queue, Worker
import frappe
from frappe.utils import getdate


@frappe.whitelist()
def get_queue_names():
	try:
		date = getdate(date)
	except Exception:
		date = getdate()

	return dict(frappe.db.sql("""select unix_timestamp(date(creation)), sum(points)
		from `tabEnergy Point Log`
		where
			date(creation) > subdate('{date}', interval 1 year) and
			date(creation) < subdate('{date}', interval -1 year) and
			user = %s and
			type != 'Review'
		group by date(creation)
		order by creation asc""".format(date = date), user))

def list_all_queues():
	"""
	:return: Iterable for all available queue instances
	"""
	return Queue.all()


def list_all_possible_job_status():
	"""
	:return: list of all possible job status
	"""
	return JobStatus


def list_all_queues_names():
	"""
	:return: Iterable of all queue names
	"""
	return [queue.name for queue in list_all_queues()]


# a bit hacky for now
def validate_job_data(
	val,
	default="None",
	humanize_func=None,
	with_utcparse=False,
	relative_to_now=False,
	append_s=False,
):
	if not val:
		return default
	if humanize_func is None and append_s is True:
		return str(val) + "s"
	elif humanize_func is None:
		return val
	else:
		if with_utcparse and relative_to_now:
			return humanize_func(utcparse(val).timestamp() - datetime.now().timestamp())
		elif with_utcparse and not relative_to_now:
			return humanize_func(utcparse(val).timestamp())
		else:
			return humanize_func(val)


def reformat_job_data(job: Job):
	"""
	Create serialized version of Job which can be consumed by DataTable
	(RQ provides to_dict) including origin(queue), created_at, data, description,
	enqueued_at, started_at, ended_at, result, exc_info, timeout, result_ttl,
	 failure_ttl, status, dependency_id, meta, ttl

	:param job: Job Instance need to be serialized
	:return: serialized job
	"""
	serialized_job = job.to_dict()
	return {
		"job_info": {
			"job_id": validate_job_data(job.get_id()),
			"job_description": validate_job_data(serialized_job.get("description")),
			"job_exc_info": validate_job_data(
				zlib.decompress(serialized_job.get("exc_info")).decode("utf-8")
				if serialized_job.get("exc_info") is not None
				else None
			),
			"job_status": validate_job_data(serialized_job.get("status")),
			"job_queue": validate_job_data(serialized_job.get("origin")),
			"job_created_time_humanize": validate_job_data(
				serialized_job.get("created_at"),
				humanize_func=humanize.naturaltime,
				with_utcparse=True,
				relative_to_now=True,
			),
			"job_enqueued_time_humanize": validate_job_data(
				serialized_job.get("enqueued_at"),
				humanize_func=humanize.naturaltime,
				with_utcparse=True,
				relative_to_now=True,
			),
			"job_ttl": validate_job_data(
				serialized_job.get("ttl"), default="Infinite", append_s=True
			),
			"job_timeout": validate_job_data(
				serialized_job.get("timeout"), default="180s", append_s=True
			),
			"job_result_ttl": validate_job_data(
				serialized_job.get("result_ttl"), default="500s", append_s=True
			),
			"job_fail_ttl": validate_job_data(
				serialized_job.get("failure_ttl"), default="1yr", append_s=True
			),
		},
	}


def get_queue(queue):
	"""
	:param queue: Queue Name or Queue ID or Queue Redis Key or Queue Instance
	:return: Queue instance
	"""
	if isinstance(queue, Queue):
		return queue

	if isinstance(queue, str):
		if queue.startswith(Queue.redis_queue_namespace_prefix):
			return Queue.from_queue_key(queue)
		else:
			return Queue.from_queue_key(Queue.redis_queue_namespace_prefix + queue)

	raise TypeError("{0} is not of class {1} or {2}".format(queue, str, Queue))


def list_jobs_on_queue(queue):
	"""
	If no worker has started jobs are not available in registries
	Worker does movement of jobs across registries
	:param queue: Queue to fetch jobs from
	:return: all valid jobs untouched by workers
	"""
	queue = get_queue(queue)
	return queue.jobs


def list_job_ids_on_queue(queue):
	"""
	If no worker has started jobs are not available in registries
	Worker does movement of jobs across registries
	:param queue: Queue to fetch jobs from
	:return: all valid jobs untouched by workers
	"""
	queue = get_queue(queue)
	return queue.job_ids


def list_jobs_in_queue_all_registries(queue):
	"""
	:param queue: List all jobs in all registries of given queue
	:return: list of jobs
	"""
	jobs = []
	for registry in REGISTRIES:
		jobs.extend(list_jobs_in_queue_registry(queue, registry))
	return jobs


def list_jobs_in_queue_registry(queue, registry, start=0, end=-1):
	"""
	:param end: end index for picking jobs
	:param start: start index for picking jobs
	:param queue: Queue name from which jobs need to be listed
	:param registry: registry class from which jobs to be returned
	:return: list of all jobs matching above criteria at present scenario

	By default returns all jobs in given queue and registry combination
	"""
	queue = get_queue(queue)
	redis_connection = resolve_connection()
	if registry == StartedJobRegistry or registry == "started":
		job_ids = queue.started_job_registry.get_job_ids(start, end)
		return [
			x
			for x in Job.fetch_many(job_ids=job_ids, connection=redis_connection)
			if x is not None
		]
	elif registry == FinishedJobRegistry or registry == "finished":
		job_ids = queue.finished_job_registry.get_job_ids(start, end)
		return [
			x
			for x in Job.fetch_many(job_ids=job_ids, connection=redis_connection)
			if x is not None
		]
	elif registry == FailedJobRegistry or registry == "failed":
		job_ids = queue.failed_job_registry.get_job_ids(start, end)
		return [
			x
			for x in Job.fetch_many(job_ids=job_ids, connection=redis_connection)
			if x is not None
		]
	elif registry == DeferredJobRegistry or registry == "deferred":
		job_ids = queue.deferred_job_registry.get_job_ids(start, end)
		return [
			x
			for x in Job.fetch_many(job_ids=job_ids, connection=redis_connection)
			if x is not None
		]
	elif registry == ScheduledJobRegistry or registry == "scheduled":
		job_ids = queue.scheduled_job_registry.get_job_ids(start, end)
		return [
			x
			for x in Job.fetch_many(job_ids=job_ids, connection=redis_connection)
			if x is not None
		]
	# although not implemented as registry this is for ease
	elif registry == "queued":
		# get_jobs API has (offset, length) as parameter, while above function has start, end
		# so below is hack to fit this on above deifinition
		if end == -1:
			# -1 means all are required so pass as it is
			return queue.get_jobs(start, end)
		else:
			# end-start+1 gives required length
			return queue.get_jobs(start, end - start + 1)
	return []


def empty_registry(registry_name, queue_name, connection=None):
	"""Empties a specific registry for a specific queue, Not in RQ, implemented
	here for performance reasons
	"""
	redis_connection = resolve_connection(connection)
	queue_instance = Queue.from_queue_key(
		Queue.redis_queue_namespace_prefix + queue_name
	)

	registry_instance = None
	if registry_name == "failed":
		registry_instance = queue_instance.failed_job_registry
	elif registry_name == "started":
		registry_instance = queue_instance.started_job_registry
	elif registry_name == "scheduled":
		registry_instance = queue_instance.scheduled_job_registry
	elif registry_name == "deferred":
		registry_instance = queue_instance.deferred_job_registry
	elif registry_name == "finished":
		registry_instance = queue_instance.finished_job_registry

	script = """
		local prefix = "{0}"
		local q = KEYS[1]
		local count = 0
		while true do
			local job_id, score = unpack(redis.call("zpopmin", q))
			if job_id == nil or score == nil then
				break
			end

			-- Delete the relevant keys
			redis.call("del", prefix..job_id)
			redis.call("del", prefix..job_id..":dependents")
			count = count + 1
		end
		return count
	""".format(
		registry_instance.job_class.redis_job_namespace_prefix
	).encode(
		"utf-8"
	)
	script = redis_connection.register_script(script)
	return script(keys=[registry_instance.key])


def delete_all_jobs_in_queues_registries(queues, registries):
	for queue in queues:
		for registry in registries:
			if registry == "queued":
				# removes all jobs from queue and from job namespace
				get_queue(queue).empty()
			else:
				empty_registry(registry, queue)


def requeue_all_jobs_in_failed_registry(queues):
	fail_count = 0
	for queue in queues:
		failed_job_registry = get_queue(queue).failed_job_registry
		job_ids = failed_job_registry.get_job_ids()
		for job_id in job_ids:
			try:
				failed_job_registry.requeue(job_id)
			except InvalidJobOperationError:
				fail_count += 1
	return fail_count


def cancel_all_queued_jobs(queues):
	"""
	:param queues: list of queues from which to cancel the jobs
	:return: None
	"""
	for queue in queues:
		job_ids = get_queue(queue).get_job_ids()
		for job_id in job_ids:
			cancel_job(job_id)


def job_count_in_queue_registry(queue, registry):
	"""
	:param queue: Queue name from which jobs need to be listed
	:param registry: registry class from which jobs to be returned
	:return: count of jobs matching above criteria
	"""
	queue = get_queue(queue)
	if registry == StartedJobRegistry or registry == "started":
		return len(queue.started_job_registry)
	elif registry == FinishedJobRegistry or registry == "finished":
		return len(queue.finished_job_registry)
	elif registry == FailedJobRegistry or registry == "failed":
		return len(queue.failed_job_registry)
	elif registry == DeferredJobRegistry or registry == "deferred":
		return len(queue.deferred_job_registry)
	elif registry == ScheduledJobRegistry or registry == "scheduled":
		return len(queue.scheduled_job_registry)
	# although not implemented as registry this is for uniformity in API
	elif registry == "queued":
		return len(queue)
	else:
		return 0


def get_redis_memory_used(connection=None):
	"""
	All memory used in redis rq: namespace
	:param connection:
	:return:
	"""
	redis_connection = resolve_connection(connection)
	script = """
		local sum = 0;
		local keys = {};
		local done = false;
		local cursor = "0"
		repeat
			local result = redis.call("SCAN", cursor, "match", ARGV[1])
			cursor = result[1];
			keys = result[2];
			for i, key in ipairs(keys) do
				local mem = redis.call("MEMORY", "USAGE", key);
				sum = sum + mem;
			end
			if cursor == "0" then
				done = true;
			end
		until done
		return sum;
	"""
	script = redis_connection.register_script(script)
	return humanize.naturalsize(script(args=[RQ_REDIS_NAMESPACE]))


def fetch_job(job_id):
	"""
	:param job_id: Job to be fetched
	:return: Job instance
	:raises NoSuchJobError if job is not found
	"""
	try:
		job = Job.fetch(job_id)
		return job
	except NoSuchJobError as e:
		logger.error("Job {} not available in redis".format(job_id))
		raise


def delete_job(job_id):
	"""
	Deletes job from the queue
	Does an implicit cancel with Job hash deleted
	:param job_id: Job id to be deleted
	:return: None
	"""
	try:
		job = fetch_job(job_id)
		job.delete(remove_from_queue=True)
	except NoSuchJobError as e:
		logger.error(
			"Job not found in redis, deletion failed for job id : {}".format(e)
		)


def requeue_job(job_id):
	"""
	Requeue job from the queue
	Will work only if job was failed
	:param job_id: Job id to be requeued
	:return: None
	"""
	try:
		job = fetch_job(job_id)
		job.requeue()
	except NoSuchJobError as e:
		logger.error("Job not found in redis, requeue failed for job id : {}".format(e))


def cancel_job(job_id):
	"""
	Only removes job from the queue
	:param job_id: Job id to be cancelled
	:return: None
	"""
	try:
		job = fetch_job(job_id)
		job.cancel()
	except NoSuchJobError as e:
		logger.error("Job not found in redis, cancel failed for job id : {}".format(e))


def find_start_block(job_counts, start):
	"""
	:return: index of block from where job picking will start from,
	cursor indicating index of starting job in selected block
	"""
	cumulative_count = 0
	for i, block in enumerate(job_counts):
		cumulative_count += block.count
		if cumulative_count > start:
			return i, start - (cumulative_count - block.count)
	# marker is start index isn't available in selected jobs
	return -1, -1


def resolve_jobs(job_counts, start, length):
	"""
	:param job_counts: list of blocks(queue, registry, job_count)
	:param start: job start index for datatables
	:param length: number of jobs to be returned for datatables
	:return: list of jobs of len <= "length"

	It may happen during processing some jobs move around registries
	so jobs may extend from the desired counted blocks
	"""
	jobs = []
	start_block, cursor = find_start_block(job_counts, start)

	if start_block == -1:
		return jobs

	for i, block in enumerate(job_counts[start_block:]):
		# below list does not contain any None, but might give some less jobs
		# as some might have been moved out from that registry, in such case we try to
		# fill our length by capturing the ones from other selected registries
		current_block_jobs = list_jobs_in_queue_registry(
			block.queue, block.registry, start=cursor
		)
		jobs.extend(current_block_jobs)
		cursor = 0
		if len(jobs) >= length:
			return jobs[:length]

