import {Injectable} from '@angular/core';

@Injectable()
export class Constants {

  public readonly baseApiUrl = "/ufmRestV2";
  public readonly baseAppApiURL = this.baseApiUrl.concat("/app");
  public readonly baseResourcesApiURL = this.baseApiUrl.concat("/resources");

}
