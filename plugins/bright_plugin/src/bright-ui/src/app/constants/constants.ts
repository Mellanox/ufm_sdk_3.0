import {Injectable} from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class Constants {

  public readonly baseApiUrl = "/ufmRestV2";
  public readonly baseResourcesApiUrl = this.baseApiUrl.concat("/resources");
  public readonly basePluginApiURL = this.baseApiUrl.concat("/plugin");
  public readonly baseBrightPluginApiURL = this.basePluginApiURL.concat("/bright");

}
