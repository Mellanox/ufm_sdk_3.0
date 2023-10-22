import {Component, OnInit, TemplateRef} from '@angular/core';
import {BsModalRef, BsModalService} from "ngx-bootstrap/modal";
import {
  CableValidationBackendService
} from "../../../../packages/cable-validation/services/cable-validation-backend.service";

@Component({
  selector: 'app-cables-validation-report-modal',
  templateUrl: './cables-validation-report-modal.component.html',
  styleUrls: ['./cables-validation-report-modal.component.scss']
})
export class CablesValidationReportModalComponent implements OnInit {

  public modalRef?: BsModalRef;
  public isCableValidationReportAvailable: boolean = false;

  constructor(private modalService: BsModalService,
              private cvBackendService: CableValidationBackendService) {
  }


  ngOnInit(): void {
    this.checkCableValidationAvailability();
  }

  public openModal(template: TemplateRef<any>) {
    this.modalRef = this.modalService.show(
      template,
      Object.assign({}, {class: 'modal-lg'})
    );
  }

  public checkCableValidationAvailability() {
    this.cvBackendService.checkIfCableValidationAvailable().subscribe({
      next: (data) => {
        this.isCableValidationReportAvailable = true;
      },
      error: () => {
        this.isCableValidationReportAvailable = false;
      }
    })
  }

}
