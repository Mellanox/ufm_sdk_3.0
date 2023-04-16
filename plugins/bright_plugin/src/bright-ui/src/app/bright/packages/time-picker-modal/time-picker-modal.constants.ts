export class TimePickerModalConstants {
    public static TIME_RANGES = [
        {label: 'Last 5 Minutes', value: 'Last 5 Minutes', serverKey: '5'},
        {label: 'Last 1 hour', value: 'Last 1 hour', serverKey: '60'},
        {label: 'Last 12 hours', value: 'Last 12 hours', serverKey: '720'},
        {label: 'Last 24 hours', value: 'Last 24 hours', serverKey: '1440'},
        {label: 'Last week', value: 'Last week', serverKey: '10080'},
        {label: 'Last month', value: 'Last month', serverKey: '43200'},
        {label: 'Last 6 months', value: 'Last 6 months', serverKey: '259200'},
        {label: 'Last 1 year', value: 'Last 1 year', serverKey: '525600'}
    ];
    public static HOURS_LIST = [
        '00:00', '01:00', '02:00', '03:00',
        '04:00', '05:00', '06:00', '07:00',
        '08:00', '09:00', '10:00', '11:00',
        '12:00', '13:00', '14:00', '15:00',
        '16:00', '17:00', '18:00', '19:00',
        '20:00', '21:00', '22:00', '23:00'
    ];

    public static TIME_RANGES_MAPPER = {
        'Last 5 Minutes': '-5min',
        'Last 1 hour': '-1h',
        'Last 12 hours': '-12h',
        'Last 24 hours': '-24h',
        'Last week': '-168h', //24*7
        'Last 2 weeks':'-336h',
        'Last month': '-720h', //24*30
        'Last 6 months': '-4392h', //183*24
        'Last 1 year': '-8760h', //365*24
    }
}