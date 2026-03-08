{{- define "ufm-plugin.discoveredNamespace" -}}
{{- $root := . -}}
{{- $ufmConfigName := printf "%s-config" $root.Values.ufmFullname -}}
{{- $found := "" -}}
{{- with (lookup "v1" "ConfigMap" "" "").items -}}
{{- range . -}}
{{- if and (not $found) (index . "data") (hasKey (index . "data") "UFM_VERSION") (eq (index . "metadata" "name") $ufmConfigName) -}}
{{- $found = index . "metadata" "namespace" -}}
{{- end -}}
{{- end -}}
{{- end -}}
{{- $found | default $root.Values.namespace | default "ufm-enterprise" -}}
{{- end }}

{{- define "ufm-plugin.namespace" -}}
{{- include "ufm-plugin.discoveredNamespace" . -}}
{{- end }}

{{- define "ufm-plugin.pvcClaimName" -}}
{{- .Values.existingClaim | default (printf "%s-files" .Values.ufmFullname) }}
{{- end }}

{{- define "ufm-plugin.configMapName" -}}
{{- .Values.configMapName | default (printf "%s-plugins" .Values.ufmFullname) }}
{{- end }}
