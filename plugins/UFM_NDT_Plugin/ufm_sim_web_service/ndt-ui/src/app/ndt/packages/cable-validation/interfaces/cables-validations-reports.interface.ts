export interface ICablesValidationReportStats {
  in_progress: number,
  no_issues: number,
  not_started: number
}

export interface ICableValidationReportIssue {
  timestamp: number,
  node_desc: string,
  rack?: string,
  unit?: string
  isCollapsed?: boolean,
  issues: Array<Array<string>>
}

export interface ICablesValidationReportResult {
  report: string,
  stats: ICablesValidationReportStats,
  issues: Array<ICableValidationReportIssue>
}
