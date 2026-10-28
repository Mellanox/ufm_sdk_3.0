
export interface ITableInfo {
  api: {
    path: string,
    params?: [{ param_name: string, param_type: string, is_optional: boolean }],
    label_of_table?: string,
    popup_data?: {column_name: string, popup_name: string}[]
  },
  component_type: string,
  condition: string,
  groups_api?: string,
  path: string,
  tab_name: string,
}

export interface IDynamicTablesData {
  tables_data: ITableInfo[],
  tables_order: {
    [p: string] : string[]
  },
  condition_icons: {
    [p: string] : string
  }
}
