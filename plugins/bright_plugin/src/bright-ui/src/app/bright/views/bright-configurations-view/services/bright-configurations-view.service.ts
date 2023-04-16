import {Injectable} from '@angular/core';
import {FormControl, Validators} from "@angular/forms";
import {isValidHost, isValidPort} from "../validators/configurations.validators";

@Injectable({
  providedIn: 'root'
})
export class BrightConfigurationsViewService {

  constructor() {
  }

  public initEnabledFormControl(value): FormControl {
    return new FormControl(
      value,
      [
        Validators.required,
      ]
    );
  }

  public initConnectionStatusFormControl(value): FormControl {
    return new FormControl(
      value,
      [
        Validators.required,
      ]
    );
  }

  public initHostFormControl(value): FormControl {
    return new FormControl(
      {
        value: value,
        disabled: !value
      },
      [
        isValidHost(),
        Validators.required,
      ]
    );
  }

  public initPortFormControl(value): FormControl {
    return new FormControl(
      value,
      [
        Validators.required,
        isValidPort()
      ]
    );
  }

  public initCertFormControl(value): FormControl {
    return new FormControl(
      value,
      [
        Validators.required,
      ]
    );
  }

  public initCertKeyFormControl(value): FormControl {
    return new FormControl(
      value,
      [
        Validators.required,
      ]
    );
  }

  public initDataRetentionPeriodFormControl(value): FormControl {
    return new FormControl(
      value.match(/\d+/g)[0],
      [
        Validators.required,
        Validators.min(1)
      ]
    );
  }
}
