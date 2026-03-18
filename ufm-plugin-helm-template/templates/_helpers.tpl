{{- define "ufm-plugin.discoveredNamespace" -}}
{{- $root := . -}}
{{- $ufmConfigName := printf "%s-config" $root.Values.ufmFullname -}}
{{- $found := "" -}}
{{- $searchList := $root.Values.namespaceSearchList | default list -}}
{{- range $searchList -}}
{{- $ns := . -}}
{{- if not $found -}}
{{- with lookup "v1" "ConfigMap" $ns $ufmConfigName -}}
{{- if and (index . "data") (hasKey (index . "data") "UFM_VERSION") -}}
{{- $found = $ns -}}
{{- end -}}
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

{{- define "ufm-plugin.anyMountHealthScripts" -}}
{{- range .Values.plugins.items -}}
{{- if .mountHealthScripts -}}y{{- end -}}
{{- end -}}
{{- end }}
