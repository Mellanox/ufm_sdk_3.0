import {Injectable} from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class Constants {

  public static baseApiUrl = "/ufmRestV2";
  public static baseResourcesApiUrl = `${Constants.baseApiUrl}/resources`;
  public static basePluginApiURL = `${Constants.baseApiUrl}/plugin`;
  public static baseBrightPluginApiURL = `${Constants.basePluginApiURL}/bright`;

  public static setBaseAPIsConstants(): void {
    const ufmRestPrefix = window['ufm_rest_base'];
    if (ufmRestPrefix) {
      Constants.baseApiUrl = ufmRestPrefix
      Constants.baseResourcesApiUrl = `${Constants.baseApiUrl}/resources`;
      Constants.basePluginApiURL = `${Constants.baseApiUrl}/plugin`;
      Constants.baseBrightPluginApiURL = `${Constants.basePluginApiURL}/bright`;
    }
  }

}
