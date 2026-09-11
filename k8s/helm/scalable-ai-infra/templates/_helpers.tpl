{{/*
Generate common labels
*/}}
{{- define "scalable-ai.labels" -}}
app.kubernetes.io/part-of: scalable-ai-infra
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Generate selector labels for a service
*/}}
{{- define "scalable-ai.selectorLabels" -}}
app: {{ .name }}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/instance: {{ .release }}
{{- end }}

{{/*
Full image reference
*/}}
{{- define "scalable-ai.image" -}}
{{ .global.imageRegistry }}/{{ .image.repository }}:{{ .image.tag | default "latest" }}
{{- end }}
