This path holds a copy of the logic original logic

# This logic is still under development and should not be used

For now, we are taking only the link down logic (Flapping links)

The current way to run it is:
1. Install the python requirements
2. Load Python and import the function using
```
 from flapping_links import get_flapping_links
```
3. Call the function with two second telemetry samples
```
get_link_flapping(prev_second_telemetry_samples, older_second_telemetry_samples)

```

This will output a datafram with all the flapping links info