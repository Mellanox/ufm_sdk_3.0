This path holds a copy of the logic from [url](https://gitlab-master.nvidia.com/ae_networking/phy_layer_utils)

For now, we are taking only the link down logic.

The current way to run it is:
```
python3 utils/netfix/two_files_analysis_template_IB.py --earlier_file /Users/bhaim/workspace/ufm_sdk_3.0/boaz-tmp/telemetry_samples/secondary_1d_20240604055416 --latest_file /Users/bhaim/workspace/ufm_sdk_3.0/boaz-tmp/telemetry_samples/secondary_1d_20240605055518 --config utils/netfix/config/example --report bob.xls
```

This will output a csv file with one sheet of links down logic