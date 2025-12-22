---
title: "Kubernetes metrics, logs, and traces via OpenTelemetry collector"
date: 2025-12-22T20:00:00+01:00
tags: [engineering, kubernetes, devops, sre, open-telemetry, observability]
author: Tom M G
draft: false
---

# The Problem
Observing distributed systems is not a trivial task. We have several machines running, each hosting workloads that minding their business, do network calls, and print logs. That makes one think "how on earth am I gonna keep it together?".

# One opinionated solution
Well, there's a widely adopted tool that works as a central piece, gracefully turning chaos into an ordered flow. It is called OpenTelemetry Collector, and this article approaches it in an opinionated way.

# Architecture overview
- One otel-collector runs as a DaemonSet to capture and process metrics, logs, and traces
- One trace-collector runs as a Deployment to reconstruct traces across different nodes
- Each node gets a subset of app metrics to scrape
- Metrics are scraped from Apps, Kubernetes, and the Host itself, and then forwarded to Victoriametrics
- Log files are tailed, and forwarded to Victorialogs
- Traces are received from app instrumentation, glued together in trace-collector, and forwarded to Victoriatraces.
  - They are also parsed to `calls_total` and `duration_milliseconds_.*` metrics

# Introduction
The [collector][otelcol] has three main pieces that are responsible for orchestrating the telemetry flow. [Receivers][otelcol-receivers], [Processors][otelcol-processors], and [Exporters][otelcol-exporters]. OpenTelemetry Collector has this repo [opentelemetry-collector-contrib][otelcol-contrib] that offers, abundantly, options of these three.

These three pieces are then orchestrated by a [Pipeline][otelcol-pipeline], and for `traces <> metrics`, transformed via [Connector][otelcol-connector].

[otelcol]: https://opentelemetry.io/docs/collector/
[otelcol-receivers]: https://opentelemetry.io/docs/collector/components/receiver/
[otelcol-processors]: https://opentelemetry.io/docs/collector/components/processor/
[otelcol-exporters]: https://opentelemetry.io/docs/collector/components/exporter/
[otelcol-contrib]: https://github.com/open-telemetry/opentelemetry-collector-contrib
[otelcol-pipeline]: https://opentelemetry.io/docs/collector/architecture/#pipelines
[otelcol-connector]: https://opentelemetry.io/docs/collector/components/connector/

# Installing the collector
The easiest way is via the [operator][otelcol-operator], which enables several `CustomResourceDefinitions`. The one we are mainly interested is `OpenTelemetryCollector`. If you `$ kubectl explain opentelemetrycollector --recursive`, it can be a bit scary of how many settings there are. But we'll approach the most relevant ones in this article.

[otelcol-operator]: https://github.com/open-telemetry/opentelemetry-operator

# Telemetry pipelines
```yaml
metrics:
  receivers: 
    - hostmetrics
    - hostmetrics/disk # Get host metrics
    - kubeletstats # Get Kubernetes metrics
    - spanmetrics # Get parsed metrics from Traces
    - prometheus # Get scraped metrics from the Cluster's service monitors
  processors:
    - memory_limiter # Keep things cool
    - resource/instance # Set "instance" label so we know, in which machine, the daemonset pod has processed the telemetry
    - k8sattributes # Label metrics with infos from the Kubernetes workload
    - transform/metrics # Sanitize non-needed labels
    - batch # Batch stuff so we don't DDoS the timeseries backend
  exporters: 
    - prometheusremotewrite # Write to the telemetry backend

logs:
  receivers:
    - filelog # Tail container log files in the host
    - otlp # Possibly receive other logs from apps's OpenTelemetry instrumentation
  processors:
    - memory_limiter # Keep things cool
    - transform/logs # Drop unwanted fields
    - batch # Don't DDoS the log storage backend
  exporters: 
    - otlphttp/victoriametrics # Write to the log backend

traces:
  receivers: 
    - otlp # Receive traces from apps' instrumentation
  processors: 
    - memory_limiter # Keep things cool
    - k8sattributes # Enrich trace metadata
    - resource/instance # Say which node has processed the span
    - transform/spanmetrics # Parse spans to metrics
    - batch # Don't DDoS the trace storage backend
  exporters: 
    - spanmetrics # Send newly-parsed metrics
    - loadbalancing # Send spans to trace-collector for gathering cross-node spans
```

OpenTelemetry Collector has the features to make it happen. In fact, these above are pieces to achieve such telemetry flow.


# Metrics
These come from four different sources
- [hostmetrics][hostmetricsreceiver] receiver
  - Scrape the machine metrics like cpu, memory, filesystem, network, etc
- [kubeletstats][kubeletstatsreceiver] receiver
  - Scrape Kubernetes metrics from cAdvisor, i.e. nodes, containers, etc
- [spanmetrics][otelcol-spanmetrics] connector
  - Receives metrics parsed from traces, e.g. `calls_total`, `duration_milliseconds_.*`
- [Prometheus][prometheusreceiver] receiver
  - Relies on [target allocator][otelcol-targetallocator] to find [service monitors][servicemonitors] to scrape

Are processed with
- [memory_limiter][otelcol-memorylimiter] processor
  - Ensures the collector doesn't trespass the max limit and crash; at the expense of losing data
- [resource][otelcol-resource] processor
  - Label the metric arbitrarily
- [k8sattributes][otelcol-k8sattributes] processor
  - Label the metric from Kubernetes resource label
- [transform][otelcol-transform] processor
  - Add and remove metric labels aiming to keep cardinality lower as possible
- [batch][otelcol-batch] processor
  - Suggestively, gathers metrics before sending them to save some network calls

And forwarded to
- [prometheusremotewrite][otelcol-prometheusremotewrite] exporter
  - Sends metrics to Victoriametrics' `insert` workload
    - In my cluster, the `prometheusremotewrite` was noticeably much more memory friendly than `otlphttp`

# Logs
These can come from two origins
- [filelog][otelcol-filelog] receiver
  - Tails pod log files logs (assuming containerd as the CRI), parses them to json when applicable, and extract resource metadata out of it
- [otlp][otelcol-otlp] receiver
  - To enable apps sending arbitrary logs not written in stdout/stderr

Are processed with
- [memory_limiter][otelcol-memorylimiter] processor
  - Ensures the collector doesn't trespass the max limit and crash; at the expense of losing data
- [transform][otelcol-transform] processor
  - Aiming to keep storage lower as possible, drops everything we don't need as a filterable field
- [batch][otelcol-batch] processor

And forwarded to
- [otlphttp][otelcol-otlphttp] exporter
  - Sends to Victorialogs `insert` workload

# Traces
These can come from a single origin
- [otlp][otelcol-otlp] receiver
  - App instrumentation reports traces via `otlp` to their node's Collector, on the `hostPort` opened by the DaemonSet

Are processed with
- [memory_limiter][otelcol-memorylimiter] processor
- [k8sattributes][otelcol-k8sattributes] processor
- [resource][otelcol-resource] processor
- [transform][otelcol-transform] processor
- [batch][otelcol-batch] processor

And forwarded to
- [spanmetrics][otelcol-spanmetrics] connector
  - Which is also one of the metrics' pipeline receiver 
- [loadbalancing][otelcol-loadbalancing] exporter
  - Routes spans by `traceID`, so all spans are gathered in the same `trace-collector`, which is necessary for tail sampling


[servicemonitors]: https://prometheus-operator.dev/docs/developer/getting-started/#using-servicemonitors
[otelcol-targetallocator]: https://opentelemetry.io/docs/platforms/kubernetes/operator/target-allocator/
[kubeletstatsreceiver]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/kubeletstatsreceiver
[hostmetricsreceiver]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/hostmetricsreceiver
[prometheusreceiver]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/prometheusreceiver#opentelemetry-operator
[otelcol-memorylimiter]: https://github.com/open-telemetry/opentelemetry-collector/tree/main/processor/memorylimiterprocessor
[otelcol-resource]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/resourceprocessor
[otelcol-k8sattributes]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/k8sattributesprocessor
[otelcol-transform]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/transformprocessor
[otelcol-batch]: https://github.com/open-telemetry/opentelemetry-collector/tree/main/processor/batchprocessor
[otelcol-filelog]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/filelogreceiver
[otelcol-otlp]: https://github.com/open-telemetry/opentelemetry-collector/tree/main/receiver/otlpreceiver
[otelcol-otlphttp]: https://github.com/open-telemetry/opentelemetry-collector/tree/main/exporter/otlphttpexporter
[otelcol-prometheusremotewrite]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/prometheusremotewriteexporter
[otelcol-spanmetrics]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/connector/spanmetricsconnector
[otelcol-loadbalancing]: https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/exporter/loadbalancingexporter


# Appendix: Full manifests
## otel-collector DaemonSet
```yaml
apiVersion: opentelemetry.io/v1beta1
kind: OpenTelemetryCollector
metadata:
  name: otel
spec:
  mode: daemonset
  image: ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-contrib:0.140.1
  resources:
    requests:
      cpu: 100m
      memory: 448Mi
    limits:
      cpu: "2"
      memory: 1536Mi
  ports:
    - name: grpc
      port: 4317
      hostPort: 4317
      targetPort: 4317
    - name: http
      port: 4318
      hostPort: 4318
      targetPort: 4318

  observability:
    metrics:
      enableMetrics: true
  env:
    - name: POD_IP
      valueFrom:
        fieldRef:
          fieldPath: status.podIP
    - name: K8S_NODE_NAME
      valueFrom:
        fieldRef:
          fieldPath: spec.nodeName

  targetAllocator:
    enabled: true
    image: ghcr.io/open-telemetry/opentelemetry-operator/target-allocator:0.138.0
    resources:
      requests:
        cpu: 25m
        memory: 128Mi
      limits:
        cpu: 250m
        memory: 256Mi
    allocationStrategy: per-node
    prometheusCR:
      enabled: true
      scrapeInterval: 30s
      serviceMonitorSelector: {}

  volumes:
    - name: varlogpods
      hostPath:
        path: /var/log/pods

  volumeMounts:
    - name: varlogpods
      mountPath: /var/log/pods

  config:
    extensions:
      health_check:
        endpoint: ${env:POD_IP}:13133

    # https://opentelemetry.io/docs/collector/components/receiver/
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318
      filelog:
        include:
        - /var/log/pods/*/*/*.log
        include_file_name: false
        include_file_path: true
        retry_on_failure:
          enabled: true
        start_at: beginning
        operators:
        - id: parser-containerd
          type: regex_parser 
          regex: ^(?P<time>[^ ^Z]+Z) (?P<stream>stdout|stderr) (?P<logtag>[^ ]*) ?(?P<log>.*)$
          timestamp:
            layout: '%Y-%m-%dT%H:%M:%S.%LZ'
            parse_from: attributes.time

        - id: parser-pod-info
          parse_from: attributes["log.file.path"]
          regex: ^.*\/(?P<namespace>[^_]+)_(?P<pod_name>[^_]+)_(?P<uid>[a-f0-9\-]+)\/(?P<container_name>[^\._]+)\/(?P<restart_count>\d+)\.log$
          type: regex_parser

        # Handle line breaks
        - type: recombine
          is_last_entry: attributes.logtag == 'F'
          combine_field: attributes.log
          combine_with: ""
          max_batch_size: 1000
          max_log_size: 1048576
          output: handle_empty_log
          source_identifier: attributes["log.file.path"]
        - field: attributes.log
          id: handle_empty_log
          if: attributes.log == nil
          type: add
          value: ""

        - type: json_parser
          parse_from: attributes.log
          if: attributes.log matches "^\\{"

        - type: add
          field: attributes.instance
          value: ${env:K8S_NODE_NAME}

        - id: export
          type: noop

      hostmetrics:
        collection_interval: 30s
        root_path: /
        scrapers:
          cpu:
            enabled:
            metrics:
              system.cpu.time:
                enabled: true
              system.cpu.utilization:
                enabled: true
              system.cpu.physical.count:
                enabled: true
          memory:
            metrics:
              system.memory.usage:
                enabled: true
              system.memory.utilization:
                enabled: true
              system.memory.limit:
                enabled: true
          load:
            cpu_average: true
            metrics:
              system.cpu.load_average.1m:
                enabled: true
              system.cpu.load_average.5m:
                enabled: true
              system.cpu.load_average.15m:
                enabled: true
          network:
            metrics:
              system.network.connections:
                enabled: true
              system.network.dropped:
                enabled: true
              system.network.errors:
                enabled: true
              system.network.io:
                enabled: true
              system.network.packets:
                enabled: true
              system.network.conntrack.count:
                enabled: true
              system.network.conntrack.max:
                enabled: true

      hostmetrics/disk:
        collection_interval: 1m
        root_path: /
        scrapers:
          disk:
            metrics:
              system.disk.io:
                enabled: true
              system.disk.operations:
                enabled: true
          filesystem:
            metrics:
              system.filesystem.usage:
                enabled: true
              system.filesystem.utilization:
                enabled: true

      kubeletstats:
        collection_interval: 30s
        auth_type: "serviceAccount"
        endpoint: "https://${env:K8S_NODE_NAME}:10250"
        insecure_skip_verify: true
        collect_all_network_interfaces:
          node: true
          pod: true

      prometheus:
        target_allocator:
          collector_id: ${env:POD_NAME}
          endpoint: http://otel-targetallocator
          interval: 30s
        config:
          scrape_configs:
          - job_name: otel-collector
            scrape_interval: 30s
            static_configs:
              - targets:
                  - ${env:POD_IP}:8888

    # https://opentelemetry.io/docs/collector/components/processor/
    processors:
      memory_limiter:
        check_interval: 1s
        limit_percentage: 75
        spike_limit_percentage: 15
      batch:
        send_batch_max_size: 2048
        send_batch_size: 1024
        timeout: 1s
      k8sattributes:
        auth_type: "serviceAccount"
        passthrough: false
        filter:
          node_from_env_var: K8S_NODE_NAME
        extract:
          metadata:
            - k8s.namespace.name
            - k8s.deployment.name
            - k8s.replicaset.name
            - k8s.statefulset.name
            - k8s.daemonset.name
            - k8s.cronjob.name
            - k8s.job.name
            - k8s.node.name
            - k8s.pod.name
            - k8s.pod.ip
            - k8s.container.name
            - container.id
          labels:
            - tag_name: owner
              key: app.kubernetes.io/owner
              from: pod
        pod_association:
        - sources:
          - from: resource_attribute
            name: k8s.pod.ip
        - sources:
          - from: resource_attribute
            name: k8s.pod.name
          - from: resource_attribute
            name: k8s.namespace.name
        - sources:
          - from: connection
      resource/instance:
        attributes:
        # Sets "instance" label on metrics
        - action: upsert
          key: service.instance.id
          value: ${env:K8S_NODE_NAME}
      transform/logs:
        error_mode: ignore
        log_statements:
          # Keep only essential fields
          - statements:
            - set(log.attributes["namespace"], resource.attributes["namespace"])
            - keep_matching_keys(log.attributes, "^(_.*|@.*|filename|log|service|job|agent|k8s\\.|container_name|instance|level|msg|message|namespace|pod_name|severity|severity_text|stream)")
          - conditions: IsMap(log.body)
            statements:
              - keep_matching_keys(log.body, "^(level|msg|message|severity|severity_text)$")

      transform/metrics:
        error_mode: ignore
        metric_statements:
        - statements:
            - set(datapoint.attributes["env"], resource.attributes["k8s.cluster.name"])
            - set(datapoint.attributes["owner"], resource.attributes["owner"]) where resource.attributes["owner"] != nil
            - set(datapoint.attributes["namespace"], resource.attributes["k8s.namespace.name"]) where resource.attributes["k8s.namespace.name"] != nil and resource.attributes["k8s.namespace.name"] != "kube-system"
            - set(datapoint.attributes["pod"], resource.attributes["k8s.pod.name"]) where resource.attributes["k8s.pod.name"] != nil
            - set(datapoint.attributes["container"], resource.attributes["k8s.container.name"]) where resource.attributes["k8s.container.name"] != nil

            # Normalize label names for kube-state-metrics, ingress-nginx, etc.
            - set(datapoint.attributes["namespace"], datapoint.attributes["exported_namespace"]) where datapoint.attributes["exported_namespace"] != nil and resource.attributes["k8s.namespace.name"] != "kube-system"
            - set(datapoint.attributes["service"], datapoint.attributes["exported_service"]) where datapoint.attributes["exported_service"] != nil
            - set(datapoint.attributes["pod"], datapoint.attributes["exported_pod"]) where datapoint.attributes["exported_pod"] != nil
            - set(datapoint.attributes["container"], datapoint.attributes["exported_container"]) where datapoint.attributes["exported_container"] != nil

        - statements:
            - delete_key(datapoint.attributes, "exported_namespace") where datapoint.attributes["exported_namespace"] != nil
            - delete_key(datapoint.attributes, "exported_service") where datapoint.attributes["exported_service"] != nil
            - delete_key(datapoint.attributes, "exported_pod") where datapoint.attributes["exported_pod"] != nil
            - delete_key(datapoint.attributes, "exported_container") where datapoint.attributes["exported_container"] != nil

      transform/spanmetrics:
        error_mode: silent
        trace_statements:
        - statements:
            - set(span.attributes["namespace"], resource.attributes["k8s.namespace.name"]) where resource.attributes["k8s.namespace.name"] != nil
            - set(span.attributes["namespace"], resource.attributes["service.namespace"]) where resource.attributes["service.namespace"] != nil

    connectors:
      spanmetrics:
        aggregation_cardinality_limit: 100000
        dimensions:
          - name: namespace
          - name: http.route
          - name: http.method
          - name: http.status_code
        exclude_dimensions:
          - status.code
          - span.name
          - span.kind
          - service.name # The "job" label usually carries the same value
        histogram:
          explicit:
            buckets:
            - 10ms
            - 50ms
            - 100ms
            - 250ms
            - 500ms
            - 1s
            - 2s
            - 5s
        metrics_expiration: 1m
        metrics_flush_interval: 30s
        namespace: ""

    # https://opentelemetry.io/docs/collector/components/exporter/
    exporters:
      debug: {}
      prometheusremotewrite:
        endpoint: http://vmmetrics-insert.victoriametrics:8480/insert/0/prometheus
        timeout: 30s
        retry_on_failure:
          enabled: true
          initial_interval: 10s
          max_interval: 60s
          max_elapsed_time: 300s
      otlphttp/victoriametrics:
        compression: gzip
        encoding: proto
        logs_endpoint: http://vmlogs-insert.victoriametrics:9481/insert/opentelemetry/v1/logs
        tls:
          insecure: true
      loadbalancing:
        routing_key: traceID
        resolver:
          dns:
            hostname: trace-collector
        protocol:
          otlp:
            tls:
              insecure: true

    # https://opentelemetry.io/docs/collector/configuration/#service
    service:
      telemetry:
        logs:
          encoding: json
          level: info

      extensions:
        - health_check

      # https://opentelemetry.io/docs/collector/configuration/#pipelines
      pipelines:
        logs:
          receivers: [filelog, otlp]
          processors:
            - memory_limiter
            - transform/logs
            - batch
          exporters: [otlphttp/victoriametrics]
        metrics:
          receivers: 
            - hostmetrics
            - hostmetrics/disk
            - kubeletstats
            - spanmetrics
            - prometheus
          processors:
            - memory_limiter
            - resource/instance
            - k8sattributes
            - transform/metrics
            - batch
          exporters: 
            - prometheusremotewrite
        traces:
          receivers: [otlp]
          processors: 
            - memory_limiter
            - k8sattributes
            - resource/instance
            - transform/spanmetrics
            - batch
          exporters: 
            - spanmetrics
            - loadbalancing
```
## otel-collector RBAC
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: otel-collector
rules:
  - apiGroups: [""]
    resources:
      - pods
      - namespaces
      - nodes
      - nodes/metrics
      - nodes/stats
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources:
      - replicasets
      - deployments
      - statefulsets
      - daemonsets
    verbs: ["get", "list", "watch"]
  - apiGroups: ["batch"]
    resources:
      - jobs
      - cronjobs
    verbs: ["get", "list", "watch"]
  - apiGroups: ["extensions"]
    resources:
      - replicasets
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: otel-collector
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: otel-collector
subjects:
  - kind: ServiceAccount
    name: otel-collector # Controller provisions the SA but not the ClusterRole
    namespace: open-telemetry
```

## trace-collector Deployment
```yaml
# trace-collector
  apiVersion: opentelemetry.io/v1beta1
  kind: OpenTelemetryCollector
  metadata:
    name: trace
  spec:
    mode: deployment
    image: ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-contrib:0.140.1
    autoscaler:
      minReplicas: 2
      maxReplicas: 6
      targetCPUUtilization: 100
    resources:
      requests:
        cpu: 100m
        memory: 384Mi
      limits:
        cpu: 500m
        memory: 1Gi
    ports:
      - name: grpc
        port: 4317
        targetPort: 4317

    observability:
      metrics:
        enableMetrics: true
    env:
      - name: POD_IP
        valueFrom:
          fieldRef:
            fieldPath: status.podIP
      - name: K8S_NODE_NAME
        valueFrom:
          fieldRef:
            fieldPath: spec.nodeName

    config:
      extensions:
        health_check:
          endpoint: ${env:POD_IP}:13133

      # https://opentelemetry.io/docs/collector/components/receiver/
      receivers:
        otlp:
          protocols:
            grpc:
              endpoint: 0.0.0.0:4317

        prometheus:
          config:
            scrape_configs:
            - job_name: trace-collector
              scrape_interval: 30s
              static_configs:
                - targets:
                    - ${env:POD_IP}:8888

      # https://opentelemetry.io/docs/collector/components/processor/
      processors:
        memory_limiter:
          check_interval: 1s
          limit_percentage: 75
          spike_limit_percentage: 15
        batch:
          send_batch_max_size: 2048
          send_batch_size: 1024
          timeout: 1s
        tail_sampling:
          policies:
            - name: drop_spann
              type: drop
              drop:
                drop_sub_policy:
                  - type: ottl_condition
                    name: sub-policy-0
                    ottl_condition:
                      error_mode: ignore
                      span:
                        - IsMatch(attributes["http.target"], "^(/health|/metrics|/ping|/ready)")

            - name: keep_slow_requests
              type: latency
              latency:
                threshold_ms: 1000

            - name: keep_error_requests
              type: numeric_attribute
              numeric_attribute:
                key: http.status_code
                min_value: 400
                max_value: 599

            - name: keep_user_spans
              type: ottl_condition
              ottl_condition:
                error_mode: ignore
                span:
                  - attributes["user.id"] != nil and attributes["user.id"] != ""

            - name: keep_1_percent_of_the_rest
              type: probabilistic
              probabilistic:
                sampling_percentage: 1

      # https://opentelemetry.io/docs/collector/components/exporter/
      exporters:
        debug: {}
        otlphttp/victoriametrics:
          compression: gzip
          encoding: proto
          traces_endpoint: http://vmtraces-insert.victoriametrics:10481/insert/opentelemetry/v1/traces
          tls:
            insecure: true

      # https://opentelemetry.io/docs/collector/configuration/#service
      service:
        telemetry:
          logs:
            encoding: json
            level: info

        extensions:
          - health_check

        # https://opentelemetry.io/docs/collector/configuration/#pipelines
        pipelines:
          logs:
            receivers: [otlp]
            processors: []
            exporters: [debug]
          metrics:
            receivers: [otlp]
            processors: []
            exporters: [debug]
          traces:
            receivers: [otlp]
            processors:
              - memory_limiter
              - tail_sampling
              - batch
            exporters: [otlphttp/victoriametrics]
```

## trace-collector RBAC
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: otel-targetallocator
rules:
  - apiGroups: [""]
    resources:
      - pods
      - services
      - endpoints
      - nodes
      - nodes/metrics
      - namespaces
      - configmaps
    verbs: ["get", "list", "watch"]
  - apiGroups: ["discovery.k8s.io"]
    resources:
      - endpointslices
    verbs: ["get", "list", "watch"]
  - apiGroups: ["monitoring.coreos.com"]
    resources:
      - probes
      - scrapeconfigs
    verbs: ["get", "list", "watch"]
  - apiGroups: ["monitoring.coreos.com"]
    resources:
      - servicemonitors
      - podmonitors
    verbs: ["*"] # targetAllocator throws a warning if this isnt permissive
  - apiGroups: ["opentelemetry.io"]
    resources:
      - opentelemetrycollectors
    verbs: ["get", "list", "watch"]
  - apiGroups: ["networking.k8s.io"]
    resources:
      - ingresses
    verbs: ["get", "list", "watch"]
  - nonResourceURLs:
      - /apis
      - /apis/*
      - /api
      - /api/*
      - /metrics
    verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: otel-targetallocator
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: otel-targetallocator
subjects:
  - kind: ServiceAccount
    name: otel-targetallocator # Controller provisions the SA but not the ClusterRole
    namespace: open-telemetry
```
