{{- define "ufm-plugin.namespace" -}}
{{- .Values.namespace | default "ufm-enterprise" }}
{{- end }}

{{- define "ufm-plugin.pvcClaimName" -}}
{{- .Values.existingClaim | default (printf "%s-files" .Values.ufmFullname) }}
{{- end }}

{{- define "ufm-plugin.configMapName" -}}
{{- .Values.configMapName | default (printf "%s-plugins" .Values.ufmFullname) }}
{{- end }}
