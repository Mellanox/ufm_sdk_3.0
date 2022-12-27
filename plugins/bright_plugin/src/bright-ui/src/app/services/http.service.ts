/*
import {Injectable, EventEmitter}    from '@angular/core';
import {catchError, Observable, of, tap} from 'rxjs';



import {HttpHeaders} from '@angular/common/http';
import * as jstz from 'jstz';
import {HttpClient, HttpRequest, HttpResponse} from '@angular/common/http';
import {SmsToastrService} from '../../../../../sms-ui-suite/sms-toastr/sms-toastr.service';
import {Constants} from "../constants/constants";


@Injectable()
export class HttpService {
    sessionExpired: EventEmitter<boolean> = new EventEmitter();
    username;
    password;

    timeZone = {
        local: jstz.determine().name()
    };

    httpErrorCount = 0;
    lastDebouncedErrorTime: Date;

    constructor(private http: HttpClient,
                private constants:Constants,
                private tService: SmsToastrService) {

    }

    addCredentials() {
        this.username = localStorage.getItem('username');
        this.password = localStorage.getItem('password');
        let headers: Headers = new Headers();
        headers.append("Authorization", "Basic " + btoa(this.username + ":" + this.password));
        headers.append('X-Requested-With', 'XMLHttpRequest');
        headers.append("Content-Type", "application/json");
        headers.append('Cache-Control', 'no-cache');
        headers.append('Pragma', 'no-cache');
        headers.append('Expires', 'Sat, 01 Jan 2000 00:00:00 GMT');
        return headers;

    }

    /!**
     * Performs a request with `request` http method.
     *!/

    request(url: string | HttpRequest<any>, options?: any): Observable<any> {
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.request(url, options));
    }

    /!**
     * Performs a request with `get` http method.
     *!/
    get(url: string, ignoreAlert?, options?: RequestOptionsArgs, debounceErrors?: boolean): Observable<any> {
        url = encodeURI(url);
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.get(url, options),ignoreAlert, debounceErrors);

    }

    /!**
     * Performs a request with `post` http method.
     *!/
    post(url: string, body: any, options?: RequestOptionsArgs, debounceErrors?: boolean): Promise<any> {
        url = encodeURI(url);
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.post(url, body, options), undefined, debounceErrors);
    }

    /!**
     * Performs a request with `put` http method.
     *!/
    put(url: string, body: any, options?: RequestOptionsArgs): Promise<any> {
        url = encodeURI(url);
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.put(url, body, options));

    }

    /!**
     * Performs a request with `delete` http method.
     *!/
    delete(url: string, ignoreAlert?, options?: RequestOptionsArgs): Promise<any> {
        url = encodeURI(url);
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.delete(url, options),ignoreAlert);
    }

    /!**
     * Performs a request with `patch` http method.
     *!/
    patch(url: string, body: any, options?: RequestOptionsArgs): Promise<any> {
        url = encodeURI(url);
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.patch(url, body, options));
    }

    /!**
     * Performs a request with `head` http method.
     *!/
    head(url: string, options?: RequestOptionsArgs): Promise<any> {
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.head(url, options));
    }

    /!**
     * Performs a request with `options` http method.
     *!/
    options(url: string, options?: RequestOptionsArgs): Promise<any> {
        if (!options) {
            options = {};
        }
        return this.intercept(this.http.options(url, options));
    }

  intercept(observable: Observable<Response>, ignoreError?: boolean, debounceErrors?: boolean): Observable<any> {
    return observable.pipe(
      tap(response =>{
        if (-1 != response.text().indexOf('Mellanox Technologies Ltd') || -1 != response.text().indexOf("UFM is running in limited mode")) {
          this.sessionExpired.emit(true);
          return of('');
        }
      }),
      catchError(err => {
        if (-1 != err.text().indexOf("UFM is running in limited mode")) {
          this.sessionExpired.emit(true);
        }
        if (ignoreError == false || ignoreError == undefined) {
          if (debounceErrors) {
            const now = new Date();
            if (this.lastDebouncedErrorTime && (this.lastDebouncedErrorTime.getTime() - now.getTime()) / 60000 > 5) {
              this.httpErrorCount = 0;
            }
            this.lastDebouncedErrorTime = new Date();
            if (++this.httpErrorCount == 10) {
              this.handleNetworkError(err);
              this.httpErrorCount = 0;
            }
          } else {
            this.handleNetworkError(err);
          }
        }
        return of(err);
      })
    );
  }


    private handleNetworkError(error: any) {
        let title = error.statusText, text = error.text();
        const url = (error.url  && error.url.split(this.constants.baseApiUrl + '/')[1]) || '';
        // here we may override server messages
        switch (error.status) {
            case 0:
                title = 'Connection Error';
                text = 'Unable to connect to server. Please check your network connection';
                break;
            case 400:
                title = 'Bad Request';
                break;
            case 401:
                title = 'Authorization Error';
                text = `You are not authorized to access the resource: ${url}`;
                break;
            case 403:
                title = 'Forbidden Error';
                text = `You don’t have permission to access the resource: ${url}`;
                break;
            case 500:
                title = 'Internal Server Error';
                break;
            case error.status.toString().includes('50') ? error.status : false:
                title = 'Server Error';
                text = 'The server is temporarily unable to service your request. Please try again later';
                break;
        }

        const toastrAlert = {
            title: title,
            text: text.trim(),
            type: 'toast-error'
        };
        this.tService.showToastr(toastrAlert);
    }


    pendTimeZoneToURL(url): string{
        if(url.indexOf('?') == -1){
            url = url + "?" + this.getUrlTimezoneAddition();
        }else{
            url = url + "&" + this.getUrlTimezoneAddition();
        }
        url = url + '&_=' + (new Date()).getTime();
        return url;
    }

    getUrlTimezoneAddition() {
        return "tz=".concat(this.timeZone.local);
    }
}
*/
