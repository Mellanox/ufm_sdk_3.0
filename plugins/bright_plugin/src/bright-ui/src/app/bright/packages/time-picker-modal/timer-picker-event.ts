export class TimePickerEvent {
    private _timeSelectionType:number;
    private _timeRangeValue:string;
    private _customDateTimeRangeValue:Array<any>;
    private _timeRangeServerKey:string;

    constructor(timeSelectionType:number,
                timeRangeValue?:string,
                customDateTimeRangeValue?:Array<any>,
                timeRangeServerKey?:string) {
        this._timeSelectionType = timeSelectionType;
        this._timeRangeValue = timeRangeValue;
        this._customDateTimeRangeValue = customDateTimeRangeValue;
        this._timeRangeServerKey = timeRangeServerKey;
    }

    get timeSelectionType():number {
        return this._timeSelectionType;
    }

    set timeSelectionType(value:number) {
        this._timeSelectionType = value;
    }

    get timeRangeValue():string {
        return this._timeRangeValue;
    }

    set timeRangeValue(value:string) {
        this._timeRangeValue = value;
    }

    get customDateTimeRangeValue():Array<any> {
        return this._customDateTimeRangeValue;
    }

    set customDateTimeRangeValue(value:Array<any>) {
        this._customDateTimeRangeValue = value;
    }

    set timeRangeServerKey(value:string) {
        this._timeRangeServerKey = value;
    }
    get timeRangeServerKey():string {
        return this._timeRangeServerKey;
    }
}