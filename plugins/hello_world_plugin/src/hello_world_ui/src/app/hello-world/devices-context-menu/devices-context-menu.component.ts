import {Component, OnInit, ViewChild, TemplateRef} from '@angular/core';
import {BsModalRef, BsModalService} from "ngx-bootstrap/modal";

@Component({
  selector: 'app-devices-context-menu',
  templateUrl: './devices-context-menu.component.html',
  styleUrls: ['./devices-context-menu.component.scss']
})
export class DevicesContextMenuComponent implements OnInit {

  @ViewChild('template', {static: true}) modalTemplate: TemplateRef<any>;
  public devices: Array<any> = [];

  modalRef?: BsModalRef;

  constructor(private modalService: BsModalService) {
  }

  ngOnInit(): void {
  }

  openModal() {
    this.modalRef = this.modalService.show(this.modalTemplate);
  }

}
