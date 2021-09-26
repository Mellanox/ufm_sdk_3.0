'''
Created on Jun 12, 2021

@author: samerd
'''
Vendors = {
    0: 'Unknown',
    597: 'IBM',
    713: 'Mellanox',
    1107: 'Yottayotta',
    1453: 'Topspin',
    1559: 'Redswitch',
    1642: 'Silverstorm',
    2126: 'Divergenet',
    2289: 'Voltaire',
    2909: 'Fujitsu2',
    4469: 'Pathscale',
    53431: 'Intel',
    57344: 'Fujitsu',
}

DeviceID = {
    0xbd36: 'QDR',
    0xc738: 'FDR',
    0xcf08: 'EDR',
    0xcb20: 'EDR',
    0xd2f0: 'HDR',
    0xd2f2: 'NDR'
}

Mtu = {
    0: None,
    1: 256,
    2: 512,
    3: 1024,
    4: 2048,
    5: 4096,
}


def get_vendor(vendor_id):
    return Vendors.get(vendor_id, Vendors[0])


def get_device_type(dev_id):
    return DeviceID.get(dev_id, "N/A")


speeds_values = dict()

SPEED_SDR = 1
SPEED_DDR = 2
SPEED_QDR = 4
SPEED_FDR10 = 8
SPEED_FDR = 16
SPEED_EDR = 32
SPEED_HDR = 64
SPEED_NDR = 128

SPEED_VALUE_SDR = 2.5
SPEED_VALUE_DDR = 5.0
SPEED_VALUE_QDR = 10.0
SPEED_VALUE_FDR10 = 10.0
SPEED_VALUE_FDR = 14.0
SPEED_VALUE_EDR = 25.0
SPEED_VALUE_HDR = 50.0
SPEED_VALUE_NDR = 100.0

SPEED_TYPE_SDR = "SDR"
SPEED_TYPE_DDR = "DDR"
SPEED_TYPE_QDR = "QDR"
SPEED_TYPE_FDR10 = "FDR10"
SPEED_TYPE_FDR = "FDR"
SPEED_TYPE_EDR = "EDR"
SPEED_TYPE_HDR = "HDR"
SPEED_TYPE_NDR = "NDR"

speed2string = {
    SPEED_SDR: SPEED_VALUE_SDR,
    SPEED_DDR: SPEED_VALUE_DDR,
    SPEED_QDR: SPEED_VALUE_QDR,
    SPEED_FDR10: SPEED_VALUE_FDR10,
    SPEED_FDR: SPEED_VALUE_FDR,
    SPEED_EDR: SPEED_VALUE_EDR,
    SPEED_HDR: SPEED_VALUE_HDR,
    SPEED_NDR: SPEED_VALUE_NDR
}

speed2type = {
    SPEED_SDR: SPEED_TYPE_SDR,
    SPEED_DDR: SPEED_TYPE_DDR,
    SPEED_QDR: SPEED_TYPE_QDR,
    SPEED_FDR10: SPEED_TYPE_FDR10,
    SPEED_FDR: SPEED_TYPE_FDR,
    SPEED_EDR: SPEED_TYPE_EDR,
    SPEED_HDR: SPEED_TYPE_HDR,
    SPEED_NDR: SPEED_TYPE_NDR
}

speed_options = (SPEED_SDR, SPEED_DDR, SPEED_QDR, SPEED_FDR10, SPEED_FDR,
                 SPEED_EDR, SPEED_HDR, SPEED_NDR)


def get_speed_val(received_speed_val, get_val_type=True):
    """
    Return the speed value for index
    @param val  speed index
    @return  list (speed values)
    """
    if (received_speed_val, get_val_type) in speeds_values:
        return speeds_values.get((received_speed_val, get_val_type))
    speed_list = []
    if received_speed_val != 0:
        for speed_val in speed_options:
            if int(received_speed_val) & int(speed_val):
                if get_val_type:
                    speed_list.append(speed2type.get(speed_val))
                else:
                    speed_list.append(speed2string.get(speed_val))
    if not speed_list:
        speed_list.append("N/A")

    speeds_values[(received_speed_val, get_val_type)] = speed_list
    return speed_list


WidthV = {
    0: ('NoState',),
    1: ('1x',),
    2: ('4x',),
    3: ('1x', '4x',),
    4: ('8x',),
    5: ('1x', '8x',),
    6: ('4x', '8x',),
    7: ('1x', '4x', '8x',),
    8: ('12x',),
    9: ('1x', '12x',),
    10: ('4x', '12x',),
    11: ('1x', '4x', '12x',),
    12: ('8x', '12x',),
    13: ('1x', '8x', '12x',),
    14: ('4x', '8x', '12x',),
    15: ('1x', '4x', '8x', '12x',),
    16: ('2x',),
    17: ('1x', '2x',),
    18: ('2x', '4x',),
    19: ('1x', '2x', '4x',),
    20: ('2x', '8x',),
    21: ('1x', '2x', '8x',),
    22: ('2x', '4x', '8x',),
    23: ('1x', '2x', '4x', '8x',),
    24: ('2x', '12x',),
    25: ('1x', '2x', '12x',),
    26: ('2x', '4x', '12x',),
    27: ('1x', '2x', '4x', '12x',),
    28: ('2x', '8x', '12x',),
    29: ('1x', '2x', '8x', '12x',),
    30: ('2x', '4x', '8x', '12x',),
    31: ('1x', '2x', '4x', '8x', '12x',),
}


def get_width_val(width):
    return WidthV.get(int(width), WidthV[0])


# Dictionary of max transfer unit
Mtu = {
    0: "Unknown",
    1: 256,
    2: 512,
    3: 1024,
    4: 2048,
    5: 4096,
}


def get_mtu(nmtu):
    return Mtu.get(nmtu, Mtu[0])


LOGICAL_STATE_MAP = {
    1: 'Down',
    2: 'Initialize',
    3: 'Armed',
    4: 'Active', }


def get_logical_state(state):
    return LOGICAL_STATE_MAP.get(state, "N/A")


PHYSICAL_STATE_MAP = {
    1: 'Sleep',
    2: 'Polling',
    3: 'Disabled',
    4: 'Port Configuration Training',
    5: 'Link Up',
    6: 'Link Error Recovery',
    7: 'Phy Test', }


def get_physical_state(state):
    return PHYSICAL_STATE_MAP.get(state, "N/A")
