import {Injectable} from '@angular/core';
import {FormControl, Validators} from "@angular/forms";
import {CV_MODE_ENUM} from "../enums/cv_mode.enum";
import {isValidPort, serverAddress} from "../validators/address.validators";

@Injectable({
  providedIn: 'root'
})
export class SettingsViewService {

  constructor() {
  }

  public isCVLocal(mode: CV_MODE_ENUM): boolean {
    return mode == CV_MODE_ENUM.LOCAL
  }

  public initModeFormControl(value: CV_MODE_ENUM): FormControl {
    return new FormControl(
      {
        value: value,
        disabled: !value
      },
      [
        Validators.required,
      ]
    );
  }

  public initAddressFormControl(value, mode: CV_MODE_ENUM): FormControl {
    const isLocal = this.isCVLocal(mode);
    return new FormControl(
      {
        value: value,
        disabled: isLocal
      },
      [
        serverAddress(),
        Validators.required,
      ]
    );
  }

  public initPortFormControl(value, mode: CV_MODE_ENUM): FormControl {
    const isLocal = this.isCVLocal(mode);
    return new FormControl(
      {
        value: value,
        disabled: isLocal
      },
      [
        Validators.required,
        isValidPort()
      ]
    );
  }

  public initUsernameFormControl(value, mode: CV_MODE_ENUM): FormControl {
    const isLocal = this.isCVLocal(mode);
    return new FormControl(
      {
        value: value,
        disabled: isLocal
      },
      [Validators.required]
    );
  }

  public initPasswordFormControl(value, mode: CV_MODE_ENUM): FormControl {
    const isLocal = this.isCVLocal(mode);
    return new FormControl(
      {
        value: value,
        disabled: isLocal
      },
      [Validators.required]
    );
  }

}
