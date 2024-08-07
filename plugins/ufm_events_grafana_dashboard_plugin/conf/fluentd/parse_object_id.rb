def filter(tag, time, record)
  objtype = record['object_id']
  type = record['object_type']
  case type
  when 'IBPort', 'Computer'
    # Match the object_id against the regex pattern
    match = /(?:Computer|Switch): (?<device_name>[^\/]+) \/ (?<port_num>[^]]+)\] \[dev_id: (?<device_guid>[a-f0-9]+)/.match(objtype)
    if match
      # Extract and assign the captured groups to new fields
      record['device_name'] = match[:device_name]
      record['port_num'] = match[:port_num]
      record['device_guid'] = match[:device_guid]
      # Assign the object_id to the matched part of the string
      record['object_id'] = "#{match[0].split('] [').first}"

      # Determine the device_type based on the prefix
      if match[0].start_with?('Computer')
        record['device_type'] = 'host'
      elsif match[0].start_with?('Switch')
        record['device_type'] = 'switch'
      end
    end
  when 'Site'
    record['object_id'] = 'default'
#  when 'Computer'
#    match = /(Computer.*)\] \[/.match(objtype)
#    record['object_id'] = match ? match[1] : objtype
  when 'Module'
    match = /(Switch.*)\] \[/.match(objtype)
    record['object_id'] = match ? match[1] : objtype
  when 'Link'
    match = /([a-f0-9]+\_[0-9]+)[\w ]+\: ([a-f0-9]+_[0-9]+)/.match(objtype)
    record['object_id'] = match ? "#{match[1]}:#{match[2]}" : objtype
  else
    record['object_id'] = objtype
  end


  # Extract and set event and event_details
  event = record['event']
  event_details = record['event_details']

  if event.nil? || event.empty?
    event = record['event_fallback']
    event_details = record['event_fallback']
  end

  record['event'] = event
  record['event_details'] = event_details

  # Remove the event_fallback field
  record.delete('event_fallback')

  record
end
