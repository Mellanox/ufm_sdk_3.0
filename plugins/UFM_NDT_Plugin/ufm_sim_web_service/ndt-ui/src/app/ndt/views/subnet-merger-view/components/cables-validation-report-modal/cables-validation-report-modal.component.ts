import {Component, OnInit, TemplateRef} from '@angular/core';
import {BsModalRef, BsModalService} from "ngx-bootstrap/modal";
import {
  CableValidationBackendService
} from "../../../../packages/cable-validation/services/cable-validation-backend.service";
import {
  ICablesValidationSettings
} from "../../../../packages/cable-validation/interfaces/cables-validation-status.interface";
import {PopoverDirective} from "ngx-bootstrap/popover";
import {Subject, Subscription} from "rxjs";
import {ActivatedRoute, Router} from "@angular/router";

@Component({
  selector: 'app-cables-validation-report-modal',
  templateUrl: './cables-validation-report-modal.component.html',
  styleUrls: ['./cables-validation-report-modal.component.scss']
})
export class CablesValidationReportModalComponent implements OnInit {

  public modalRef?: BsModalRef;
  public isCableValidationReportAvailable: boolean = false;

  /**
   * Popover variables
   * */
  public shownPopover: PopoverDirective;
  public leftPopover: PopoverDirective;
  public popoverSubject: Subject<any> = new Subject<any>();
  public popoverTimer: any;

  public popoverSubjectSubscription: Subscription;


  constructor(private modalService: BsModalService,
              private cvBackendService: CableValidationBackendService,
              private activatedRoute: ActivatedRoute,
              private router: Router) {

    this.popoverSubjectSubscription = this.popoverSubject.asObservable()
      .subscribe(data => {
        if (data == 'leave') {
          this.popoverTimer = setTimeout(() => {
            this.leftPopover.hide();
          }, 3000)
        } else if (data == 'enter' && this.leftPopover) {
          if (this.leftPopover == this.shownPopover) {
            clearTimeout(this.popoverTimer);
          } else {
            this.leftPopover.hide();
          }
        }
      });
  }


  ngOnInit(): void {
    this.checkCableValidationAvailability();
  }

  ngOnDestroy(): void {
    this.popoverSubjectSubscription.unsubscribe();
  }

  public openModal(template: TemplateRef<any>) {
    this.modalRef = this.modalService.show(
      template,
      Object.assign({}, {class: 'modal-lg'})
    );
  }

  public checkCableValidationAvailability() {
    this.cvBackendService.getCableValidationConfigurations().subscribe({
      next: (data: ICablesValidationSettings) => {
        this.isCableValidationReportAvailable = data.is_enabled;
      },
      error: () => {
        this.isCableValidationReportAvailable = false;
      }
    })
  }

  /**
   * @desc this function used to handel mouse enter event
   * @param pop
   */
  public enterPopover(pop: PopoverDirective): void {
    this.shownPopover = pop;
    this.popoverSubject.next('enter');
  }

  /**
   * @desc this function used to handel mouse leave event
   * @param pop
   */
  public leavePopover(pop: PopoverDirective): void {
    this.leftPopover = pop;
    this.popoverSubject.next('leave');
  }


  public navigateToSettings(): void {
    this.router.navigate(['../settings'], {relativeTo: this.activatedRoute})
  }

}
