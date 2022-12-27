/**
 * @MODULES
 */
import {ChangeDetectorRef, Component, EventEmitter, Input, OnInit, ViewChild} from '@angular/core';

/**
 * @COMPONENTS
 * */
import {BehaviorSubject, Subscription} from "rxjs";
import {NavigationEnd, Router} from '@angular/router';

/**
 * @CONSTANTS
 */
import {DeviceJobsConstants} from "./constants/device-jobs.constants";
import {XCoreAgGridConstants} from "sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {UfmDevicesConstants} from "../../packages/ufm-devices/constants/ufm-devices.constants";

/**
 * @SERVICES
 */
import {XCoreAgGridOptions} from "sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {BrightBackendService} from "../../packages/bright/services/bright-backend.service";
import {
  IXCoreAgGridExtraOptions
} from "sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-extra-options.interface";
import {ContextMenuItem, DevicesJobsContextMenu} from "./classes/devices-jobs-context-menu";
import {UfmDevicesBackendService} from "../../packages/ufm-devices/services/ufm-devices-backend.service";


@Component({
  selector: 'app-devices-jobs-view',
  templateUrl: './devices-jobs-view.component.html',
  styleUrls: ['./devices-jobs-view.component.scss']
})
export class DevicesJobsViewComponent implements OnInit {

  /**
   * @Inputs
   */
  @Input() selectedDevice;
  @Input() bright_ip: string;
  @Input() bright_port: string;

  /**
     * @VARIABLES
     * */
    private routerParamsSub:Subscription;
    public dataIsLoading = true;
    public tableData = [];
    public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
    public contextMenuItems:[ContextMenuItem];
    public devicesJobsContextMenu:DevicesJobsContextMenu = new DevicesJobsContextMenu();

  /**
   * @CHILDREN
   */
  @ViewChild('statusTemp', {static: true}) statusTemp;
  @ViewChild("jobsStatisticsModal", {static: true}) jobsStatisticsModal;

  constructor(private backend: BrightBackendService,
              private router: Router,
              private ufmDevicesBackendService: UfmDevicesBackendService,
              private cdr: ChangeDetectorRef) {
    this.routerParamsSub = this.router.events.subscribe((event)=>{
      if(event instanceof NavigationEnd) {
        this.loadData();
      }
    });
  }

  get JOB_STATUS_MAP() {
    return DeviceJobsConstants.JOB_STATUS_MAP;
  }

  ngOnInit() {
    this.setTableOptions();
    this.loadData();
    this.contextMenuItems = this.devicesJobsContextMenu.buildContextMenu(this.onJobDetailsContextMenuClick);
  }

  ngOnDestroy() {
    if(this.routerParamsSub) {
      this.routerParamsSub.unsubscribe();
    }
    this.cdr.detectChanges();
  }

  public onJobDetailsContextMenuClick(row: any) {
    let jobType: string = row[DeviceJobsConstants.JOBS_SERVER_FIELDS.childType];
    jobType = jobType.charAt(0).toLowerCase() + jobType.slice(1)
    let uniqueKey = row[DeviceJobsConstants.JOBS_SERVER_FIELDS.uniqueKey];
    let url = 'https://' + this.bright_ip + ':' + this.bright_port + '/bright-view/#/j1/job/list/j2/' + jobType + '/' + uniqueKey + '/settings';
    window.open(url, "_blank");
  }

  public setTableOptions(): void {
    Object.assign(
      this.tableOptions.gridOptions,
      this.getJobsTableOptions()
    );
    Object.assign(
      this.tableOptions.extraOptions,
      this.getExtraTableOptions()
    );
  }

  public loadData(): void {
    this.dataIsLoading = true;
    this.ufmDevicesBackendService.getDeviceInfo(this.getDeviceGUIDFromURL()).subscribe((data) => {
      this.backend.getDeviceJobs([data[0][UfmDevicesConstants.DEVICE_SERVER_KEYS.system_name]]).subscribe(data => {
        this.tableData = data;
        this.dataIsLoading = false;
        this.cdr.detectChanges();
      });
    });
  }

  /**
   * @desc this function prepare table option
   * @returns {{}}
   */
  private getJobsTableOptions() {
    return {
      [XCoreAgGridConstants.columnDefs]: [
        {
          [XCoreAgGridConstants.field]: DeviceJobsConstants.JOBS_SERVER_FIELDS.childType,
          [XCoreAgGridConstants.headerName]: 'Type',
          [XCoreAgGridConstants.valueGetter]: (params: any) => {
            return DeviceJobsConstants.JOB_TYPE_MAP[params.data[params.column.colId]] || params.data[params.column.colId];
          }
        },
        {
          [XCoreAgGridConstants.field]: DeviceJobsConstants.JOBS_SERVER_FIELDS.jobID,
          [XCoreAgGridConstants.headerName]: 'Job ID'
        },
        {
          [XCoreAgGridConstants.field]: DeviceJobsConstants.JOBS_SERVER_FIELDS.username,
          [XCoreAgGridConstants.headerName]: 'User'
        },
        {
          [XCoreAgGridConstants.field]: DeviceJobsConstants.JOBS_SERVER_FIELDS.inqueue,
          [XCoreAgGridConstants.headerName]: 'Inqueue'
        },
        {
          [XCoreAgGridConstants.field]: DeviceJobsConstants.JOBS_SERVER_FIELDS.starttime,
          [XCoreAgGridConstants.headerName]: 'Running Time',
          [XCoreAgGridConstants.valueGetter]: (params: any) => {
            let duration = new Date(params.data[DeviceJobsConstants.JOBS_SERVER_FIELDS.endtime]).getTime()
              - new Date(params.data[DeviceJobsConstants.JOBS_SERVER_FIELDS.starttime]).getTime();
            return this.convertDurationToString(duration);
          }
        },
        {
          [XCoreAgGridConstants.field]: DeviceJobsConstants.JOBS_SERVER_FIELDS.status,
          [XCoreAgGridConstants.headerName]: 'Status',
          [XCoreAgGridConstants.cellRendererParams]: {
            [XCoreAgGridConstants.ngTemplate]: this.statusTemp
          }
        },
      ]
    }
  }

  /**
   * @desc this function called to prepare ag-grid extra option
   * @returns {{}}
   */
  private getExtraTableOptions(): IXCoreAgGridExtraOptions {
    return {
      [XCoreAgGridConstants.selectRowByKey]: new BehaviorSubject<any>(false),
      [XCoreAgGridConstants.showContextMenu]: new EventEmitter<any>(false),
      [XCoreAgGridConstants.tableName]: "Device-Jobs",
      [XCoreAgGridConstants.exportToCSV]: true
    };
  }

  onContextMenuClick($event: any) {
    this.tableOptions.extraOptions[XCoreAgGridConstants.showContextMenu].emit($event);
  }

  /**
   * takes time duration and returns meaningful time string.
   * @param duration
   */
  private convertDurationToString(duration: number) {
    const portions: string[] = [];

    const msInHour = 1000 * 60 * 60;
    const hours = Math.trunc(duration / msInHour);
    if (hours > 0) {
      portions.push(hours + 'h');
      duration = duration - (hours * msInHour);
    }

    const msInMinute = 1000 * 60;
    const minutes = Math.trunc(duration / msInMinute);
    if (minutes > 0) {
      portions.push(minutes + 'm');
      duration = duration - (minutes * msInMinute);
    }

    const seconds = Math.trunc(duration / 1000);
    if (seconds > 0) {
      portions.push(seconds + 's');
    }

    return portions.join(' ');
  }

  private getDeviceGUIDFromURL(): string {
    const urlParts = this.router.url.split("/");
    return urlParts[urlParts.indexOf('bright') - 1];
  }


}
