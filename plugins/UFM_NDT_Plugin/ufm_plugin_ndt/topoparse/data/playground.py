import json

if __name__ == '__main__':
    # d1 = json.load(open("pkeys.json"))
    # d2 = json.load(open("/auto/swgwork/mohammadash/sim-14-7/pkeys.json"))
    # print(d1['0x0002'])
    # print(d2['0x0002'])
    # print(len(d1['0x0002']["guids"]), len(d2['0x0002']["guids"]))
    small = {
        "active_speed": "QDR",
        "active_width": "4x",
        "capabilities": [],
        "description": "Switch IB Port",
        "dname": "1",
        "enabled_speed": [
            "SDR",
            "DDR",
            "QDR"
        ],
        "enabled_width": [
            "1x",
            "4x"
        ],
        "external_number": 1,
        "guid": "248a070300a29d74",
        "lid": 917,
        "mtu": 4096,
        "name": "248a070300a29d74_1",
        "node_description": "N/A",
        "number": 1,
        "severity": "Info",
        "supported_speed": [
            "SDR",
            "DDR",
            "QDR"
        ],
        "supported_width": [
            "1x",
            "4x"
        ]
    }

    large = {
        "active_speed": "QDR",
        "active_width": "4x",
        "capabilities": [],
        "description": "Switch IB Port",
        "dname": "1",
        "enabled_speed": [
            "SDR",
            "DDR",
            "QDR"
        ],
        "enabled_width": [
            "1x",
            "4x"
        ],
        "external_number": 1,
        "guid": "248a070300a29d74",
        "lid": 917,
        "logical_state": "N/A",
        "mtu": 4096,
        "name": "248a070300a29d74_1",
        "node_description": "mtlx-cai-ubuntu mlx5_0:1",
        "number": 1,
        "peer": "506b4b0300854600_25",
        "physical_state": "Link Up",
        "severity": "Info",
        "supported_speed": [
            "SDR",
            "DDR",
            "QDR"
        ],
        "supported_width": [
            "1x",
            "4x"
        ],
        "systemID": "248a070300a29d74",
        "system_name": "mtlx-cai-ubuntu mlx5_0",
        "tier": 4
    }

    for item in large:
        if item in small and large[item] == small[item]:
            continue
        print(item)
