import {Component, OnInit, ViewChild} from '@angular/core';
import {XCoreAgGridComponent} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid.component";
import {
  ICablesValidationReportResult,
  ICableValidationReportIssue
} from "../../interfaces/cables-validations-reports.interface";
import {
  XCoreAgGridOptions
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/x-core-ag-grid-options/x-core-ag-grid-options";
import {CableValidationConstants} from "../../constants/cable-validation.constants";
import {
  XCoreAgGridConstants
} from "../../../../../../../sms-ui-suite/x-core-ag-grid/constants/x-core-ag-grid.constants";
import {CableValidationBackendService} from "../../services/cable-validation-backend.service";

@Component({
  selector: 'app-cable-validation-table',
  templateUrl: './cable-validation-table.component.html',
  styleUrls: ['./cable-validation-table.component.scss']
})
export class CableValidationTableComponent implements OnInit {

  @ViewChild('nodeDescTemplate', {static: true}) private nodeDescTemplate;
  @ViewChild('issueTemplate', {static: true}) private issueTemplate;
  @ViewChild('rightControlButtonsTmp', {static: true}) public rightControlButtonsTmp;
  @ViewChild(XCoreAgGridComponent)
  private issuesTable;

  public report: ICablesValidationReportResult;
  public tableOptions: XCoreAgGridOptions = new XCoreAgGridOptions()
  public issuesColor = CableValidationConstants.reportAPIKeys.issue_color_based_on_type;

  public nodeIssues = {};
  public isLoading = false;


  constructor(private cvBackend: CableValidationBackendService) {
  }

  ngOnInit(): void {
    this._setTableOptions();
    this.loadData();
  }

  public loadData(): void {
    this.isLoading = true;
    this.nodeIssues = {};
    this.cvBackend.getCableValidation().subscribe({
      next: (data: ICablesValidationReportResult) => {
        if (data && data.issues.length) {
          this._parsingReportIssues(data);
          setTimeout(() => {
            this.expandAllRows();
          }, 50)
        } else {
          this.report = data;
          this.isLoading = false;
        }
      },
      error: (error) => {
        this.report = undefined;
        this.isLoading = false;
      }
    });
  }

  private _setTableOptions(): void {
    Object.assign(
      this.tableOptions.gridOptions,
      {
        [XCoreAgGridConstants.paginationPageSize]: 100,
        [XCoreAgGridConstants.columnDefs]: [
          {
            [XCoreAgGridConstants.field]: CableValidationConstants.reportAPIKeys.node_desc,
            [XCoreAgGridConstants.headerName]: 'Node Description',
            [XCoreAgGridConstants.cellRendererParams]: {
              [XCoreAgGridConstants.ngTemplate]: this.nodeDescTemplate
            },
            [XCoreAgGridConstants.sortable]: false,
            [XCoreAgGridConstants.filterParams]: {
              valueGetter: (params) => {
                return params.data[CableValidationConstants.reportAPIKeys.parent_node_desc] || params.data[CableValidationConstants.reportAPIKeys.node_desc];
              }
            }
          },
          {
            [XCoreAgGridConstants.field]: CableValidationConstants.reportAPIKeys.rack,
            [XCoreAgGridConstants.headerName]: 'Rack'
          },
          {
            [XCoreAgGridConstants.field]: CableValidationConstants.reportAPIKeys.unit,
            [XCoreAgGridConstants.headerName]: 'Unit'
          },
          {
            [XCoreAgGridConstants.field]: 'issue',
            [XCoreAgGridConstants.headerName]: 'Issue',
            [XCoreAgGridConstants.filter]: false,
            [XCoreAgGridConstants.cellRendererParams]: {
              [XCoreAgGridConstants.ngTemplate]: this.issueTemplate
            }
          },
          {
            [XCoreAgGridConstants.field]: 'source',
            [XCoreAgGridConstants.headerName]: 'Source Switch Port',
            [XCoreAgGridConstants.filter]: false
          },
          {
            [XCoreAgGridConstants.field]: 'expected_neighbor',
            [XCoreAgGridConstants.headerName]: 'Expected Neighbor',
            [XCoreAgGridConstants.filter]: false
          },
          {
            [XCoreAgGridConstants.field]: 'discovered_neighbor',
            [XCoreAgGridConstants.headerName]: 'Discovered Neighbor',
            [XCoreAgGridConstants.filter]: false
          }
        ]
      }
    )

    Object.assign(
      this.tableOptions.extraOptions,
      {
        [XCoreAgGridConstants.suppressColumnsFiltering]: true,
        [XCoreAgGridConstants.customSuppressRowClickSelection]: true,
        [XCoreAgGridConstants.showResetFiltersMessage]: false,
        [XCoreAgGridConstants.rightAdditionalControlsTemplate]: this.rightControlButtonsTmp
      }
    )
  }

  private _parsingReportIssues(data: ICablesValidationReportResult): void {
    data?.issues?.map((issue) => {
      issue.isCollapsed = true
      return issue;
    })
    this.report = data;
    this.isLoading = false;
  }

  private _parsingNodeIssues(row: ICableValidationReportIssue) {
    const result = row.issues.map((item, index) => {
      let _rowObj = {}
      item.forEach((issue, _index) => {
        _rowObj[CableValidationConstants.reportAPIKeys.node_issues_columns_order[_index]] = issue;
      });
      _rowObj[CableValidationConstants.reportAPIKeys.parent_node_desc] = row.node_desc
      return _rowObj;
    })
    this.nodeIssues[row.node_desc] = result;
    return result;
  }

  public expandCollapseRow(node): void {
    const row = node.data;
    row['isCollapsed'] = !row['isCollapsed'];
    const rowsList = this.nodeIssues[row.node_desc] || this._parsingNodeIssues(row);
    if (!row['isCollapsed']) {
      this.issuesTable.agGridHelpers.gridApi.applyTransaction({
        add: rowsList,
        addIndex: node.rowIndex + 1
      })
    } else {
      this.issuesTable.agGridHelpers.gridApi.applyTransaction({
        remove: rowsList
      });
    }
  }

  public expandAllRows(): void {
    const count = this.issuesTable.agGridHelpers.gridApi.getDisplayedRowCount();
    const rowNodes = [];
    for (let i = 0; i < count; i++) {
      const rowNode = this.issuesTable.agGridHelpers.gridApi.getDisplayedRowAtIndex(i);
      rowNodes.push(rowNode);
    }
    rowNodes.forEach((node) => {
      this.expandCollapseRow(node);
    });
  }

}
