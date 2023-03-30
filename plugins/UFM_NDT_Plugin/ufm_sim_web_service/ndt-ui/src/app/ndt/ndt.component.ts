import {Component, OnInit} from '@angular/core';
import {NdtViewService} from "./services/ndt-view.service";

@Component({
  selector: 'app-ndt',
  templateUrl: './ndt.component.html',
  styleUrls: ['./ndt.component.scss']
})
export class NdtComponent implements OnInit {

  /**
   * @VARIABLES
   */
  public sidebarItems = [];
  public selectedSideBarItem;

  constructor(private ndtViewService: NdtViewService) {
  }

  ngOnInit(): void {
    this.sidebarItems = this.ndtViewService.getSideBarMenuItems();
  }

  public get NdtViewService(){
    return NdtViewService;
  }

  public onSelectedItemChanged($event) {
    this.selectedSideBarItem = $event;
  }

}
