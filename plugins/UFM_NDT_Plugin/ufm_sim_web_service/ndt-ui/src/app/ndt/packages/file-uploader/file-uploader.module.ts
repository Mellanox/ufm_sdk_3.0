/**
 @copyright:
 Copyright (C) Mellanox Technologies Ltd. 2017-2019. ALL RIGHTS RESERVED.

 This software product is a proprietary product of Mellanox Technologies
 Ltd. (the "Company") and all right, title, and interest in and to the
 software product, including all associated intellectual property rights,
 are and shall remain exclusively with the Company.

 This software product is governed by the End User License Agreement
 provided with the software product.

 @author: Anan Al-Aghbar
 @date:    3rd,Mar,2019
 **/

import {NgModule} from '@angular/core';
import {CommonModule} from '@angular/common';
import {ModalModule} from 'ngx-bootstrap/modal';
import {FileUploadModule} from 'ng2-file-upload';
import {FileUploaderComponent} from './file-uploader.component';

import {ProgressbarModule} from 'ngx-bootstrap/progressbar';


@NgModule({
  imports: [
    CommonModule,
    ModalModule,
    FileUploadModule,
    ProgressbarModule
  ],
  declarations: [FileUploaderComponent],
  exports: [FileUploaderComponent]
})

export class FileUploaderModule {
}
