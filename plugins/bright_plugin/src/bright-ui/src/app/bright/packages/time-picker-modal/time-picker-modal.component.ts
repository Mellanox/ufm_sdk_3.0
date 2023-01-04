/**
 * @COMPONENTS
 */
import {Component, EventEmitter, Input, OnChanges, OnInit, Output} from '@angular/core';
import {TimePickerEvent} from "./timer-picker-event";
import * as moment from 'moment';

/**
 * @ENUMS
 */
import {TimePickerType} from "./time-picker-type.enum";

/**
 * @PROVIDERS
 */
import {TimePickerModalConstants} from "./time-picker-modal.constants";



@Component({
    selector: 'time-picker-modal',
    templateUrl: './time-picker-modal.component.html',
    styleUrls: ['./time-picker-modal.component.scss']
})

export class TimePickerModalComponent implements OnInit, OnChanges {

    /**
     *@INPUTS
     */
    @Input() selectedTime = this.timeRanges[1].label;
    @Input() selectedTimeLabelFormatter:Function;
    @Input() rightAlign;

    /**
     *
     * @OUTPUTS
     */
    @Output() timeSelectionUpdated:EventEmitter<TimePickerEvent> = new EventEmitter();


    /**
     *@VARIABLES
     */

    public bsConfig = {
        dateInputFormat: 'DD/MM/YY',
        displayMonths: 1,
        containerClass: 'user-preferences-dark-blue theme-dark-blue',
        maxDate: new Date()
    };


    public timeSelectionType:TimePickerType;
    public selectedTimeLabel:string;
    public selectedTimeRange:string;
    public selectedCustomTimeRange:Array<any>;
    public selectedHour = this.hoursList[0];
    public fromTime:string;
    public toTime:string;
    public timeRangeMap:{};
    constructor() {
    }

    ngOnInit():void {
        this.initTimeRangeMap();
        this.initTimeModalData();
    }

    ngOnChanges(changes):void {
        if (changes.selectedTime && changes.selectedTime.currentValue && !changes.selectedTime.firstChange) {
            this.initTimeModalData();
        }

    }

    ngOnDestroy(){

    }

    /**
     * @desc this function to initialize the time modal data/variables
     * @returns void
     */

    private initTimeModalData():void {

        //Default Value for Date Range Picker
        let hour = window['parseInt'](this.selectedHour.split(':')[0]);
        let today = new Date();
        today.setHours(hour, 0, 0, 0);
        let yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        this.selectedCustomTimeRange = [yesterday, today];


        if (this.selectedTime.indexOf('Last') > -1) {
            this.timeSelectionType = TimePickerType.TIME_RANGE;
            this.selectedTimeRange = this.selectedTime;
        } else {
            this.timeSelectionType = TimePickerType.CUSTOM_DATE_RANGE;
            this.selectedCustomTimeRange = [
                new Date(this.selectedTime[0]),
                new Date(this.selectedTime[1])
            ];
            this.selectedHour = ('0' + this.selectedCustomTimeRange[0].getHours()).slice(-2) + ':00';
        }

        this.updateTimeSelection();
    }

    changeDateInterval(dp) {
        setTimeout(() => {
            dp.show();
            this.updateInnerTimeLabel();
        });
    }

    /**
     * @desc this function will update the inner time label of the custom date range
     * @returns void
     */

    private updateInnerTimeLabel() {
        function formatDate(date) {
            return moment(date).format('DD/MM/YY    HH:mm');
        }

        if (this.selectedCustomTimeRange) {
            this.fromTime = formatDate(this.selectedCustomTimeRange[0]);
            this.toTime = formatDate(this.selectedCustomTimeRange[1]);
        }
    }

    /**
     * @returns instance of the TIME_RANGES options {{label: string, value: string}[]}
     */

    public get timeRanges() {
        return TimePickerModalConstants.TIME_RANGES;
    }

    /**
     * @returns instance of the HOURS_LIST options {string[]}
     */

    public get hoursList() {
        return TimePickerModalConstants.HOURS_LIST;
    }


    /**
     * @desc this function will be called when the selected hour is changed and do the necessary changes accordingly
     * @returns void
     */

    public updateSelectedHour(hour):void {
        this.selectedHour = hour;
        let intHour = parseInt(hour.split(':')[0]);
        this.selectedCustomTimeRange[0] = new Date(this.selectedCustomTimeRange[0].setHours(intHour));
        this.selectedCustomTimeRange[1] = new Date(this.selectedCustomTimeRange[1].setHours(intHour));
        this.updateInnerTimeLabel();
    }

    /**
     * @desc this function will be called when the selected time/date is changed and will emit the changes
     * @returns void
     */

    public updateTimeSelection():void {
        let timePickerEvent:TimePickerEvent=this.prepareTimePickerEventValue();
        this.timeSelectionUpdated.emit(timePickerEvent);
    }

    public prepareTimePickerEventValue():TimePickerEvent{
        let timePickerEvent:TimePickerEvent = new TimePickerEvent(this.timeSelectionType);
        switch (this.timeSelectionType) {
            case TimePickerType.TIME_RANGE:
                timePickerEvent.timeRangeValue = this.selectedTimeRange;
                timePickerEvent.timeRangeServerKey = this.timeRangeMap[timePickerEvent.timeRangeValue].serverKey;
                this.selectedTimeLabel = timePickerEvent.timeRangeValue;
                break;
            case TimePickerType.CUSTOM_DATE_RANGE:
                timePickerEvent.customDateTimeRangeValue = this.selectedCustomTimeRange;
                this.selectedTimeLabel = this.selectedTimeLabelFormatter ? this.selectedTimeLabelFormatter(timePickerEvent) : "Custom";
                break;
        }
        return timePickerEvent
    }

    /**
     * @desc this function create a map from TIME_RANGES constant list and use label as unique key
     * @return void
     */

    private initTimeRangeMap():void {
        this.timeRangeMap = {};
        TimePickerModalConstants.TIME_RANGES.forEach((item)=> {
            this.timeRangeMap[item.label] = item;
        });
    }


}
