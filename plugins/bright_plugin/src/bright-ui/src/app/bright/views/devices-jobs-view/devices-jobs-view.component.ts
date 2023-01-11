/**
 * @MODULES
 */
import {ChangeDetectorRef, Component, EventEmitter, OnInit, ViewChild} from '@angular/core';

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
import {BrightConstants} from "../../packages/bright/constants/bright.constants";
import {TimePickerEvent} from "../../packages/time-picker-modal/timer-picker-event";
import {TimePickerModalConstants} from "../../packages/time-picker-modal/time-picker-modal.constants";
import {TimePickerType} from "../../packages/time-picker-modal/time-picker-type.enum";


@Component({
  selector: 'app-devices-jobs-view',
  templateUrl: './devices-jobs-view.component.html',
  styleUrls: ['./devices-jobs-view.component.scss']
})
export class DevicesJobsViewComponent implements OnInit {

  /**
   * @VARIABLES
   * */
  private routerParamsSub: Subscription;
  public dataIsLoading = true;
  public tableData = [];
  public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
  public brightConf = {};
  public contextMenuItems: [ContextMenuItem];
  public devicesJobsContextMenu: DevicesJobsContextMenu = new DevicesJobsContextMenu();

  public selectedTime: string = this.timeRanges[3].label;
  public selectedTimeRangeInMS;
  /**
   * @CHILDREN
   */
  @ViewChild('controlBtnsTemplate',{static: true}) controlBtnsTemplate;
  @ViewChild('statusTemp', {static: true}) statusTemp;
  @ViewChild("jobsStatisticsModal", {static: true}) jobsStatisticsModal;

  constructor(private backend: BrightBackendService,
              private router: Router,
              private ufmDevicesBackendService: UfmDevicesBackendService,
              private cdr: ChangeDetectorRef) {
    this.routerParamsSub = this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd && this.selectedTimeRangeInMS) {
        this.loadData();
      }
    });
  }

  get JOB_STATUS_MAP() {
    return DeviceJobsConstants.JOB_STATUS_MAP;
  }

  get bright_ip() {
    return this.brightConf[BrightConstants.brightConfKeys.brightConfig] &&
      this.brightConf[BrightConstants.brightConfKeys.brightConfig][BrightConstants.brightConfKeys.host];
  }

  get bright_port() {
    return this.brightConf[BrightConstants.brightConfKeys.brightConfig] &&
      this.brightConf[BrightConstants.brightConfKeys.brightConfig][BrightConstants.brightConfKeys.port];
  }

  get bright_status() {
    return this.brightConf[BrightConstants.brightConfKeys.brightConfig] &&
      this.brightConf[BrightConstants.brightConfKeys.brightConfig][BrightConstants.brightConfKeys.status][BrightConstants.brightConfKeys.status];
  }

  get bright_timezone() {
    return this.brightConf[BrightConstants.brightConfKeys.brightConfig] &&
      this.brightConf[BrightConstants.brightConfKeys.brightConfig][BrightConstants.brightConfKeys.timezone];
  }

  get BrightConstants() {
    return BrightConstants;
  }

  ngOnInit() {
    this.setTableOptions();
    this.contextMenuItems = this.devicesJobsContextMenu.buildContextMenu(this.onJobDetailsContextMenuClick);
  }

  ngOnDestroy() {
    if (this.routerParamsSub) {
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
    this.backend.getBrightConf().subscribe({
      next: (confData) => {
        this.brightConf = confData;
        this.ufmDevicesBackendService.getDeviceInfo(this.getDeviceGUIDFromURL()).subscribe({
          next: (data) => {
            this.backend.getDeviceJobs([data[0][UfmDevicesConstants.DEVICE_SERVER_KEYS.system_name]],
              this.selectedTimeRangeInMS.start, this.selectedTimeRangeInMS.end).subscribe({
              next: (data) => {
                this.tableData = data;
                this.dataIsLoading = false;
                this.cdr.detectChanges();
              },
              error: (err) => {
                console.error(err);
                this.dataIsLoading = false;
                this.cdr.detectChanges();
              }
            });
          },
          error: (err) => {
            console.error(err);
            this.dataIsLoading = false;
            this.cdr.detectChanges();
          }
        });
      },
      error: (err) => {
        console.error(err);
        this.dataIsLoading = false;
        this.cdr.detectChanges();
      }
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
          [XCoreAgGridConstants.headerName]: 'Job ID',
          [XCoreAgGridConstants.sort]: "desc",
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
          [XCoreAgGridConstants.field]: DeviceJobsConstants.JOBS_SERVER_FIELDS.submittime,
          [XCoreAgGridConstants.headerName]: 'Submit Time',
          [XCoreAgGridConstants.valueGetter]: (params: any) => {
            const submitTime = new Date(params.data[DeviceJobsConstants.JOBS_SERVER_FIELDS.submittime]);
            const timeZonesDiffInMS = this.getTimeZonesDiffInMSec(this.bright_timezone, this.backend.getLocalTimezone())
            return new Date(submitTime.getTime() - timeZonesDiffInMS).toLocaleString();
          }
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
      [XCoreAgGridConstants.exportToCSV]: true,
      [XCoreAgGridConstants.rightAdditionalControlsTemplate]: this.controlBtnsTemplate
    };
  }

  onContextMenuClick($event: any) {
    // NOT FULLY IMPLEMENTED YET
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

  public updateTimeFilterLabel($event): void {
    let endTimeInMilliseconds: number;
    let startTimeInMilliseconds: number;
    switch ($event.timeSelectionType) {
      case TimePickerType.TIME_RANGE:
        let timeRange: number = Number($event.timeRangeServerKey);
        endTimeInMilliseconds = new Date().getTime();
        startTimeInMilliseconds = endTimeInMilliseconds - (1000 * 60 * timeRange);
        break;
      case TimePickerType.CUSTOM_DATE_RANGE:
        startTimeInMilliseconds = $event.customDateTimeRangeValue[0].getTime();
        endTimeInMilliseconds = $event.customDateTimeRangeValue[1].getTime();
        break;
    }
    this.selectedTimeRangeInMS = {
      start: startTimeInMilliseconds,
      end: endTimeInMilliseconds
    };
    this.loadData();
  }

  /**
   * @desc this function will be sent to TimePickerModalComponent as input called selectedTimeLabelFormatter that format selected time label
   * @returns {string}
   * @param $event TimePickerEvent
   */
  public selectedTimeLabel = ($event: TimePickerEvent): string => {
    return $event.customDateTimeRangeValue[0].toLocaleString() + '   -   ' + $event.customDateTimeRangeValue[1].toLocaleString();
  }

  /**
   * @returns instance of the TIME_RANGES options {{label: string, value: string}[]}
   */

  public get timeRanges() {
    return TimePickerModalConstants.TIME_RANGES;
  }

  /**
   * @desc this function used to get the diff between 2 time zones in milliseconds
   * @param zone1
   * @param zone2
   */
  public getTimeZonesDiffInMSec(zone1: string, zone2: string): number {
    try {
      const d = new Date();
      // - was replaced by / due to Bug #3070915 which appeared in MAC
      const strDate1: string = d.toLocaleString("en-US", {timeZone: zone1}).replace(/-/g, "/");
      const strDate2: string = d.toLocaleString("en-US", {timeZone: zone2}).replace(/-/g, "/");
      return new Date(strDate1).getTime() - new Date(strDate2).getTime();
    } catch (exception) {
      return 0
    }
  }


}
