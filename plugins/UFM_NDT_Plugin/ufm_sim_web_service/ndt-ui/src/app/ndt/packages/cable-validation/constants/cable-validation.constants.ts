import {SubnetMergerConstants} from "../../subnet-merger/constants/subnet-merger.constants";

export class CableValidationConstants {

  public static reportAPIKeys = {
    report: 'report',
    stats: 'stats',
    stats_in_progress: 'in_progress',
    stats_no_issues: 'no_issues',
    stats_not_started: 'not_started',
    issues: 'issues',
    timestamp: 'timestamp',
    node_desc: 'node_desc',
    unit: 'unit',
    rack: 'rack',
    parent_node_desc: 'parent_node_desc',
    node_issues_columns_order: ['issue', 'source', 'expected_neighbor', 'discovered_neighbor'],
    issue_color_based_on_type: {
      "Marginal Cable Grade": "#F0AD4E",
      "Poor Cable Grade": "#ff0000"
    }
  }

  public static API_URLs = {
    cableValidationSettings: `${SubnetMergerConstants.baseApiUrl}/cable_validation_connection_configuration`,
    cableValidationReport: `${SubnetMergerConstants.baseApiUrl}/cable_validation_report`
  }

  public static API_SERVER_KEYS = {
    'mode': 'mode',
    'status': 'status',
    'address': 'address',
    'port': 'port',
    'username': 'username',
    'password': 'password',
    'isEnabled': 'is_enabled'
  }

}
