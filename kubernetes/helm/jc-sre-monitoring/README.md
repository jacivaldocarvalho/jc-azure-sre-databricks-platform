# jc-sre-monitoring

Helm chart that deploys the `kube-prometheus-stack` and registers the
JC SRE API as a monitored target.

## What it installs

- **kube-prometheus-stack**: Prometheus Operator, Prometheus, Alertmanager, Grafana, node-exporter, kube-state-metrics
- **ServiceMonitor**: tells Prometheus to scrape the `jc-sre-api` Service
- **Grafana dashboard**: provisioned via ConfigMap sidecar

## Usage

From the repository root:

    helm dependency update kubernetes/helm/jc-sre-monitoring
    helm upgrade --install jc-sre-monitoring kubernetes/helm/jc-sre-monitoring \
      --namespace jc-sre \
      --create-namespace \
      --wait

## Accessing Grafana

    kubectl port-forward -n jc-sre svc/jc-sre-monitoring-grafana 3000:80

Then open http://localhost:3000 and log in with `admin` / `prom-operator`.

## Accessing Prometheus

    kubectl port-forward -n jc-sre svc/jc-sre-monitoring-kube-prometheus-prometheus 9090:9090

Then open http://localhost:9090.
