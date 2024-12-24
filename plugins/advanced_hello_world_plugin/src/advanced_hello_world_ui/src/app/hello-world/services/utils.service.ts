import {Injectable}    from '@angular/core';


@Injectable({
  providedIn: 'root'
})
export class UtilsService {

  constructor() {
  }

  /**
   * This function takes list of dictionaries and returns a map of [column name -> number of distinct values]
   * @param data : list of dictionaries
   */
  public static prepareValuesOccurrencesMap(data){
    let occurrencesMap;
    let valuesMap: {[p: string]: Set<any> | any} = {};
    if (data.length) {
      data.forEach(dataRow => {
        Object.keys(dataRow).forEach((key) => {
          if(typeof dataRow[key] == 'object' && dataRow[key]){
            if (!valuesMap[key]) {
              valuesMap[key] = {};
            }
            Object.keys(dataRow[key]).forEach(subKey => {
              if (!valuesMap[key][subKey]) {
                valuesMap[key][subKey] = new Set();
              }
              valuesMap[key][subKey].add(dataRow[key][subKey])
            })
          } else {
            if (!valuesMap[key]){
              valuesMap[key] = new Set();
            }
            valuesMap[key].add(dataRow[key]);
          }
        });
      })
      occurrencesMap = {}
      Object.keys(valuesMap).forEach(key => {
        if(typeof data[0][key] == 'object'){
          occurrencesMap[key] = {};
          Object.keys(valuesMap[key]).forEach(subKey => {
            occurrencesMap[key][subKey] = valuesMap[key][subKey].size
          })
        } else {
          occurrencesMap[key] = valuesMap[key].size
        }
      })
    }
    return occurrencesMap;
  }

  /**
   * For performance reasons, some tables APIs return data as list of lists;
   * the first list presents the column names, the other items present data.
   * This function takes list of lists and returns them as list of dictionaries.
   * @param data : list of lists
   */
  public static parseListOfListData(data) {
    let headers = data[0];
    let rows = data.slice(1);
    rows = rows.map(row => {
      let dict = {}
      row.forEach((value, index) => {
        dict[headers[index]] = value;
      })
      return dict;
    })
    return rows;
  }

  public static downloadFile(url: string): void {
    let link = document.createElement("a");
    link.download = window.name;
    link.href = url;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }


}
