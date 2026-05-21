---
title: "Postgres elevated memory in idleness"
date: 2026-05-21T19:00:00Z
tags: [engineering, postgres, db, databases, sre, linux, memory]
author: Tom M G
draft: false
---

# Context
Postgres container memory usage was elevated, while access and operations were effectively none. No active queries, no visible application traffic, no meaningful transaction rate, and no obvious maintenance task explaining the high consumption.

The first instinct is to look for a leak. But with databases is easy to confuse useful retained memory with harmful memory pressure. Postgres and the operating system both treat unused RAM as an opportunity to avoid future disk reads.

# Troubleshooting
Check the configured memory settings
```sql
select
  name,
  setting,
  unit,
  source
from pg_settings
where name in (
  'shared_buffers',
  'work_mem',
  'hash_mem_multiplier',
  'maintenance_work_mem',
  'autovacuum_work_mem',
  'temp_buffers',
  'max_connections',
  'effective_cache_size'
)
order by name;
```

Check what `pg_stat_activity` shows as long running operations
```sql
select
  state,
  wait_event_type,
  wait_event,
  count(*) as sessions
from pg_stat_activity
where pid <> pg_backend_pid()
group by state, wait_event_type, wait_event
order by sessions desc;
```

Then list the sessions that could plausibly allocate memory
```sql
select
  pid,
  backend_type,
  usename,
  application_name,
  client_addr,
  state,
  now() - query_start as query_age,
  wait_event_type,
  wait_event,
  left(query, 160) as query
from pg_stat_activity
where state is distinct from 'idle'
order by query_age desc nulls last;
```

Check memory contexts
```sql
select
  name,
  ident,
  parent,
  pg_size_pretty(total_bytes) as total,
  pg_size_pretty(used_bytes) as used,
  pg_size_pretty(free_bytes) as free
from pg_backend_memory_contexts
order by total_bytes desc
limit 30;
```

Check whether queries are spilling because memory is too small
```sql
select
  datname,
  temp_files,
  pg_size_pretty(temp_bytes) as temp_written
from pg_stat_database
order by temp_bytes desc;
```


To see what is occupying `shared_buffers`, `pg_buffercache` is helpful:
```sql
create extension if not exists pg_buffercache;

select
  coalesce(n.nspname, '<unknown>') as schema,
  coalesce(c.relname, '<unknown>') as relation,
  count(*) as buffers,
  pg_size_pretty(count(*) * current_setting('block_size')::bigint) as buffered
from pg_buffercache b
left join pg_class c
  on pg_relation_filenode(c.oid) = b.relfilenode
left join pg_namespace n
  on n.oid = c.relnamespace
where b.reldatabase in (
  0,
  (select oid from pg_database where datname = current_database())
)
group by n.nspname, c.relname
order by count(*) desc
limit 30;
```

In container metrics, check what corresponds to a larger share of the total usage
```
100
* sum(container_memory_cache{namespace="<ns>", pod=~"<name>.*"}) by (pod, container) 
/ sum(container_memory_usage_bytes{namespace="<ns>", pod=~"<name>.*"}) by (pod, container)
```

```
100
* sum(container_memory_rss_bytes{namespace="<ns>", pod=~"<name>.*"}) by (pod, container) 
/ sum(container_memory_usage_bytes{namespace="<ns>", pod=~"<name>.*"}) by (pod, container)
```


# How Postgres uses memory
Postgres has a few different memory categories, and they do not all behave like short-lived application heap.

`shared_buffers` is the most visible one. It is a shared cache managed by Postgres for table and index pages. Once pages are read and this cache is warmed, the memory is expected to stay useful. A quiet database does not mean Postgres should eagerly empty this cache.

Backend processes also keep memory for connection-local state. Settings such as `work_mem` and `maintenance_work_mem` describe how much memory certain operations may use, but they are not all fully reserved at startup. They become relevant when a sort, hash, vacuum, index build, or similar operation actually needs them.

There are also background processes: checkpointer, WAL writer, autovacuum, stats, and friends. Even when application traffic is absent, Postgres is not a single sleeping process.

# Practical takeaway
For Postgres, high memory during idle time is not automatically a problem. It becomes a problem when it comes with low `MemAvailable` (`sum(container_memory_available_bytes{namespace="<ns>", pod=~"<name>.*"}) by (pod, container)`), cgroup pressure, swap activity, OOM events, continuously growing private RSS, or query behavior that allocates memory without returning to a stable baseline.
