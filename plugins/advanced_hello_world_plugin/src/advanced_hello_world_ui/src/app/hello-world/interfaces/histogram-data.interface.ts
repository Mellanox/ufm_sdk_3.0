
export interface IHistogramData {
  bar_color_range: {
    [p: string]: [number, number]
  }
  bins_count: number,
  data: number[],
  graph_title: string,
  xlable: string,
  ylable: string,
  filterable_columns: string[]
}
