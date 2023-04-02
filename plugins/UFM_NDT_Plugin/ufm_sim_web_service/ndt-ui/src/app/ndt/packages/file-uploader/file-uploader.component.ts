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

import {Component, ViewChild, Output, EventEmitter, Input} from '@angular/core';
import {FileUploader, FileItem} from 'ng2-file-upload';
import {IFileUploaderOptions} from "./interfaces/file-uploader-options.interface";
import {SmsToastrService} from "../../../../../sms-ui-suite/sms-toastr/sms-toastr.service";

@Component({
  selector: 'app-file-uploader',
  templateUrl: './file-uploader.component.html',
  styleUrls: ['./file-uploader.component.css']
})

export class FileUploaderComponent {

  @Input() options: IFileUploaderOptions; // configurations
  @Output() onFileUploaded: EventEmitter<any> = new EventEmitter(true);

  @ViewChild('fileUploaderModalTemplate', {static: false}) fileUploaderModalTemplate;

  public uploader: FileUploader;
  public selectedFile: FileItem;

  constructor(private tService: SmsToastrService) {

  }

  ngOnInit() {

  }

  ngOnChanges() {
    if (this.options) {
      let uploaderConfigurations = {};
      uploaderConfigurations["url"] = this.options.url;
      this.uploader = new FileUploader(uploaderConfigurations);
    }
    let self = this;
    this.uploader.onAfterAddingFile = (fileItem: FileItem) => {
      self.selectedFile = fileItem;
      self.uploadFile();
    };
    this.uploader.onErrorItem = (item: FileItem, response: string, status: number) => {
      let title = 'Uploading Error';
      let text = response.length == 0 ? 'Unable to connect to server. Please check your network connection' : response;
      switch (status) {
        case 0:
          title = 'Connection Error';
          text = 'Unable to connect to server. Please check your network connection';
          break;
        case 400:
          title = 'Bad Request';
          break;
        case 401:
          title = 'Authorization Error';
          text = `You are not authorized to access the resource: ${this.options.url}`;
          break;
        case 403:
          title = 'Forbidden Error';
          text = `You don’t have permission to access the resource: ${this.options.url}`;
          break;
        case 404:
          title = 'API Resource Not Found';
          text = `The following API resource not found: ${this.options.url}`;
          break;
        case 500:
          title = 'Internal Server Error';
          break;
        case status.toString().includes('50') ? status : false:
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
    };
    this.uploader.onSuccessItem = (item: FileItem, response: string, status: number) => {
      let parsedResponse;
      try {
        parsedResponse = JSON.parse(response)
      } catch (exception) {
        parsedResponse = undefined;
      }
      this.onFileUploaded.emit(parsedResponse);
    };
  }

  uploadFile() {
    this.uploader.uploadItem(this.selectedFile);
  }
}
