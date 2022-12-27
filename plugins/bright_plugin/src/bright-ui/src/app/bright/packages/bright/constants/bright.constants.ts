/**
 @copyright:
 Copyright (C) Nvidia Technologies Ltd. 2014-2022. ALL RIGHTS RESERVED.

 This software product is a proprietary product of Mellanox Technologies
 Ltd. (the "Company") and all right, title, and interest in and to the
 software product, including all associated intellectual property rights,
 are and shall remain exclusively with the Company.

 This software product is governed by the End User License Agreement
 provided with the software product.

 @author: Nasr Ajaj
 @date:    11th,May,22
 **/

import {Injectable} from '@angular/core';
import {Constants} from "../../../../constants/constants";


@Injectable({
  providedIn: 'root'
})
export class BrightConstants {

    constructor(private globalConstants:Constants){}

    public readonly brightAPIsUrls ={
        jobs: this.globalConstants.baseBrightPluginApiURL.concat("/jobs"),
        nodes: this.globalConstants.baseBrightPluginApiURL.concat("/nodes")
    };

}
