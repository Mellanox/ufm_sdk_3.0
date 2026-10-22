/**
 * @MODULES
 */
import {ChangeDetectorRef, Component, EventEmitter, Input, OnInit, Output, ViewChild} from '@angular/core';
/**
 * @COMPONENTS
 */
import {XCoreAgGridComponent} from "../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid.component";

/**
 * @CONSTANTS
 */

import {ITableInfo} from "../interfaces/table-info.interface";
import {BehaviorSubject} from "rxjs";
import {
  XCoreAgGridOptions
} from "../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {XCoreAgGridConstants} from "../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {UtilsService} from "../services/utils.service";
import {Constants} from "../constants/constants";

@Component({
  selector: 'app-inventory-general-table',
  templateUrl: './inventory-general-table.component.html',
  styleUrls: ['./inventory-general-table.component.scss']
})
export class InventoryGeneralTableComponent implements OnInit {
  /**
   * @INPUTS
   */
  @Input('data') data;
  @Input('tableName') tableName: string;
  @Input() componentInfo: ITableInfo;
  @Input() rightAdditionalTemplate;
  @Input() isDataLoading: boolean;
  @Input() presentObjectAsGroupHeader: boolean;
  @Input() autoSize: boolean = true;

  /**
   * @OUTPUTS
   */
  @Output() onRowSelectionChange: EventEmitter<any> = new EventEmitter<any>();

  /**
   * @CHILDREN
   */
  @ViewChild('inventoryTable', {static: false}) inventoryTable: XCoreAgGridComponent;

  /**
   * @VARIABLES
   */
  public tableData;
  public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions();
  public isReady: boolean = false;
  public valuesOccurrencesMap;

  constructor(private cdr: ChangeDetectorRef) {
    this.tableOptions = new XCoreAgGridOptions();
  }

  ngOnInit(): void {
  }

  ngOnChanges(changes) {
    if (changes.data && typeof changes.data.currentValue != 'undefined') {
      this.prepareTable(changes.data.firstChange);
    }
  }

  ngOnDestroy() {
    this.cdr.detectChanges();
  }

  private prepareTable(isFirstChange?: boolean) {
    this.isReady = false;
    if (this.data) {
      this.tableData = this.data;
      this.valuesOccurrencesMap = UtilsService.prepareValuesOccurrencesMap(this.tableData);
      this.prepareTableOptions(isFirstChange);
      this.isReady = true;
    } else {
      this.isReady = true;
    }
  }

  /**
   * @desc this function used to create XCoreAgGridOptions by looping over json and creat column for each key
   * @private
   */
  private prepareTableOptions(isFirstChange?: boolean): void {
    const options = {
      [XCoreAgGridConstants.paginationPageSize]: "20",
      [XCoreAgGridConstants.columnDefs]: []
    };
    if (!this.data.length) {
      return;
    }
    let firstRow = this.data[0];
    Object.keys(firstRow).forEach((key) => {
      if (!Array.isArray(firstRow[key])) {
        if (typeof firstRow[key] == 'object' && firstRow[key]) {
          if (this.presentObjectAsGroupHeader) {
            let groupedColumn = {
              [XCoreAgGridConstants.headerName]: key,
              [XCoreAgGridConstants.children]: []
            }
            Object.keys(firstRow[key]).forEach((subKey) => {
              groupedColumn[XCoreAgGridConstants.children].push({
                [XCoreAgGridConstants.field]: key,
                [XCoreAgGridConstants.headerName]: subKey,
                [XCoreAgGridConstants.filter]: (this.valuesOccurrencesMap[key][subKey] && this.valuesOccurrencesMap[key][subKey] <= Constants.OCCURRENCES_VALUE_FILTER_THRESHOLD) ?
                  XCoreAgGridConstants.checkboxFilter : true,
                [XCoreAgGridConstants.valueGetter]: (params) => {
                  return params.data[params.colDef.field][subKey];
                }
              })
            })
            options[XCoreAgGridConstants.columnDefs].push(groupedColumn);
          } else {
            Object.keys(firstRow[key]).forEach((subKey) => {
              options[XCoreAgGridConstants.columnDefs].push({
                [XCoreAgGridConstants.field]: key,
                [XCoreAgGridConstants.headerName]: subKey,
                [XCoreAgGridConstants.filter]: (this.valuesOccurrencesMap[key][subKey] && this.valuesOccurrencesMap[key][subKey] <= Constants.OCCURRENCES_VALUE_FILTER_THRESHOLD) ?
                  XCoreAgGridConstants.checkboxFilter : true,
                [XCoreAgGridConstants.valueGetter]: (params) => {
                  return params.data[params.colDef.field][subKey];
                }
              })
            })
          }
        } else {
          options[XCoreAgGridConstants.columnDefs].push({
            [XCoreAgGridConstants.field]: key,
            [XCoreAgGridConstants.headerName]: key,
            [XCoreAgGridConstants.filter]: (this.valuesOccurrencesMap[key] && this.valuesOccurrencesMap[key] <= Constants.OCCURRENCES_VALUE_FILTER_THRESHOLD) ?
              XCoreAgGridConstants.checkboxFilter : true,
            [XCoreAgGridConstants.valueGetter]: (params) => {
              return params.data[params.colDef.field];
            }
          })
        }
      }
    })
    Object.assign(this.tableOptions.gridOptions, options);
    Object.assign(this.tableOptions.extraOptions, {
      [XCoreAgGridConstants.quickInputFilter]: true,
      [XCoreAgGridConstants.rightAdditionalControlsTemplate]: this.rightAdditionalTemplate,
      [XCoreAgGridConstants.tableName]: this.tableName || `${this.componentInfo.condition}_${this.componentInfo.path}_data_table`,
      [XCoreAgGridConstants.exportToCSV]: true,
      [XCoreAgGridConstants.exportToCSVIcon]: Constants.CSV_ICON
    });
    if (this.autoSize) {
      Object.assign(this.tableOptions.extraOptions, {
        [XCoreAgGridConstants.autoSizeColumns]: {skipHeader: false,}
      });
    }
    if (isFirstChange) {
      Object.assign(this.tableOptions.extraOptions, {
        [XCoreAgGridConstants.selectRowByKey]: new BehaviorSubject<any>(false)
      });
    }
    setTimeout(() => {
      if (!isFirstChange) {
        if (this.inventoryTable.agGridHelpers.gridApi) {
          this.inventoryTable.agGridHelpers.updateColumnDefsAfterRendered(this.tableOptions, this.inventoryTable, null, true);
        }
      }
    })
  }

  public onRowSelection(event): void {
    this.onRowSelectionChange.emit(event);
  }

}
