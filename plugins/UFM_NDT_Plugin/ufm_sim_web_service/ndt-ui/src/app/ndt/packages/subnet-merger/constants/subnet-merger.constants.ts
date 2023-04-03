import {NdtViewService} from "../../../services/ndt-view.service";

export class SubnetMergerConstants {

  public static reportAPIKeys = {
    "status": "status" as "status",
    "timestamp": "timestamp" as "timestamp",
    "NDT_file": "NDT_file" as "NDT_file",
    "report": "report" as "report",
    "category": "category" as "category",
    "description": "description" as "description",
    "reportID": "report_id" as "report_id",
    "reportScope": "report_scope" as "report_scope"
  }

  public static NDTFileKeys = {
    "file": "file" as "file",
    "timestamp": "timestamp" as "timestamp",
    "file_type": "file_type" as "file_type",
    "file_status": "file_status" as "file_status",
    "sha_1": "sha-1" as "sha-1",
    "last_deployed_file": "last_deployed_file" as "last_deployed_file"
  }

  public static validateAPIKeys = {
    "NDTFileName": "ndt_file_name" as "ndt_file_name"
  }

  public static boundariesStates = {
    "boundaryPortState": "boundary_port_state" as "boundary_port_state",
    "noDiscover": "No-discover" as "No-discover",
    "disabled": "Disabled" as "Disabled",
  }

  public static baseApiUrl = `${NdtViewService.isRunningFromUFM ? NdtViewService.ufmRESTBase + '/plugin/ndt' : ''}`;

  public static mergerAPIs = {
    uploadNDT: `${SubnetMergerConstants.baseApiUrl}/merger_upload_ndt`,
    NDTsList: `${SubnetMergerConstants.baseApiUrl}/merger_ndts_list`,
    validateNDT: `${SubnetMergerConstants.baseApiUrl}/merger_verify_ndt`,
    deployNDTFile: `${SubnetMergerConstants.baseApiUrl}/merger_deploy_ndt_config`,
    validationReports: `${SubnetMergerConstants.baseApiUrl}/merger_verify_ndt_reports`,
    updateBoundaryPortsState: `${SubnetMergerConstants.baseApiUrl}/merger_update_topoconfig`,
    lastDeployedNDT: `${SubnetMergerConstants.baseApiUrl}/merger_deployed_ndt`

  }

}
