/**
 * @COMPONENTS
 */

export interface ContextMenuItem {
  name: string,
  callbackFunction: Function
}
export class DevicesJobsContextMenu {

    /**
     * @desc abstract function used to build original context menu
     * @param rows:Array<any>
     */
    public buildContextMenu(onJobDetailsClick: Function): [ContextMenuItem] {
      return [{
                "name": "Job Statistics",
                "callbackFunction": onJobDetailsClick
      }];
    }


}
