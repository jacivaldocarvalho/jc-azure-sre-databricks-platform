{{/*
Expand the name of the chart.
*/}}
{{- define "jc-sre-api.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "jc-sre-api.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s" $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "jc-sre-api.labels" -}}
app.kubernetes.io/name: {{ include "jc-sre-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: jc-azure-sre-databricks-platform
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "jc-sre-api.selectorLabels" -}}
app.kubernetes.io/name: {{ include "jc-sre-api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
