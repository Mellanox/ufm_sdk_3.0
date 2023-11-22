import {Component, Input, OnInit} from '@angular/core';
import {IHistogramData} from "../interfaces/histogram-data.interface";

@Component({
  selector: 'app-generic-histogram',
  templateUrl: './generic-histogram.component.html',
  styleUrls: ['./generic-histogram.component.scss']
})
export class GenericHistogramComponent implements OnInit {

  /**
   * @Input
   */
  @Input() histogramData: IHistogramData;
  @Input() rawData;
  /**
   * @VARIABLES
   */
  public chartOptions;
  public isReady: boolean;
  public binsCount = 10;
  public filteredColumns;
  public ALL_COLUMN_FILTER = 'All';

  constructor() {
  }

  ngOnInit(): void {
    if (this.histogramData.filterable_columns?.length) {
      this.filteredColumns = [this.filterableColumns[0]];
    }
    if(this.histogramData.bins_count) {
      this.binsCount = this.histogramData.bins_count;
    }
    this.initChartOptions();
  }

  private initChartOptions(): void {
    let series = this.histogramData.filterable_columns?.length &&  !this.isAllFilterableColumnsSelected()? this.filteredColumns.map(column => {
      return {
        type: 'histogram',
        xKey: column.name,
        xName: this.histogramData.xlable,
        highlightStyle: {item: {fill: '#76B900FF'}},
        strokeWidth: 0,
        binCount: this.binsCount,
      }
    }):
      [
        {
          type: 'histogram',
          xKey: 'value',
          xName: this.histogramData.xlable,
          fill: '#76B900FF',
          highlightStyle: {item: {fill: '#76B900FF'}},
          strokeWidth: 0,
          binCount: this.binsCount,
        }
      ]
    this.chartOptions = {
      data: this.getChartData(),
      theme: {
        palette: {
          fills: ['rgba(253, 127, 111, 0.5)', 'rgba(126, 176, 213, 0.5)', 'rgba(196, 130, 25, 0.5)', 'rgba(77, 114, 10, 0.5)',
                  'rgba(28, 239, 245, 0.5)', 'rgba(255, 238, 101, 0.5)', 'rgba(90, 77, 176, 0.5)', 'rgba(108, 54, 80, 0.5)',
                  'rgba(139, 211, 199, 0.5)', 'rgba(2, 255, 155, 0.5)', 'rgba(35, 98, 143, 0.5)', 'rgba(148, 12, 144, 0.5)',
                  'rgba(255, 127, 0, 0.5)', 'rgba(143, 35, 35, 0.5)', 'rgba(157, 204, 0, 0.5)', 'rgba(0, 51, 128, 0.5)'],
          strokes: []
        },
      },
      series: series,
      legend: {
        enabled: !!(this.histogramData.filterable_columns?.length && !this.isAllFilterableColumnsSelected()),
        position: 'top'
      },
      axes: [
        {
          type: 'number',
          position: 'bottom',
          title: { text: this.histogramData.xlable },
          gridStyle: {
            visible: false
          }
        },
        {
          type: 'number',
          position: 'left',
          title: { text: this.histogramData.ylable },
        },
      ]
    };
  }

  private getChartData() {
    if (!this.histogramData.filterable_columns || this.isAllFilterableColumnsSelected()) {
      return this.histogramData.data.map(value => {return {value: value}});
    } else {
      return this.rawData
    }
  }

  public numberOnly(event): boolean {
    const charCode = (event.which) ? event.which : event.keyCode;
    if (charCode > 31 && (charCode < 48 || charCode > 57)) {
      return false;
    }
    return true;
  }

  public binsCountChanged(event) {
    this.initChartOptions();
  }

  private isAllFilterableColumnsSelected() {
    return this.filteredColumns.map(item => item.name).includes(this.ALL_COLUMN_FILTER);
  }

  public get filterableColumns() {
    return [{name: this.ALL_COLUMN_FILTER}].concat(this.histogramData.filterable_columns.map(column => {
      return {name: column};
    }));
  }

  public onFilteredColumnChanged(event) {
    let newFilteredColumns;
    if(event.length == 0 || (!this.isAllFilterableColumnsSelected() && event.map(item => item.name).includes(this.ALL_COLUMN_FILTER))) {
      newFilteredColumns = [{name: this.ALL_COLUMN_FILTER}]
    } else if (event.length > 1 && this.isAllFilterableColumnsSelected()){
      newFilteredColumns = event.filter(column => column.name != this.ALL_COLUMN_FILTER);
    } else {
      newFilteredColumns = event;
    }
    if (JSON.stringify(this.filteredColumns) !== JSON.stringify(newFilteredColumns)) {
      this.filteredColumns = newFilteredColumns;
    }
    this.initChartOptions()
  }

}
