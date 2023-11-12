/**
 * @COMPONENTS
 */
import {ValidatorFn, AbstractControl} from '@angular/forms';


export const IP_V4_REGEX = "(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])";
export const PORT_REGEX = "([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5])";
export const IP_V6_REGEX = "(([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))"


/**
 * @desc used to check if the value is a valid serverAddress, and the valid serverAddress is ipv4/ipv6 or hostname
 * @param message
 * @returns {function(AbstractControl): ({}|null)}
 */
export function serverAddress(message?:string):ValidatorFn {
    return (control:AbstractControl):{[key:string]:any} | null => {
        let ipv4AddressObj:{[key:string]:any} | null = isValidIpv4Address()(control);
        let ipv6AddressObj:{[key:string]:any} | null = isValidIpv6Address()(control);
        let hostnameObj:{[key:string]:any} | null = hostname()(control);

        if (!ipv4AddressObj || !ipv6AddressObj || !hostnameObj) {
            return null;
        }
        return {
            address: {
                message: message?message:" Please enter a valid hostname or IP address"
            }
        }
    }
}

export function hostname(): ValidatorFn {
  return (control: AbstractControl): {[key: string]: any} | null => {
    // tslint:disable-next-line:max-line-length
    const reg = /^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$/g;
    if (!reg.test(control.value)) {
      return {
        hostname: {
          message: 'Please enter a valid hostname or IP address'
        }
      };
    }

    return null;
  };
}


export function isValidIpv6Address(message?:string):ValidatorFn {
  return (control:AbstractControl):{[key:string]:any} | null => {
    const ipRegEx = new RegExp("^" + IP_V6_REGEX + "$");

    if (!ipRegEx.test(control.value)) {
      return {
        ipv6Address: {
          message: message ? message : "Please enter a valid ipv6 address"
        }
      }
    }

    return null;
  }

}

export function isValidIpv4Address(message?:string):ValidatorFn {
  return (control:AbstractControl):{[key:string]:any} | null => {

    const ipRegEx = new RegExp("^" + IP_V4_REGEX + "$");

    if (!ipRegEx.test(control.value)) {
      return {
        ipv4Address: {
          message: message ? message : "Please enter a valid ipv4 address"
        }
      }
    }

    return null;
  }

}



/**
 * @desc used to check if the value is a valid ipv6 socket address. socket address is [ipv6]:port
 * @param message
 * @returns {function(AbstractControl): ({}|null)}
 */
export function isValidPort(message?:string):ValidatorFn {
  return (control:AbstractControl):{[key:string]:any} | null => {

    const ipRegEx = new RegExp("^" + PORT_REGEX + "$");

    if (!ipRegEx.test(control.value)) {
      return {
        port: {
          message: message ? message : " Please enter a valid port value"
        }
      }
    }

    return null;
  }

}



