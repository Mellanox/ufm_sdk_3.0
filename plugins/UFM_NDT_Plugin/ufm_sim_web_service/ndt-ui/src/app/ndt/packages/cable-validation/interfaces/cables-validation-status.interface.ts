import {CV_MODE_ENUM} from "../../../views/settings-view/enums/cv_mode.enum";

export interface ICablesValidationSettings {
  mode: CV_MODE_ENUM,
  is_enabled: boolean,
  address: string,
  port?: string,
  username?: string,
  password?: string
}
